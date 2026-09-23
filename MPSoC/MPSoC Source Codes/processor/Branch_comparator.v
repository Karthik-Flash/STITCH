`timescale 1ns / 1ps
//////////////////////////////////////////////////////////////////////////////////
// Company: 
// Engineer: 
// 
// Create Date: 28.05.2021 18:20:31
// Design Name: 
// Module Name: Branch_comparator
// Project Name: 
// Target Devices: 
// Tool Versions: 
// Description: 
// 
// Dependencies: 
// 
// Revision:
// Revision 0.01 - File Created
// Additional Comments:
// 
//////////////////////////////////////////////////////////////////////////////////


module Branch_comparator(
input [31:0] Read_Data1,
input [31:0] Read_Data2,
input [6:0] Opcode,
input [2:0] funct,
output reg IF_Flush
    );
    always@(*)
    begin
    if ((Read_Data1 == Read_Data2) && (Opcode == 7'b1100011) && (funct ==3'b000))
    IF_Flush =1;
    else if  ((Read_Data1 != Read_Data2) && (Opcode == 7'b1100011) && (funct ==3'b001))
    IF_Flush =1;
    else
     IF_Flush =0;
    end
endmodule
