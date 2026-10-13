Module `mux3` -- ALU-operand forwarding multiplexer of a 5-stage RISC-V pipeline (combinational).
Ports (keep exactly): input [1:0] sel; input [31:0] id_ex_output_data1, ex_forwarding, mem_forwarding;
output reg [31:0] alu_in.
Behaviour: sel=2'b00 -> alu_in = id_ex_output_data1; sel=2'b01 -> ex_forwarding; sel=2'b10 -> mem_forwarding.
sel=2'b11 does not occur in operation.
