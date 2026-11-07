// SIGN-OFF copy of golden/tb/tb_rr_arbiter.v, made by scripts/make_tasks.py: seed + 1000, twice the traffic.
`timescale 1ns/1ps
// rr_arbiter: random requests and advance against a pointer model; checks the grant every cycle and that
// every requester that keeps asking is granted within 4 advances.
module tb;
    reg clk = 0, reset = 1, advance = 0;
    reg  [3:0] req = 0;
    wire [3:0] gnt;
    reg  [3:0] expected;
    integer last = 3, k, idx, errors = 0, cyc, seed = 1007, grants = 0;
    integer waiting [0:3];

    rr_arbiter dut (.clk(clk), .reset(reset), .req(req), .advance(advance), .gnt(gnt));

    always #5 clk = ~clk;

    initial begin
        for (k = 0; k < 4; k = k + 1) waiting[k] = 0;
        repeat (3) @(negedge clk);
        reset = 0;
        for (cyc = 0; cyc < 40000; cyc = cyc + 1) begin
            @(negedge clk);
            req = (cyc % 1000 < 500) ? ($random(seed) | $random(seed)) : $random(seed);
            advance = ($random(seed) % 3) != 0;
            if (cyc == 12345) begin
                reset = 1; @(posedge clk); last = 3; @(negedge clk); reset = 0;
                for (k = 0; k < 4; k = k + 1) waiting[k] = 0;   // the reset restarts the priority: restart the count
            end
            #1;
            expected = 4'b0000;
            for (k = 4; k >= 1; k = k - 1) begin
                idx = (last + k) % 4;
                if (req[idx]) expected = 4'b0001 << idx;
            end
            if (gnt !== expected) begin
                errors = errors + 1;
                if (errors <= 10) $display("FAIL cycle %0d: req %b last %0d: gnt %b, expected %b", cyc, req, last, gnt, expected);
            end
            @(posedge clk);
            if (advance && expected != 0) begin
                grants = grants + 1;
                for (k = 0; k < 4; k = k + 1)
                    if (expected[k]) begin last = k; waiting[k] = 0; end
                    else if (req[k]) waiting[k] = waiting[k] + 1;
                    else waiting[k] = 0;
                for (k = 0; k < 4; k = k + 1)
                    if (waiting[k] > 3) begin
                        errors = errors + 1; $display("FAIL cycle %0d: requester %0d passed over %0d times", cyc, k, waiting[k]);
                    end
            end
        end
        if (errors == 0) $display("ALL TESTS PASSED (%0d cycles, %0d grants taken)", cyc, grants);
        else $display("FAIL: %0d errors", errors);
        $finish;
    end
endmodule
