`timescale 1ns / 1ps
//////////////////////////////////////////////////////////////////////////////////
// Company: 
// Engineer: 
// 
// Create Date: 06.05.2021 11:40:45
// Design Name: 
// Module Name: new
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


module new1(
input rd_clk,
input wr_clk,
input [31:0]data_in,
input reset,
input wr_en,
input [7:0] dest, 
input [7:0] source,
output empty,
output full_int,
output [31:0] niout,
 output wr_o
    );

wire [31:0]data_out;
wire rd_en;
wire wr_dir,rd_dir;
wire [2:0]wr_add;
wire [2:0]rd_add;
//fifoasync F1(rd_clk,wr_clk,data_in[31:0],reset,rd_en,wr_en,data_out[31:0],empty,full);
rp1 R1(data_out,dest,source,rd_clk,wr_clk,wr_en,reset,niout,rd_en,wr_o);

router_fifo F2(reset, rd_clk, rd_en, data_in, wr_clk,  wr_en,rd_add, wr_add, wr_dir, rd_dir
                   ,data_out,full_int, empty) ; 
endmodule
