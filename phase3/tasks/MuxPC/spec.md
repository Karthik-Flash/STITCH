Module `MuxPC` -- next-PC select of a RISC-V core (combinational).
Ports (keep exactly): input [31:0] next_address, B_addr, J_addr; input [1:0] PCsrc; output reg [31:0] input_to_ifu.
PCsrc=00 -> next_address (PC+4); 01 -> J_addr (jump); 10 -> B_addr (branch/flush). PCsrc=11 does not occur in operation.
