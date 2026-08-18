`timescale 1ns/1ps
module dff_sync_reset_tb;
  reg  clk = 0, rst = 1, d = 0;
  wire q;
  integer fail = 0;

  dff_sync_reset uut (.clk(clk), .rst(rst), .d(d), .q(q));

  always #5 clk = ~clk;

  // Check q at negedge (after posedge has settled)
  task check_q;
    input expected;
    begin
      @(negedge clk);
      if (q !== expected) begin
        $display("FAIL: expected q=%b got q=%b (rst=%b d=%b)", expected, q, rst, d);
        fail = fail + 1;
      end
    end
  endtask

  initial begin
    // Hold reset for 3 cycles — q should stay 0
    rst = 1; d = 1;
    check_q(1'b0); // rst=1, q must be 0 regardless of d
    check_q(1'b0);
    check_q(1'b0);

    // Release reset, d=1 → q should become 1
    @(negedge clk); rst = 0; d = 1;
    check_q(1'b1);

    // d=0 → q should become 0
    @(negedge clk); d = 0;
    check_q(1'b0);

    // d=1 again
    @(negedge clk); d = 1;
    check_q(1'b1);

    // Synchronous reset while d=1 — q must return to 0
    @(negedge clk); rst = 1; d = 1;
    check_q(1'b0); // synchronous reset takes effect on next posedge

    // Release reset, d=0
    @(negedge clk); rst = 0; d = 0;
    check_q(1'b0);

    if (fail == 0) $display("ALL TESTS PASSED");
    $finish;
  end
endmodule
