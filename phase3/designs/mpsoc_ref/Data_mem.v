`timescale 1ns / 1ps



















module Data_mem (
	input wire [31:0] addr,          
	input wire [31:0] write_data,    
	input wire memwrite, memread,
	input wire clk,                  
	output reg [31:0] read_data ,
	output reg wr_en, 
	output   [31:0] output1
	
);

reg [31:0] MEM[0:255];  

integer i;

initial begin
  
  for (i = 0; i < 256; i = i + 1) begin
    MEM[i] = i;
  end
  
  MEM[0] = 32'd10; 
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
