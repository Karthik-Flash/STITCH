module noc_xbar4(input [3:0] gnt, input [31:0] in0, input [31:0] in1, input [31:0] in2, input [31:0] in3,
                 output reg [31:0] out_data, output reg out_valid);
  always @(*) begin
    case(gnt)
      4'b0001: out_data = in0;
      4'b0010: out_data = in1;
      4'b0100: out_data = in2;
      4'b1000: out_data = in3;
      default: out_data = 32'b0;
    endcase
    out_valid = |gnt;
  end
endmodule
