/* verilator lint_off UNUSED */
/* verilator lint_off UNDRIVEN */
module irs(reset, empty, rd_en, rd_clk, tailer, tailer_org, header, rd_en_out, data_sel, en1, en2, en4, en5, en6);
  input reset;
  input empty;
  input rd_en;
  input rd_clk;
  input tailer;
  input tailer_org;
  input header;
  output rd_en_out;
  output data_sel;
  output en1;
  output en2;
  output en4;
  output en5;
  output en6;
endmodule
