module register_1bit(din, reset, clk, clr, ce, dout);
  input din; input reset; input clk; input clr; input ce;
  output reg dout;
  always @(posedge clk or posedge reset) begin
    if (reset)    dout <= 1'b0;
    else if (clr) dout <= 1'b0;
    else if (ce)  dout <= din;
  end
endmodule