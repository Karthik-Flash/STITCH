`timescale 1ns / 1ps
//////////////////////////////////////////////////////////////////////////////////
// Company: 
// Engineer: 
// 
// Create Date: 06/16/2021 05:22:15 PM
// Design Name: 
// Module Name: test
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


module test();


reg rd_clk,wr_clk, reset,rd_en;
wire [31:0] result;



 main main(rd_clk,wr_clk,reset,rd_en,result);


always #2 wr_clk=!wr_clk;
always #5 rd_clk=!rd_clk;

initial begin
wr_clk=0;
rd_clk=0;
reset=1;
rd_en=0;

#200
reset=0;
rd_en=1;


#50000
$finish;
end


endmodule
