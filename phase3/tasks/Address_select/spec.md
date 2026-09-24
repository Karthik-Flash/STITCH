Module `Address_select` -- JAL target and PC-source select of a RISC-V core (combinational).
Ports (keep names): input [31:0] Instruction_code; input IF_Flush; input [31:0] PC (the full 32-bit program
counter); output reg [31:0] J_addr; output reg [1:0] PCsrc.
Imm (20 bits) = {Instruction_code[31], Instruction_code[19:12], Instruction_code[20], Instruction_code[30:21]};
Shft_2 = Imm << 2 kept to 20 bits; X = Shft_2 sign-extended to 32 bits; J_addr = X + PC.
PCsrc = 2'b10 when IF_Flush==1; else 2'b01 when Instruction_code[6:0]==7'b1101111 (JAL); else 2'b00.
J_addr must always be defined (it may be computed unconditionally). Purely combinational: no latches.
