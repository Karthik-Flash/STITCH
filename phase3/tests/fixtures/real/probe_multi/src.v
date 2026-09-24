module multi_t(input clk, input rst, input d, output reg q, output w);
  always @(posedge clk) q <= d;
  always @(posedge clk or posedge rst) if (rst) q <= 1'b0;
  assign w = d;
  assign w = ~d;
endmodule
