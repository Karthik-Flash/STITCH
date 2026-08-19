// adder_with_overflow_tb.v
// 8-bit adder with a carry-out flag.
//   sum      = (a + b) truncated to 8 bits
//   overflow = carry-out of the 8-bit addition (1 when a + b > 255)
//
// LLM failure mode this targets:
//   always @(*) begin
//     sum = a + b;          <-- 'overflow' never assigned anywhere
//   end
// Verilator: "Signal is not driven: 'overflow'" (UNDRIVEN)
// iverilog:  every overflow check reads x, so FAIL lines appear on both the
//            carry and the no-carry vectors -- but nothing says why.
//
// Note the oracle uses !== (case inequality) so an undriven x is caught
// rather than silently comparing unknown against 0.
`timescale 1ns/1ps
module adder_with_overflow_tb;
    reg  [7:0] a, b;
    wire [7:0] sum;
    wire       overflow;
    integer    errors = 0;

    adder_with_overflow dut(.a(a), .b(b), .sum(sum), .overflow(overflow));

    task check(input [7:0] ta, input [7:0] tb_in,
               input [7:0] esum, input eovf, input [127:0] name);
        begin
            a = ta; b = tb_in; #10;
            if (sum !== esum) begin
                $display("FAIL %0s: a=%0d b=%0d sum got %b expected %b",
                          name, ta, tb_in, sum, esum);
                errors = errors + 1;
            end
            if (overflow !== eovf) begin
                $display("FAIL %0s: a=%0d b=%0d overflow got %b expected %b",
                          name, ta, tb_in, overflow, eovf);
                errors = errors + 1;
            end
        end
    endtask

    initial begin
        // ---- No carry-out: overflow must be 0 --------------------------
        check(8'd0,   8'd0,   8'd0,   1'b0, "zero");
        check(8'd1,   8'd1,   8'd2,   1'b0, "one_plus_one");
        check(8'd100, 8'd27,  8'd127, 1'b0, "no_carry_mid");
        check(8'd255, 8'd0,   8'd255, 1'b0, "max_plus_zero");
        check(8'd128, 8'd127, 8'd255, 1'b0, "boundary_255");

        // ---- Carry-out: overflow must be 1, sum wraps ------------------
        check(8'd255, 8'd1,   8'd0,   1'b1, "wrap_to_zero");
        check(8'd128, 8'd128, 8'd0,   1'b1, "half_plus_half");
        check(8'd255, 8'd255, 8'd254, 1'b1, "max_plus_max");
        check(8'd200, 8'd100, 8'd44,  1'b1, "carry_mid");
        check(8'd129, 8'd127, 8'd0,   1'b1, "boundary_256");

        // ---- Back to no-carry, to catch a stuck overflow flag ----------
        check(8'd10,  8'd20,  8'd30,  1'b0, "recover_no_carry");

        if (errors == 0) $display("ALL TESTS PASSED");
        else             $display("FAIL: %0d test(s) failed", errors);
        $finish;
    end
endmodule
