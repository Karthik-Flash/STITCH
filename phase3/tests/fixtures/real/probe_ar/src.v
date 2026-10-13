module ar_t(input clk, reset, clr, d, output reg q);
  always @(posedge clk, posedge reset) if (clr | reset) q <= 0; else q <= d;
endmodule
