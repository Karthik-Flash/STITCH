// datapath_mux_alu_tb.v
// 8-bit datapath: case-based ALU -> mode mux -> enable gate.
//   enable=1, mode=0 : out = ALU(op) of a,b
//   enable=1, mode=1 : out = bypass
//   enable=0         : out = 8'b0   <- LLMs forget this branch entirely
//
// LLM failure mode this targets:
//   always @(*) begin
//     case (op) ... endcase           // ALU: correct
//     if (mode) out = bypass;         // mux: correct
//     else      out = alu_result;
//   end                               <-- 'enable' never referenced
//
// Expected from Verilator: "Signal is not used: 'enable'" (UNUSEDSIGNAL)
// iverilog: FAIL only on the enable=0 vectors -- no cause given
//
// The enable=1 vectors come FIRST and cover every op and both mode values, so
// if the ALU or the mux is wrong the failure set says so immediately and is
// distinguishable from the gating defect.
`timescale 1ns/1ps
module datapath_mux_alu_tb;
    reg  [7:0] a, b, bypass;
    reg  [1:0] op;
    reg        mode, enable;
    wire [7:0] out;
    integer    errors = 0;

    datapath_mux_alu dut(.a(a), .b(b), .bypass(bypass), .op(op),
                         .mode(mode), .enable(enable), .out(out));

    task check(input [7:0] eout, input [255:0] name);
        begin
            #10;
            if (out !== eout) begin
                $display("FAIL %0s: en=%b mode=%b op=%b a=%h b=%h byp=%h got %h expected %h",
                          name, enable, mode, op, a, b, bypass, out, eout);
                errors = errors + 1;
            end
        end
    endtask

    initial begin
        a = 8'h12; b = 8'h34; bypass = 8'hEE;

        // ---- enable=1, mode=0 : the ALU path, all four ops --------------
        enable = 1'b1; mode = 1'b0;
        op = 2'b00; check(8'h46, "en1_mode0_add");   // 12 + 34
        op = 2'b01; check(8'hDE, "en1_mode0_sub");   // 12 - 34 (wraps)
        op = 2'b10; check(8'h10, "en1_mode0_and");   // 12 & 34
        op = 2'b11; check(8'h36, "en1_mode0_or");    // 12 | 34

        // ---- enable=1, mode=1 : the bypass path, op must be ignored -----
        mode = 1'b1;
        op = 2'b00; check(8'hEE, "en1_mode1_add");
        op = 2'b11; check(8'hEE, "en1_mode1_or");

        // ---- enable=0 : output must be zero for EVERY combination -------
        // Without the enable branch the datapath keeps driving its result.
        enable = 1'b0;
        mode = 1'b0;
        op = 2'b00; check(8'h00, "en0_mode0_add");
        op = 2'b01; check(8'h00, "en0_mode0_sub");
        op = 2'b10; check(8'h00, "en0_mode0_and");
        op = 2'b11; check(8'h00, "en0_mode0_or");
        mode = 1'b1;
        op = 2'b00; check(8'h00, "en0_mode1_add");
        op = 2'b11; check(8'h00, "en0_mode1_or");

        // ---- different operands, still gated off -------------------------
        // Chosen so the enabled result is NON-zero, otherwise a stuck-at-zero
        // output would pass the re-enable check below by coincidence.
        a = 8'hF0; b = 8'h05; bypass = 8'h7F;
        mode = 1'b0; op = 2'b00; check(8'h00, "en0_other_operands");

        // ---- re-enable to confirm a clean transition back ----------------
        enable = 1'b1;
        mode = 1'b0; op = 2'b00; check(8'hF5, "reenable_add");   // F0 + 05
        mode = 1'b1;             check(8'h7F, "reenable_bypass");
        enable = 1'b0;
        mode = 1'b1;             check(8'h00, "disable_again");

        if (errors == 0) $display("ALL TESTS PASSED");
        else             $display("FAIL: %0d test(s) failed", errors);
        $finish;
    end
endmodule
