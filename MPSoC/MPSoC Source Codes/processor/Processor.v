`timescale 1ns / 1ps
//////////////////////////////////////////////////////////////////////////////////
// Company: 
// Engineer: 
// 
// Create Date:    16:36:57 03/27/2021 
// Design Name: 
// Module Name:    Processor 
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

module Processor(
    input clock,
	 input reset,
	 output wr_en,
	 output  [31:0] output1);
	 
      wire zero_flag;
	  wire[31:0] inst_code;
	  wire[31:0] PC;
	  wire pc_write;
	  wire if_id_write;
	  wire [31:0] if_id_pc, id_inst_code, id_ex_pc; 
	  wire [31:0] output_data1,output_data2,write_data1, write_data2;
	  wire [31:0]sign_extend, bit_extend, offset_u;
	  wire [4:0]rs1,rs2,rd,if_id_register_rs1,if_id_register_rs2,ex_mem_register_rs2;
	  wire [31:0]id_ex_output_data1,id_ex_output_data2,id_ex_sign_extend_immediate;
	  wire [4:0]id_ex_register_rs1,id_ex_register_rs2,id_ex_register_rd;
	  wire id_ex_memtoreg,id_ex_alusrc,id_ex_memread,id_ex_memwrite,id_ex_branch,id_ex_regwrite_control;
	  wire [3:0]id_ex_alu_control;
	  wire [31:0]alu_result, result_ex_mem, result_mem_wb;
	  wire [2:0]funct3;
	  wire [6:0] funct7, opcode;
	  wire [3:0] if_id_alu_control;
	  wire [10:0]control;
	  wire control_sel;
     wire if_id_regwrite_control,if_id_memtoreg,if_id_alusrc,if_id_memread,if_id_memwrite,if_id_branch,if_id_branch2,if_id_jump;
	  wire zero_flag_ex_mem;
	  wire [4:0] ex_mem_register_rd, mem_wb_register_rd;
	  wire [31:0] ex_mem_output_data_1, ex_mem_output_data_2, read_data, read_data_mem_wb;
	  wire ex_mem_memtoreg,ex_mem_regwrite,ex_mem_memread,ex_mem_memwrite,ex_mem_branch,ex_mem_jump, mem_wb_memtoreg,mem_wb_regwrite;
	  wire [1:0]FWD_RS1,FWD_RS2 ,ex_mem_FWD_RS1, ex_mem_FWD_RS2;
	  wire [31:0]in1,in2,alu_mux;
	  wire pc_src,pc_src_1, id_ex_jump,ex_mem_branch2;
	  wire [31:0] next_address_branch, input_to_ifu, ex_mem_next_address_branch, next_address;
	  wire enable;
	  //wire [31:0]alu_result;
   // wire [31:0]mul_result;
    wire [31:0] result;
    wire IF_Flush;
	 wire [31:0] B_addr, J_addr;
	 wire [1:0] PCsrc;
	// assign J_addr = 32'h04;
	  //assign if_id_write = 1;
	 
	  
	  
	  IFU Instruction_fetch_module(clock, reset,pc_write,input_to_ifu, inst_code,PC);
	  
	 
	  if_id IF_ID_register(reset,clock, if_id_write, IF_Flush,inst_code, PC, if_id_pc,id_inst_code,if_id_register_rs1,if_id_register_rs2);
	  
	   stall_unit s( id_ex_memread,if_id_register_rs1,if_id_register_rs2,id_ex_register_rd,
	    pc_write,if_id_write,control_sel );
	  
	  Decoder decoder_module(id_inst_code,mem_wb_register_rd, output_data1, output_data2, clock, reset, 
									 write_data1, sign_extend, mem_wb_regwrite,rs1,rs2,rd,funct3,funct7,opcode);
			
	  control control_module(funct7,funct3,opcode, control_sel,if_id_alu_control,
				 control,enable, if_id_regwrite_control,if_id_memtoreg,if_id_alusrc,if_id_memread,if_id_memwrite,if_id_branch,if_id_branch2,if_id_jump);
		
	  id_ex ID_EX_register(rs1,rs2,rd,output_data1, output_data2, sign_extend, clock, control, if_id_pc,enable,if_id_jump,
			id_ex_output_data1,id_ex_output_data2,id_ex_sign_extend_immediate,
			id_ex_register_rs1,id_ex_register_rs2,id_ex_register_rd,
			id_ex_memtoreg,id_ex_alusrc,id_ex_memread,id_ex_memwrite,id_ex_branch,id_ex_regwrite_control,id_ex_jump,
			id_ex_alu_control,id_ex_pc,id_ex_enable,if_id_branch2,id_ex_branch2);
			
	  forwarding_unit forwarding_module(id_ex_register_rs1,id_ex_register_rs2,ex_mem_register_rd, mem_wb_register_rd,ex_mem_regwrite,mem_wb_regwrite,
	  ex_mem_memwrite,ex_mem_register_rs2,FWD_RS1,FWD_RS2);
	  
	  mux3 m1(FWD_RS1,id_ex_output_data1,result_ex_mem,write_data1,in1);
	  
	  mux3 m2(FWD_RS2,id_ex_output_data2,result_ex_mem,write_data1,alu_mux);	//take alu_mux as the output of second mux3 to feed it to mux just before alu
	  
	  new_mux m3(id_ex_alusrc,alu_mux,id_ex_sign_extend_immediate,in2);
	  
	  adder Adder_module_branch(id_ex_pc, id_ex_sign_extend_immediate, next_address_branch);
	  
	  adder Adder_module(PC, 4, next_address); 
	  
	  //ALU ALU_module(in1, in2, id_ex_alu_control, alu_result, zero_flag);
	  execution_unit e(in1,in2, id_ex_enable, id_ex_alu_control, result,zero_flag);
	  
	  // mux1 m0( alu_result, mul_result, enable,result);
	  
	 // pc_src Pc_src_control(ex_mem_jump, ex_mem_branch,ex_mem_branch2,zero_flag, pc_src_1);
	  Address_select  a1( inst_code, IF_Flush,PC,J_addr,PCsrc);
	 // new_mux address_mux(pc_src_1, next_address, next_address_branch, input_to_ifu);
	 MuxPC address_mux( next_address,B_addr, J_addr,PCsrc,input_to_ifu);
		
	  ex_mem EX_MEM_register(clock, zero_flag, zero_flag_ex_mem,id_ex_register_rs2, ex_mem_register_rs2, id_ex_register_rd, ex_mem_register_rd, result, 
	  result_ex_mem,id_ex_output_data2,ex_mem_output_data_2, id_ex_memtoreg,id_ex_regwrite_control,id_ex_memread,id_ex_memwrite,id_ex_branch,
	  ex_mem_memtoreg,ex_mem_regwrite,ex_mem_memread,ex_mem_memwrite,ex_mem_branch,ex_mem_next_address_branch, next_address_branch,
	  id_ex_enable,
	   ex_mem_enable,id_ex_jump,ex_mem_jump,id_ex_output_data1,ex_mem_output_data_1,FWD_RS1,FWD_RS2, ex_mem_FWD_RS1, ex_mem_FWD_RS2,
	    id_ex_branch2, ex_mem_branch2);
	  
	  Data_mem Data_memory_module(result_ex_mem, write_data2, ex_mem_memwrite, ex_mem_memread, clock, read_data,wr_en,
	   output1);
	  
	  mem_wb MEM_WB_register(clock, ex_mem_register_rd, mem_wb_register_rd, result_ex_mem, result_mem_wb ,read_data, read_data_mem_wb, ex_mem_memtoreg, ex_mem_regwrite, mem_wb_memtoreg,mem_wb_regwrite );
	  
	  mem_wb_mux Multiplexer_module(ex_mem_FWD_RS2,ex_mem_memwrite,ex_mem_output_data_2,mem_wb_memtoreg, read_data, result_mem_wb,write_data1,write_data2);
	  
	  Branch_comparator b (output_data1,output_data2,opcode,funct3,IF_Flush);
	  
	  Branch_Cal b2 (if_id_pc,sign_extend,B_addr );
	  

endmodule