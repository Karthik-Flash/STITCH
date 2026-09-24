`timescale 1ns / 1ps
module tb;
  reg clk, clr, ce; reg [3:0] din, exp; wire [3:0] dout; integer i, err;
  register_4bit dut(din, clk, clr, ce, dout);
  always #5 clk = ~clk;
  initial begin
    err = 0; clk = 0; clr = 1; ce = 0; din = 0;
    @(posedge clk); #1; exp = 4'b0000;
    if (dout !== exp) begin err = err + 1; $display("FAIL clear"); end
    for (i = 0; i < 200; i = i + 1) begin
      @(negedge clk); clr = (i % 17 == 0); ce = $random; din = $random;
      #2 din = $random;                                    // change din mid-cycle: must NOT pass through
      #1 if (dout !== exp) begin err = err + 1; $display("FAIL transparent between edges i=%0d", i); end
      @(posedge clk); #1;
      if (clr) exp = 4'b0000; else if (ce) exp = din;
      if (dout !== exp) begin err = err + 1; $display("FAIL edge i=%0d dout=%h exp=%h", i, dout, exp); end
    end
    if (err == 0) $display("ALL TESTS PASSED"); else $display("FAIL: %0d errors", err);
    $finish;
  end
endmodule
