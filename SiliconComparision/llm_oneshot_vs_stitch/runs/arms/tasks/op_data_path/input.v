module op_data_path (
    input [31:0] data_from_link1_ch1, data_from_link1_ch2, data_from_link1_ch3, data_from_link1_ch4,
                 data_from_link2_ch1, data_from_link2_ch2, data_from_link2_ch3, data_from_link2_ch4,
                 data_from_link3_ch1, data_from_link3_ch2, data_from_link3_ch3, data_from_link3_ch4,
                 data_from_link4_ch1, data_from_link4_ch2, data_from_link4_ch3, data_from_link4_ch4,
                 data_from_core_ch1, data_from_core_ch2, data_from_core_ch3, data_from_core_ch4,
    input [3:0] sel_vc_link1, sel_vc_link2, sel_vc_link3, sel_vc_link4, sel_vc_core,
    input gnt_vc_link1_ch1, gnt_vc_link1_ch2, gnt_vc_link1_ch3, gnt_vc_link1_ch4, gnt_vc_link2_ch1,
          gnt_vc_link2_ch2, gnt_vc_link2_ch3, gnt_vc_link2_ch4, gnt_vc_link3_ch1, gnt_vc_link3_ch2,
          gnt_vc_link3_ch3, gnt_vc_link3_ch4, gnt_vc_link4_ch1, gnt_vc_link4_ch2, gnt_vc_link4_ch3,
          gnt_vc_link4_ch4, gnt_vc_core_ch1, gnt_vc_core_ch2, gnt_vc_core_ch3, gnt_vc_core_ch4,
    output [31:0] data_out_link1, data_out_link2, data_out_link3, data_out_link4, data_out_core, data_out_l1,
                  data_out_l2, data_out_l3, data_out_l4, data_out_c,
    input rd_clk1, rd_clk2, rd_clk3, rd_clk4, rd_clk_core
);

    wire [31:0] data_out_l1, data_out_l2, data_out_l3, data_out_l4, data_out_c;
    wire [31:0] data_out_link1, data_out_link2, data_out_link3, data_out_link4, data_out_core;
    wire [1:0] vc_id_link1, vc_id_link2, vc_id_link3, vc_id_link4, vc_id_core;
    wire gnt_or_link1, gnt_or_link2, gnt_or_link3, gnt_or_link4, gnt_or_core;

    // Select data for each output port
    always @(*) begin
        case (sel_vc_link1)
            4'b0000: data_out_l1 = data_from_link2_ch1;
            4'b0001: data_out_l1 = data_from_link2_ch2;
            4'b0010: data_out_l1 = data_from_link2_ch3;
            4'b0011: data_out_l1 = data_from_link2_ch4;
            4'b0100: data_out_l1 = data_from_link3_ch1;
            4'b0101: data_out_l1 = data_from_link3_ch2;
            4'b0110: data_out_l1 = data_from_link3_ch3;
            4'b0111: data_out_l1 = data_from_link3_ch4;
            4'b1000: data_out_l1 = data_from_link4_ch1;
            4'b1001: data_out_l1 = data_from_link4_ch2;
            4'b1010: data_out_l1 = data_from_link4_ch3;
            4'b1011: data_out_l1 = data_from_link4_ch4;
            4'b1100: data_out_l1 = data_from_core_ch1;
            4'b1101: data_out_l1 = data_from_core_ch2;
            4'b1110: data_out_l1 = data_from_core_ch3;
            4'b1111: data_out_l1 = data_from_core_ch4;
            default: data_out_l1 = 32'h00000000;
        endcase
    end

    always @(*) begin
        case (sel_vc_link2)
            4'b0000: data_out_l2 = data_from_link1_ch1;
            4'b0001: data_out_l2 = data_from_link1_ch2;
            4'b0010: data_out_l2 = data_from_link1_ch3;
            4'b0011: data_out_l2 = data_from_link1_ch4;
            4'b0100: data_out_l2 = data_from_link3_ch1;
            4'b0101: data_out_l2 = data_from_link3_ch2;
            4'b0110: data_out_l2 = data_from_link3_ch3;
            4'b0111: data_out_l2 = data_from_link3_ch4;
            4'b1000: data_out_l2 = data_from_link4_ch1;
            4'b1001: data_out_l2 = data_from_link4_ch2;
            4'b1010: data_out_l2 = data_from_link4_ch3;
            4'b1011: data_out_l2 = data_from_link4_ch4;
            4'b1100: data_out_l2 = data_from_core_ch1;
            4'b1101: data_out_l2 = data_from_core_ch2;
            4'b1110: data_out_l2 = data_from_core_ch3;
            4'b1111: data_out_l2 = data_from_core_ch4;
            default: data_out_l2 = 32'h00000000;
        endcase
    end

    always @(*) begin
        case (sel_vc_link3)
            4'b0000: data_out_l3 = data_from_link1_ch1;
            4'b0001: data_out_l3 = data_from_link1_ch2;
            4'b0010: data_out_l3 = data_from_link1_ch3;
            4'b0011: data_out_l3 = data_from_link1_ch4;
            4'b0100: data_out_l3 = data_from_link2_ch1;
            4'b0101: data_out_l3 = data_from_link2_ch2;
            4'b0110: data_out_l3 = data_from_link2_ch3;
            4'b0111: data_out_l3 = data_from_link2_ch4;
            4'b1000: data_out_l3 = data_from_link4_ch1;
            4'b1001: data_out_l3 = data_from_link4_ch2;
            4'b1010: data_out_l3 = data_from_link4_ch3;
            4'b1011: data_out_l3 = data_from_link4_ch4;
            4'b1100: data_out_l3 = data_from_core_ch1;
            4'b1101: data_out_l3 = data_from_core_ch2;
            4'b1110: data_out_l3 = data_from_core_ch3;
            4'b1111: data_out_l3 = data_from_core_ch4;
            default: data_out_l3 = 32'h00000000;
        endcase
    end

    always @(*) begin
        case (sel_vc_link4)
            4'b0000: data_out_l4 = data_from_link1_ch1;
            4'b0001: data_out_l4 = data_from_link1_ch2;
            4'b0010: data_out_l4 = data_from_link1_ch3;
            4'b0011: data_out_l4 = data_from_link1_ch4;
            4'b0100: data_out_l4 = data_from_link2_ch1;
            4'b0101: data_out_l4 = data_from_link2_ch2;
            4'b0110: data_out_l4 = data_from_link2_ch3;
            4'b0111: data_out_l4 = data_from_link2_ch4;
            4'b1000: data_out_l4 = data_from_link3_ch1;
            4'b1001: data_out_l4 = data_from_link3_ch2;
            4'b1010: data_out_l4 = data_from_link3_ch3;
            4'b1011: data_out_l4 = data_from_link3_ch4;
            4'b1100: data_out_l4 = data_from_core_ch1;
            4'b1101: data_out_l4 = data_from_core_ch2;
            4'b1110: data_out_l4 = data_from_core_ch3;
            4'b1111: data_out_l4 = data_from_core_ch4;
            default: data_out_l4 = 32'h00000000;
        endcase
    end

    always @(*) begin
        case (sel_vc_core)
            4'b0000: data_out_c = data_from_link1_ch1;
            4'b0001: data_out_c = data_from_link1_ch2;
            4'b0010: data_out_c = data_from_link1_ch3;
            4'b0011: data_out_c = data_from_link1_ch4;
            4'b0100: data_out_c = data_from_link2_ch1;
            4'b0101: data_out_c = data_from_link2_ch2;
            4'b0110: data_out_c = data_from_link2_ch3;
            4'b0111: data_out_c = data_from_link2_ch4;
            4'b1000: data_out_c = data_from_link3_ch1;
            4'b1001: data_out_c = data_from_link3_ch2;
            4'b1010: data_out_c = data_from_link3_ch3;
            4'b1011: data_out_c = data_from_link3_ch4;
            4'b1100: data_out_c = data_from_link4_ch1;
            4'b1101: data_out_c = data_from_link4_ch2;
            4'b1110: data_out_c = data_from_link4_ch3;
            4'b1111: data_out_c = data_from_link4_ch4;
            default: data_out_c = 32'h00000000;
        endcase
    end

    // Calculate vc_id and gnt_or for each output port
    always @(*) begin
        vc_id_link1 = (gnt_vc_link1_ch3 | gnt_vc_link1_ch4) << 1 | (gnt_vc_link1_ch2 | gnt_vc_link1_ch4);
        gnt_or_link1 = gnt_vc_link1_ch1 | gnt_vc_link1_ch2 | gnt_vc_link1_ch3 | gnt_vc_link1_ch4;
    end

    always @(*) begin
        vc_id_link2 = (gnt_vc_link2_ch3 | gnt_vc_link2_ch4) << 1 | (gnt_vc_link2_ch2 | gnt_vc_link2_ch4);
        gnt_or_link2 = gnt_vc_link2_ch1 | gnt_vc_link2_ch2 | gnt_vc_link2_ch3 | gnt_vc_link2_ch4;
    end

    always @(*) begin
        vc_id_link3 = (gnt_vc_link3_ch3 | gnt_vc_link3_ch4) << 1 | (gnt_vc_link3_ch2 | gnt_vc_link3_ch4);
        gnt_or_link3 = gnt_vc_link3_ch1 | gnt_vc_link3_ch2 | gnt_vc_link3_ch3 | gnt_vc_link3_ch4;
    end

    always @(*) begin
        vc_id_link4 = (gnt_vc_link4_ch3 | gnt_vc_link4_ch4) << 1 | (gnt_vc_link4_ch2 | gnt_vc_link4_ch4);
        gnt_or_link4 = gnt_vc_link4_ch1 | gnt_vc_link4_ch2 | gnt_vc_link4_ch3 | gnt_vc_link4_ch4;
    end

    always @(*) begin
        vc_id_core = (gnt_vc_core_ch3 | gnt_vc_core_ch4) << 1 | (gnt_vc_core_ch2 | gnt_vc_core_ch4);
        gnt_or_core = gnt_vc_core_ch1 | gnt_vc_core_ch2 | gnt_vc_core_ch3 | gnt_vc_core_ch4;
    end

    // Instantiate final_op_data for each output port
    final_op_data final_op_data_link1 (
        .data_in(data_out_l1),
        .vc_id(vc_id_link1),
        .gnt_or(gnt_or_link1),
        .data_out(data_out_link1)
    );

    final_op_data final_op_data_link2 (
        .data_in(data_out_l2),
        .vc_id(vc_id_link2),
        .gnt_or(gnt_or_link2),
        .data_out(data_out_link2)
    );

    final_op_data final_op_data_link3 (
        .data_in(data_out_l3),
        .vc_id(vc_id_link3),
        .gnt_or(gnt_or_link3),
        .data_out(data_out_link3)
    );

    final_op_data final_op_data_link4 (
        .data_in(data_out_l4),
        .vc_id(vc_id_link4),
        .gnt_or(gnt_or_link4),
        .data_out(data_out_link4)
    );

    final_op_data final_op_data_core (
        .data_in(data_out_c),
        .vc_id(vc_id_core),
        .gnt_or(gnt_or_core),
        .data_out(data_out_core)
    );

endmodule
