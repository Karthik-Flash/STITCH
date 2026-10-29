`timescale 1ns / 1ps























module IFU(
	input clock,
	input reset,
	input pc_write,
	input [31:0] next_pc,
	output [31:0]inst_code,
	output reg [31:0]PC
    );
	 
	 wire [31:0] inst_address;
	 
	 
	 
	 
	 address_fetch fetch_add_unit(next_pc, inst_address, clock,reset);
	 Inst_mem_integrated inst_mem_unit(reset,inst_address, inst_code);
	 
	 always@(*)
   begin
   if (reset==1)
   PC=-4;
   else
   begin
   if (pc_write==0)
   PC=PC;
   else
   PC=inst_address;
  end 
   end
	 


endmodule
