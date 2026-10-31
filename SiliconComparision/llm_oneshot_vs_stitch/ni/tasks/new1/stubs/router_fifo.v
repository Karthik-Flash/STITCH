/* verilator lint_off UNUSED */
/* verilator lint_off UNDRIVEN */
module router_fifo(reset, rd_clk, rd_en, data_in, wr_clk, wr_en, rd_add, wr_add, wr_dir, rd_dir, data_out, full_ext, full_int, empty);
  input reset;
  input rd_clk;
  input rd_en;
  input [31:0] data_in;
  input wr_clk;
  input wr_en;
  output [2:0] rd_add;
  output [2:0] wr_add;
  output wr_dir;
  output rd_dir;
  output [31:0] data_out;
  output full_ext;
  output full_int;
  output empty;
endmodule
