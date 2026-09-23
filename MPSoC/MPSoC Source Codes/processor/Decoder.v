`timescale 1ns / 1ps
//////////////////////////////////////////////////////////////////////////////////
// Company: 
// Engineer: 
// 
// Create Date:    16:24:30 03/27/2021 
// Design Name: 
// Module Name:    Decoder 
// Project Name: 
// Target Devices: 
// Tool versions: 
// Description: 
//
// Dependencies: 
//
// Revision: 
// Revision 0.01 - File Created
// Additional Comments: 
//
//////////////////////////////////////////////////////////////////////////////////
module Decoder(input_instr, write_reg, output_data_1,output_data_2,clock,reset,write_data,sign_extend,regwrite,rs1,rs2,rd,funct3,funct7,opcode);
		
	input [31:0] input_instr; // 32 bit instruction code input from instruction fetch stage
	input clock;
	input reset;
	input regwrite;

	input [31:0] write_data; // 32 bit result coming from ALU or Data Memory
	
	input [4:0] write_reg;
   output [31:0] sign_extend;
	reg [31:0] sign_extend;
   output reg [31:0] output_data_1; // 32 bit output from from decoder going as input to ALU

	
	
	output [31:0] output_data_2; // 32 bit output from from decoder going as input to ALU
	reg [31:0] output_data_2; // 32 bit output from from decoder going as input to ALU
	reg [31:0] register_risc [31:0]; //32 memory locations created each of lenth 32 bits
	output wire [4:0] rs1;
	output wire [4:0] rs2;
	output wire [4:0] rd;
	output wire [2:0] funct3;
	output wire [6:0] funct7;
	output wire [6:0] opcode;
	wire [11:0] Immediate3;
	wire [11:0] Shift2;
	wire [31:0] SgnEx;
	assign rs1=input_instr[19:15];
	assign rs2=input_instr[24:20];
	assign rd =input_instr[11:7];
	assign opcode=input_instr[6:0];
	assign funct3=input_instr[14:12];
	assign funct7=input_instr[31:25];
	assign Immediate3={input_instr[31],input_instr[7],input_instr[30:25],input_instr[11:8]};
	assign Shift2 = Immediate3<<2;
	assign SgnEx ={{20{Shift2[11]}},Shift2};
	
	
	
	
	
	always @(posedge clock) begin
	if(reset == 1)
	begin
	register_risc[0]=32'd0;
	register_risc[1]=32'd2;
	register_risc[2]=32'd4;
	register_risc[3]=32'd3;
	register_risc[4]=32'd4;
	register_risc[5]=32'd6; //t0
	register_risc[6]=32'd1; //t1
	register_risc[7]=32'd2;
	register_risc[8]=32'd1; //s0
	register_risc[9]=32'd10; //s1
	register_risc[10]=32'd10;
	register_risc[11]=32'd11;
	register_risc[12]=32'd12;
	register_risc[13]=32'd13;
	register_risc[14]=32'd14;
	register_risc[15]=32'd15;
	register_risc[16]=32'd16;
	register_risc[17]=32'd17;
	register_risc[18]=32'd18;
	register_risc[19]=32'd19;
	register_risc[20]=32'd20;
	register_risc[21]=32'd21;
	register_risc[22]=32'd22;
	register_risc[23]=32'd23;
	register_risc[24]=32'd24;
	register_risc[25]=32'd25;
	register_risc[26]=32'd26;
	register_risc[27]=32'd27;
	register_risc[28]=32'd28;
	register_risc[29]=32'd29;
	register_risc[30]=32'd30;
	register_risc[31]=32'd31;
	end
	end
	
	always @(*) begin 
	
	if(reset == 0)
	begin
		output_data_1=register_risc[rs1];
		output_data_2=register_risc[rs2];
		if(regwrite)
		register_risc[write_reg]=write_data;
		else
		register_risc[write_reg]=register_risc[write_reg];
	end
	/*
	case(input_instr[6:0])
	 7'b1100111:sign_extend={{20{input_instr[31]}},input_instr[31:20]}; // JALR instruction
	 7'b0010011:sign_extend={{20{input_instr[31]}},input_instr[31:20]}; // I type
	 7'b0100011:sign_extend={{20{input_instr[31]}},input_instr[31:25],input_instr[11:7]}; // store instructions
	 7'b1101111:sign_extend={{19{input_instr[31]}},input_instr[31],input_instr[7],input_instr[30:25],input_instr[11:8],1'b0}; //  JAL instruction
	 7'b1100011:sign_extend={{19{input_instr[31]}},input_instr[31],input_instr[11],input_instr[30:25],input_instr[10:7],1'b0}; // conditional branch jump instructions
	 7'b0110111:sign_extend={input_instr[31:12],{12{1'b0}}}; // offset for lui 
	 7'b0010111:sign_extend={input_instr[31:12],{12{1'b0}}}; // offset for auipc
	 default: sign_extend=32'h0;
	endcase
	*/
	case(input_instr[6:0])
	 7'b1100111: sign_extend={{20{input_instr[31]}},input_instr[31:20]}; // JALR instruction
	 7'b0010011: sign_extend={{20{input_instr[31]}},input_instr[31:20]}; // I type
	 7'b0100011:sign_extend={{20{input_instr[31]}},input_instr[31:25],input_instr[11:7]}; // store instructions
	 7'b0000011:sign_extend={{20{input_instr[31]}},input_instr[31:20]}; //load
	 7'b1100011: sign_extend=SgnEx; //conditional branch
	 //7'b1100011: sign_extend={{19{input_instr[31]}},input_instr[31],input_instr[7],input_instr[30:25],input_instr[11:8],1'b0}; // conditional branch
	 7'b1101111: sign_extend={{11{input_instr[31]}},input_instr[31],input_instr[19:12],input_instr[20],input_instr[30:21],1'b0}; // JAL
	 7'b0110111: sign_extend={input_instr[31:12],{12{1'b0}}}; // offset for lui 
	 7'b0010111: sign_extend={input_instr[31:12],{12{1'b0}}}; // offset for auipc
	 default: sign_extend=32'h0;
	endcase
end

	

endmodule