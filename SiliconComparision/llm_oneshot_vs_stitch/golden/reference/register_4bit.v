`timescale 1ns / 1ps
module register_4bit(din, clk, clr, ce, dout);
  input [3:0] din; input clk; input clr; input ce;
  output reg [3:0] dout;
  always @(posedge clk) begin
    if (clr)     dout <= 4'b0000;
    else if (ce) dout <= din;
  end
endmodule
