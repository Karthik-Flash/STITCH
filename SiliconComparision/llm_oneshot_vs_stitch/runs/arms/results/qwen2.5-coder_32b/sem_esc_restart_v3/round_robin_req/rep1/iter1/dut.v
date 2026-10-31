module round_robin_req (
    input reset, rd_clk, all_vc_not_busy, req_1, req_2, req_3, req_4, req_5, req_6, req_7, req_8, req_9, req_10,
          req_11, req_12, req_13, req_14, req_15, req_16,
    output g1, g2, g3, g4, g5, g6, g7, g8, g9, g10, g11, g12, g13, g14, g15, g16,
    input tailer1, tailer2, tailer3, tailer4, tailer5, tailer6, tailer7, tailer8, tailer9, tailer10, tailer11,
          tailer12, tailer13, tailer14, tailer15, tailer16,
    output g_b1, g_b2, g_b3, g_b4, gnt1, gnt2, gnt3, gnt4, gnt5, gnt6, gnt7, gnt8, gnt9, gnt10, gnt11, gnt12,
           gnt13, gnt14, gnt15, gnt16, req1, req2, req3, req4, req5, req6, req7, req8, req9, req10, req11, req12,
           req13, req14, req15, req16, g1_latched, g2_latched, g3_latched, g4_latched, g5_latched, g6_latched,
           g7_latched, g8_latched, g9_latched, g10_latched, g11_latched, g12_latched, g13_latched, g14_latched,
           g15_latched, g16_latched, g1_int, g2_int, g3_int, g4_int, g5_int, g6_int, g7_int, g8_int, g9_int,
           g10_int, g11_int, g12_int, g13_int, g14_int, g15_int, g16_int, t1, t2, t3, t4, req_b1, req_b2, req_b3,
           req_b4, nreq_1, nreq_2, nreq_3, nreq_4, nreq_5, nreq_6, nreq_7, nreq_8, nreq_9, nreq_10, nreq_11,
           nreq_12, nreq_13, nreq_14, nreq_15, nreq_16
);

    wire [15:1] req;
    wire [15:1] gi;
    wire [15:1] gi_int;
    wire [15:1] gi_latched;
    wire [15:1] nreq;
    wire [4:1] req_b;
    wire [4:1] t;
    wire [15:1] gnt;

    assign req = {req_16, req_15, req_14, req_13, req_12, req_11, req_10, req_9, req_8, req_7, req_6, req_5, req_4, req_3, req_2, req_1};
    assign nreq = ~req;

    genvar i;
    generate
        for (i = 1; i <= 16; i = i + 1) begin : gen_gi
            assign gi[i] = gnt[i] & gi_latched[i];
        end
    endgenerate

    generate
        for (i = 1; i <= 16; i = i + 1) begin : gen_gi_int
            dff_synch_reset dff_gi_int (
                .d(gi[i]),
                .reset(reset),
                .clk(rd_clk),
                .q(gi_int[i])
            );
        end
    endgenerate

    generate
        for (i = 1; i <= 16; i = i + 1) begin : gen_gi_latched
            dff_asynch_clr dff_gi_latched (
                .d(gi_int[i]),
                .clr(nreq[i]),
                .clk(rd_clk),
                .q(gi_latched[i])
            );
        end
    endgenerate

    generate
        for (i = 1; i <= 16; i = i + 1) begin : gen_req
            assign req[i] = req[i] & ~gi_latched[i];
        end
    endgenerate

    assign req_b[1] = req[4] | req[3] | req[2] | req[1];
    assign req_b[2] = req[8] | req[7] | req[6] | req[5];
    assign req_b[3] = req[12] | req[11] | req[10] | req[9];
    assign req_b[4] = req[16] | req[15] | req[14] | req[13];

    assign t[1] = all_vc_not_busy & req_b[1];
    assign t[2] = all_vc_not_busy & req_b[2];
    assign t[3] = all_vc_not_busy & req_b[3];
    assign t[4] = all_vc_not_busy & req_b[4];

    rr_arbiter arb_group1 (
        .req1(req[1]),
        .req2(req[2]),
        .req3(req[3]),
        .req4(req[4]),
        .reset(reset),
        .gnt1(gnt[1]),
        .gnt2(gnt[2]),
        .gnt3(gnt[3]),
        .gnt4(gnt[4]),
        .clk(rd_clk)
    );

    rr_arbiter arb_group2 (
        .req1(req[5]),
        .req2(req[6]),
        .req3(req[7]),
        .req4(req[8]),
        .reset(reset),
        .gnt1(gnt[5]),
        .gnt2(gnt[6]),
        .gnt3(gnt[7]),
        .gnt4(gnt[8]),
        .clk(rd_clk)
    );

    rr_arbiter arb_group3 (
        .req1(req[9]),
        .req2(req[10]),
        .req3(req[11]),
        .req4(req[12]),
        .reset(reset),
        .gnt1(gnt[9]),
        .gnt2(gnt[10]),
        .gnt3(gnt[11]),
        .gnt4(gnt[12]),
        .clk(rd_clk)
    );

    rr_arbiter arb_group4 (
        .req1(req[13]),
        .req2(req[14]),
        .req3(req[15]),
        .req4(req[16]),
        .reset(reset),
        .gnt1(gnt[13]),
        .gnt2(gnt[14]),
        .gnt3(gnt[15]),
        .gnt4(gnt[16]),
        .clk(rd_clk)
    );

    rr_arbiter arb_top (
        .req1(t[1]),
        .req2(t[2]),
        .req3(t[3]),
        .req4(t[4]),
        .reset(reset),
        .gnt1(g_b1),
        .gnt2(g_b2),
        .gnt3(g_b3),
        .gnt4(g_b4),
        .clk(rd_clk)
    );

    assign g1 = gnt[1] & g_b1;
    assign g2 = gnt[2] & g_b1;
    assign g3 = gnt[3] & g_b1;
    assign g4 = gnt[4] & g_b1;
    assign g5 = gnt[5] & g_b2;
    assign g6 = gnt[6] & g_b2;
    assign g7 = gnt[7] & g_b2;
    assign g8 = gnt[8] & g_b2;
    assign g9 = gnt[9] & g_b3;
    assign g10 = gnt[10] & g_b3;
    assign g11 = gnt[11] & g_b3;
    assign g12 = gnt[12] & g_b3;
    assign g13 = gnt[13] & g_b4;
    assign g14 = gnt[14] & g_b4;
    assign g15 = gnt[15] & g_b4;
    assign g16 = gnt[16] & g_b4;

    assign req1 = req[1];
    assign req2 = req[2];
    assign req3 = req[3];
    assign req4 = req[4];
    assign req5 = req[5];
    assign req6 = req[6];
    assign req7 = req[7];
    assign req8 = req[8];
    assign req9 = req[9];
    assign req10 = req[10];
    assign req11 = req[11];
    assign req12 = req[12];
    assign req13 = req[13];
    assign req14 = req[14];
    assign req15 = req[15];
    assign req16 = req[16];

    assign g1_latched = gi_latched[1];
    assign g2_latched = gi_latched[2];
    assign g3_latched = gi_latched[3];
    assign g4_latched = gi_latched[4];
    assign g5_latched = gi_latched[5];
    assign g6_latched = gi_latched[6];
    assign g7_latched = gi_latched[7];
    assign g8_latched = gi_latched[8];
    assign g9_latched = gi_latched[9];
    assign g10_latched = gi_latched[10];
    assign g11_latched = gi_latched[11];
    assign g12_latched = gi_latched[12];
    assign g13_latched = gi_latched[13];
    assign g14_latched = gi_latched[14];
    assign g15_latched = gi_latched[15];
    assign g16_latched = gi_latched[16];

    assign g1_int = gi_int[1];
    assign g2_int = gi_int[2];
    assign g3_int = gi_int[3];
    assign g4_int = gi_int[4];
    assign g5_int = gi_int[5];
    assign g6_int = gi_int[6];
    assign g7_int = gi_int[7];
    assign g8_int = gi_int[8];
    assign g9_int = gi_int[9];
    assign g10_int = gi_int[10];
    assign g11_int = gi_int[11];
    assign g12_int = gi_int[12];
    assign g13_int = gi_int[13];
    assign g14_int = gi_int[14];
    assign g15_int = gi_int[15];
    assign g16_int = gi_int[16];

    assign req_b1 = req_b[1];
    assign req_b2 = req_b[2];
    assign req_b3 = req_b[3];
    assign req_b4 = req_b[4];

    assign t1 = t[1];
    assign t2 = t[2];
    assign t3 = t[3];
    assign t4 = t[4];

endmodule
