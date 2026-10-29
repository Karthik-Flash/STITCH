`timescale 1ns / 1ps
module noc_xbar4(input [3:0] gnt, input [31:0] in0, input [31:0] in1, input [31:0] in2, input [31:0] in3,
                 output [31:0] out_data, output out_valid);
  assign out_data = (in0 & {32{gnt[0]}}) | (in1 & {32{gnt[1]}}) | (in2 & {32{gnt[2]}}) | (in3 & {32{gnt[3]}});
  assign out_valid = |gnt;
endmodule
