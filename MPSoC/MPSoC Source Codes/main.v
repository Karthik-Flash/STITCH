`timescale 1ns / 1ps
//////////////////////////////////////////////////////////////////////////////////
// Company: 
// Engineer: 
// 
// Create Date: 06/16/2021 05:20:44 PM
// Design Name: 
// Module Name: main
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


module main(input wr_clk,rd_clk,
input reset,
input rd_en,
output [31:0] result);

wire wr_en, empty, full_int,wr_o;
wire rd_clk,wr_clk;
wire [7:0] dest,source;
wire [31:0] result,data_in_core_r1,data_in_core_r2,data_in_core_r3,data_in_core_r4,
data_out_core_r1, data_out_core_r2, data_out_core_r3, data_out_core_r4,data_out;

assign dest=8'h11;
assign source=8'h00;


Processor p1(wr_clk,reset,wr_en,result);
new1 N1(rd_clk,wr_clk,result,reset,wr_en,dest,source,empty,full_int,data_in_core_r1,wr_o);
top_2x2_router ro1(rd_clk,reset,data_in_core_r1,data_in_core_r2,data_in_core_r3,data_in_core_r4,
data_out_core_r1, data_out_core_r2, data_out_core_r3, data_out_core_r4);
nidepack r2(data_out_core_r4,wr_clk,rd_clk,rd_en,reset,data_out);

endmodule