`timescale 1ns / 1ps
//////////////////////////////////////////////////////////////////////////////////
// Company: 
// Engineer: 
// 
// Create Date: 21.05.2021 12:00:53
// Design Name: 
// Module Name: nidepack
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


module nidepack(
input [31:0] flit,
input rd_clk,
input wr_clk,
input rd_en,
input reset,
output [31:0]data_out

    );
    wire [2:0]rd_add;
    wire [2:0]wr_add;
    wire wr_dir;
    wire rd_dir;
    wire full_ext;
    wire full_int;
    wire empty;
    wire [31:0] depack_out;
    wire wr_en;
    //wire rd_en;
depack D1(flit,wr_clk,reset,depack_out,wr_en);
router_fifo F1(reset, rd_clk, rd_en, depack_out, wr_clk,wr_en,rd_add, wr_add, wr_dir, rd_dir
                   ,data_out,full_int, empty) ;
endmodule