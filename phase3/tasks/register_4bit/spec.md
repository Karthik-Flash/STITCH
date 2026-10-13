Module `register_4bit` -- 4-bit pipeline/VC-state register used inside every NoC router.
Ports (keep exactly, same order): input [3:0] din; input clk; input clr; input ce; output [3:0] dout.
On every rising edge of clk: if clr==1, dout <= 4'b0000; else if ce==1, dout <= din; otherwise dout holds.
