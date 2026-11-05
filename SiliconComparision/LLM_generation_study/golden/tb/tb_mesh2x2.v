`timescale 1ns/1ps
// 2x2 mesh of four golden routers, wired as top_4_router of the board-verified original
// (r1 8'h00, r2 8'h01, r3 8'h10, r4 8'h11; unused edge inputs idle, unused edge full_in low).
// Part 1 replays the packets the original was tested with on the ZedBoard (Outputs_2x2/*.png): r1's core
// sends head, payload and tail flits to r2, r3 and r4. Each must arrive unchanged, in order, at that core only.
// Part 2: every core sends random packets to the 3 other cores under random core backpressure; a scoreboard
// checks order per source and destination, packet integrity, and that everything is delivered.
module mesh2x2 (
    input         clk,
    input         reset,
    input  [31:0] din1, din2, din3, din4,
    input         fin1, fin2, fin3, fin4,
    output [31:0] dout1, dout2, dout3, dout4,
    output        fout1, fout2, fout3, fout4
);
    localparam [31:0] IDLE = 32'h6000_0000;
    wire [31:0] r1_l1, r1_l3, r2_l1, r2_l4, r3_l2, r3_l3, r4_l2, r4_l4;
    wire [31:0] r1_l2, r1_l4, r2_l2, r2_l3, r3_l1, r3_l4, r4_l1, r4_l3;
    wire        f1_l1, f1_l3, f2_l1, f2_l4, f3_l2, f3_l3, f4_l2, f4_l4;
    wire        f1_l2, f1_l4, f2_l2, f2_l3, f3_l1, f3_l4, f4_l1, f4_l3;

    router_5port r1 (.clk(clk), .reset(reset), .current_address(8'h00),
        .data_in_link1(r3_l2), .data_in_link2(IDLE), .data_in_link3(r2_l4), .data_in_link4(IDLE), .data_in_core(din1),
        .full_in_link1(f3_l2), .full_in_link2(1'b0), .full_in_link3(f2_l4), .full_in_link4(1'b0), .full_in_core(fin1),
        .data_out_link1(r1_l1), .data_out_link2(r1_l2), .data_out_link3(r1_l3), .data_out_link4(r1_l4), .data_out_core(dout1),
        .full_out_link1(f1_l1), .full_out_link2(f1_l2), .full_out_link3(f1_l3), .full_out_link4(f1_l4), .full_out_core(fout1));
    router_5port r2 (.clk(clk), .reset(reset), .current_address(8'h01),
        .data_in_link1(r4_l2), .data_in_link2(IDLE), .data_in_link3(IDLE), .data_in_link4(r1_l3), .data_in_core(din2),
        .full_in_link1(f4_l2), .full_in_link2(1'b0), .full_in_link3(1'b0), .full_in_link4(f1_l3), .full_in_core(fin2),
        .data_out_link1(r2_l1), .data_out_link2(r2_l2), .data_out_link3(r2_l3), .data_out_link4(r2_l4), .data_out_core(dout2),
        .full_out_link1(f2_l1), .full_out_link2(f2_l2), .full_out_link3(f2_l3), .full_out_link4(f2_l4), .full_out_core(fout2));
    router_5port r3 (.clk(clk), .reset(reset), .current_address(8'h10),
        .data_in_link1(IDLE), .data_in_link2(r1_l1), .data_in_link3(r4_l4), .data_in_link4(IDLE), .data_in_core(din3),
        .full_in_link1(1'b0), .full_in_link2(f1_l1), .full_in_link3(f4_l4), .full_in_link4(1'b0), .full_in_core(fin3),
        .data_out_link1(r3_l1), .data_out_link2(r3_l2), .data_out_link3(r3_l3), .data_out_link4(r3_l4), .data_out_core(dout3),
        .full_out_link1(f3_l1), .full_out_link2(f3_l2), .full_out_link3(f3_l3), .full_out_link4(f3_l4), .full_out_core(fout3));
    router_5port r4 (.clk(clk), .reset(reset), .current_address(8'h11),
        .data_in_link1(IDLE), .data_in_link2(r2_l1), .data_in_link3(IDLE), .data_in_link4(r3_l3), .data_in_core(din4),
        .full_in_link1(1'b0), .full_in_link2(f2_l1), .full_in_link3(1'b0), .full_in_link4(f3_l3), .full_in_core(fin4),
        .data_out_link1(r4_l1), .data_out_link2(r4_l2), .data_out_link3(r4_l3), .data_out_link4(r4_l4), .data_out_core(dout4),
        .full_out_link1(f4_l1), .full_out_link2(f4_l2), .full_out_link3(f4_l3), .full_out_link4(f4_l4), .full_out_core(fout4));
endmodule

module tb;
    localparam NPKT = 300, QN = 2048, IDLE = 32'h6000_0000;
    reg clk = 0, reset = 1;
    reg  [31:0] din [0:3];
    reg         fin [0:3];
    wire [31:0] d1, d2, d3, d4;
    wire        fo1, fo2, fo3, fo4;

    mesh2x2 mesh (.clk(clk), .reset(reset), .din1(din[0]), .din2(din[1]), .din3(din[2]), .din4(din[3]),
                  .fin1(fin[0]), .fin2(fin[1]), .fin3(fin[2]), .fin4(fin[3]),
                  .dout1(d1), .dout2(d2), .dout3(d3), .dout4(d4), .fout1(fo1), .fout2(fo2), .fout3(fo3), .fout4(fo4));

    always #5 clk = ~clk;

    function [31:0] dout_of; input integer p;
        dout_of = (p == 0) ? d1 : (p == 1) ? d2 : (p == 2) ? d3 : d4;
    endfunction
    function fout_of; input integer p;
        fout_of = (p == 0) ? fo1 : (p == 1) ? fo2 : (p == 2) ? fo3 : fo4;
    endfunction
    function [7:0] addr_of; input integer p;
        addr_of = (p == 0) ? 8'h00 : (p == 1) ? 8'h01 : (p == 2) ? 8'h10 : 8'h11;
    endfunction

    reg [31:0] exq [0:16*QN-1];
    integer exh [0:15], ext [0:15];
    integer pkts [0:3], plen [0:3], pidx [0:3], pdst [0:3];
    reg     fprev [0:3], busy [0:3], finprev [0:3];
    integer bsrc [0:3];
    integer cyc = 0, k, o, s, q, bd, bf, errors = 0, sent = 0, recv = 0, seed = 31, drain, pending, board_ok = 0;
    reg [31:0] f, d;

    task fail; input [8*80-1:0] msg; begin
        errors = errors + 1;
        if (errors <= 20) $display("FAIL cycle %0d: %0s", cyc, msg);
    end endtask

    task push; input integer src; input integer dst; input [31:0] fl; begin
        q = src * 4 + dst; exq[q * QN + ext[q]] = fl; ext[q] = ext[q] + 1; sent = sent + 1;
    end endtask

    // every negedge: check core outputs against the scoreboard, then set new core backpressure
    task check_cores; input random_backpressure; begin
        for (o = 0; o < 4; o = o + 1) begin
            d = dout_of(o);
            if (d[30:29] != 2'b11) begin
                if (finprev[o]) fail("flit sent to a core while its full_in was high");
                s = -1;
                for (k = 0; k < 4; k = k + 1)
                    if (k != o && exh[k * 4 + o] != ext[k * 4 + o] && exq[(k * 4 + o) * QN + exh[k * 4 + o]] === d) s = k;
                if (s < 0) begin
                    fail("flit at a core that is not the next one expected from any source");
                    $display("    core %0d got %h", o + 1, d);
                end else begin
                    if (busy[o] && s != bsrc[o]) fail("packets interleaved at a core");
                    if (d[30:29] == 2'b01) begin
                        if (busy[o]) fail("head flit inside a packet");
                        busy[o] = 1; bsrc[o] = s;
                    end else if (!busy[o]) fail("body or tail flit without a head flit");
                    if (d[30:29] == 2'b10) busy[o] = 0;
                    exh[s * 4 + o] = exh[s * 4 + o] + 1;
                    recv = recv + 1;
                end
            end
            fin[o] = random_backpressure ? (($random(seed) & 3) == 0) : 1'b0;
            finprev[o] = fin[o];
        end
    end endtask

    initial begin
        for (k = 0; k < 4; k = k + 1) begin
            din[k] = IDLE; fin[k] = 0; pkts[k] = 0; pidx[k] = 0; fprev[k] = 0; busy[k] = 0; finprev[k] = 0;
        end
        for (q = 0; q < 16; q = q + 1) begin exh[q] = 0; ext[q] = 0; end
        repeat (4) @(negedge clk);
        reset = 0;

        // Part 1: the board test, one flit at a time as with the VIO
        for (bd = 1; bd < 4; bd = bd + 1) begin : board
            reg [31:0] pk [0:2];
            pk[0] = (bd == 1) ? 32'h2000_0001 : (bd == 2) ? 32'h2000_0010 : 32'h2000_0011;
            pk[1] = (bd == 1) ? 32'h000F_0001 : (bd == 2) ? 32'h01F0_0010 : 32'h0011_0011;
            pk[2] = (bd == 1) ? 32'h4000_0001 : (bd == 2) ? 32'h4000_0010 : 32'h4000_0011;
            for (bf = 0; bf < 3; bf = bf + 1) begin
                @(negedge clk); cyc = cyc + 1; check_cores(0);
                din[0] = pk[bf]; push(0, bd, pk[bf]);
                @(negedge clk); cyc = cyc + 1; check_cores(0);
                din[0] = IDLE;
                repeat (8) begin @(negedge clk); cyc = cyc + 1; check_cores(0); end
            end
        end
        pending = 0;
        for (q = 0; q < 16; q = q + 1) pending = pending + ext[q] - exh[q];
        if (pending == 0 && errors == 0) board_ok = 1;
        else fail("board test packets not delivered as on the ZedBoard");

        // Part 2: random all-to-all traffic
        drain = 0;
        while (drain < 3000 && cyc < 200000) begin
            @(negedge clk);
            cyc = cyc + 1;
            check_cores(1);
            for (k = 0; k < 4; k = k + 1) begin
                din[k] = IDLE;
                if (!fprev[k] && pkts[k] < NPKT && ($random(seed) & 3) != 0) begin
                    if (pidx[k] == 0) begin
                        pdst[k] = ($random(seed) & 32'h7fffffff) % 3;
                        if (pdst[k] >= k) pdst[k] = pdst[k] + 1;
                        plen[k] = 2 + (($random(seed) & 32'h7fffffff) % 5);
                    end
                    f = $random(seed);
                    f[30:29] = (pidx[k] == 0) ? 2'b01 : (pidx[k] == plen[k] - 1) ? 2'b10 : 2'b00;
                    f[26:24] = k;
                    f[23:16] = pkts[k];
                    f[15:8]  = pidx[k];
                    if (pidx[k] == 0) f[7:0] = addr_of(pdst[k]);
                    din[k] = f;
                    push(k, pdst[k], f);
                    pidx[k] = pidx[k] + 1;
                    if (pidx[k] == plen[k]) begin pidx[k] = 0; pkts[k] = pkts[k] + 1; end
                end
                fprev[k] = fout_of(k);
            end
            pending = 0;
            for (q = 0; q < 16; q = q + 1) pending = pending + ext[q] - exh[q];
            if (pkts[0] + pkts[1] + pkts[2] + pkts[3] == 4 * NPKT) begin
                if (pending == 0) drain = 3000; else drain = drain + 1;
            end
        end
        if (pending != 0) fail("flits never delivered (lost or deadlock)");
        if (errors == 0)
            $display("ALL TESTS PASSED (board test: 9 flits to r2, r3, r4 delivered; random: %0d packets, %0d flits, %0d cycles)",
                     4 * NPKT, recv - 9, cyc);
        else $display("FAIL: %0d errors, board test %0s, %0d of %0d flits received", errors, board_ok ? "ok" : "failed", recv, sent);
        $finish;
    end
endmodule
