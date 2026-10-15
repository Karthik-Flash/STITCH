`timescale 1ns / 1ps



















 module mem_wb(clk,ex_mem_register_rd,mem_wb_register_rd, result_ex_mem,result_mem_wb,read_data,read_data_mem_wb,	ex_mem_memtoreg,ex_mem_regwrite, mem_wb_memtoreg,mem_wb_regwrite);
	
	input clk;
	input wire 	ex_mem_memtoreg,ex_mem_regwrite;
	input wire [4:0] ex_mem_register_rd;
	
	input wire [31:0] result_ex_mem;
	input wire [31:0] read_data;
	output reg [4:0] mem_wb_register_rd;
	output reg [31:0] result_mem_wb;
	output reg [31:0] read_data_mem_wb;
	output reg  mem_wb_memtoreg,mem_wb_regwrite;
	
	always @(posedge clk)
	begin
	mem_wb_register_rd= ex_mem_register_rd;
	result_mem_wb= result_ex_mem;
	read_data_mem_wb= read_data;
	mem_wb_memtoreg=ex_mem_memtoreg;
   mem_wb_regwrite= ex_mem_regwrite;	 
	end
  


endmodule