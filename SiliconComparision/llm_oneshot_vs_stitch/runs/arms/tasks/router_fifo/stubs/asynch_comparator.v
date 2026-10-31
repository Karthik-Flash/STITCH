/* verilator lint_off UNUSED */
/* verilator lint_off UNDRIVEN */
module asynch_comparator(rd_ptr, wr_ptr, rd_dir, wr_dir, full_ext, full_int, empty);
  input [2:0] rd_ptr;
  input [2:0] wr_ptr;
  input rd_dir;
  input wr_dir;
  output full_ext;
  output full_int;
  output empty;
endmodule
