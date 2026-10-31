// ni_pair: wrapper, not golden. Never generated and never prompted.
// The two halves of the MPSoC network interface (phase3/designs/mpsoc_ref/main.v) with the 2x2 router between them
// removed: the packetiser's flit output niout drives the depacketiser's flit input directly. Clocks as in main.v:
// new1 gets (rd_clk, wr_clk), nidepack gets wr_clk as its rd_clk and rd_clk as its wr_clk (depack writes on the
// network clock that rp1 sends on). Every other port of either half is a port of ni_pair.
// Test bench: wrapper/ni_pair/tb_signoff.v (pipeline/make_tasks.py). ORFS top of every NI hand-off design.
`timescale 1ns / 1ps
module ni_pair(
  input rd_clk,
  input wr_clk,
  input reset,
  input [31:0] data_in,
  input wr_en,
  input [7:0] dest,
  input [7:0] source,
  input rd_en,
  output empty,
  output full_int,
  output [31:0] niout,
  output wr_o,
  output [31:0] data_out
);
  new1 N1 (.rd_clk(rd_clk), .wr_clk(wr_clk), .data_in(data_in), .reset(reset), .wr_en(wr_en), .dest(dest),
           .source(source), .empty(empty), .full_int(full_int), .niout(niout), .wr_o(wr_o));
  nidepack D1 (.flit(niout), .rd_clk(wr_clk), .wr_clk(rd_clk), .rd_en(rd_en), .reset(reset), .data_out(data_out));
endmodule
