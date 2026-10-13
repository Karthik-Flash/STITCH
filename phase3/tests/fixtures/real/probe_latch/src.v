module latch_t(input [1:0] op, input [7:0] a, b, output reg [7:0] y, output reg z);
  always @(*) begin
    case (op)
      2'b00: begin y = a + b; z = (a+b)==0; end
      2'b01: y = a - b;
    endcase
  end
endmodule
