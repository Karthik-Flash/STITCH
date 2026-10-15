`timescale 1ns / 1ps





















module execute(input [31:0] in1,in2, 
input id_ex_enable,
input[3:0] id_ex_alu_control,

output  [31:0] alu_result,
output  [31:0] mul_result,
    output  zero_flag
    );
    
alu a (in1,in2,id_ex_enable,id_ex_alu_control,alu_result,zero_flag);
multiply m(in1,in2,id_ex_enable,id_ex_alu_control,mul_result);
endmodule



