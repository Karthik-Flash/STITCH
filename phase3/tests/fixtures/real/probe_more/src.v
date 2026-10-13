module sub(input [7:0] a, input b, output [7:0] y); assign y = a ^ {8{b}}; endmodule
module more_t(input clk, input rst, input [3:0] d, input [31:0] wide, input [1:0] s, output reg [3:0] q, output reg [3:0] l, output [7:0] y, output reg p, output [3:0] half);
  always_comb begin if (s == 2'b00) l = d; end
  always @(posedge clk) q = d;
  always @(*) p <= d[0];
  sub u0(.a(wide), .y(y));
  assign half[1:0] = d[1:0];
endmodule
