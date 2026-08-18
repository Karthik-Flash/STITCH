`timescale 1ns/1ps
module counter_4bit_tb;
  reg  clk = 0, rst = 1;
  wire [3:0] count;
  integer fail = 0;
  integer i;

  counter_4bit uut (.clk(clk), .rst(rst), .count(count));

  always #5 clk = ~clk;

  initial begin
    // Reset — count must be 0
    rst = 1;
    @(negedge clk);
    if (count !== 4'd0) begin
      $display("FAIL: after reset, count=%0d (expected 0)", count); fail = fail + 1;
    end
    @(negedge clk);
    if (count !== 4'd0) begin
      $display("FAIL: count changed while rst=1 (got %0d)", count); fail = fail + 1;
    end

    // Release reset and count 0..15 then wrap back to 0
    @(negedge clk); rst = 0;
    // count should be 0 on the first cycle after rst deasserts (or increment starts)
    // After rst=0 seen at posedge, count increments. At negedge: count=1.
    for (i = 1; i <= 16; i = i + 1) begin
      @(negedge clk);
      if (count !== (i % 16)) begin
        $display("FAIL: expected count=%0d got %0d (cycle %0d)", i % 16, count, i);
        fail = fail + 1;
      end
    end

    // Apply reset mid-count — count must return to 0
    @(negedge clk); rst = 1;
    @(negedge clk);
    if (count !== 4'd0) begin
      $display("FAIL: mid-run reset: count=%0d (expected 0)", count); fail = fail + 1;
    end

    if (fail == 0) $display("ALL TESTS PASSED");
    $finish;
  end
endmodule
