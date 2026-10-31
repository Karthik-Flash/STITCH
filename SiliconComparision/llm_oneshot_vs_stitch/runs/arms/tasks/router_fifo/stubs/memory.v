/* verilator lint_off UNUSED */
/* verilator lint_off UNDRIVEN */
module memory(reset, rd_clk, rd_add, wr_clk, wr_add, data_in, wr_en, rd_en, data_out);
  input reset;
  input rd_clk;
  input [2:0] rd_add;
  input wr_clk;
  input [2:0] wr_add;
  input [31:0] data_in;
  input wr_en;
  input rd_en;
  output [31:0] data_out;
endmodule
