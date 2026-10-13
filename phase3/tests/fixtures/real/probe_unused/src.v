module unused_t(input en, input [2:0] sel, input [7:0] unused_bus, output reg [7:0] y, output z);
  always @(*) y = 8'b1 << sel;
endmodule
