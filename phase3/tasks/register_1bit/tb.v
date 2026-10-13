`timescale 1ns / 1ps
module tb;
  reg clk, reset, clr, ce, din, exp; wire dout; integer i, err;
  register_1bit dut(din, reset, clk, clr, ce, dout);
  always #5 clk = ~clk;
  initial begin
    err = 0; clk = 0; reset = 0; clr = 0; ce = 1; din = 1;
    @(posedge clk); #1; exp = 1; if (dout !== exp) begin err = err + 1; $display("FAIL load"); end
    #2 reset = 1; #1; exp = 0; if (dout !== 0) begin err = err + 1; $display("FAIL async reset"); end
    #3 reset = 0;
    for (i = 0; i < 200; i = i + 1) begin
      @(negedge clk); clr = (i % 11 == 0); ce = $random; din = $random;
      @(posedge clk); #1;
      if (clr) exp = 0; else if (ce) exp = din;
      if (dout !== exp) begin err = err + 1; $display("FAIL i=%0d", i); end
    end
    if (err == 0) $display("ALL TESTS PASSED"); else $display("FAIL: %0d errors", err);
    $finish;
  end
endmodule
