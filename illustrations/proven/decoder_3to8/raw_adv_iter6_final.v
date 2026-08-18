```verilog
module decoder_3to8 (
    input enable,
    input [2:0] in,
    output reg [7:0] out
);

  always @(*) begin
    case (in)
      3'd0: begin
        out = 8'b0000_0001;
      end
      3'd1: begin
        out = 8'b0000_0010;
      end
      3'd2: begin
        out = 8'b0000_0100;
      end
      3'd3: begin
        out = 8'b0000_1000;
      end
      3'd4: begin
        out = 8'b0001_0000;
      end
      3'd5: begin
        out = 8'b0010_0000;
      end
      3'd6: begin
        out = 8