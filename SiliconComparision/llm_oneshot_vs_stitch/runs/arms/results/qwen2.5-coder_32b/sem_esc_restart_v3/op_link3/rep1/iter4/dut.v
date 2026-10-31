module op_link3 (
    input rd_clk, reset, req_link1_vc1, req_link1_vc2, req_link1_vc3, req_link1_vc4, req_link2_vc1, req_link2_vc2,
          req_link2_vc3, req_link2_vc4, req_link4_vc1, req_link4_vc2, req_link4_vc3, req_link4_vc4, req_core_vc1,
          req_core_vc2, req_core_vc3, req_core_vc4, rok_link1_vc1, rok_link1_vc2, rok_link1_vc3, rok_link1_vc4,
          rok_link2_vc1, rok_link2_vc2, rok_link2_vc3, rok_link2_vc4, rok_link4_vc1, rok_link4_vc2, rok_link4_vc3,
          rok_link4_vc4, rok_core_vc1, rok_core_vc2, rok_core_vc3, rok_core_vc4, tailer_link1_vc1,
          tailer_link1_vc2, tailer_link1_vc3, tailer_link1_vc4, tailer_link2_vc1, tailer_link2_vc2,
          tailer_link2_vc3, tailer_link2_vc4, tailer_link4_vc1, tailer_link4_vc2, tailer_link4_vc3,
          tailer_link4_vc4, tailer_core_vc1, tailer_core_vc2, tailer_core_vc3, tailer_core_vc4, full_vc1,
          full_vc2, full_vc3, full_vc4,
    output rd_en_vc1_link1_vc1, rd_en_vc1_link1_vc2, rd_en_vc1_link1_vc3, rd_en_vc1_link1_vc4,
           rd_en_vc1_link2_vc1, rd_en_vc1_link2_vc2, rd_en_vc1_link2_vc3, rd_en_vc1_link2_vc4,
           rd_en_vc1_link4_vc1, rd_en_vc1_link4_vc2, rd_en_vc1_link4_vc3, rd_en_vc1_link4_vc4, rd_en_vc1_core_vc1,
           rd_en_vc1_core_vc2, rd_en_vc1_core_vc3, rd_en_vc1_core_vc4, rd_en_vc2_link1_vc1, rd_en_vc2_link1_vc2,
           rd_en_vc2_link1_vc3, rd_en_vc2_link1_vc4, rd_en_vc2_link2_vc1, rd_en_vc2_link2_vc2,
           rd_en_vc2_link2_vc3, rd_en_vc2_link2_vc4, rd_en_vc2_link4_vc1, rd_en_vc2_link4_vc2,
           rd_en_vc2_link4_vc3, rd_en_vc2_link4_vc4, rd_en_vc2_core_vc1, rd_en_vc2_core_vc2, rd_en_vc2_core_vc3,
           rd_en_vc2_core_vc4, rd_en_vc3_link1_vc1, rd_en_vc3_link1_vc2, rd_en_vc3_link1_vc3, rd_en_vc3_link1_vc4,
           rd_en_vc3_link2_vc1, rd_en_vc3_link2_vc2, rd_en_vc3_link2_vc3, rd_en_vc3_link2_vc4,
           rd_en_vc3_link4_vc1, rd_en_vc3_link4_vc2, rd_en_vc3_link4_vc3, rd_en_vc3_link4_vc4, rd_en_vc3_core_vc1,
           rd_en_vc3_core_vc2, rd_en_vc3_core_vc3, rd_en_vc3_core_vc4, rd_en_vc4_link1_vc1, rd_en_vc4_link1_vc2,
           rd_en_vc4_link1_vc3, rd_en_vc4_link1_vc4, rd_en_vc4_link2_vc1, rd_en_vc4_link2_vc2,
           rd_en_vc4_link2_vc3, rd_en_vc4_link2_vc4, rd_en_vc4_link4_vc1, rd_en_vc4_link4_vc2,
           rd_en_vc4_link4_vc3, rd_en_vc4_link4_vc4, rd_en_vc4_core_vc1, rd_en_vc4_core_vc2, rd_en_vc4_core_vc3,
           rd_en_vc4_core_vc4, gnt_vc1, gnt_vc2, gnt_vc3, gnt_vc4,
    output [3:0] ip_link_vc
);

    wire [3:0] encoded_addr;
    wire g1, g2, g3, g4, g5, g6, g7, g8, g9, g10, g11, g12, g13, g14, g15, g16;
    wire [1:0] link_1, vc_id_1, link_2, vc_id_2, link_3, vc_id_3, link_4, vc_id_4;
    wire b1, b2, b3, b4;
    wire tailer1, tailer2, tailer3, tailer4, tailer5, tailer6, tailer7, tailer8, tailer9, tailer10, tailer11, tailer12, tailer13, tailer14, tailer15, tailer16;
    wire gnt_or, ce_b1, ce_b2, ce_b3, ce_b4, clr_b1, clr_b2, clr_b3, clr_b4, e1, e2, e3, e4;
    wire [3:0] ip_link_vc_int;
    wire ready_vc1, ready_vc2, ready_vc3, ready_vc4;
    wire gnt_vc1_int, gnt_vc2_int, gnt_vc3_int, gnt_vc4_int;
    wire all_vc_not_busy;
    wire and_out1, and_out2, and_out3, and_out4, b0, b0_logic;

    // Instantiate round_robin_req
    round_robin_req u_round_robin_req (
        .reset(reset),
        .rd_clk(rd_clk),
        .all_vc_not_busy(all_vc_not_busy),
        .req_1(req_link1_vc1),
        .req_2(req_link1_vc2),
        .req_3(req_link1_vc3),
        .req_4(req_link1_vc4),
        .req_5(req_link2_vc1),
        .req_6(req_link2_vc2),
        .req_7(req_link2_vc3),
        .req_8(req_link2_vc4),
        .req_9(req_link4_vc1),
        .req_10(req_link4_vc2),
        .req_11(req_link4_vc3),
        .req_12(req_link4_vc4),
        .req_13(req_core_vc1),
        .req_14(req_core_vc2),
        .req_15(req_core_vc3),
        .req_16(req_core_vc4),
        .g1(g1),
        .g2(g2),
        .g3(g3),
        .g4(g4),
        .g5(g5),
        .g6(g6),
        .g7(g7),
        .g8(g8),
        .g9(g9),
        .g10(g10),
        .g11(g11),
        .g12(g12),
        .g13(g13),
        .g14(g14),
        .g15(g15),
        .g16(g16),
        .tailer1(tailer_link1_vc1),
        .tailer2(tailer_link1_vc2),
        .tailer3(tailer_link1_vc3),
        .tailer4(tailer_link1_vc4),
        .tailer5(tailer_link2_vc1),
        .tailer6(tailer_link2_vc2),
        .tailer7(tailer_link2_vc3),
        .tailer8(tailer_link2_vc4),
        .tailer9(tailer_link4_vc1),
        .tailer10(tailer_link4_vc2),
        .tailer11(tailer_link4_vc3),
        .tailer12(tailer_link4_vc4),
        .tailer13(tailer_core_vc1),
        .tailer14(tailer_core_vc2),
        .tailer15(tailer_core_vc3),
        .tailer16(tailer_core_vc4),
        .g_b1(),
        .g_b2(),
        .g_b3(),
        .g_b4(),
        .gnt1(),
        .gnt2(),
        .gnt3(),
        .gnt4(),
        .gnt5(),
        .gnt6(),
        .gnt7(),
        .gnt8(),
        .gnt9(),
        .gnt10(),
        .gnt11(),
        .gnt12(),
        .gnt13(),
        .gnt14(),
        .gnt15(),
        .gnt16(),
        .req1(),
        .req2(),
        .req3(),
        .req4(),
        .req5(),
        .req6(),
        .req7(),
        .req8(),
        .req9(),
        .req10(),
        .req11(),
        .req12(),
        .req13(),
        .req14(),
        .req15(),
        .req16(),
        .g1_latched(),
        .g2_latched(),
        .g3_latched(),
        .g4_latched(),
        .g1_int(),
        .g2_int(),
        .g3_int(),
        .g4_int(),
        .t1(),
        .t2(),
        .t3(),
        .t4(),
        .req_b1(),
        .req_b2(),
        .req_b3(),
        .req_b4(),
        .nreq_1(),
        .nreq_2(),
        .nreq_3(),
        .nreq_4(),
        .nreq_5(),
        .nreq_6(),
        .nreq_7(),
        .nreq_8(),
        .nreq_9(),
        .nreq_10(),
        .nreq_11(),
        .nreq_12(),
        .nreq_13(),
        .nreq_14(),
        .nreq_15(),
        .nreq_16()
    );

    // Instantiate encoder
    encoder u_encoder (
        .g1(g1),
        .g2(g2),
        .g3(g3),
        .g4(g4),
        .g5(g5),
        .g6(g6),
        .g7(g7),
        .g8(g8),
        .g9(g9),
        .g10(g10),
        .g11(g11),
        .g12(g12),
        .g13(g13),
        .g14(g14),
        .g15(g15),
        .g16(g16),
        .encoded_addr(encoded_addr)
    );

    // Instantiate allot_vc
    allot_vc u_allot_vc (
        .reset(reset),
        .rd_clk(rd_clk),
        .encoded_addr(encoded_addr),
        .g1(g1),
        .g2(g2),
        .g3(g3),
        .g4(g4),
        .g5(g5),
        .g6(g6),
        .g7(g7),
        .g8(g8),
        .g9(g9),
        .g10(g10),
        .g11(g11),
        .g12(g12),
        .g13(g13),
        .g14(g14),
        .g15(g15),
        .g16(g16),
        .link_1(link_1),
        .vc_id_1(vc_id_1),
        .link_2(link_2),
        .vc_id_2(vc_id_2),
        .link_3(link_3),
        .vc_id_3(vc_id_3),
        .link_4(link_4),
        .vc_id_4(vc_id_4),
        .b1(b1),
        .b2(b2),
        .b3(b3),
        .b4(b4),
        .tailer1(tailer_link1_vc1),
        .tailer2(tailer_link1_vc2),
        .tailer3(tailer_link1_vc3),
        .tailer4(tailer_link1_vc4),
        .tailer5(tailer_link2_vc1),
        .tailer6(tailer_link2_vc2),
        .tailer7(tailer_link2_vc3),
        .tailer8(tailer_link2_vc4),
        .tailer9(tailer_link4_vc1),
        .tailer10(tailer_link4_vc2),
        .tailer11(tailer_link4_vc3),
        .tailer12(tailer_link4_vc4),
        .tailer13(tailer_core_vc1),
        .tailer14(tailer_core_vc2),
        .tailer15(tailer_core_vc3),
        .tailer16(tailer_core_vc4),
        .gnt_or(gnt_or),
        .ce_b1(ce_b1),
        .ce_b2(ce_b2),
        .ce_b3(ce_b3),
        .ce_b4(ce_b4),
        .clr_b1(clr_b1),
        .clr_b2(clr_b2),
        .clr_b3(clr_b3),
        .clr_b4(clr_b4),
        .e1({3'b000, e1}),
        .e2({3'b000, e2}),
        .e3({3'b000, e3}),
        .e4({3'b000, e4})
    );

    // Instantiate rr_comb_new
    rr_comb_new u_rr_comb_new (
        .reset(reset),
        .clk(rd_clk),
        .r1(ready_vc1),
        .r2(ready_vc2),
        .r3(ready_vc3),
        .r4(ready_vc4),
        .g1(gnt_or),
        .g2(1'b0),
        .g3(1'b0),
        .g4(1'b0),
        .l1(1'b0),
        .l2(1'b0),
        .l3(1'b0),
        .l4(1'b0),
        .mux_out1(),
        .mux_out2(),
        .mux_out3(),
        .mux_out4(),
        .and_out1(and_out1),
        .and_out2(and_out2),
        .and_out3(and_out3),
        .and_out4(and_out4),
        .or_out(),
        .b1(),
        .b0(b0),
        .b1_logic(),
        .b0_logic(b0_logic),
        .g1(gnt_vc1_int),
        .g2(gnt_vc2_int),
        .g3(gnt_vc3_int),
        .g4(gnt_vc4_int)
    );

    // Combinational block to determine ready_vc1 to ready_vc4
    always @(*) begin
        ready_vc1 = b1 & rok_link1_vc1 & ~full_vc1;
        ready_vc2 = b2 & rok_link2_vc1 & ~full_vc2;
        ready_vc3 = b3 & rok_link4_vc1 & ~full_vc3;
        ready_vc4 = b4 & rok_core_vc1 & ~full_vc4;
    end

    // Combinational block to determine ip_link_vc
    always @(*) begin
        case ({gnt_vc1_int, gnt_vc2_int, gnt_vc3_int, gnt_vc4_int})
            4'b0001: ip_link_vc_int = {link_1, vc_id_1};
            4'b0010: ip_link_vc_int = {link_2, vc_id_2};
            4'b0100: ip_link_vc_int = {link_3, vc_id_3};
            4'b1000: ip_link_vc_int = {link_4, vc_id_4};
            default: ip_link_vc_int = 4'b0000;
        endcase
    end

    // Combinational block to determine all_vc_not_busy
    always @(*) begin
        all_vc_not_busy = ~b1 & ~b2 & ~b3 & ~b4;
    end

    // Instantiate demux_16 for rd_en_vc1
    demux_16 u_demux_16_vc1 (
        .ip(gnt_vc1_int),
        .sel(encoded_addr),
        .op1(rd_en_vc1_link1_vc1),
        .op2(rd_en_vc1_link1_vc2),
        .op3(rd_en_vc1_link1_vc3),
        .op4(rd_en_vc1_link1_vc4),
        .op5(rd_en_vc1_link2_vc1),
        .op6(rd_en_vc1_link2_vc2),
        .op7(rd_en_vc1_link2_vc3),
        .op8(rd_en_vc1_link2_vc4),
        .op9(rd_en_vc1_link4_vc1),
        .op10(rd_en_vc1_link4_vc2),
        .op11(rd_en_vc1_link4_vc3),
        .op12(rd_en_vc1_link4_vc4),
        .op13(rd_en_vc1_core_vc1),
        .op14(rd_en_vc1_core_vc2),
        .op15(rd_en_vc1_core_vc3),
        .op16(rd_en_vc1_core_vc4)
    );

    // Instantiate demux_16 for rd_en_vc2
    demux_16 u_demux_16_vc2 (
        .ip(gnt_vc2_int),
        .sel(encoded_addr),
        .op1(rd_en_vc2_link1_vc1),
        .op2(rd_en_vc2_link1_vc2),
        .op3(rd_en_vc2_link1_vc3),
        .op4(rd_en_vc2_link1_vc4),
        .op5(rd_en_vc2_link2_vc1),
        .op6(rd_en_vc2_link2_vc2),
        .op7(rd_en_vc2_link2_vc3),
        .op8(rd_en_vc2_link2_vc4),
        .op9(rd_en_vc2_link4_vc1),
        .op10(rd_en_vc2_link4_vc2),
        .op11(rd_en_vc2_link4_vc3),
        .op12(rd_en_vc2_link4_vc4),
        .op13(rd_en_vc2_core_vc1),
        .op14(rd_en_vc2_core_vc2),
        .op15(rd_en_vc2_core_vc3),
        .op16(rd_en_vc2_core_vc4)
    );

    // Instantiate demux_16 for rd_en_vc3
    demux_16 u_demux_16_vc3 (
        .ip(gnt_vc3_int),
        .sel(encoded_addr),
        .op1(rd_en_vc3_link1_vc1),
        .op2(rd_en_vc3_link1_vc2),
        .op3(rd_en_vc3_link1_vc3),
        .op4(rd_en_vc3_link1_vc4),
        .op5(rd_en_vc3_link2_vc1),
        .op6(rd_en_vc3_link2_vc2),
        .op7(rd_en_vc3_link2_vc3),
        .op8(rd_en_vc3_link2_vc4),
        .op9(rd_en_vc3_link4_vc1),
        .op10(rd_en_vc3_link4_vc2),
        .op11(rd_en_vc3_link4_vc3),
        .op12(rd_en_vc3_link4_vc4),
        .op13(rd_en_vc3_core_vc1),
        .op14(rd_en_vc3_core_vc2),
        .op15(rd_en_vc3_core_vc3),
        .op16(rd_en_vc3_core_vc4)
    );

    // Instantiate demux_16 for rd_en_vc4
    demux_16 u_demux_16_vc4 (
        .ip(gnt_vc4_int),
        .sel(encoded_addr),
        .op1(rd_en_vc4_link1_vc1),
        .op2(rd_en_vc4_link1_vc2),
        .op3(rd_en_vc4_link1_vc3),
        .op4(rd_en_vc4_link1_vc4),
        .op5(rd_en_vc4_link2_vc1),
        .op6(rd_en_vc4_link2_vc2),
        .op7(rd_en_vc4_link2_vc3),
        .op8(rd_en_vc4_link2_vc4),
        .op9(rd_en_vc4_link4_vc1),
        .op10(rd_en_vc4_link4_vc2),
        .op11(rd_en_vc4_link4_vc3),
        .op12(rd_en_vc4_link4_vc4),
        .op13(rd_en_vc4_core_vc1),
        .op14(rd_en_vc4_core_vc2),
        .op15(rd_en_vc4_core_vc3),
        .op16(rd_en_vc4_core_vc4)
    );

    // Register outputs
    reg [3:0] ip_link_vc_reg;
    reg gnt_vc1_reg, gnt_vc2_reg, gnt_vc3_reg, gnt_vc4_reg;

    always @(posedge rd_clk or posedge reset) begin
        if (reset) begin
            ip_link_vc_reg <= 4'b0000;
            gnt_vc1_reg <= 1'b0;
            gnt_vc2_reg <= 1'b0;
            gnt_vc3_reg <= 1'b0;
            gnt_vc4_reg <= 1'b0;
        end else begin
            ip_link_vc_reg <= ip_link_vc_int;
            gnt_vc1_reg <= gnt_vc1_int;
            gnt_vc2_reg <= gnt_vc2_int;
            gnt_vc3_reg <= gnt_vc3_int;
            gnt_vc4_reg <= gnt_vc4_int;
        end
    end

    assign ip_link_vc = ip_link_vc_reg;
    assign gnt_vc1 = gnt_vc1_reg;
    assign gnt_vc2 = gnt_vc2_reg;
    assign gnt_vc3 = gnt_vc3_reg;
    assign gnt_vc4 = gnt_vc4_reg;

endmodule
