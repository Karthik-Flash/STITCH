// SIGN-OFF copy of golden/tb/tb_input_port.v, made by scripts/make_tasks.py: seed + 1000, twice the traffic.
`timescale 1ns/1ps
// input_port: random flit stream (head, body, tail and idle flits) and random reads against a model of the
// buffer and of the held route; checks flit, req and full_out every cycle.
module tb;
    reg clk = 0, reset = 1, rd_en = 0;
    reg  [31:0] data_in = 32'h6000_0000;
    reg  [7:0]  current_address = 8'h11;
    wire        full_out;
    wire [31:0] flit;
    wire [4:0]  req;

    input_port dut (.clk(clk), .reset(reset), .data_in(data_in), .current_address(current_address),
                    .rd_en(rd_en), .full_out(full_out), .flit(flit), .req(req));

    always #5 clk = ~clk;

    function [4:0] route;
        input [31:0] f;
        input [7:0]  a;
        begin
            if (f[30:29] != 2'b01)      route = 5'b00000;
            else if (f[7:4] > a[7:4])   route = 5'b00001;
            else if (f[7:4] < a[7:4])   route = 5'b00010;
            else if (f[3:0] > a[3:0])   route = 5'b00100;
            else if (f[3:0] < a[3:0])   route = 5'b01000;
            else                        route = 5'b10000;
        end
    endfunction

    reg [31:0] q [0:3];
    reg [4:0]  held = 0, exp_req;
    reg        do_wr, do_rd;
    integer head = 0, count = 0, errors = 0, cyc, seed = 1013, writes = 0, held_used = 0;

    initial begin
        repeat (3) @(negedge clk);
        reset = 0;
        for (cyc = 0; cyc < 60000; cyc = cyc + 1) begin
            @(negedge clk);
            exp_req = (count == 0) ? 5'b00000 :
                      (q[head][30:29] == 2'b01) ? route(q[head], current_address) : held;
            if (full_out !== (count >= 3)) begin
                errors = errors + 1; $display("FAIL cycle %0d: full_out=%b, model count %0d", cyc, full_out, count);
            end
            if (count > 0 && flit !== q[head]) begin
                errors = errors + 1; $display("FAIL cycle %0d: flit=%h, expected %h", cyc, flit, q[head]);
            end
            if (req !== exp_req) begin
                errors = errors + 1; $display("FAIL cycle %0d: req=%b, expected %b", cyc, req, exp_req);
            end
            if (count > 0 && q[head][30:29] != 2'b01 && held != 0) held_used = held_used + 1;
            if (errors > 20) begin $display("FAIL: too many errors"); $finish; end
            data_in = $random(seed);
            data_in[7:4] = $random(seed) & 3;
            data_in[3:0] = $random(seed) & 3;
            rd_en = ((cyc / 700) % 2 == 0) ? ($random(seed) % 3 == 0) : ($random(seed) % 3 != 0);
            if (cyc % 1000 == 999) begin
                current_address[7:4] = $random(seed) & 3;
                current_address[3:0] = $random(seed) & 3;
            end
            @(posedge clk);
            do_wr = (data_in[30:29] != 2'b11) && (count != 4);
            do_rd = rd_en && (count != 0);
            if (do_rd) begin
                if (q[head][30:29] == 2'b01) held = route(q[head], current_address);
                head = (head + 1) % 4; count = count - 1;
            end
            if (do_wr) begin
                q[(head + count) % 4] = data_in; count = count + 1; writes = writes + 1;
            end
        end
        if (held_used == 0) begin errors = errors + 1; $display("FAIL: held route never exercised"); end
        if (errors == 0) $display("ALL TESTS PASSED (%0d cycles, %0d flits written, held route used %0d times)", cyc, writes, held_used);
        else $display("FAIL: %0d errors", errors);
        $finish;
    end
endmodule
