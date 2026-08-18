`timescale 1ns/1ps
// Mealy FSM detecting sequence 1011.
// detected = (state==S3) & in  — combinational output.
// After detecting 1011, the trailing '1' is reused (overlapping).
module fsm_seq_detector_tb;
  reg  clk = 0, rst = 1, in;
  wire detected;
  integer fail = 0;

  fsm_seq_detector uut (.clk(clk), .rst(rst), .in(in), .detected(detected));

  always #5 clk = ~clk;

  // Apply input BEFORE posedge, check detected BEFORE posedge (combinational).
  // We set 'in' at negedge, then check detected just before the next posedge.
  task apply_and_check;
    input bit_in;
    input expected_det;
    begin
      @(negedge clk); in = bit_in;   // set input
      #3;                             // settle combinational output
      if (detected !== expected_det) begin
        $display("FAIL: in=%b  expected detected=%b  got detected=%b (at time %0t)",
                 bit_in, expected_det, detected, $time);
        fail = fail + 1;
      end
      // posedge clk advances state
    end
  endtask

  initial begin
    in = 0;
    // ── Reset ──────────────────────────────────────────────────────────────
    rst = 1;
    @(negedge clk); @(negedge clk);
    @(negedge clk); rst = 0;

    // ── Test 1: sequence 1-0-1-1 → detect on 4th bit ─────────────────────
    apply_and_check(1'b1, 1'b0); // S0→S1, detected=0
    apply_and_check(1'b0, 1'b0); // S1→S2, detected=0
    apply_and_check(1'b1, 1'b0); // S2→S3, detected=0
    apply_and_check(1'b1, 1'b1); // S3+in=1 → detected=1, next→S1
    @(posedge clk); // latch the state transition

    // ── Test 2: overlapping — after 1011, FSM is in S1 (from trailing 1).
    // Feed 0-1-1 to get second detection (1_011 overlapping).
    apply_and_check(1'b0, 1'b0); // S1→S2
    apply_and_check(1'b1, 1'b0); // S2→S3
    apply_and_check(1'b1, 1'b1); // detected again (overlapping 1011)
    @(posedge clk);

    // ── Test 3: no detection on 1-0-1-0 ─────────────────────────────────
    // Reset first
    @(negedge clk); rst = 1;
    @(negedge clk); rst = 0;
    apply_and_check(1'b1, 1'b0); // S0→S1
    apply_and_check(1'b0, 1'b0); // S1→S2
    apply_and_check(1'b1, 1'b0); // S2→S3
    apply_and_check(1'b0, 1'b0); // S3+in=0 → detected=0, →S2
    @(posedge clk);

    // ── Test 4: reset clears state ──────────────────────────────────────
    apply_and_check(1'b1, 1'b0);
    apply_and_check(1'b0, 1'b0);
    @(negedge clk); rst = 1;   // reset mid-sequence
    @(negedge clk); rst = 0;
    // Should be in S0 now — 1-0-1-1 from scratch
    apply_and_check(1'b1, 1'b0);
    apply_and_check(1'b0, 1'b0);
    apply_and_check(1'b1, 1'b0);
    apply_and_check(1'b1, 1'b1); // detected
    @(posedge clk);

    if (fail == 0) $display("ALL TESTS PASSED");
    $finish;
  end
endmodule
