`timescale 1ns / 1ps



















module adder(
input [31:0] current_pc,
input [31:0] imm_val, 
output [31:0] next_address
);

	assign next_address = current_pc + imm_val;

endmodule