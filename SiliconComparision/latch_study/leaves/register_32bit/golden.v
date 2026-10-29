`timescale 1ns / 1ps
module register_32bit(din, clk, clr, ce, dout);
  input [31:0] din; input clk; input clr; input ce;
  output reg [31:0] dout;
  always @(posedge clk) begin
    if (clr)     dout <= 32'h60000000;
    else if (ce) dout <= din;
  end
endmodule
