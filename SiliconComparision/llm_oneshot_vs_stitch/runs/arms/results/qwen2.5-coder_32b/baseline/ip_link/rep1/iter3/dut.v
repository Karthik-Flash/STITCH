module ip_link (
    input reset, rd_clk, wr_clk,
    input [31:0] data_in,
    input [7:0] current_address,
    output [31:0] data_out_vc1, data_out_vc2, data_out_vc3, data_out_vc4,
    output full_vc1, full_vc2, full_vc3, full_vc4, req_l1_vc1, req_l1_vc2, req_l1_vc3, req_l1_vc4, req_l2_vc1,
           req_l2_vc2, req_l2_vc3, req_l2_vc4, req_l3_vc1, req_l3_vc2, req_l3_vc3, req_l3_vc4, req_l4_vc1,
           req_l4_vc2, req_l4_vc3, req_l4_vc4, req_c_vc1, req_c_vc2, req_c_vc3, req_c_vc4,
    input rd_en1, rd_en2, rd_en3, rd_en4, rd_en5, rd_en6, rd_en7, rd_en8, rd_en9, rd_en10, rd_en11, rd_en12,
          rd_en13, rd_en14, rd_en15, rd_en16, rd_en17, rd_en18, rd_en19, rd_en20, rd_en21, rd_en22, rd_en23,
          rd_en24, rd_en25, rd_en26, rd_en27, rd_en28, rd_en29, rd_en30, rd_en31, rd_en32, rd_en33, rd_en34,
          rd_en35, rd_en36, rd_en37, rd_en38, rd_en39, rd_en40, rd_en41, rd_en42, rd_en43, rd_en44, rd_en45,
          rd_en46, rd_en47, rd_en48, rd_en49, rd_en50, rd_en51, rd_en52, rd_en53, rd_en54, rd_en55, rd_en56,
          rd_en57, rd_en58, rd_en59, rd_en60, rd_en61, rd_en62, rd_en63, rd_en64,
    output tailer_vc1, tailer_vc2, tailer_vc3, tailer_vc4, rok_vc1, rok_vc2, rok_vc3, rok_vc4
);

    wire [3:0] vc_select;
    wire [3:0] rd_en_vc1, rd_en_vc2, rd_en_vc3, rd_en_vc4;
    wire [31:0] data_out_vc1_w, data_out_vc2_w, data_out_vc3_w, data_out_vc4_w;
    wire full_vc1_w, full_vc2_w, full_vc3_w, full_vc4_w;
    wire req_l1_vc1_w, req_l1_vc2_w, req_l1_vc3_w, req_l1_vc4_w;
    wire req_l2_vc1_w, req_l2_vc2_w, req_l2_vc3_w, req_l2_vc4_w;
    wire req_l3_vc1_w, req_l3_vc2_w, req_l3_vc3_w, req_l3_vc4_w;
    wire req_l4_vc1_w, req_l4_vc2_w, req_l4_vc3_w, req_l4_vc4_w;
    wire req_c_vc1_w, req_c_vc2_w, req_c_vc3_w, req_c_vc4_w;
    wire tailer_vc1_w, tailer_vc2_w, tailer_vc3_w, tailer_vc4_w;
    wire empty_synch_rdclk_vc1, empty_synch_rdclk_vc2, empty_synch_rdclk_vc3, empty_synch_rdclk_vc4;
    wire wr_en_vc1, wr_en_vc2, wr_en_vc3, wr_en_vc4;

    assign vc_select = data_in[28:27];
    assign rd_en_vc1 = {rd_en16, rd_en15, rd_en14, rd_en13};
    assign rd_en_vc2 = {rd_en20, rd_en19, rd_en18, rd_en17};
    assign rd_en_vc3 = {rd_en24, rd_en23, rd_en22, rd_en21};
    assign rd_en_vc4 = {rd_en28, rd_en27, rd_en26, rd_en25};

    assign wr_en_vc1 = (data_in[30:29] == 2'b01);
    assign wr_en_vc2 = (data_in[30:29] == 2'b10);
    assign wr_en_vc3 = (data_in[30:29] == 2'b00);
    assign wr_en_vc4 = (data_in[30:29] == 2'b11) & (data_in != 32'h6000_0000);

    ip_chnl chnl1 (
        .reset(reset), .rd_clk(rd_clk), .wr_clk(wr_clk),
        .rd_en(rd_en_vc1), .wr_en(wr_en_vc1),
        .data_in(data_in), .current_address(current_address),
        .full_ext(full_vc1_w), .empty_synch_rdclk(empty_synch_rdclk_vc1),
        .req_l1(req_l1_vc1_w), .req_l2(req_l2_vc1_w), .req_l3(req_l3_vc1_w), .req_l4(req_l4_vc1_w), .req_c(req_c_vc1_w),
        .data_out(data_out_vc1_w), .tailer(tailer_vc1_w), .tailer_org(), .nxt_reset(), .data_sel(), .header(), .empty(),
        .fifo_out(), .header_flit(), .reg_out(), .mux_data_out(), .header_out()
    );

    ip_chnl chnl2 (
        .reset(reset), .rd_clk(rd_clk), .wr_clk(wr_clk),
        .rd_en(rd_en_vc2), .wr_en(wr_en_vc2),
        .data_in(data_in), .current_address(current_address),
        .full_ext(full_vc2_w), .empty_synch_rdclk(empty_synch_rdclk_vc2),
        .req_l1(req_l1_vc2_w), .req_l2(req_l2_vc2_w), .req_l3(req_l3_vc2_w), .req_l4(req_l4_vc2_w), .req_c(req_c_vc2_w),
        .data_out(data_out_vc2_w), .tailer(tailer_vc2_w), .tailer_org(), .nxt_reset(), .data_sel(), .header(), .empty(),
        .fifo_out(), .header_flit(), .reg_out(), .mux_data_out(), .header_out()
    );

    ip_chnl chnl3 (
        .reset(reset), .rd_clk(rd_clk), .wr_clk(wr_clk),
        .rd_en(rd_en_vc3), .wr_en(wr_en_vc3),
        .data_in(data_in), .current_address(current_address),
        .full_ext(full_vc3_w), .empty_synch_rdclk(empty_synch_rdclk_vc3),
        .req_l1(req_l1_vc3_w), .req_l2(req_l2_vc3_w), .req_l3(req_l3_vc3_w), .req_l4(req_l4_vc3_w), .req_c(req_c_vc3_w),
        .data_out(data_out_vc3_w), .tailer(tailer_vc3_w), .tailer_org(), .nxt_reset(), .data_sel(), .header(), .empty(),
        .fifo_out(), .header_flit(), .reg_out(), .mux_data_out(), .header_out()
    );

    ip_chnl chnl4 (
        .reset(reset), .rd_clk(rd_clk), .wr_clk(wr_clk),
        .rd_en(rd_en_vc4), .wr_en(wr_en_vc4),
        .data_in(data_in), .current_address(current_address),
        .full_ext(full_vc4_w), .empty_synch_rdclk(empty_synch_rdclk_vc4),
        .req_l1(req_l1_vc4_w), .req_l2(req_l2_vc4_w), .req_l3(req_l3_vc4_w), .req_l4(req_l4_vc4_w), .req_c(req_c_vc4_w),
        .data_out(data_out_vc4_w), .tailer(tailer_vc4_w), .tailer_org(), .nxt_reset(), .data_sel(), .header(), .empty(),
        .fifo_out(), .header_flit(), .reg_out(), .mux_data_out(), .header_out()
    );

    assign data_out_vc1 = data_out_vc1_w;
    assign data_out_vc2 = data_out_vc2_w;
    assign data_out_vc3 = data_out_vc3_w;
    assign data_out_vc4 = data_out_vc4_w;
    assign full_vc1 = full_vc1_w;
    assign full_vc2 = full_vc2_w;
    assign full_vc3 = full_vc3_w;
    assign full_vc4 = full_vc4_w;
    assign req_l1_vc1 = req_l1_vc1_w;
    assign req_l1_vc2 = req_l1_vc2_w;
    assign req_l1_vc3 = req_l1_vc3_w;
    assign req_l1_vc4 = req_l1_vc4_w;
    assign req_l2_vc1 = req_l2_vc1_w;
    assign req_l2_vc2 = req_l2_vc2_w;
    assign req_l2_vc3 = req_l2_vc3_w;
    assign req_l2_vc4 = req_l2_vc4_w;
    assign req_l3_vc1 = req_l3_vc1_w;
    assign req_l3_vc2 = req_l3_vc2_w;
    assign req_l3_vc3 = req_l3_vc3_w;
    assign req_l3_vc4 = req_l3_vc4_w;
    assign req_l4_vc1 = req_l4_vc1_w;
    assign req_l4_vc2 = req_l4_vc2_w;
    assign req_l4_vc3 = req_l4_vc3_w;
    assign req_l4_vc4 = req_l4_vc4_w;
    assign req_c_vc1 = req_c_vc1_w;
    assign req_c_vc2 = req_c_vc2_w;
    assign req_c_vc3 = req_c_vc3_w;
    assign req_c_vc4 = req_c_vc4_w;
    assign tailer_vc1 = tailer_vc1_w;
    assign tailer_vc2 = tailer_vc2_w;
    assign tailer_vc3 = tailer_vc3_w;
    assign tailer_vc4 = tailer_vc4_w;
    assign rok_vc1 = ~empty_synch_rdclk_vc1;
    assign rok_vc2 = ~empty_synch_rdclk_vc2;
    assign rok_vc3 = ~empty_synch_rdclk_vc3;
    assign rok_vc4 = ~empty_synch_rdclk_vc4;

endmodule
