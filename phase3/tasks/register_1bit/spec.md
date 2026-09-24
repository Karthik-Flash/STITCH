Module `register_1bit` -- 1-bit router state register with asynchronous reset and synchronous clear.
Ports (keep exactly, same order): input din, reset, clk, clr, ce; output reg dout.
reset is ASYNCHRONOUS and active-high: dout goes to 0 immediately when reset rises.
On a rising clk edge (reset low): if clr==1 dout <= 0; else if ce==1 dout <= din; else hold.
The design must be synthesizable with Yosys (standard async-reset flip-flop coding style).
