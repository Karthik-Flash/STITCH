/* verilator lint_off UNUSED */
/* verilator lint_off UNDRIVEN */
module routing_algo_mesh(header_in, current_address, reset, req_link1, req_link2, req_core, req_link3, req_link4);
  input [31:0] header_in;
  input [7:0] current_address;
  input reset;
  output req_link1;
  output req_link2;
  output req_core;
  output req_link3;
  output req_link4;
endmodule
