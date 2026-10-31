/* verilator lint_off UNUSED */
/* verilator lint_off UNDRIVEN */
module new1(rd_clk, wr_clk, data_in, reset, wr_en, dest, source, empty, full_int, niout, wr_o);
  input rd_clk;
  input wr_clk;
  input [31:0] data_in;
  input reset;
  input wr_en;
  input [7:0] dest;
  input [7:0] source;
  output empty;
  output full_int;
  output [31:0] niout;
  output wr_o;
endmodule
