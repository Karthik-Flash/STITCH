Module `register_32bit` -- 32-bit pipeline/VC-state register used inside every NoC router.
Ports (keep exactly, same order): input [31:0] din; input clk; input clr; input ce; output [31:0] dout.
On every rising edge of clk: if clr==1, dout <= 32'h60000000; else if ce==1, dout <= din; otherwise dout holds.
