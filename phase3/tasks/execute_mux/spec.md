Module `execute_mux` -- selects the ALU or the M-extension unit result (combinational).
Ports (keep exactly): input [31:0] alu_result, mul_result; input id_ex_enable; output reg [31:0] result.
result = alu_result when id_ex_enable==1, otherwise mul_result.
