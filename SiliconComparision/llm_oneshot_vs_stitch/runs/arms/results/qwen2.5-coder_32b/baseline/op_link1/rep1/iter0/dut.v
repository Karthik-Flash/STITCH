module op_link1 (
    input rd_clk, reset, req_link2_vc1, req_link2_vc2, req_link2_vc3, req_link2_vc4, req_link3_vc1, req_link3_vc2,
          req_link3_vc3, req_link3_vc4, req_link4_vc1, req_link4_vc2, req_link4_vc3, req_link4_vc4, req_core_vc1,
          req_core_vc2, req_core_vc3, req_core_vc4, rok_link1_vc1, rok_link1_vc2, rok_link1_vc3, rok_link1_vc4,
          rok_link2_vc1, rok_link2_vc2, rok_link2_vc3, rok_link2_vc4, rok_link3_vc1, rok_link3_vc2, rok_link3_vc3,
          rok_link3_vc4, rok_link4_vc1, rok_link4_vc2, rok_link4_vc3, rok_link4_vc4, rok_core_vc1, rok_core_vc2,
          rok_core_vc3, rok_core_vc4, tailer_link2_vc1, tailer_link2_vc2, tailer_link2_vc3, tailer_link2_vc4,
          tailer_link3_vc1, tailer_link3_vc2, tailer_link3_vc3, tailer_link3_vc4, tailer_link4_vc1,
          tailer_link4_vc2, tailer_link4_vc3, tailer_link4_vc4, tailer_core_vc1, tailer_core_vc2, tailer_core_vc3,
          tailer_core_vc4, full_vc1, full_vc2, full_vc3, full_vc4,
    output rd_en_vc1_link2_vc1, rd_en_vc1_link2_vc2, rd_en_vc1_link2_vc3, rd_en_vc1_link2_vc4,
           rd_en_vc1_link3_vc1, rd_en_vc1_link3_vc2, rd_en_vc1_link3_vc3, rd_en_vc1_link3_vc4,
           rd_en_vc1_link4_vc1, rd_en_vc1_link4_vc2, rd_en_vc1_link4_vc3, rd_en_vc1_link4_vc4, rd_en_vc1_core_vc1,
           rd_en_vc1_core_vc2, rd_en_vc1_core_vc3, rd_en_vc1_core_vc4, rd_en_vc2_link2_vc1, rd_en_vc2_link2_vc2,
           rd_en_vc2_link2_vc3, rd_en_vc2_link2_vc4, rd_en_vc2_link3_vc1, rd_en_vc2_link3_vc2,
           rd_en_vc2_link3_vc3, rd_en_vc2_link3_vc4, rd_en_vc2_link4_vc1, rd_en_vc2_link4_vc2,
           rd_en_vc2_link4_vc3, rd_en_vc2_link4_vc4, rd_en_vc2_core_vc1, rd_en_vc2_core_vc2, rd_en_vc2_core_vc3,
           rd_en_vc2_core_vc4, rd_en_vc3_link2_vc1, rd_en_vc3_link2_vc2, rd_en_vc3_link2_vc3, rd_en_vc3_link2_vc4,
           rd_en_vc3_link3_vc1, rd_en_vc3_link3_vc2, rd_en_vc3_link3_vc3, rd_en_vc3_link3_vc4,
           rd_en_vc3_link4_vc1, rd_en_vc3_link4_vc2, rd_en_vc3_link4_vc3, rd_en_vc3_link4_vc4, rd_en_vc3_core_vc1,
           rd_en_vc3_core_vc2, rd_en_vc3_core_vc3, rd_en_vc3_core_vc4, rd_en_vc4_link2_vc1, rd_en_vc4_link2_vc2,
           rd_en_vc4_link2_vc3, rd_en_vc4_link2_vc4, rd_en_vc4_link3_vc1, rd_en_vc4_link3_vc2,
           rd_en_vc4_link3_vc3, rd_en_vc4_link3_vc4, rd_en_vc4_link4_vc1, rd_en_vc4_link4_vc2,
           rd_en_vc4_link4_vc3, rd_en_vc4_link4_vc4, rd_en_vc4_core_vc1, rd_en_vc4_core_vc2, rd_en_vc4_core_vc3,
           rd_en_vc4_core_vc4, gnt_vc1, gnt_vc2, gnt_vc3, gnt_vc4,
    output [3:0] ip_link_vc,
    output all_vc_not_busy, ready_vc1, ready_vc2, ready_vc3, ready_vc4, b1, b2, b3, b4, mux_rok_out_vc1,
           mux_rok_out_vc2, mux_rok_out_vc3, mux_rok_out_vc4
);

    wire [3:0] encoded_addr;
    wire g1, g2, g3, g4, g5, g6, g7, g8, g9, g10, g11, g12, g13, g14, g15, g16;
    wire link_1, vc_id_1, link_2, vc_id_2, link_3, vc_id_3, link_4, vc_id_4;
    wire b1_int, b2_int, b3_int, b4_int;
    wire tailer1, tailer2, tailer3, tailer4, tailer5, tailer6, tailer7, tailer8, tailer9, tailer10, tailer11, tailer12, tailer13, tailer14, tailer15, tailer16;
    wire gnt_or, ce_b1, ce_b2, ce_b3, ce_b4, clr_b1, clr_b2, clr_b3, clr_b4, e1, e2, e3, e4;
    wire [15:1] req;
    wire [3:0] ip;
    wire [3:0] sel;
    wire [15:1] rd_en;
    wire [3:0] mux_rok_out;
    wire [3:0] mux_full_out;
    wire [3:0] mux_rok;
    wire [3:0] mux_full;
    wire [3:0] ready;
    wire [3:0] gnt;
    wire [3:0] gnt_int;
    wire [3:0] b;
    wire [3:0] b_logic;
    wire [3:0] b0_logic;
    wire [3:0] b0;

    assign req[1] = req_link2_vc1;
    assign req[2] = req_link2_vc2;
    assign req[3] = req_link2_vc3;
    assign req[4] = req_link2_vc4;
    assign req[5] = req_link3_vc1;
    assign req[6] = req_link3_vc2;
    assign req[7] = req_link3_vc3;
    assign req[8] = req_link3_vc4;
    assign req[9] = req_link4_vc1;
    assign req[10] = req_link4_vc2;
    assign req[11] = req_link4_vc3;
    assign req[12] = req_link4_vc4;
    assign req[13] = req_core_vc1;
    assign req[14] = req_core_vc2;
    assign req[15] = req_core_vc3;
    assign req[16] = req_core_vc4;

    assign tailer1 = tailer_link2_vc1;
    assign tailer2 = tailer_link2_vc2;
    assign tailer3 = tailer_link2_vc3;
    assign tailer4 = tailer_link2_vc4;
    assign tailer5 = tailer_link3_vc1;
    assign tailer6 = tailer_link3_vc2;
    assign tailer7 = tailer_link3_vc3;
    assign tailer8 = tailer_link3_vc4;
    assign tailer9 = tailer_link4_vc1;
    assign tailer10 = tailer_link4_vc2;
    assign tailer11 = tailer_link4_vc3;
    assign tailer12 = tailer_link4_vc4;
    assign tailer13 = tailer_core_vc1;
    assign tailer14 = tailer_core_vc2;
    assign tailer15 = tailer_core_vc3;
    assign tailer16 = tailer_core_vc4;

    assign mux_rok[1] = rok_link2_vc1;
    assign mux_rok[2] = rok_link2_vc2;
    assign mux_rok[3] = rok_link2_vc3;
    assign mux_rok[4] = rok_link2_vc4;
    assign mux_rok[5] = rok_link3_vc1;
    assign mux_rok[6] = rok_link3_vc2;
    assign mux_rok[7] = rok_link3_vc3;
    assign mux_rok[8] = rok_link3_vc4;
    assign mux_rok[9] = rok_link4_vc1;
    assign mux_rok[10] = rok_link4_vc2;
    assign mux_rok[11] = rok_link4_vc3;
    assign mux_rok[12] = rok_link4_vc4;
    assign mux_rok[13] = rok_core_vc1;
    assign mux_rok[14] = rok_core_vc2;
    assign mux_rok[15] = rok_core_vc3;
    assign mux_rok[16] = rok_core_vc4;

    assign mux_full[1] = full_vc1;
    assign mux_full[2] = full_vc2;
    assign mux_full[3] = full_vc3;
    assign mux_full[4] = full_vc4;

    round_robin_req u_round_robin_req (
        .reset(reset),
        .rd_clk(rd_clk),
        .all_vc_not_busy(all_vc_not_busy),
        .req_1(req[1]), .req_2(req[2]), .req_3(req[3]), .req_4(req[4]), .req_5(req[5]), .req_6(req[6]), .req_7(req[7]), .req_8(req[8]),
        .req_9(req[9]), .req_10(req[10]), .req_11(req[11]), .req_12(req[12]), .req_13(req[13]), .req_14(req[14]), .req_15(req[15]), .req_16(req[16]),
        .g1(g1), .g2(g2), .g3(g3), .g4(g4), .g5(g5), .g6(g6), .g7(g7), .g8(g8), .g9(g9), .g10(g10), .g11(g11), .g12(g12), .g13(g13), .g14(g14), .g15(g15), .g16(g16),
        .tailer1(tailer1), .tailer2(tailer2), .tailer3(tailer3), .tailer4(tailer4), .tailer5(tailer5), .tailer6(tailer6), .tailer7(tailer7), .tailer8(tailer8),
        .tailer9(tailer9), .tailer10(tailer10), .tailer11(tailer11), .tailer12(tailer12), .tailer13(tailer13), .tailer14(tailer14), .tailer15(tailer15), .tailer16(tailer16),
        .g_b1(), .g_b2(), .g_b3(), .g_b4(),
        .gnt1(), .gnt2(), .gnt3(), .gnt4(), .gnt5(), .gnt6(), .gnt7(), .gnt8(), .gnt9(), .gnt10(), .gnt11(), .gnt12(), .gnt13(), .gnt14(), .gnt15(), .gnt16(),
        .req1(), .req2(), .req3(), .req4(), .req5(), .req6(), .req7(), .req8(), .req9(), .req10(), .req11(), .req12(), .req13(), .req14(), .req15(), .req16(),
        .g1_latched(), .g2_latched(), .g3_latched(), .g4_latched(), .g5_latched(), .g6_latched(), .g7_latched(), .g8_latched(), .g9_latched(), .g10_latched(), .g11_latched(), .g12_latched(), .g13_latched(), .g14_latched(), .g15_latched(), .g16_latched(),
        .g1_int(), .g2_int(), .g3_int(), .g4_int(), .g5_int(), .g6_int(), .g7_int(), .g8_int(), .g9_int(), .g10_int(), .g11_int(), .g12_int(), .g13_int(), .g14_int(), .g15_int(), .g16_int(),
        .t1(), .t2(), .t3(), .t4(),
        .req_b1(), .req_b2(), .req_b3(), .req_b4(),
        .nreq_1(), .nreq_2(), .nreq_3(), .nreq_4(), .nreq_5(), .nreq_6(), .nreq_7(), .nreq_8(), .nreq_9(), .nreq_10(), .nreq_11(), .nreq_12(), .nreq_13(), .nreq_14(), .nreq_15(), .nreq_16()
    );

    encoder u_encoder (
        .g1(g1), .g2(g2), .g3(g3), .g4(g4), .g5(g5), .g6(g6), .g7(g7), .g8(g8), .g9(g9), .g10(g10), .g11(g11), .g12(g12), .g13(g13), .g14(g14), .g15(g15), .g16(g16),
        .encoded_addr(encoded_addr)
    );

    allot_vc u_allot_vc (
        .reset(reset),
        .rd_clk(rd_clk),
        .encoded_addr(encoded_addr),
        .g1(g1), .g2(g2), .g3(g3), .g4(g4), .g5(g5), .g6(g6), .g7(g7), .g8(g8), .g9(g9), .g10(g10), .g11(g11), .g12(g12), .g13(g13), .g14(g14), .g15(g15), .g16(g16),
        .link_1(link_1), .vc_id_1(vc_id_1), .link_2(link_2), .vc_id_2(vc_id_2), .link_3(link_3), .vc_id_3(vc_id_3), .link_4(link_4), .vc_id_4(vc_id_4),
        .b1(b1_int), .b2(b2_int), .b3(b3_int), .b4(b4_int),
        .tailer1(tailer1), .tailer2(tailer2), .tailer3(tailer3), .tailer4(tailer4), .tailer5(tailer5), .tailer6(tailer6), .tailer7(tailer7), .tailer8(tailer8),
        .tailer9(tailer9), .tailer10(tailer10), .tailer11(tailer11), .tailer12(tailer12), .tailer13(tailer13), .tailer14(tailer14), .tailer15(tailer15), .tailer16(tailer16),
        .gnt_or(gnt_or),
        .ce_b1(ce_b1), .ce_b2(ce_b2), .ce_b3(ce_b3), .ce_b4(ce_b4),
        .clr_b1(clr_b1), .clr_b2(clr_b2), .clr_b3(clr_b3), .clr_b4(clr_b4),
        .e1(e1), .e2(e2), .e3(e3), .e4(e4)
    );

    assign ip = {link_4, vc_id_4, link_3, vc_id_3, link_2, vc_id_2, link_1, vc_id_1};
    assign sel = encoded_addr;

    demux_16 u_demux_16_1 (
        .ip(gnt_int[0]),
        .sel(sel),
        .op1(rd_en[1]), .op2(rd_en[2]), .op3(rd_en[3]), .op4(rd_en[4]), .op5(rd_en[5]), .op6(rd_en[6]), .op7(rd_en[7]), .op8(rd_en[8]),
        .op9(rd_en[9]), .op10(rd_en[10]), .op11(rd_en[11]), .op12(rd_en[12]), .op13(rd_en[13]), .op14(rd_en[14]), .op15(rd_en[15]), .op16(rd_en[16])
    );

    demux_16 u_demux_16_2 (
        .ip(gnt_int[1]),
        .sel(sel),
        .op1(rd_en[1]), .op2(rd_en[2]), .op3(rd_en[3]), .op4(rd_en[4]), .op5(rd_en[5]), .op6(rd_en[6]), .op7(rd_en[7]), .op8(rd_en[8]),
        .op9(rd_en[9]), .op10(rd_en[10]), .op11(rd_en[11]), .op12(rd_en[12]), .op13(rd_en[13]), .op14(rd_en[14]), .op15(rd_en[15]), .op16(rd_en[16])
    );

    demux_16 u_demux_16_3 (
        .ip(gnt_int[2]),
        .sel(sel),
        .op1(rd_en[1]), .op2(rd_en[2]), .op3(rd_en[3]), .op4(rd_en[4]), .op5(rd_en[5]), .op6(rd_en[6]), .op7(rd_en[7]), .op8(rd_en[8]),
        .op9(rd_en[9]), .op10(rd_en[10]), .op11(rd_en[11]), .op12(rd_en[12]), .op13(rd_en[13]), .op14(rd_en[14]), .op15(rd_en[15]), .op16(rd_en[16])
    );

    demux_16 u_demux_16_4 (
        .ip(gnt_int[3]),
        .sel(sel),
        .op1(rd_en[1]), .op2(rd_en[2]), .op3(rd_en[3]), .op4(rd_en[4]), .op5(rd_en[5]), .op6(rd_en[6]), .op7(rd_en[7]), .op8(rd_en[8]),
        .op9(rd_en[9]), .op10(rd_en[10]), .op11(rd_en[11]), .op12(rd_en[12]), .op13(rd_en[13]), .op14(rd_en[14]), .op15(rd_en[15]), .op16(rd_en[16])
    );

    rr_comb_new u_rr_comb_new (
        .reset(reset),
        .clk(rd_clk),
        .r1(ready[0]), .r2(ready[1]), .r3(ready[2]), .r4(ready[3]),
        .g1(gnt_int[0]), .g2(gnt_int[1]), .g3(gnt_int[2]), .g4(gnt_int[3]),
        .l1(), .l2(), .l3(), .l4(),
        .mux_out1(mux_rok_out[0]), .mux_out2(mux_rok_out[1]), .mux_out3(mux_rok_out[2]), .mux_out4(mux_rok_out[3]),
        .and_out1(), .and_out2(), .and_out3(), .and_out4(),
        .or_out(gnt_or),
        .b1(b1_int), .b0(b0),
        .b1_logic(b1_logic), .b0_logic(b0_logic)
    );

    always @(*) begin
        case (ip)
            4'b0001: ip_link_vc = 4'b0001;
            4'b0010: ip_link_vc = 4'b0010;
            4'b0011: ip_link_vc = 4'b0011;
            4'b0100: ip_link_vc = 4'b0100;
            4'b0101: ip_link_vc = 4'b0101;
            4'b0110: ip_link_vc = 4'b0110;
            4'b0111: ip_link_vc = 4'b0111;
            4'b1000: ip_link_vc = 4'b1000;
            4'b1001: ip_link_vc = 4'b1001;
            4'b1010: ip_link_vc = 4'b1010;
            4'b1011: ip_link_vc = 4'b1011;
            4'b1100: ip_link_vc = 4'b1100;
            4'b1101: ip_link_vc = 4'b1101;
            4'b1110: ip_link_vc = 4'b1110;
            4'b1111: ip_link_vc = 4'b1111;
            default: ip_link_vc = 4'b0000;
        endcase
    end

    always @(posedge rd_clk or posedge reset) begin
        if (reset) begin
            b1 <= 1'b0;
            b2 <= 1'b0;
            b3 <= 1'b0;
            b4 <= 1'b0;
        end else begin
            b1 <= (clr_b1) ? 1'b0 : (ce_b1) ? 1'b1 : b1;
            b2 <= (clr_b2) ? 1'b0 : (ce_b2) ? 1'b1 : b2;
            b3 <= (clr_b3) ? 1'b0 : (ce_b3) ? 1'b1 : b3;
            b4 <= (clr_b4) ? 1'b0 : (ce_b4) ? 1'b1 : b4;
        end
    end

    always @(*) begin
        ready[0] = b1_int & mux_rok_out[0] & ~mux_full_out[0];
        ready[1] = b2_int & mux_rok_out[1] & ~mux_full_out[1];
        ready[2] = b3_int & mux_rok_out[2] & ~mux_full_out[2];
        ready[3] = b4_int & mux_rok_out[3] & ~mux_full_out[3];
    end

    always @(*) begin
        case (encoded_addr)
            4'b0001: rd_en_vc1_link2_vc1 = rd_en[1];
            4'b0010: rd_en_vc1_link2_vc2 = rd_en[2];
            4'b0011: rd_en_vc1_link2_vc3 = rd_en[3];
            4'b0100: rd_en_vc1_link2_vc4 = rd_en[4];
            4'b0101: rd_en_vc1_link3_vc1 = rd_en[5];
            4'b0110: rd_en_vc1_link3_vc2 = rd_en[6];
            4'b0111: rd_en_vc1_link3_vc3 = rd_en[7];
            4'b1000: rd_en_vc1_link3_vc4 = rd_en[8];
            4'b1001: rd_en_vc1_link4_vc1 = rd_en[9];
            4'b1010: rd_en_vc1_link4_vc2 = rd_en[10];
            4'b1011: rd_en_vc1_link4_vc3 = rd_en[11];
            4'b1100: rd_en_vc1_link4_vc4 = rd_en[12];
            4'b1101: rd_en_vc1_core_vc1 = rd_en[13];
            4'b1110: rd_en_vc1_core_vc2 = rd_en[14];
            4'b1111: rd_en_vc1_core_vc3 = rd_en[15];
            default: rd_en_vc1_core_vc4 = rd_en[16];
        endcase
    end

    always @(*) begin
        case (encoded_addr)
            4'b0001: rd_en_vc2_link2_vc1 = rd_en[1];
            4'b0010: rd_en_vc2_link2_vc2 = rd_en[2];
            4'b0011: rd_en_vc2_link2_vc3 = rd_en[3];
            4'b0100: rd_en_vc2_link2_vc4 = rd_en[4];
            4'b0101: rd_en_vc2_link3_vc1 = rd_en[5];
            4'b0110: rd_en_vc2_link3_vc2 = rd_en[6];
            4'b0111: rd_en_vc2_link3_vc3 = rd_en[7];
            4'b1000: rd_en_vc2_link3_vc4 = rd_en[8];
            4'b1001: rd_en_vc2_link4_vc1 = rd_en[9];
            4'b1010: rd_en_vc2_link4_vc2 = rd_en[10];
            4'b1011: rd_en_vc2_link4_vc3 = rd_en[11];
            4'b1100: rd_en_vc2_link4_vc4 = rd_en[12];
            4'b1101: rd_en_vc2_core_vc1 = rd_en[13];
            4'b1110: rd_en_vc2_core_vc2 = rd_en[14];
            4'b1111: rd_en_vc2_core_vc3 = rd_en[15];
            default: rd_en_vc2_core_vc4 = rd_en[16];
        endcase
    end

    always @(*) begin
        case (encoded_addr)
            4'b0001: rd_en_vc3_link2_vc1 = rd_en[1];
            4'b0010: rd_en_vc3_link2_vc2 = rd_en[2];
            4'b0011: rd_en_vc3_link2_vc3 = rd_en[3];
            4'b0100: rd_en_vc3_link2_vc4 = rd_en[4];
            4'b0101: rd_en_vc3_link3_vc1 = rd_en[5];
            4'b0110: rd_en_vc3_link3_vc2 = rd_en[6];
            4'b0111: rd_en_vc3_link3_vc3 = rd_en[7];
            4'b1000: rd_en_vc3_link3_vc4 = rd_en[8];
            4'b1001: rd_en_vc3_link4_vc1 = rd_en[9];
            4'b1010: rd_en_vc3_link4_vc2 = rd_en[10];
            4'b1011: rd_en_vc3_link4_vc3 = rd_en[11];
            4'b1100: rd_en_vc3_link4_vc4 = rd_en[12];
            4'b1101: rd_en_vc3_core_vc1 = rd_en[13];
            4'b1110: rd_en_vc3_core_vc2 = rd_en[14];
            4'b1111: rd_en_vc3_core_vc3 = rd_en[15];
            default: rd_en_vc3_core_vc4 = rd_en[16];
        endcase
    end

    always @(*) begin
        case (encoded_addr)
            4'b0001: rd_en_vc4_link2_vc1 = rd_en[1];
            4'b0010: rd_en_vc4_link2_vc2 = rd_en[2];
            4'b0011: rd_en_vc4_link2_vc3 = rd_en[3];
            4'b0100: rd_en_vc4_link2_vc4 = rd_en[4];
            4'b0101: rd_en_vc4_link3_vc1 = rd_en[5];
            4'b0110: rd_en_vc4_link3_vc2 = rd_en[6];
            4'b0111: rd_en_vc4_link3_vc3 = rd_en[7];
            4'b1000: rd_en_vc4_link3_vc4 = rd_en[8];
            4'b1001: rd_en_vc4_link4_vc1 = rd_en[9];
            4'b1010: rd_en_vc4_link4_vc2 = rd_en[10];
            4'b1011: rd_en_vc4_link4_vc3 = rd_en[11];
            4'b1100: rd_en_vc4_link4_vc4 = rd_en[12];
            4'b1101: rd_en_vc4_core_vc1 = rd_en[13];
            4'b1110: rd_en_vc4_core_vc2 = rd_en[14];
            4'b1111: rd_en_vc4_core_vc3 = rd_en[15];
            default: rd_en_vc4_core_vc4 = rd_en[16];
        endcase
    end

    assign ready_vc1 = ready[0];
    assign ready_vc2 = ready[1];
    assign ready_vc3 = ready[2];
    assign ready_vc4 = ready[3];

    assign b1 = b1_int;
    assign b2 = b2_int;
    assign b3 = b3_int;
    assign b4 = b4_int;

    assign mux_rok_out_vc1 = mux_rok_out[0];
    assign mux_rok_out_vc2 = mux_rok_out[1];
    assign mux_rok_out_vc3 = mux_rok_out[2];
    assign mux_rok_out_vc4 = mux_rok_out[3];

    assign gnt_vc1 = gnt_int[0];
    assign gnt_vc2 = gnt_int[1];
    assign gnt_vc3 = gnt_int[2];
    assign gnt_vc4 = gnt_int[3];

endmodule
