/* verilator lint_off UNUSED */
/* verilator lint_off UNDRIVEN */
module rr_arbiter(req1, req2, req3, req4, reset, gnt1, gnt2, gnt3, gnt4, clk);
  input req1;
  input req2;
  input req3;
  input req4;
  input reset;
  output gnt1;
  output gnt2;
  output gnt3;
  output gnt4;
  input clk;
endmodule
