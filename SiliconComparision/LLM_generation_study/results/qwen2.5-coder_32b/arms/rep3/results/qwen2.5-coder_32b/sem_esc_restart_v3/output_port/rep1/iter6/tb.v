`timescale 1ns/1ps
// output_port: random requests, flits and full_in against a model of the arbiter, the hold (owner) and the
// output register; checks pop every cycle and data_out after every clock edge.
module tb;
    reg clk = 0, reset = 1, full_in = 0;
    reg  [3:0]  req = 0;
    reg  [31:0] flit0 = 0, flit1 = 0, flit2 = 0, flit3 = 0;
    wire [31:0] data_out;
    wire [3:0]  pop;

    output_port dut (.clk(clk), .reset(reset), .req(req), .flit0(flit0), .flit1(flit1), .flit2(flit2),
                     .flit3(flit3), .full_in(full_in), .data_out(data_out), .pop(pop));

    always #5 clk = ~clk;

    reg  [3:0]  owner = 0, gnt, sel, exp_pop;
    reg  [31:0] exp_out = 32'h6000_0000, sel_flit;
    reg         send;
    integer last = 3, k, idx, errors = 0, cyc, seed = 17, sent = 0, held_cycles = 0, blocked = 0;

    initial begin
        repeat (3) @(negedge clk);
        reset = 0;
        for (cyc = 0; cyc < 30000; cyc = cyc + 1) begin
            @(negedge clk);
            if (data_out !== exp_out) begin
                errors = errors + 1; $display("FAIL cycle %0d: data_out=%h, expected %h", cyc, data_out, exp_out);
            end
            req = $random(seed);
            flit0 = $random(seed); flit1 = $random(seed); flit2 = $random(seed); flit3 = $random(seed);
            // tail flits rarer than other types, so packets hold the output for several cycles
            if (flit0[30:29] == 2'b10 && $random(seed) % 2) flit0[30:29] = 2'b00;
            if (flit1[30:29] == 2'b10 && $random(seed) % 2) flit1[30:29] = 2'b00;
            if (flit2[30:29] == 2'b10 && $random(seed) % 2) flit2[30:29] = 2'b00;
            if (flit3[30:29] == 2'b10 && $random(seed) % 2) flit3[30:29] = 2'b00;
            full_in = ((cyc / 900) % 3 == 2) ? ($random(seed) % 4 != 0) : ($random(seed) % 4 == 0);
            #1;
            gnt = 4'b0000;
            if (owner == 0)
                for (k = 4; k >= 1; k = k - 1) begin
                    idx = (last + k) % 4;
                    if (req[idx]) gnt = 4'b0001 << idx;
                end
            sel  = (owner != 0) ? owner : gnt;
            send = ((sel & req) != 0) && !full_in;
            exp_pop = send ? sel : 4'b0000;
            case (sel)
                4'b0001: sel_flit = flit0;
                4'b0010: sel_flit = flit1;
                4'b0100: sel_flit = flit2;
                4'b1000: sel_flit = flit3;
                default: sel_flit = 32'h6000_0000;
            endcase
            if (pop !== exp_pop) begin
                errors = errors + 1; $display("FAIL cycle %0d: req %b owner %b: pop=%b, expected %b", cyc, req, owner, pop, exp_pop);
            end
            if (errors > 20) begin $display("FAIL: too many errors"); $finish; end
            if (owner != 0) held_cycles = held_cycles + 1;
            if ((sel & req) != 0 && full_in) blocked = blocked + 1;
            @(posedge clk);
            if (send) begin
                sent = sent + 1;
                exp_out = sel_flit;
                if (owner == 0)
                    for (k = 0; k < 4; k = k + 1) if (gnt[k]) last = k;
                owner = (sel_flit[30:29] == 2'b10) ? 4'b0000 : sel;
            end else
                exp_out = 32'h6000_0000;
        end
        if (held_cycles == 0 || blocked == 0) begin
            errors = errors + 1; $display("FAIL: corner cases not reached (held %0d, blocked %0d)", held_cycles, blocked);
        end
        if (errors == 0) $display("ALL TESTS PASSED (%0d cycles, %0d flits sent, %0d cycles held, %0d blocked by full_in)", cyc, sent, held_cycles, blocked);
        else $display("FAIL: %0d errors", errors);
        $finish;
    end
endmodule
