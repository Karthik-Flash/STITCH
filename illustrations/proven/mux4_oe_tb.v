// mux4_oe_tb.v
// 4-to-1 multiplexer with active-high output enable.
// oe=1: out = selected input per sel
// oe=0: out = 8'b0   <- LLMs forget this branch entirely
//
// LLM failure mode:
//   always @(*) begin
//     case (sel) 2'd0: out = a; ... endcase   <-- 'oe' never referenced
//   end
// Verilator: "Signal is not used: 'oe'" (UNUSEDSIGNAL)
// iverilog: FAIL only on the oe=0 tests -- no cause given
`timescale 1ns/1ps
module tb;
    reg        oe;
    reg  [1:0] sel;
    reg  [7:0] a, b, c, d;
    wire [7:0] out;
    integer errors = 0;

    mux4_oe dut(.oe(oe), .sel(sel), .a(a), .b(b), .c(c), .d(d), .out(out));

    task check(input [7:0] eo, input [127:0] name);
        begin
            if (out !== eo) begin
                $display("FAIL %0s: oe=%b sel=%0d got %h expected %h",
                          name, oe, sel, out, eo);
                errors = errors + 1;
            end
        end
    endtask

    initial begin
        a = 8'hA1; b = 8'hB2; c = 8'hC3; d = 8'hD4;

        // Enabled: all four select values
        oe = 1;
        sel = 2'd0; #10; check(8'hA1, "oe1_sel0");
        sel = 2'd1; #10; check(8'hB2, "oe1_sel1");
        sel = 2'd2; #10; check(8'hC3, "oe1_sel2");
        sel = 2'd3; #10; check(8'hD4, "oe1_sel3");

        // Disabled: output must be zero for EVERY select value.
        // Without the oe branch the mux keeps driving the selected input.
        oe = 0;
        sel = 2'd0; #10; check(8'h00, "oe0_sel0");
        sel = 2'd1; #10; check(8'h00, "oe0_sel1");
        sel = 2'd2; #10; check(8'h00, "oe0_sel2");
        sel = 2'd3; #10; check(8'h00, "oe0_sel3");

        // Re-enable to confirm clean transition back
        oe = 1;
        sel = 2'd2; #10; check(8'hC3, "reenable_sel2");
        oe = 0;
        sel = 2'd2; #10; check(8'h00, "disable_again");

        if (errors == 0) $display("ALL TESTS PASSED");
        else             $display("FAIL: %0d test(s) failed", errors);
        $finish;
    end
endmodule
