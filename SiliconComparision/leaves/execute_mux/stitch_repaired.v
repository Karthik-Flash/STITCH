module execute_mux(input [31:0] alu_result,
input [31:0] mul_result,
input id_ex_enable,
output reg [31:0] result);

always @(*) begin
	if(id_ex_enable)
		result = alu_result;
	else
		result = mul_result;
end
endmodule
