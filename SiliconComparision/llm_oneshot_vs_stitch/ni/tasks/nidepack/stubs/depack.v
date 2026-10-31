/* verilator lint_off UNUSED */
/* verilator lint_off UNDRIVEN */
module depack(flit, wr_clk, reset, data_out, wr_en, c_rd);
  input [31:0] flit;
  input wr_clk;
  input reset;
  output [31:0] data_out;
  output wr_en;
  output c_rd;
endmodule
