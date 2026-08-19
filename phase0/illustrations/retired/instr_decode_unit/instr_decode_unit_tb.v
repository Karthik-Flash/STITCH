// instr_decode_unit_tb.v
// 4-bit instruction decoder: case on instr[3:2] -> four control outputs,
// gated by 'valid'.
//   valid=1 : control signals decoded from the opcode
//   valid=0 : all control signals 0   <- LLMs forget this branch entirely
//
// LLM failure mode this targets:
//   always @(*) begin
//     case (instr[3:2]) ... endcase   // decode: correct
//   end                               <-- 'valid' never referenced
//
// Redesigned 2026-08-19: instr narrowed from [7:0] to [3:0] so every bit is
// meaningful -- no competing partial-bus UNUSEDSIGNAL to steal the directive.
//
// Expected from Verilator: "Signal is not used: 'valid'" (UNUSEDSIGNAL)
// iverilog: FAIL only on the valid=0 vectors -- no cause given
//
// The valid=1 vectors come FIRST and cover all four opcodes plus both alu_op
// source bits, so a genuine decode bug is distinguishable from the gating
// defect by which block of vectors fails.
`timescale 1ns/1ps
module instr_decode_unit_tb;
    reg  [3:0] instr;
    reg        valid;
    wire [1:0] alu_op;
    wire       reg_write, mem_read, mem_write;
    integer    errors = 0;

    instr_decode_unit dut(.instr(instr), .valid(valid), .alu_op(alu_op),
                          .reg_write(reg_write), .mem_read(mem_read),
                          .mem_write(mem_write));

    task check(input [1:0] e_alu, input e_rw, input e_mr, input e_mw,
               input [255:0] name);
        begin
            #10;
            if (alu_op !== e_alu || reg_write !== e_rw
                    || mem_read !== e_mr || mem_write !== e_mw) begin
                $display("FAIL %0s: valid=%b instr=%b got alu_op=%b rw=%b mr=%b mw=%b expected %b %b %b %b",
                          name, valid, instr, alu_op, reg_write, mem_read,
                          mem_write, e_alu, e_rw, e_mr, e_mw);
                errors = errors + 1;
            end
        end
    endtask

    initial begin
        // ---- valid=1 : every opcode decodes correctly --------------------
        valid = 1'b1;
        instr = 4'b00_00; check(2'b00, 1'b1, 1'b0, 1'b0, "alu_op00");
        instr = 4'b00_01; check(2'b01, 1'b1, 1'b0, 1'b0, "alu_op01");
        instr = 4'b00_10; check(2'b10, 1'b1, 1'b0, 1'b0, "alu_op10");
        instr = 4'b00_11; check(2'b11, 1'b1, 1'b0, 1'b0, "alu_op11");
        instr = 4'b01_00; check(2'b00, 1'b1, 1'b1, 1'b0, "load");
        instr = 4'b01_11; check(2'b00, 1'b1, 1'b1, 1'b0, "load_alu_bits_ignored");
        instr = 4'b10_00; check(2'b00, 1'b0, 1'b0, 1'b1, "store");
        instr = 4'b10_11; check(2'b00, 1'b0, 1'b0, 1'b1, "store_alu_bits_ignored");
        instr = 4'b11_00; check(2'b00, 1'b0, 1'b0, 1'b0, "nop");
        instr = 4'b11_11; check(2'b00, 1'b0, 1'b0, 1'b0, "nop_alu_bits_ignored");

        // ---- valid=0 : every control signal must be deasserted -----------
        // Without the valid branch the decoder keeps asserting control.
        valid = 1'b0;
        instr = 4'b00_00; check(2'b00, 1'b0, 1'b0, 1'b0, "inv_alu_op00");
        instr = 4'b00_11; check(2'b00, 1'b0, 1'b0, 1'b0, "inv_alu_op11");
        instr = 4'b01_00; check(2'b00, 1'b0, 1'b0, 1'b0, "inv_load");
        instr = 4'b10_00; check(2'b00, 1'b0, 1'b0, 1'b0, "inv_store");
        instr = 4'b11_00; check(2'b00, 1'b0, 1'b0, 1'b0, "inv_nop");

        // ---- toggle back and forth ---------------------------------------
        valid = 1'b1; instr = 4'b01_00; check(2'b00, 1'b1, 1'b1, 1'b0, "revalidate_load");
        valid = 1'b0;                   check(2'b00, 1'b0, 1'b0, 1'b0, "invalidate_again");
        valid = 1'b1; instr = 4'b10_00; check(2'b00, 1'b0, 1'b0, 1'b1, "revalidate_store");

        if (errors == 0) $display("ALL TESTS PASSED");
        else             $display("FAIL: %0d test(s) failed", errors);
        $finish;
    end
endmodule
