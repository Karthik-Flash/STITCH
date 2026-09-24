Module `riscv_alu_flags` -- 32-bit RISC-V integer ALU with status flags (combinational).
Ports (keep exactly): input [31:0] a, b; input [3:0] alu_ctrl; output reg [31:0] result;
output reg zero, negative, carry, overflow.
alu_ctrl: 0000 ADD, 0001 SUB (a + ~b + 1), 0010 AND, 0011 OR, 0100 XOR, 0101 SLL (b[4:0]), 0110 SRL,
0111 SRA, 1000 SLT (signed, result 1/0), 1001 SLTU (unsigned). Codes 1010-1111 are unused: result = 0.
zero = (result == 0); negative = result[31].
carry = carry-out of the 33-bit ADD/SUB (for SUB: carry of a + ~b + 1, i.e. 1 means no borrow).
overflow = signed overflow of ADD/SUB. For every other operation carry = 0 and overflow = 0.
Purely combinational: no latches.
