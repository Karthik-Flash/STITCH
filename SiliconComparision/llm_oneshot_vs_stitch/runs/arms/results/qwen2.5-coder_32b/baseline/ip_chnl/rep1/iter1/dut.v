module ip_chnl (
    input reset, rd_clk, wr_clk, rd_en, wr_en,
    input [31:0] data_in,
    input [7:0] current_address,
    output full_ext, empty_synch_rdclk, req_l1, req_l2, req_l3, req_l4, req_c,
    output [31:0] data_out,
    output tailer, tailer_org, nxt_reset, data_sel, header, empty,
    output [31:0] fifo_out, header_flit, reg_out, mux_data_out, header_out
);

    reg [31:0] fifo_out_w;
    reg [31:0] header_flit_w;
    reg header_w, tailer_org_w, tailer_w, empty_w, full_ext_w;
    reg rd_en_out_w, en1_w, en2_w, en4_w, en5_w, en6_w;
    reg req_link1_w, req_link2_w, req_core_w, req_link3_w, req_link4_w;

    // Instantiate router_fifo
    router_fifo u_router_fifo (
        .reset(reset),
        .rd_clk(rd_clk),
        .rd_en(rd_en),
        .data_in(data_in),
        .wr_clk(wr_clk),
        .wr_en(wr_en),
        .rd_add(2'b00),
        .wr_add(2'b00),
        .wr_dir(2'b00),
        .rd_dir(2'b00),
        .data_out(fifo_out_w),
        .full_ext(full_ext_w),
        .full_int(),
        .empty(empty_w)
    );

    // Instantiate register_32bit
    register_32bit u_register_32bit (
        .din(fifo_out_w),
        .clk(rd_clk),
        .clr(reset | tailer_w),
        .ce(header_w),
        .dout(header_flit_w)
    );

    // Instantiate irs
    irs u_irs (
        .reset(reset),
        .empty(empty_w),
        .rd_en(rd_en),
        .rd_clk(rd_clk),
        .tailer(tailer_w),
        .tailer_org(tailer_org_w),
        .header(header_w),
        .rd_en_out(rd_en_out_w),
        .data_sel(data_sel),
        .en1(en1_w),
        .en2(en2_w),
        .en4(en4_w),
        .en5(en5_w),
        .en6(en6_w)
    );

    // Instantiate routing_algo_mesh
    routing_algo_mesh u_routing_algo_mesh (
        .header_in(header_out),
        .current_address(current_address),
        .reset(reset),
        .req_link1(req_link1_w),
        .req_link2(req_link2_w),
        .req_core(req_core_w),
        .req_link3(req_link3_w),
        .req_link4(req_link4_w)
    );

    // Instantiate dff_synch_reset for tailer
    dff_synch_reset u_dff_synch_reset_tailer (
        .d(tailer_org_w),
        .reset(reset),
        .clk(rd_clk),
        .q(tailer_w)
    );

    // Instantiate dff_synch_set for empty_synch_rdclk
    dff_synch_set u_dff_synch_set_empty (
        .d(empty_w),
        .set(reset),
        .clk(rd_clk),
        .q(empty_synch_rdclk)
    );

    // Combinational logic for header and tailer detection
    always @(*) begin
        case (fifo_out_w[30:29])
            2'b01: begin
                header_w = 1'b1;
                tailer_org_w = 1'b0;
            end
            2'b10: begin
                header_w = 1'b0;
                tailer_org_w = 1'b1;
            end
            default: begin
                header_w = 1'b0;
                tailer_org_w = 1'b0;
            end
        endcase
    end

    // Combinational logic for header_out and mux_data_out
    always @(*) begin
        if (header_w) begin
            header_out = fifo_out_w;
        end else begin
            header_out = header_flit_w;
        end

        if (rd_en) begin
            if (data_sel) begin
                mux_data_out = header_flit_w;
            end else begin
                mux_data_out = fifo_out_w;
            end
        end else begin
            mux_data_out = 32'h6000_0000;
        end
    end

    // Combinational logic for routing requests
    always @(*) begin
        req_l1 = req_link1_w;
        req_l2 = req_link2_w;
        req_l3 = req_link3_w;
        req_l4 = req_link4_w;
        req_c = req_core_w;
    end

    // Assign outputs
    assign full_ext = full_ext_w;
    assign empty = empty_w;
    assign fifo_out = fifo_out_w;
    assign header_flit = header_flit_w;
    assign header = header_w;
    assign tailer_org = tailer_org_w;
    assign tailer = tailer_w;
    assign data_out = mux_data_out;
    assign reg_out = header_flit_w;

endmodule
