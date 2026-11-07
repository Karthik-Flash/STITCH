// SIGN-OFF copy of golden/tb/tb_router_5port.v, made by scripts/make_tasks.py: seed + 1000, twice the traffic.
`timescale 1ns/1ps
// router_5port: random wormhole traffic on all 5 inputs with random backpressure on all 5 outputs.
// Router address 8'h11; destinations are those a row-first mesh delivers to each input (no U-turn).
// Senders use the full_out timing of a neighbouring router (worst case: a flit sampled at edge k+1 was
// decided from full_out during cycle k-1). A scoreboard checks, at every output:
//   - each flit is the next expected flit of its source for that output (right port, order, no loss or copy),
//   - packets are not interleaved and start with a head flit,
//   - no flit leaves while the downstream full_in was high,
// and, at the end, that every flit was delivered and the router is idle again.
module tb;
    localparam NPKT = 800, QN = 8192, IDLE = 32'h6000_0000;

    reg clk = 0, reset = 1;
    reg  [7:0]  addr = 8'h11;
    reg  [31:0] din [0:4];
    reg         fin [0:4];
    wire [31:0] do0, do1, do2, do3, do4;
    wire        fo0, fo1, fo2, fo3, fo4;

    router_5port dut (
        .clk(clk), .reset(reset), .current_address(addr),
        .data_in_link1(din[0]), .data_in_link2(din[1]), .data_in_link3(din[2]), .data_in_link4(din[3]),
        .data_in_core(din[4]),
        .full_in_link1(fin[0]), .full_in_link2(fin[1]), .full_in_link3(fin[2]), .full_in_link4(fin[3]),
        .full_in_core(fin[4]),
        .data_out_link1(do0), .data_out_link2(do1), .data_out_link3(do2), .data_out_link4(do3),
        .data_out_core(do4),
        .full_out_link1(fo0), .full_out_link2(fo1), .full_out_link3(fo2), .full_out_link4(fo3),
        .full_out_core(fo4));

    always #5 clk = ~clk;

    function [31:0] dout_of; input integer p;
        dout_of = (p == 0) ? do0 : (p == 1) ? do1 : (p == 2) ? do2 : (p == 3) ? do3 : do4;
    endfunction
    function fout_of; input integer p;
        fout_of = (p == 0) ? fo0 : (p == 1) ? fo1 : (p == 2) ? fo2 : (p == 3) ? fo3 : fo4;
    endfunction
    function integer route_port; input [7:0] d;   // output index for destination d at address addr
        route_port = (d[7:4] > addr[7:4]) ? 0 : (d[7:4] < addr[7:4]) ? 1 :
                     (d[3:0] > addr[3:0]) ? 2 : (d[3:0] < addr[3:0]) ? 3 : 4;
    endfunction
    function legal; input integer k; input integer r; input integer c;   // what a row-first mesh delivers to input k
        legal = (k == 0) ? (r <= 1) : (k == 1) ? (r >= 1) : (k == 2) ? (r == 1 && c <= 1) :
                (k == 3) ? (r == 1 && c >= 1) : !(r == 1 && c == 1);
    endfunction

    // expected flits per (source, output)
    reg [31:0] exq [0:25*QN-1];
    integer exh [0:24], ext [0:24];
    // sender state
    integer pkts [0:4], plen [0:4], pidx [0:4], pout [0:4];
    reg [7:0] pdst [0:4];
    reg       fprev [0:4];
    // receiver state
    reg       busy [0:4], finprev [0:4];
    integer   bsrc [0:4];

    integer cyc = 0, k, o, r, c, s, q, errors = 0, sent = 0, recv = 0, stalls = 0, seed = 1021, drain, fullc = 0;
    reg [31:0] f, d;

    task fail; input [8*80-1:0] msg; begin
        errors = errors + 1;
        if (errors <= 20) $display("FAIL cycle %0d: %0s", cyc, msg);
    end endtask

    task drive_senders; begin
        for (k = 0; k < 5; k = k + 1) begin
            din[k] = IDLE;
            if (!fprev[k] && pkts[k] < NPKT && ($random(seed) & 7) < 4 + (cyc / 3000) % 4) begin
                if (pidx[k] == 0) begin
                    r = $random(seed) & 3; c = $random(seed) & 3;
                    while (r > 2 || c > 2 || !legal(k, r, c)) begin r = $random(seed) & 3; c = $random(seed) & 3; end
                    pdst[k] = {r[3:0], c[3:0]};
                    pout[k] = route_port(pdst[k]);
                    plen[k] = 2 + (($random(seed) & 32'h7fffffff) % 5);
                end
                f = $random(seed);
                f[30:29] = (pidx[k] == 0) ? 2'b01 : (pidx[k] == plen[k] - 1) ? 2'b10 : 2'b00;
                f[26:24] = k;
                f[23:16] = pkts[k];
                f[15:8]  = pidx[k];
                if (pidx[k] == 0) f[7:0] = pdst[k];
                din[k] = f;
                q = (k * 5 + pout[k]);
                exq[q * QN + ext[q]] = f; ext[q] = ext[q] + 1;
                sent = sent + 1;
                pidx[k] = pidx[k] + 1;
                if (pidx[k] == plen[k]) begin pidx[k] = 0; pkts[k] = pkts[k] + 1; end
            end
            fprev[k] = fout_of(k);
            if (fprev[k]) fullc = fullc + 1;
        end
    end endtask

    task check_outputs; begin
        for (o = 0; o < 5; o = o + 1) begin
            d = dout_of(o);
            if (d[30:29] != 2'b11) begin
                s = d[26:24];
                if (finprev[o]) fail("flit sent while full_in was high");
                if (s > 4 || s == o) fail("flit from an impossible source (U-turn or corrupted)");
                else begin
                    if (busy[o] && s != bsrc[o]) fail("packets interleaved on one output");
                    if (d[30:29] == 2'b01) begin
                        if (busy[o]) fail("head flit inside a packet");
                        busy[o] = 1; bsrc[o] = s;
                    end else if (!busy[o]) fail("body or tail flit without a head flit");
                    if (d[30:29] == 2'b10) busy[o] = 0;
                    q = s * 5 + o;
                    if (exh[q] == ext[q]) fail("unexpected flit (misrouted or duplicated)");
                    else begin
                        if (d !== exq[q * QN + exh[q]]) begin
                            fail("flit differs from the next expected one");
                            $display("    output %0d got %h, expected %h", o, d, exq[q * QN + exh[q]]);
                        end
                        exh[q] = exh[q] + 1;
                    end
                    recv = recv + 1;
                end
            end
            // new backpressure; phases: none, light, heavy, long stalls
            case (((cyc / 1500) + o) % 4)
                0: fin[o] = 0;
                1: fin[o] = ($random(seed) & 7) < 2;
                2: fin[o] = ($random(seed) & 7) != 0;
                default: fin[o] = (cyc % 100) < 50;
            endcase
            if (fin[o]) stalls = stalls + 1;
            finprev[o] = fin[o];
        end
    end endtask

    integer pending;
    initial begin
        for (k = 0; k < 5; k = k + 1) begin
            din[k] = IDLE; fin[k] = 0; pkts[k] = 0; pidx[k] = 0; fprev[k] = 0; busy[k] = 0; finprev[k] = 0;
        end
        for (q = 0; q < 25; q = q + 1) begin exh[q] = 0; ext[q] = 0; end
        repeat (4) @(negedge clk);
        reset = 0;
        @(negedge clk);
        if (do0 !== IDLE || do1 !== IDLE || do2 !== IDLE || do3 !== IDLE || do4 !== IDLE) fail("outputs not idle after reset");
        if (fo0 || fo1 || fo2 || fo3 || fo4) fail("full_out high after reset");
        drain = 0;
        while (drain < 3000 && cyc < 200000) begin
            @(negedge clk);
            cyc = cyc + 1;
            check_outputs;
            drive_senders;
            pending = 0;
            for (q = 0; q < 25; q = q + 1) pending = pending + ext[q] - exh[q];
            if (pkts[0] + pkts[1] + pkts[2] + pkts[3] + pkts[4] == 5 * NPKT) begin
                if (pending == 0) drain = 3000; else drain = drain + 1;
            end
        end
        if (cyc >= 100000) fail("traffic not finished after 100000 cycles");
        if (pending != 0) fail("flits never delivered (lost or deadlock)");
        repeat (4) @(negedge clk);
        if (do0 !== IDLE || do1 !== IDLE || do2 !== IDLE || do3 !== IDLE || do4 !== IDLE) fail("outputs not idle at the end");
        if (fo0 || fo1 || fo2 || fo3 || fo4) fail("full_out high at the end");
        if (fullc == 0) fail("full_out never went high (buffers never filled)");
        if (errors == 0)
            $display("ALL TESTS PASSED (%0d cycles, %0d packets, %0d flits sent and received, %0d output stall cycles, %0d full_out cycles)",
                     cyc, 5 * NPKT, recv, stalls, fullc);
        else $display("FAIL: %0d errors, %0d of %0d flits received, %0d pending", errors, recv, sent, pending);
        $finish;
    end
endmodule
