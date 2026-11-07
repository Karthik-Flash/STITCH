// SIGN-OFF copy of golden/tb/tb_flit_mux.v, made by scripts/make_tasks.py: seed + 1000.
`timescale 1ns/1ps
// flit_mux: all 16 select values, each with 200 random input sets.
module tb;
    reg  [3:0]  sel;
    reg  [31:0] in0, in1, in2, in3;
    wire [31:0] out;
    reg  [31:0] expected;
    integer s, r, errors = 0, seed = 1003;

    flit_mux dut (.sel(sel), .in0(in0), .in1(in1), .in2(in2), .in3(in3), .out(out));

    initial begin
        for (s = 0; s < 16; s = s + 1)
            for (r = 0; r < 200; r = r + 1) begin
                sel = s; in0 = $random(seed); in1 = $random(seed); in2 = $random(seed); in3 = $random(seed);
                #1;
                case (sel)
                    4'b0001: expected = in0;
                    4'b0010: expected = in1;
                    4'b0100: expected = in2;
                    4'b1000: expected = in3;
                    default: expected = 32'h6000_0000;
                endcase
                if (out !== expected) begin
                    errors = errors + 1;
                    if (errors <= 10) $display("FAIL: sel %b: out %h, expected %h", sel, out, expected);
                end
            end
        if (errors == 0) $display("ALL TESTS PASSED (3200 cases)");
        else $display("FAIL: %0d errors", errors);
        $finish;
    end
endmodule
