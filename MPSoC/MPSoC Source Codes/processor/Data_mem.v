`timescale 1ns / 1ps
//////////////////////////////////////////////////////////////////////////////////
// Company: 
// Engineer: 
// 
// Create Date:    16:41:50 03/27/2021 
// Design Name: 
// Module Name:    Data_mem 
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
module Data_mem (
	input wire [31:0] addr,          // Memory Address
	input wire [31:0] write_data,    // Memory Address Contents
	input wire memwrite, memread,
	input wire clk,                  // clock
	output reg [31:0] read_data ,
	output reg wr_en, // Output of Memory Address Contents
	output   [31:0] output1
	
);

reg [31:0] MEM[0:255];  // 256 words of 32-bit memory

integer i;

initial begin
  //read_data = 0;
  for (i = 0; i < 256; i = i + 1) begin
    MEM[i] = i;
  end
  
  MEM[0] = 32'd10; //s0
  MEM[1] = 32'd32;
  MEM[2] = 32'd20;
   MEM[3] = 32'd12;
    MEM[4] = 32'd45;
     MEM[5] = 32'd56;
      MEM[6] = 32'd21;
       MEM[7] = 32'd67;
        MEM[8] = 32'd10;
         MEM[9] = 32'd67;
         MEM[10] = 32'd70;
end

assign output1 = MEM[10];
always @(posedge clk)
begin
if(MEM[10]!=32'd70)
wr_en=1;
end
always @(posedge clk) begin
  if (memwrite == 1'b1) begin
    MEM[addr] = write_data;
  end
  
  if (memread == 1'b1) begin
    read_data = MEM[addr];
  end
end

endmodule
