`timescale 1ns / 1ps





















module execution_unit(input [31:0] in1,in2, 
input id_ex_enable,
input[3:0] id_ex_alu_control,

output  [31:0] result,
    output  zero_flag
    );
    wire [31:0] alu_result;
    wire [31:0] mul_result;
  execute e2(in1,in2,id_ex_enable,id_ex_alu_control,alu_result,mul_result,zero_flag);
  execute_mux m11( alu_result, mul_result, id_ex_enable, result);
   
endmodule

