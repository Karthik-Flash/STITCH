/* verilator lint_off UNUSED */
/* verilator lint_off UNDRIVEN */
module rp1(data_in, dest, source, rd_clk, wr_clk, wr_en, reset, niout, rd_en, wr_o);
  input [31:0] data_in;
  input [7:0] dest;
  input [7:0] source;
  input rd_clk;
  input wr_clk;
  input wr_en;
  input reset;
  output [31:0] niout;
  output rd_en;
  output wr_o;
endmodule
