`timescale 1ns / 1ps



















module if_id(
	input reset, clk,if_id_write,IF_Flush,
	input wire[31:0]if_Instruction_Code,
	input wire[31:0]if_pc,
	output reg [31:0]id_pc,
	output reg [31:0]id_Instruction_Code,
	output reg [4:0]if_id_register_rs1,
	output reg [4:0]if_id_register_rs2);

always @(posedge clk) begin
    if (reset ==1)
    begin 
    id_Instruction_Code <= 0;
    if_id_register_rs1 <= id_Instruction_Code[19:15];
    if_id_register_rs2 <= id_Instruction_Code[24:20];
    end  
    else 
    if ( IF_Flush ==1) 
    begin
     id_pc=if_pc;
    id_Instruction_Code <= 32'h0;
    if_id_register_rs1 <= id_Instruction_Code[19:15];
	if_id_register_rs2 <= id_Instruction_Code[24:20];
    end 
    else if  ( if_id_write ==0) 
    begin
    id_pc=32'b0;
    id_Instruction_Code <= 32'h0;
    if_id_register_rs1 <= id_Instruction_Code[19:15];
	if_id_register_rs2 <= id_Instruction_Code[24:20]; 
	end
	else begin
            id_pc=if_pc;
			id_Instruction_Code<=if_Instruction_Code;
			if_id_register_rs1 <= id_Instruction_Code[19:15];
			if_id_register_rs2 <= id_Instruction_Code[24:20];
    end
    
    end
    endmodule
    
    
    
    
    





























