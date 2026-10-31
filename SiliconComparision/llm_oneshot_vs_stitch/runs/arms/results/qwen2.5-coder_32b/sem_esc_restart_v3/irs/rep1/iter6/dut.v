module irs (
    input reset, empty, rd_en, rd_clk, tailer, tailer_org, header,
    output rd_en_out, data_sel, en1, en2, en4, en5, en6
);

    wire en1_w, en2_w;
    reg data_sel_w, en4_reg, en5_reg, en6_reg, data_sel_reg, flag_A_reg, flag_B_reg;
    reg en4_next, en5_next, en6_next, flag_A_w, flag_B_w;

    // Instantiate dff_asynch_clr for en4
    dff_asynch_clr dff_en4 (
        .d(en4_next),
        .clr(reset),
        .clk(rd_clk),
        .q(en4_reg)
    );

    // Instantiate dff_asynch_clr for en5
    dff_asynch_clr dff_en5 (
        .d(en5_next),
        .clr(reset),
        .clk(rd_clk),
        .q(en5_reg)
    );

    // Instantiate dff_asynch_clr for en6
    dff_asynch_clr dff_en6 (
        .d(en6_next),
        .clr(reset),
        .clk(rd_clk),
        .q(en6_reg)
    );

    // Instantiate dff_asynch_clr for data_sel
    dff_asynch_clr dff_data_sel (
        .d(data_sel_w),
        .clr(reset),
        .clk(rd_clk),
        .q(data_sel_reg)
    );

    // Instantiate dff_asynch_clr for flag_A
    dff_asynch_clr dff_flag_A (
        .d(flag_A_w),
        .clr(reset),
        .clk(rd_clk),
        .q(flag_A_reg)
    );

    // Instantiate dff_asynch_clr for flag_B
    dff_asynch_clr dff_flag_B (
        .d(flag_B_w),
        .clr(reset),
        .clk(rd_clk),
        .q(flag_B_reg)
    );

    // Assignments for en1 and en2
    assign en1_w = ~empty;
    assign en2_w = rd_en;

    // Clocked logic for en4
    always @(posedge rd_clk or posedge reset) begin
        if (reset) begin
            en4_next <= 1'b0;
        end else if (header) begin
            en4_next <= 1'b1;
        end
    end

    // Clocked logic for en5
    always @(posedge rd_clk or posedge reset) begin
        if (reset) begin
            en5_next <= 1'b0;
        end else if (tailer) begin
            en5_next <= en4_reg;
        end
    end

    // Clocked logic for en6
    always @(posedge rd_clk or posedge reset) begin
        if (reset) begin
            en6_next <= 1'b0;
        end else begin
            en6_next <= en5_reg;
        end
    end

    // Clocked logic for data_sel
    always @(posedge rd_clk or posedge reset) begin
        if (reset) begin
            data_sel_w <= 1'b0;
        end else if (rd_en && ~flag_A_reg && ~flag_B_reg) begin
            data_sel_w <= 1'b1;
        end else begin
            data_sel_w <= 1'b0;
        end
    end

    // Clocked logic for flag_A
    always @(posedge rd_clk or posedge reset) begin
        if (reset) begin
            flag_A_w <= 1'b0;
        end else begin
            flag_A_w <= data_sel_reg;
        end
    end

    // Clocked logic for flag_B
    always @(posedge rd_clk or posedge reset) begin
        if (reset || tailer) begin
            flag_B_w <= 1'b0;
        end else if (data_sel_reg && ~data_sel_w) begin
            flag_B_w <= 1'b1;
        end
    end

    // Combinational logic for outputs
    always @(*) begin
        if (tailer_org) begin
            rd_en_out = en4_reg ? en2_w : en1_w;
            data_sel = data_sel_reg;
            en1 = en1_w;
            en2 = en2_w;
            en4 = en4_reg;
            en5 = en5_reg;
            en6 = en6_reg;
        end else begin
            rd_en_out = 1'b0;
            data_sel = 1'b0;
            en1 = 1'b0;
            en2 = 1'b0;
            en4 = 1'b0;
            en5 = 1'b0;
            en6 = 1'b0;
        end
    end

endmodule
