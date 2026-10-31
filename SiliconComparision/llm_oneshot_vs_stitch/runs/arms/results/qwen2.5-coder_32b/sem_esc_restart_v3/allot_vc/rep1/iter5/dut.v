module allot_vc (
    input reset, rd_clk,
    input [3:0] encoded_addr,
    input g1, g2, g3, g4, g5, g6, g7, g8, g9, g10, g11, g12, g13, g14, g15, g16,
    output [1:0] link_1, vc_id_1, link_2, vc_id_2, link_3, vc_id_3, link_4, vc_id_4,
    output b1, b2, b3, b4,
    input tailer1, tailer2, tailer3, tailer4, tailer5, tailer6, tailer7, tailer8, tailer9, tailer10, tailer11,
          tailer12, tailer13, tailer14, tailer15, tailer16,
    output gnt_or, ce_b1, ce_b2, ce_b3, ce_b4, clr_b1, clr_b2, clr_b3, clr_b4,
    output [3:0] e1, e2, e3, e4
);

    wire gnt_or_w;
    wire ce_b1_w, ce_b2_w, ce_b3_w, ce_b4_w;
    wire clr_b1_w, clr_b2_w, clr_b3_w, clr_b4_w;
    reg [3:0] ek;
    wire [1:0] link_k, vc_id_k;
    reg clr_bk;
    wire tailer_select;
    reg ce_bk;

    // Instantiate mux to select tailer based on ek
    mux mux_tailer (
        tailer1, tailer2, tailer3, tailer4, tailer5, tailer6, tailer7, tailer8, tailer9, tailer10, tailer11,
        tailer12, tailer13, tailer14, tailer15, tailer16,
        ek, tailer_select, rd_clk
    );

    // Instantiate register_4bit for ek
    register_4bit reg_ek (
        encoded_addr, rd_clk, reset, ce_bk, ek
    );

    // Instantiate register_1bit for b1, b2, b3, b4
    register_1bit reg_b1 (1'b0, reset, rd_clk, clr_b1_w, ce_b1_w, b1);
    register_1bit reg_b2 (1'b0, reset, rd_clk, clr_b2_w, ce_b2_w, b2);
    register_1bit reg_b3 (1'b0, reset, rd_clk, clr_b3_w, ce_b3_w, b3);
    register_1bit reg_b4 (1'b0, reset, rd_clk, clr_b4_w, ce_b4_w, b4);

    // Combinational logic for gnt_or
    assign gnt_or = gnt_or_w;
    assign gnt_or_w = g1 | g2 | g3 | g4 | g5 | g6 | g7 | g8 | g9 | g10 | g11 | g12 | g13 | g14 | g15 | g16;

    // Combinational logic for ce_b1, ce_b2, ce_b3, ce_b4
    assign ce_b1 = ce_b1_w;
    assign ce_b1_w = ~b1 & gnt_or_w;
    assign ce_b2 = ce_b2_w;
    assign ce_b2_w = b1 & ~b2 & gnt_or_w;
    assign ce_b3 = ce_b3_w;
    assign ce_b3_w = b1 & b2 & ~b3 & gnt_or_w;
    assign ce_b4 = ce_b4_w;
    assign ce_b4_w = b1 & b2 & b3 & ~b4 & gnt_or_w;

    // Combinational logic for clr_b1, clr_b2, clr_b3, clr_b4
    assign clr_b1 = clr_b1_w;
    assign clr_b1_w = clr_bk;
    assign clr_b2 = clr_b2_w;
    assign clr_b2_w = clr_bk;
    assign clr_b3 = clr_b3_w;
    assign clr_b3_w = clr_bk;
    assign clr_b4 = clr_b4_w;
    assign clr_b4_w = clr_bk;

    // Combinational logic for clr_bk
    assign clr_bk = reset ? 1'b0 : tailer_select;

    // Combinational logic for link_k and vc_id_k
    assign link_k = ek[3:2];
    assign vc_id_k = ek[1:0];

    // Combinational logic for e1, e2, e3, e4
    assign e1 = {link_k, vc_id_k};
    assign e2 = {link_k, vc_id_k};
    assign e3 = {link_k, vc_id_k};
    assign e4 = {link_k, vc_id_k};

    // Combinational logic for link_1, vc_id_1, link_2, vc_id_2, link_3, vc_id_3, link_4, vc_id_4
    assign link_1 = link_k;
    assign vc_id_1 = vc_id_k;
    assign link_2 = link_k;
    assign vc_id_2 = vc_id_k;
    assign link_3 = link_k;
    assign vc_id_3 = vc_id_k;
    assign link_4 = link_k;
    assign vc_id_4 = vc_id_k;

    // Clocked logic for ce_bk
    always @(posedge rd_clk) begin
        if (reset) begin
            ce_bk <= 1'b0;
        end else begin
            ce_bk <= gnt_or_w;
        end
    end

endmodule
