`timescale 1ns/1ps
// Galois LFSR  x^8+x^6+x^5+x^4+1
// Update rule (right-shift, feedback=lfsr[0]):
//   next = {fb, lfsr[7], lfsr[6], lfsr[5]^fb, lfsr[4]^fb, lfsr[3]^fb, lfsr[2], lfsr[1]}
// From 8'hFF: step1 = 8'hE3
// From 8'hAB: step1 = 8'hC9,  step2 = 8'hF8
module lfsr_8bit_tb;
  reg clk = 0, rst = 1, load = 0, enable = 0;
  reg [7:0] seed;
  wire [7:0] lfsr_out;
  integer fail = 0;

  lfsr_8bit uut (.clk(clk), .rst(rst), .load(load), .enable(enable),
                 .seed(seed), .lfsr_out(lfsr_out));

  always #5 clk = ~clk;

  task check;
    input [7:0] expected;
    input [63:0] label;
    begin
      @(negedge clk);
      if (lfsr_out !== expected) begin
        $display("FAIL [%s]: expected 8'h%h got 8'h%h", label, expected, lfsr_out);
        fail = fail + 1;
      end
    end
  endtask

  initial begin
    // ── 1. Reset ──────────────────────────────────────────────────────────
    rst = 1; load = 0; enable = 0; seed = 8'h00;
    @(negedge clk);
    if (lfsr_out !== 8'hFF) begin
      $display("FAIL [reset]: expected 8'hFF got 8'h%h", lfsr_out); fail = fail + 1;
    end
    @(negedge clk); // hold reset another cycle
    if (lfsr_out !== 8'hFF) begin
      $display("FAIL [reset hold]: expected 8'hFF got 8'h%h", lfsr_out); fail = fail + 1;
    end

    // ── 2. Load seed 8'hFF, then step once ────────────────────────────────
    @(negedge clk); rst = 0; load = 1; seed = 8'hFF;
    @(negedge clk); // posedge latches load=1 → lfsr=8'hFF
    if (lfsr_out !== 8'hFF) begin
      $display("FAIL [load FF]: expected 8'hFF got 8'h%h", lfsr_out); fail = fail + 1;
    end
    // Step: from 8'hFF → 8'hE3
    @(negedge clk); load = 0; enable = 1;
    @(negedge clk); // one enable step
    if (lfsr_out !== 8'hE3) begin
      $display("FAIL [FF step1]: expected 8'hE3 got 8'h%h", lfsr_out); fail = fail + 1;
    end

    // ── 3. Load seed 8'hAB, step twice ────────────────────────────────────
    @(negedge clk); enable = 0; load = 1; seed = 8'hAB;
    @(negedge clk); // latched → 8'hAB
    if (lfsr_out !== 8'hAB) begin
      $display("FAIL [load AB]: expected 8'hAB got 8'h%h", lfsr_out); fail = fail + 1;
    end
    // Step 1: 8'hAB → 8'hC9
    @(negedge clk); load = 0; enable = 1;
    @(negedge clk);
    if (lfsr_out !== 8'hC9) begin
      $display("FAIL [AB step1]: expected 8'hC9 got 8'h%h", lfsr_out); fail = fail + 1;
    end
    // Step 2: 8'hC9 → 8'hF8
    @(negedge clk);
    if (lfsr_out !== 8'hF8) begin
      $display("FAIL [AB step2]: expected 8'hF8 got 8'h%h", lfsr_out); fail = fail + 1;
    end

    // ── 4. Enable=0 → hold value ──────────────────────────────────────────
    @(negedge clk); enable = 0;
    @(negedge clk);
    if (lfsr_out !== 8'hF8) begin
      $display("FAIL [hold]: value changed when enable=0 (got 8'h%h)", lfsr_out); fail = fail + 1;
    end
    @(negedge clk);
    if (lfsr_out !== 8'hF8) begin
      $display("FAIL [hold2]: value changed when enable=0 (got 8'h%h)", lfsr_out); fail = fail + 1;
    end

    // ── 5. LFSR never stuck at zero (check 8 steps from non-zero seed) ───
    @(negedge clk); load = 1; seed = 8'hA5; enable = 0;
    @(negedge clk); load = 0; enable = 1;
    begin : nozero_check
      integer k;
      for (k = 0; k < 8; k = k + 1) begin
        @(negedge clk);
        if (lfsr_out === 8'h00) begin
          $display("FAIL [nozero]: LFSR reached all-zero state at step %0d", k); fail = fail + 1;
        end
      end
    end

    if (fail == 0) $display("ALL TESTS PASSED");
    $finish;
  end
endmodule
