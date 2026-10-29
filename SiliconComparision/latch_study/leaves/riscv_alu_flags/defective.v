`timescale 1ns / 1ps
module riscv_alu_flags(input [31:0] a, input [31:0] b, input [3:0] alu_ctrl,
                       output reg [31:0] result, output reg zero, output reg negative,
                       output reg carry, output reg overflow);
  always @(*) begin
    case (alu_ctrl)
      4'b0000: begin {carry, result} = {1'b0, a} + {1'b0, b};
                     overflow = (a[31] == b[31]) && (result[31] != a[31]); end
      4'b0001: begin {carry, result} = {1'b0, a} + {1'b0, ~b} + 33'd1;
                     overflow = (a[31] != b[31]) && (result[31] != a[31]); end
      4'b0010: result = a & b;
      4'b0011: result = a | b;
      4'b0100: result = a ^ b;
      4'b0101: result = a << b[4:0];
      4'b0110: result = a >> b[4:0];
      4'b0111: result = $signed(a) >>> b[4:0];
      4'b1000: result = ($signed(a) < $signed(b)) ? 32'd1 : 32'd0;
      4'b1001: result = (a < b) ? 32'd1 : 32'd0;
    endcase
    zero     = (result == 32'd0);
    negative = result[31];
  end
endmodule
