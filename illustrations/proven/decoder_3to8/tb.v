// decoder_3to8_tb.v
// 3-to-8 one-hot decoder with enable.
// enable=1: out = one-hot(in)
// enable=0: out = 8'b0  <- LLMs forget this branch entirely
//
// LLM failure mode:
//   always @(*) begin
//     if (enable) begin
//       case(in) 3'b000: out=8'b00000001; ... endcase
//     end                        <-- missing else out = 0;
//   end
// Yosys: "Inferred latch for signal \out" because out not assigned when enable=0
// iverilog: FAIL only shows wrong value for enable=0 tests -- no cause given
module decoder_3to8_tb;
    reg       enable;
    reg [2:0] in;
    wire [7:0] out;

    decoder_3to8 dut(.enable(enable),.in(in),.out(out));

    integer fail = 0;

    task check;
        input       een;
        input [2:0] ein;
        input [7:0] eout;
        begin
            enable=een; in=ein; #10;
            if (out !== eout) begin
                $display("FAIL en=%0d in=%0d: got %b, exp %b",
                          een, ein, out, eout);
                fail = fail + 1;
            end
        end
    endtask

    initial begin
        // ── Enabled: verify all 8 one-hot outputs ────────────────────────
        check(1, 3'd0, 8'b0000_0001);
        check(1, 3'd1, 8'b0000_0010);
        check(1, 3'd2, 8'b0000_0100);
        check(1, 3'd3, 8'b0000_1000);
        check(1, 3'd4, 8'b0001_0000);
        check(1, 3'd5, 8'b0010_0000);
        check(1, 3'd6, 8'b0100_0000);
        check(1, 3'd7, 8'b1000_0000);

        // ── Disabled: ALL inputs must produce 8'b0 ───────────────────────
        // Without else branch: latch holds last enabled output -> FAIL
        // With Yosys "Inferred latch for \out" feedback: LLM adds else -> PASS
        check(0, 3'd0, 8'b0000_0000);
        check(0, 3'd1, 8'b0000_0000);
        check(0, 3'd3, 8'b0000_0000);
        check(0, 3'd5, 8'b0000_0000);
        check(0, 3'd7, 8'b0000_0000);

        // ── Toggle enable: check clean transitions ────────────────────────
        check(1, 3'd2, 8'b0000_0100);  // re-enable after disable
        check(0, 3'd2, 8'b0000_0000);  // disable again
        check(1, 3'd6, 8'b0100_0000);

        if (fail == 0)
            $display("ALL TESTS PASSED");
        else
            $display("FAIL: %0d test(s) failed", fail);

        $finish;
    end
endmodule
