// Reference implementation for the instr_decode_unit illustration candidate.
// Redesigned 2026-08-19: 'instr' narrowed from [7:0] to [3:0] so every bit is
// meaningful and no competing UNUSEDSIGNAL fires (see
// illustrations/retired/retired_candidates.md, and this candidate's own
// README for the pre-redesign failure). Internal structure is a classic
// opcode decoder -- a case on instr[3:2] driving four control outputs -- with
// the gating port 'valid' at the TOP level, the only place the interpreter
// can see it.
module instr_decode_unit (
    input      [3:0] instr,
    input            valid,
    output reg [1:0] alu_op,
    output reg       reg_write,
    output reg       mem_read,
    output reg       mem_write
);
    always @(*) begin
        if (valid) begin
            case (instr[3:2])
                2'b00: begin                       // ALU
                    alu_op    = instr[1:0];
                    reg_write = 1'b1;
                    mem_read  = 1'b0;
                    mem_write = 1'b0;
                end
                2'b01: begin                       // LOAD
                    alu_op    = 2'b00;
                    reg_write = 1'b1;
                    mem_read  = 1'b1;
                    mem_write = 1'b0;
                end
                2'b10: begin                       // STORE
                    alu_op    = 2'b00;
                    reg_write = 1'b0;
                    mem_read  = 1'b0;
                    mem_write = 1'b1;
                end
                default: begin                     // NOP
                    alu_op    = 2'b00;
                    reg_write = 1'b0;
                    mem_read  = 1'b0;
                    mem_write = 1'b0;
                end
            endcase
        end else begin
            alu_op    = 2'b00;
            reg_write = 1'b0;
            mem_read  = 1'b0;
            mem_write = 1'b0;
        end
    end
endmodule
