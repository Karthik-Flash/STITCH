/* verilator lint_off UNUSED */
/* verilator lint_off UNDRIVEN */
module ip_chnl(reset, rd_clk, wr_clk, rd_en, wr_en, data_in, current_address, full_ext, empty_synch_rdclk, req_l1, req_l2, req_l3, req_l4, req_c, data_out, tailer, tailer_org, nxt_reset, data_sel, header, empty, fifo_out, header_flit, reg_out, mux_data_out, header_out);
  input reset;
  input rd_clk;
  input wr_clk;
  input rd_en;
  input wr_en;
  input [31:0] data_in;
  input [7:0] current_address;
  output full_ext;
  output empty_synch_rdclk;
  output req_l1;
  output req_l2;
  output req_l3;
  output req_l4;
  output req_c;
  output [31:0] data_out;
  output tailer;
  output tailer_org;
  output nxt_reset;
  output data_sel;
  output header;
  output empty;
  output [31:0] fifo_out;
  output [31:0] header_flit;
  output [31:0] reg_out;
  output [31:0] mux_data_out;
  output [31:0] header_out;
endmodule
