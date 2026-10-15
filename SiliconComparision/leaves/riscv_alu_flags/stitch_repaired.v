module riscv_alu_flags (
  input [31:0] a,
  input [31:0] b,
  input [3:0] alu_ctrl,
  output reg [31:0] result,
  output reg zero,
  output reg negative,
  output reg carry,
  output reg overflow
);

  always @(*) begin
    case(alu_ctrl)
      4'b0000: begin // ADD
        {carry, result} = a + b;
        overflow = (a[31] == b[31]) && (result[31] != a[31]);
      end
      4'b0001: begin // SUB
        {carry, result} = a - b;
        overflow = (a[31] != b[31]) && (result[31] != a[31]);
      end
      4'b0010: begin // AND
        result = a & b;
        carry = 1'b0;
        overflow = 1'b0;
      end
      4'b0011: begin // OR
        result = a | b;
        carry = 1'b0;
        overflow = 1'b0;
      end
      4'b0100: begin // XOR
        result = a ^ b;
        carry = 1'b0;
        overflow = 1'b0;
      end
      4'b0101: begin // SLL
        result = $signed(a) << b[4:0];
        carry = 1'b0;
        overflow = 1'b0;
      end
      4'b0110: begin // SRL
        result = a >> b[4:0];
        carry = 1'b0;
        overflow = 1'b0;
      end
      4'b0111: begin // SRA
        result = $signed(a) >>> b[4:0];
        carry = 1'b0;
        overflow = 1'b0;
      end
      4'b1000: begin // SLT
        result = {31'b0, ($signed(a) < $signed(b))};
        carry = 1'b0;
        overflow = 1'b0;
      end
      4'b1001: begin // SLTU
        result = {31'b0, (a < b)};
        carry = 1'b0;
        overflow = 1'b0;
      end
      default: begin
        result = 32'b0;
        carry = 1'b0;
        overflow = 1'b0;
      end
    endcase
    zero = (result == 32'b0);
    negative = result[31];
  end
endmodule
