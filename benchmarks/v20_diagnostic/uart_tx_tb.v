`timescale 1ns/1ps
// Overrides BAUD_DIV=4 for fast simulation.
// Frame: start(0) + 8 data bits LSB-first + stop(1).
// Each bit = BAUD_DIV=4 clock cycles.
// Sampling strategy:
//   - After start seen at posedge t0, state→START. tx_out=0 from t0 onwards (registered).
//   - Start bit: t0..t3 (4 cycles).  Data bit N: t(4+N*4)..t(4+N*4+3).
//   - We sample at negedge of first cycle of each bit period.
module uart_tx_tb;
  localparam BAUD = 4;

  reg        clk = 0, rst = 1, start = 0;
  reg  [7:0] data_in;
  wire       tx_out, busy, done;
  integer fail = 0;

  uart_tx #(.BAUD_DIV(BAUD)) uut (
    .clk(clk), .rst(rst), .start(start),
    .data_in(data_in), .tx_out(tx_out), .busy(busy), .done(done)
  );

  always #5 clk = ~clk;

  // Send one byte and verify the entire frame.
  // Call from negedge. Returns after done has been seen.
  task send_and_verify;
    input [7:0] byte_val;
    integer i;
    reg [7:0] captured;
    begin
      captured = 8'hxx;

      // Assert start at negedge, seen at next posedge
      @(negedge clk); start = 1; data_in = byte_val;
      @(posedge clk);             // t0: FSM latches start → START state
      @(negedge clk); start = 0;

      // At this negedge (after t0): busy=1, tx_out=0 (start bit begins)
      if (!busy) begin
        $display("FAIL [%h]: busy not asserted after start", byte_val); fail = fail + 1;
      end
      if (tx_out !== 1'b0) begin
        $display("FAIL [%h]: start bit should be 0, got %b", byte_val, tx_out); fail = fail + 1;
      end

      // Advance BAUD cycles to first data bit, sample each at negedge of bit start
      for (i = 0; i < 8; i = i + 1) begin
        repeat(BAUD) @(posedge clk);
        @(negedge clk);
        captured[i] = tx_out;  // LSB-first
      end

      // Check captured byte matches sent byte
      if (captured !== byte_val) begin
        $display("FAIL [%h]: sent 8'h%h  captured 8'h%h  (bits wrong)",
                 byte_val, byte_val, captured);
        fail = fail + 1;
      end

      // Check stop bit
      repeat(BAUD) @(posedge clk);
      @(negedge clk);
      if (tx_out !== 1'b1) begin
        $display("FAIL [%h]: stop bit should be 1, got %b", byte_val, tx_out); fail = fail + 1;
      end

      // Wait for done pulse + return to idle (allow BAUD+2 cycles)
      repeat(BAUD + 2) @(posedge clk);
      @(negedge clk);
      if (busy) begin
        $display("FAIL [%h]: busy still high after done", byte_val); fail = fail + 1;
      end
      if (tx_out !== 1'b1) begin
        $display("FAIL [%h]: tx_out not idle-high after done, got %b", byte_val, tx_out); fail = fail + 1;
      end
    end
  endtask

  initial begin
    rst = 1; start = 0; data_in = 8'h00;
    repeat(4) @(posedge clk);
    @(negedge clk); rst = 0;
    repeat(2) @(posedge clk);

    // Verify tx_out is idle-high before any transmission
    @(negedge clk);
    if (tx_out !== 1'b1) begin
      $display("FAIL: tx_out not idle-high (got %b)", tx_out); fail = fail + 1;
    end

    // ── Test 1: send 8'hA5 = 10100101, LSB-first: 1,0,1,0,0,1,0,1 ───────
    send_and_verify(8'hA5);

    // ── Test 2: send 8'h3C = 00111100, LSB-first: 0,0,1,1,1,1,0,0 ───────
    send_and_verify(8'h3C);

    // ── Test 3: send 8'hFF (all 1s data) ─────────────────────────────────
    send_and_verify(8'hFF);

    // ── Test 4: send 8'h00 (all 0s data) ─────────────────────────────────
    send_and_verify(8'h00);

    if (fail == 0) $display("ALL TESTS PASSED");
    $finish;
  end
endmodule
