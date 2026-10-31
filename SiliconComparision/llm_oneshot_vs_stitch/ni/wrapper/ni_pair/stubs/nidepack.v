/* verilator lint_off UNUSED */
/* verilator lint_off UNDRIVEN */
module nidepack(flit, rd_clk, wr_clk, rd_en, reset, data_out);
  input [31:0] flit;
  input rd_clk;
  input wr_clk;
  input rd_en;
  input reset;
  output [31:0] data_out;
endmodule
