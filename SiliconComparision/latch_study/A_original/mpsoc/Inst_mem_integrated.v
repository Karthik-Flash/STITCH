`timescale 1ns / 1ps





















module Inst_mem_integrated(
input reset,
input [31:0] inst_add,
output [31:0] inst_code
);




wire [31:0]inst_code1;



inst_mem inst_mem_mod(inst_add, reset,  inst_code1);
assign inst_code = inst_code1;

endmodule