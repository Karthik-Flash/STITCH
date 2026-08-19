// The DEFECT this candidate targets: 'valid' is declared at the top level and
// never read. The opcode decode itself is entirely correct, so the only
// failing vectors are the valid=0 ones -- the decoder_3to8 defect scaled up
// into a module with four control outputs.
//
// Redesigned 2026-08-19: 'instr' narrowed to [3:0] so this warning is the
// ONLY UNUSEDSIGNAL Verilator can emit -- no competing partial-bus warning.
//
// Expected from Verilator: "Signal is not used: 'valid'" (UNUSEDSIGNAL)
// iverilog:  every valid=0 vector asserts control signals it should not
//
// Hand-written for the pre-screen. Defect shape the spec is designed to
// elicit, not a captured model response.
module instr_decode_unit (
    input      [3:0] instr,
    input            valid,
    output reg [1:0] alu_op,
    output reg       reg_write,
    output reg       mem_read,
    output reg       mem_write
);
    always @(*) begin
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
    end
endmodule
