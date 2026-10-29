`timescale 1ns / 1ps
module execute_mux(input [31:0] alu_result,
input [31:0] mul_result,
input id_ex_enable,
output reg [31:0] result);

always @(*) begin
	if(id_ex_enable == 1)
	result= alu_result;
	else if(id_ex_enable == 0)
	result = mul_result;
	end
endmodule
