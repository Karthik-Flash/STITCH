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
