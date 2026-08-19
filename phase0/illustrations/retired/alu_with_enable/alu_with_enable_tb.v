// alu_with_enable_tb.v
// 8-bit ALU (ADD/SUB/AND/OR) gated by an active-high enable.
//   enable=1 : out = ALU(op) of a,b
//   enable=0 : out = 8'b0   <- LLMs forget this branch entirely
//
// LLM failure mode this targets:
//   always @(*) begin
//     case (op) ... endcase   // ALU: correct
//   end                       <-- 'enable' never referenced
//
// Expected from Verilator: "Signal is not used: 'enable'" (UNUSEDSIGNAL)
// iverilog: FAIL only on the enable=0 vectors -- no cause given
//
// The enable=1 vectors come FIRST and cover all four ops, so if the ALU
// itself is wrong the failure set says so immediately and is distinguishable
// from the gating defect.
`timescale 1ns/1ps
module alu_with_enable_tb;
    reg  [7:0] a, b;
    reg  [1:0] op;
    reg        enable;
    wire [7:0] out;
    integer    errors = 0;

    alu_with_enable dut(.a(a), .b(b), .op(op), .enable(enable), .out(out));

    task check(input [7:0] eout, input [255:0] name);
        begin
            #10;
            if (out !== eout) begin
                $display("FAIL %0s: en=%b op=%b a=%h b=%h got %h expected %h",
                          name, enable, op, a, b, out, eout);
                errors = errors + 1;
            end
        end
    endtask

    initial begin
        a = 8'h12; b = 8'h34;

        // ---- enable=1 : all four ops must compute correctly -------------
        enable = 1'b1;
        op = 2'b00; check(8'h46, "en1_add");   // 12 + 34
        op = 2'b01; check(8'hDE, "en1_sub");   // 12 - 34 (wraps)
        op = 2'b10; check(8'h10, "en1_and");   // 12 & 34
        op = 2'b11; check(8'h36, "en1_or");    // 12 | 34

        // ---- enable=0 : output must be zero for EVERY op -----------------
        // Without the enable branch the ALU keeps driving its result.
        enable = 1'b0;
        op = 2'b00; check(8'h00, "en0_add");
        op = 2'b01; check(8'h00, "en0_sub");
        op = 2'b10; check(8'h00, "en0_and");
        op = 2'b11; check(8'h00, "en0_or");

        // ---- different operands, still gated off --------------------------
        // Chosen so the enabled result is non-zero, so a stuck-at-zero output
        // does not pass the re-enable check below by coincidence.
        a = 8'hF0; b = 8'h05;
        op = 2'b00; check(8'h00, "en0_other_operands");

        // ---- re-enable to confirm a clean transition back -----------------
        enable = 1'b1;
        op = 2'b00; check(8'hF5, "reenable_add");   // F0 + 05
        enable = 1'b0;
        check(8'h00, "disable_again");

        if (errors == 0) $display("ALL TESTS PASSED");
        else             $display("FAIL: %0d test(s) failed", errors);
        $finish;
    end
endmodule
