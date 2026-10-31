module top_module (
    input clk,
    input clr,
    input [31:0] data_in_link1,
    input [31:0] data_in_link2,
    input [31:0] data_in_link3,
    input [31:0] data_in_link4,
    input [31:0] data_in_core,
    input full_in_link1_vc1,
    input full_in_link1_vc2,
    input full_in_link1_vc3,
    input full_in_link1_vc4,
    input full_in_link2_vc1,
    input full_in_link2_vc2,
    input full_in_link2_vc3,
    input full_in_link2_vc4,
    input full_in_link3_vc1,
    input full_in_link3_vc2,
    input full_in_link3_vc3,
    input full_in_link3_vc4,
    input full_in_link4_vc1,
    input full_in_link4_vc2,
    input full_in_link4_vc3,
    input full_in_link4_vc4,
    input full_in_core_vc1,
    input full_in_core_vc2,
    input full_in_core_vc3,
    input full_in_core_vc4,
    input [7:0] current_address,
    output [31:0] data_out_link1,
    output [31:0] data_out_link2,
    output [31:0] data_out_link3,
    output [31:0] data_out_link4,
    output [31:0] data_out_core,
    output full_out_link1_vc1,
    output full_out_link1_vc2,
    output full_out_link1_vc3,
    output full_out_link1_vc4,
    output full_out_link2_vc1,
    output full_out_link2_vc2,
    output full_out_link2_vc3,
    output full_out_link2_vc4,
    output full_out_link3_vc1,
    output full_out_link3_vc2,
    output full_out_link3_vc3,
    output full_out_link3_vc4,
    output full_out_link4_vc1,
    output full_out_link4_vc2,
    output full_out_link4_vc3,
    output full_out_link4_vc4,
    output full_out_core_vc1,
    output full_out_core_vc2,
    output full_out_core_vc3,
    output full_out_core_vc4,
    output [31:0] data_out_link1_vc1,
    output [31:0] data_out_link1_vc2,
    output [31:0] data_out_link1_vc3,
    output [31:0] data_out_link1_vc4,
    output [31:0] data_out_link2_vc1,
    output [31:0] data_out_link2_vc2,
    output [31:0] data_out_link2_vc3,
    output [31:0] data_out_link2_vc4,
    output [31:0] data_out_link3_vc1,
    output [31:0] data_out_link3_vc2,
    output [31:0] data_out_link3_vc3,
    output [31:0] data_out_link3_vc4,
    output [31:0] data_out_link4_vc1,
    output [31:0] data_out_link4_vc2,
    output [31:0] data_out_link4_vc3,
    output [31:0] data_out_link4_vc4,
    output [31:0] data_out_core_vc1,
    output [31:0] data_out_core_vc2,
    output [31:0] data_out_core_vc3,
    output [31:0] data_out_core_vc4,
    output [3:0] sel_vc_link1,
    output [3:0] sel_vc_link2,
    output [3:0] sel_vc_link3,
    output [3:0] sel_vc_link4,
    output [3:0] sel_vc_core,
    output [31:0] data_out_l1,
    output [31:0] data_out_l2,
    output [31:0] data_out_l3,
    output [31:0] data_out_l4,
    output [31:0] data_out_c
);

    wire [31:0] ip_link1_out_vc1, ip_link1_out_vc2, ip_link1_out_vc3, ip_link1_out_vc4;
    wire [31:0] ip_link2_out_vc1, ip_link2_out_vc2, ip_link2_out_vc3, ip_link2_out_vc4;
    wire [31:0] ip_link3_out_vc1, ip_link3_out_vc2, ip_link3_out_vc3, ip_link3_out_vc4;
    wire [31:0] ip_link4_out_vc1, ip_link4_out_vc2, ip_link4_out_vc3, ip_link4_out_vc4;
    wire [31:0] ip_core_out_vc1, ip_core_out_vc2, ip_core_out_vc3, ip_core_out_vc4;

    wire [3:0] req_l1_link1, req_l1_link2, req_l1_link3, req_l1_link4, req_l1_core;
    wire [3:0] req_l2_link1, req_l2_link2, req_l2_link3, req_l2_link4, req_l2_core;
    wire [3:0] req_l3_link1, req_l3_link2, req_l3_link3, req_l3_link4, req_l3_core;
    wire [3:0] req_l4_link1, req_l4_link2, req_l4_link3, req_l4_link4, req_l4_core;
    wire [3:0] req_c_link1, req_c_link2, req_c_link3, req_c_link4, req_c_core;

    wire [3:0] rok_link1, rok_link2, rok_link3, rok_link4, rok_core;
    wire [3:0] tailer_link1, tailer_link2, tailer_link3, tailer_link4, tailer_core;
    reg [3:0] full_out_link1_vc1_reg, full_out_link1_vc2_reg, full_out_link1_vc3_reg, full_out_link1_vc4_reg;
    reg [3:0] full_out_link2_vc1_reg, full_out_link2_vc2_reg, full_out_link2_vc3_reg, full_out_link2_vc4_reg;
    reg [3:0] full_out_link3_vc1_reg, full_out_link3_vc2_reg, full_out_link3_vc3_reg, full_out_link3_vc4_reg;
    reg [3:0] full_out_link4_vc1_reg, full_out_link4_vc2_reg, full_out_link4_vc3_reg, full_out_link4_vc4_reg;
    reg [3:0] rd_en_link1, rd_en_link2, rd_en_link3, rd_en_link4, rd_en_core;
    reg [3:0] gnt_link1, gnt_link2, gnt_link3, gnt_link4, gnt_core;
    reg [3:0] sel_vc_link1_reg, sel_vc_link2_reg, sel_vc_link3_reg, sel_vc_link4_reg, sel_vc_core_reg;

    wire [31:0] op_data_path_link1, op_data_path_link2, op_data_path_link3, op_data_path_link4, op_data_path_core;

    ip_link ip_link1_inst (
        .reset(clr),
        .rd_clk(clk),
        .wr_clk(clk),
        .data_in(data_in_link1),
        .current_address(current_address),
        .data_out_vc1(ip_link1_out_vc1),
        .data_out_vc2(ip_link1_out_vc2),
        .data_out_vc3(ip_link1_out_vc3),
        .data_out_vc4(ip_link1_out_vc4),
        .full_vc1(full_in_link1_vc1),
        .full_vc2(full_in_link1_vc2),
        .full_vc3(full_in_link1_vc3),
        .full_vc4(full_in_link1_vc4),
        .req_l1_vc1(req_l1_link1[0]),
        .req_l1_vc2(req_l1_link1[1]),
        .req_l1_vc3(req_l1_link1[2]),
        .req_l1_vc4(req_l1_link1[3]),
        .req_l2_vc1(req_l2_link1[0]),
        .req_l2_vc2(req_l2_link1[1]),
        .req_l2_vc3(req_l2_link1[2]),
        .req_l2_vc4(req_l2_link1[3]),
        .req_l3_vc1(req_l3_link1[0]),
        .req_l3_vc2(req_l3_link1[1]),
        .req_l3_vc3(req_l3_link1[2]),
        .req_l3_vc4(req_l3_link1[3]),
        .req_l4_vc1(req_l4_link1[0]),
        .req_l4_vc2(req_l4_link1[1]),
        .req_l4_vc3(req_l4_link1[2]),
        .req_l4_vc4(req_l4_link1[3]),
        .req_c_vc1(req_c_link1[0]),
        .req_c_vc2(req_c_link1[1]),
        .req_c_vc3(req_c_link1[2]),
        .req_c_vc4(req_c_link1[3]),
        .rd_en1(rd_en_link1[0]),
        .rd_en2(rd_en_link1[1]),
        .rd_en3(rd_en_link1[2]),
        .rd_en4(rd_en_link1[3]),
        .tailer_vc1(tailer_link1[0]),
        .tailer_vc2(tailer_link1[1]),
        .tailer_vc3(tailer_link1[2]),
        .tailer_vc4(tailer_link1[3]),
        .rok_vc1(rok_link1[0]),
        .rok_vc2(rok_link1[1]),
        .rok_vc3(rok_link1[2]),
        .rok_vc4(rok_link1[3]),
        .full_vc1(full_out_link1_vc1_reg),
        .full_vc2(full_out_link1_vc2_reg),
        .full_vc3(full_out_link1_vc3_reg),
        .full_vc4(full_out_link1_vc4_reg),
        .rd_en_vc1_link1_vc1(rd_en_link1[0]),
        .rd_en_vc1_link1_vc2(rd_en_link1[1]),
        .rd_en_vc1_link1_vc3(rd_en_link1[2]),
        .rd_en_vc1_link1_vc4(rd_en_link1[3]),
        .rd_en_vc1_link2_vc1(rd_en_link2[0]),
        .rd_en_vc1_link2_vc2(rd_en_link2[1]),
        .rd_en_vc1_link2_vc3(rd_en_link2[2]),
        .rd_en_vc1_link2_vc4(rd_en_link2[3]),
        .rd_en_vc1_link3_vc1(rd_en_link3[0]),
        .rd_en_vc1_link3_vc2(rd_en_link3[1]),
        .rd_en_vc1_link3_vc3(rd_en_link3[2]),
        .rd_en_vc1_link3_vc4(rd_en_link3[3]),
        .rd_en_vc1_link4_vc1(rd_en_link4[0]),
        .rd_en_vc1_link4_vc2(rd_en_link4[1]),
        .rd_en_vc1_link4_vc3(rd_en_link4[2]),
        .rd_en_vc1_link4_vc4(rd_en_link4[3]),
        .gnt_vc1(gnt_link1[0]),
        .gnt_vc2(gnt_link1[1]),
        .gnt_vc3(gnt_link1[2]),
        .gnt_vc4(gnt_link1[3]),
        .sel_vc(sel_vc_link1_reg)
    );

    ip_link ip_link2_inst (
        .reset(clr),
        .rd_clk(clk),
        .wr_clk(clk),
        .data_in(data_in_link2),
        .current_address(current_address),
        .data_out_vc1(ip_link2_out_vc1),
        .data_out_vc2(ip_link2_out_vc2),
        .data_out_vc3(ip_link2_out_vc3),
        .data_out_vc4(ip_link2_out_vc4),
        .full_vc1(full_in_link2_vc1),
        .full_vc2(full_in_link2_vc2),
        .full_vc3(full_in_link2_vc3),
        .full_vc4(full_in_link2_vc4),
        .req_l1_vc1(req_l1_link2[0]),
        .req_l1_vc2(req_l1_link2[1]),
        .req_l1_vc3(req_l1_link2[2]),
        .req_l1_vc4(req_l1_link2[3]),
        .req_l2_vc1(req_l2_link2[0]),
        .req_l2_vc2(req_l2_link2[1]),
        .req_l2_vc3(req_l2_link2[2]),
        .req_l2_vc4(req_l2_link2[3]),
        .req_l3_vc1(req_l3_link2[0]),
        .req_l3_vc2(req_l3_link2[1]),
        .req_l3_vc3(req_l3_link2[2]),
        .req_l3_vc4(req_l3_link2[3]),
        .req_l4_vc1(req_l4_link2[0]),
        .req_l4_vc2(req_l4_link2[1]),
        .req_l4_vc3(req_l4_link2[2]),
        .req_l4_vc4(req_l4_link2[3]),
        .req_c_vc1(req_c_link2[0]),
        .req_c_vc2(req_c_link2[1]),
        .req_c_vc3(req_c_link2[2]),
        .req_c_vc4(req_c_link2[3]),
        .rd_en1(rd_en_link2[0]),
        .rd_en2(rd_en_link2[1]),
        .rd_en3(rd_en_link2[2]),
        .rd_en4(rd_en_link2[3]),
        .tailer_vc1(tailer_link2[0]),
        .tailer_vc2(tailer_link2[1]),
        .tailer_vc3(tailer_link2[2]),
        .tailer_vc4(tailer_link2[3]),
        .rok_vc1(rok_link2[0]),
        .rok_vc2(rok_link2[1]),
        .rok_vc3(rok_link2[2]),
        .rok_vc4(rok_link2[3]),
        .full_vc1(full_out_link2_vc1_reg),
        .full_vc2(full_out_link2_vc2_reg),
        .full_vc3(full_out_link2_vc3_reg),
        .full_vc4(full_out_link2_vc4_reg),
        .rd_en_vc1_link1_vc1(rd_en_link1[0]),
        .rd_en_vc1_link1_vc2(rd_en_link1[1]),
        .rd_en_vc1_link1_vc3(rd_en_link1[2]),
        .rd_en_vc1_link1_vc4(rd_en_link1[3]),
        .rd_en_vc1_link2_vc1(rd_en_link2[0]),
        .rd_en_vc1_link2_vc2(rd_en_link2[1]),
        .rd_en_vc1_link2_vc3(rd_en_link2[2]),
        .rd_en_vc1_link2_vc4(rd_en_link2[3]),
        .rd_en_vc1_link3_vc1(rd_en_link3[0]),
        .rd_en_vc1_link3_vc2(rd_en_link3[1]),
        .rd_en_vc1_link3_vc3(rd_en_link3[2]),
        .rd_en_vc1_link3_vc4(rd_en_link3[3]),
        .rd_en_vc1_link4_vc1(rd_en_link4[0]),
        .rd_en_vc1_link4_vc2(rd_en_link4[1]),
        .rd_en_vc1_link4_vc3(rd_en_link4[2]),
        .rd_en_vc1_link4_vc4(rd_en_link4[3]),
        .gnt_vc1(gnt_link2[0]),
        .gnt_vc2(gnt_link2[1]),
        .gnt_vc3(gnt_link2[2]),
        .gnt_vc4(gnt_link2[3]),
        .sel_vc(sel_vc_link2_reg)
    );

    ip_link ip_link3_inst (
        .reset(clr),
        .rd_clk(clk),
        .wr_clk(clk),
        .data_in(data_in_link3),
        .current_address(current_address),
        .data_out_vc1(ip_link3_out_vc1),
        .data_out_vc2(ip_link3_out_vc2),
        .data_out_vc3(ip_link3_out_vc3),
        .data_out_vc4(ip_link3_out_vc4),
        .full_vc1(full_in_link3_vc1),
        .full_vc2(full_in_link3_vc2),
        .full_vc3(full_in_link3_vc3),
        .full_vc4(full_in_link3_vc4),
        .req_l1_vc1(req_l1_link3[0]),
        .req_l1_vc2(req_l1_link3[1]),
        .req_l1_vc3(req_l1_link3[2]),
        .req_l1_vc4(req_l1_link3[3]),
        .req_l2_vc1(req_l2_link3[0]),
        .req_l2_vc2(req_l2_link3[1]),
        .req_l2_vc3(req_l2_link3[2]),
        .req_l2_vc4(req_l2_link3[3]),
        .req_l3_vc1(req_l3_link3[0]),
        .req_l3_vc2(req_l3_link3[1]),
        .req_l3_vc3(req_l3_link3[2]),
        .req_l3_vc4(req_l3_link3[3]),
        .req_l4_vc1(req_l4_link3[0]),
        .req_l4_vc2(req_l4_link3[1]),
        .req_l4_vc3(req_l4_link3[2]),
        .req_l4_vc4(req_l4_link3[3]),
        .req_c_vc1(req_c_link3[0]),
        .req_c_vc2(req_c_link3[1]),
        .req_c_vc3(req_c_link3[2]),
        .req_c_vc4(req_c_link3[3]),
        .rd_en1(rd_en_link3[0]),
        .rd_en2(rd_en_link3[1]),
        .rd_en3(rd_en_link3[2]),
        .rd_en4(rd_en_link3[3]),
        .tailer_vc1(tailer_link3[0]),
        .tailer_vc2(tailer_link3[1]),
        .tailer_vc3(tailer_link3[2]),
        .tailer_vc4(tailer_link3[3]),
        .rok_vc1(rok_link3[0]),
        .rok_vc2(rok_link3[1]),
        .rok_vc3(rok_link3[2]),
        .rok_vc4(rok_link3[3]),
        .full_vc1(full_out_link3_vc1_reg),
        .full_vc2(full_out_link3_vc2_reg),
        .full_vc3(full_out_link3_vc3_reg),
        .full_vc4(full_out_link3_vc4_reg),
        .rd_en_vc1_link1_vc1(rd_en_link1[0]),
        .rd_en_vc1_link1_vc2(rd_en_link1[1]),
        .rd_en_vc1_link1_vc3(rd_en_link1[2]),
        .rd_en_vc1_link1_vc4(rd_en_link1[3]),
        .rd_en_vc1_link2_vc1(rd_en_link2[0]),
        .rd_en_vc1_link2_vc2(rd_en_link2[1]),
        .rd_en_vc1_link2_vc3(rd_en_link2[2]),
        .rd_en_vc1_link2_vc4(rd_en_link2[3]),
        .rd_en_vc1_link3_vc1(rd_en_link3[0]),
        .rd_en_vc1_link3_vc2(rd_en_link3[1]),
        .rd_en_vc1_link3_vc3(rd_en_link3[2]),
        .rd_en_vc1_link3_vc4(rd_en_link3[3]),
        .rd_en_vc1_link4_vc1(rd_en_link4[0]),
        .rd_en_vc1_link4_vc2(rd_en_link4[1]),
        .rd_en_vc1_link4_vc3(rd_en_link4[2]),
        .rd_en_vc1_link4_vc4(rd_en_link4[3]),
        .gnt_vc1(gnt_link3[0]),
        .gnt_vc2(gnt_link3[1]),
        .gnt_vc3(gnt_link3[2]),
        .gnt_vc4(gnt_link3[3]),
        .sel_vc(sel_vc_link3_reg)
    );

    ip_link ip_link4_inst (
        .reset(clr),
        .rd_clk(clk),
        .wr_clk(clk),
        .data_in(data_in_link4),
        .current_address(current_address),
        .data_out_vc1(ip_link4_out_vc1),
        .data_out_vc2(ip_link4_out_vc2),
        .data_out_vc3(ip_link4_out_vc3),
        .data_out_vc4(ip_link4_out_vc4),
        .full_vc1(full_in_link4_vc1),
        .full_vc2(full_in_link4_vc2),
        .full_vc3(full_in_link4_vc3),
        .full_vc4(full_in_link4_vc4),
        .req_l1_vc1(req_l1_link4[0]),
        .req_l1_vc2(req_l1_link4[1]),
        .req_l1_vc3(req_l1_link4[2]),
        .req_l1_vc4(req_l1_link4[3]),
        .req_l2_vc1(req_l2_link4[0]),
        .req_l2_vc2(req_l2_link4[1]),
        .req_l2_vc3(req_l2_link4[2]),
        .req_l2_vc4(req_l2_link4[3]),
        .req_l3_vc1(req_l3_link4[0]),
        .req_l3_vc2(req_l3_link4[1]),
        .req_l3_vc3(req_l3_link4[2]),
        .req_l3_vc4(req_l3_link4[3]),
        .req_l4_vc1(req_l4_link4[0]),
        .req_l4_vc2(req_l4_link4[1]),
        .req_l4_vc3(req_l4_link4[2]),
        .req_l4_vc4(req_l4_link4[3]),
        .req_c_vc1(req_c_link4[0]),
        .req_c_vc2(req_c_link4[1]),
        .req_c_vc3(req_c_link4[2]),
        .req_c_vc4(req_c_link4[3]),
        .rd_en1(rd_en_link4[0]),
        .rd_en2(rd_en_link4[1]),
        .rd_en3(rd_en_link4[2]),
        .rd_en4(rd_en_link4[3]),
        .tailer_vc1(tailer_link4[0]),
        .tailer_vc2(tailer_link4[1]),
        .tailer_vc3(tailer_link4[2]),
        .tailer_vc4(tailer_link4[3]),
        .rok_vc1(rok_link4[0]),
        .rok_vc2(rok_link4[1]),
        .rok_vc3(rok_link4[2]),
        .rok_vc4(rok_link4[3]),
        .full_vc1(full_out_link4_vc1_reg),
        .full_vc2(full_out_link4_vc2_reg),
        .full_vc3(full_out_link4_vc3_reg),
        .full_vc4(full_out_link4_vc4_reg),
        .rd_en_vc1_link1_vc1(rd_en_link1[0]),
        .rd_en_vc1_link1_vc2(rd_en_link1[1]),
        .rd_en_vc1_link1_vc3(rd_en_link1[2]),
        .rd_en_vc1_link1_vc4(rd_en_link1[3]),
        .rd_en_vc1_link2_vc1(rd_en_link2[0]),
        .rd_en_vc1_link2_vc2(rd_en_link2[1]),
        .rd_en_vc1_link2_vc3(rd_en_link2[2]),
        .rd_en_vc1_link2_vc4(rd_en_link2[3]),
        .rd_en_vc1_link3_vc1(rd_en_link3[0]),
        .rd_en_vc1_link3_vc2(rd_en_link3[1]),
        .rd_en_vc1_link3_vc3(rd_en_link3[2]),
        .rd_en_vc1_link3_vc4(rd_en_link3[3]),
        .rd_en_vc1_link4_vc1(rd_en_link4[0]),
        .rd_en_vc1_link4_vc2(rd_en_link4[1]),
        .rd_en_vc1_link4_vc3(rd_en_link4[2]),
        .rd_en_vc1_link4_vc4(rd_en_link4[3]),
        .gnt_vc1(gnt_link4[0]),
        .gnt_vc2(gnt_link4[1]),
        .gnt_vc3(gnt_link4[2]),
        .gnt_vc4(gnt_link4[3]),
        .sel_vc(sel_vc_link4_reg)
    );

    ip_link ip_core_inst (
        .reset(clr),
        .rd_clk(clk),
        .wr_clk(clk),
        .data_in(data_in_core),
        .current_address(current_address),
        .data_out_vc1(ip_core_out_vc1),
        .data_out_vc2(ip_core_out_vc2),
        .data_out_vc3(ip_core_out_vc3),
        .data_out_vc4(ip_core_out_vc4),
        .full_vc1(full_in_core_vc1),
        .full_vc2(full_in_core_vc2),
        .full_vc3(full_in_core_vc3),
        .full_vc4(full_in_core_vc4),
        .req_l1_vc1(req_l1_core[0]),
        .req_l1_vc2(req_l1_core[1]),
        .req_l1_vc3(req_l1_core[2]),
        .req_l1_vc4(req_l1_core[3]),
        .req_l2_vc1(req_l2_core[0]),
        .req_l2_vc2(req_l2_core[1]),
        .req_l2_vc3(req_l2_core[2]),
        .req_l2_vc4(req_l2_core[3]),
        .req_l3_vc1(req_l3_core[0]),
        .req_l3_vc2(req_l3_core[1]),
        .req_l3_vc3(req_l3_core[2]),
        .req_l3_vc4(req_l3_core[3]),
        .req_l4_vc1(req_l4_core[0]),
        .req_l4_vc2(req_l4_core[1]),
        .req_l4_vc3(req_l4_core[2]),
        .req_l4_vc4(req_l4_core[3]),
        .req_c_vc1(req_c_core[0]),
        .req_c_vc2(req_c_core[1]),
        .req_c_vc3(req_c_core[2]),
        .req_c_vc4(req_c_core[3]),
        .rd_en1(rd_en_core[0]),
        .rd_en2(rd_en_core[1]),
        .rd_en3(rd_en_core[2]),
        .rd_en4(rd_en_core[3]),
        .tailer_vc1(tailer_core[0]),
        .tailer_vc2(tailer_core[1]),
        .tailer_vc3(tailer_core[2]),
        .tailer_vc4(tailer_core[3]),
        .rok_vc1(rok_core[0]),
        .rok_vc2(rok_core[1]),
        .rok_vc3(rok_core[2]),
        .rok_vc4(rok_core[3]),
        .full_vc1(full_out_core_vc1),
        .full_vc2(full_out_core_vc2),
        .full_vc3(full_out_core_vc3),
        .full_vc4(full_out_core_vc4),
        .rd_en_vc1_link1_vc1(rd_en_link1[0]),
        .rd_en_vc1_link1_vc2(rd_en_link1[1]),
        .rd_en_vc1_link1_vc3(rd_en_link1[2]),
        .rd_en_vc1_link1_vc4(rd_en_link1[3]),
        .rd_en_vc1_link2_vc1(rd_en_link2[0]),
        .rd_en_vc1_link2_vc2(rd_en_link2[1]),
        .rd_en_vc1_link2_vc3(rd_en_link2[2]),
        .rd_en_vc1_link2_vc4(rd_en_link2[3]),
        .rd_en_vc1_link3_vc1(rd_en_link3[0]),
        .rd_en_vc1_link3_vc2(rd_en_link3[1]),
        .rd_en_vc1_link3_vc3(rd_en_link3[2]),
        .rd_en_vc1_link3_vc4(rd_en_link3[3]),
        .rd_en_vc1_link4_vc1(rd_en_link4[0]),
        .rd_en_vc1_link4_vc2(rd_en_link4[1]),
        .rd_en_vc1_link4_vc3(rd_en_link4[2]),
        .rd_en_vc1_link4_vc4(rd_en_link4[3]),
        .gnt_vc1(gnt_core[0]),
        .gnt_vc2(gnt_core[1]),
        .gnt_vc3(gnt_core[2]),
        .gnt_vc4(gnt_core[3]),
        .sel_vc(sel_vc_core_reg)
    );

    op_data_path op_data_path_inst (
        .clk(clk),
        .reset(clr),
        .data_from_link1_ch1(ip_link1_out_vc1),
        .data_from_link1_ch2(ip_link1_out_vc2),
        .data_from_link1_ch3(ip_link1_out_vc3),
        .data_from_link1_ch4(ip_link1_out_vc4),
        .data_from_link2_ch1(ip_link2_out_vc1),
        .data_from_link2_ch2(ip_link2_out_vc2),
        .data_from_link2_ch3(ip_link2_out_vc3),
        .data_from_link2_ch4(ip_link2_out_vc4),
        .data_from_link3_ch1(ip_link3_out_vc1),
        .data_from_link3_ch2(ip_link3_out_vc2),
        .data_from_link3_ch3(ip_link3_out_vc3),
        .data_from_link3_ch4(ip_link3_out_vc4),
        .data_from_link4_ch1(ip_link4_out_vc1),
        .data_from_link4_ch2(ip_link4_out_vc2),
        .data_from_link4_ch3(ip_link4_out_vc3),
        .data_from_link4_ch4(ip_link4_out_vc4),
        .data_from_core_ch1(ip_core_out_vc1),
        .data_from_core_ch2(ip_core_out_vc2),
        .data_from_core_ch3(ip_core_out_vc3),
        .data_from_core_ch4(ip_core_out_vc4),
        .sel_vc_link1(sel_vc_link1_reg),
        .sel_vc_link2(sel_vc_link2_reg),
        .sel_vc_link3(sel_vc_link3_reg),
        .sel_vc_link4(sel_vc_link4_reg),
        .sel_vc_core(sel_vc_core_reg),
        .gnt_vc_link1_ch1(gnt_link1[0]),
        .gnt_vc_link1_ch2(gnt_link1[1]),
        .gnt_vc_link1_ch3(gnt_link1[2]),
        .gnt_vc_link1_ch4(gnt_link1[3]),
        .gnt_vc_link2_ch1(gnt_link2[0]),
        .gnt_vc_link2_ch2(gnt_link2[1]),
        .gnt_vc_link2_ch3(gnt_link2[2]),
        .gnt_vc_link2_ch4(gnt_link2[3]),
        .gnt_vc_link3_ch1(gnt_link3[0]),
        .gnt_vc_link3_ch2(gnt_link3[1]),
        .gnt_vc_link3_ch3(gnt_link3[2]),
        .gnt_vc_link3_ch4(gnt_link3[3]),
        .gnt_vc_link4_ch1(gnt_link4[0]),
        .gnt_vc_link4_ch2(gnt_link4[1]),
        .gnt_vc_link4_ch3(gnt_link4[2]),
        .gnt_vc_link4_ch4(gnt_link4[3]),
        .gnt_vc_core_ch1(gnt_core[0]),
        .gnt_vc_core_ch2(gnt_core[1]),
        .gnt_vc_core_ch3(gnt_core[2]),
        .gnt_vc_core_ch4(gnt_core[3]),
        .data_out_link1(op_data_path_link1),
        .data_out_link2(op_data_path_link2),
        .data_out_link3(op_data_path_link3),
        .data_out_link4(op_data_path_link4),
        .data_out_core(op_data_path_core),
        .data_out_l1(data_out_l1),
        .data_out_l2(data_out_l2),
        .data_out_l3(data_out_l3),
        .data_out_l4(data_out_l4),
        .data_out_c(data_out_c)
    );

    assign data_out_link1 = op_data_path_link1;
    assign data_out_link2 = op_data_path_link2;
    assign data_out_link3 = op_data_path_link3;
    assign data_out_link4 = op_data_path_link4;
    assign data_out_core = op_data_path_core;

    assign data_out_link1_vc1 = ip_link1_out_vc1;
    assign data_out_link1_vc2 = ip_link1_out_vc2;
    assign data_out_link1_vc3 = ip_link1_out_vc3;
    assign data_out_link1_vc4 = ip_link1_out_vc4;
    assign data_out_link2_vc1 = ip_link2_out_vc1;
    assign data_out_link2_vc2 = ip_link2_out_vc2;
    assign data_out_link2_vc3 = ip_link2_out_vc3;
    assign data_out_link2_vc4 = ip_link2_out_vc4;
    assign data_out_link3_vc1 = ip_link3_out_vc1;
    assign data_out_link3_vc2 = ip_link3_out_vc2;
    assign data_out_link3_vc3 = ip_link3_out_vc3;
    assign data_out_link3_vc4 = ip_link3_out_vc4;
    assign data_out_link4_vc1 = ip_link4_out_vc1;
    assign data_out_link4_vc2 = ip_link4_out_vc2;
    assign data_out_link4_vc3 = ip_link4_out_vc3;
    assign data_out_link4_vc4 = ip_link4_out_vc4;
    assign data_out_core_vc1 = ip_core_out_vc1;
    assign data_out_core_vc2 = ip_core_out_vc2;
    assign data_out_core_vc3 = ip_core_out_vc3;
    assign data_out_core_vc4 = ip_core_out_vc4;

    assign full_out_link1_vc1 = full_out_link1_vc1_reg;
    assign full_out_link1_vc2 = full_out_link1_vc2_reg;
    assign full_out_link1_vc3 = full_out_link1_vc3_reg;
    assign full_out_link1_vc4 = full_out_link1_vc4_reg;
    assign full_out_link2_vc1 = full_out_link2_vc1_reg;
    assign full_out_link2_vc2 = full_out_link2_vc2_reg;
    assign full_out_link2_vc3 = full_out_link2_vc3_reg;
    assign full_out_link2_vc4 = full_out_link2_vc4_reg;
    assign full_out_link3_vc1 = full_out_link3_vc1_reg;
    assign full_out_link3_vc2 = full_out_link3_vc2_reg;
    assign full_out_link3_vc3 = full_out_link3_vc3_reg;
    assign full_out_link3_vc4 = full_out_link3_vc4_reg;
    assign full_out_link4_vc1 = full_out_link4_vc1_reg;
    assign full_out_link4_vc2 = full_out_link4_vc2_reg;
    assign full_out_link4_vc3 = full_out_link4_vc3_reg;
    assign full_out_link4_vc4 = full_out_link4_vc4_reg;

    assign sel_vc_link1 = sel_vc_link1_reg;
    assign sel_vc_link2 = sel_vc_link2_reg;
    assign sel_vc_link3 = sel_vc_link3_reg;
    assign sel_vc_link4 = sel_vc_link4_reg;
    assign sel_vc_core = sel_vc_core_reg;

    always @(*) begin
        req_l1_link1 = 4'b0000;
        req_l2_link1 = 4'b0000;
        req_l3_link1 = 4'b0000;
        req_l4_link1 = 4'b0000;
        req_c_link1 = 4'b0000;

        req_l1_link2 = 4'b0000;
        req_l2_link2 = 4'b0000;
        req_l3_link2 = 4'b0000;
        req_l4_link2 = 4'b0000;
        req_c_link2 = 4'b0000;

        req_l1_link3 = 4'b0000;
        req_l2_link3 = 4'b0000;
        req_l3_link3 = 4'b0000;
        req_l4_link3 = 4'b0000;
        req_c_link3 = 4'b0000;

        req_l1_link4 = 4'b0000;
        req_l2_link4 = 4'b0000;
        req_l3_link4 = 4'b0000;
        req_l4_link4 = 4'b0000;
        req_c_link4 = 4'b0000;

        req_l1_core = 4'b0000;
        req_l2_core = 4'b0000;
        req_l3_core = 4'b0000;
        req_l4_core = 4'b0000;
        req_c_core = 4'b0000;

        case (ip_link1_out_vc1[30:29])
            2'b01: begin
                if (ip_link1_out_vc1[7:4] > current_address[7:4])
                    req_l1_link1 = 4'b1111;
                else if (ip_link1_out_vc1[7:4] < current_address[7:4])
                    req_l2_link1 = 4'b1111;
                else if (ip_link1_out_vc1[3:0] > current_address[3:0])
                    req_l3_link1 = 4'b1111;
                else if (ip_link1_out_vc1[3:0] < current_address[3:0])
                    req_l4_link1 = 4'b1111;
                else
                    req_c_link1 = 4'b1111;
            end
            2'b10: begin
                if (ip_link1_out_vc1[7:4] > current_address[7:4])
                    req_l1_link1 = 4'b1111;
                else if (ip_link1_out_vc1[7:4] < current_address[7:4])
                    req_l2_link1 = 4'b1111;
                else if (ip_link1_out_vc1[3:0] > current_address[3:0])
                    req_l3_link1 = 4'b1111;
                else if (ip_link1_out_vc1[3:0] < current_address[3:0])
                    req_l4_link1 = 4'b1111;
                else
                    req_c_link1 = 4'b1111;
            end
            2'b11: begin
                req_c_link1 = 4'b1111;
            end
            default: begin
                req_c_link1 = 4'b1111;
            end
        endcase

        case (ip_link1_out_vc2[30:29])
            2'b01: begin
                if (ip_link1_out_vc2[7:4] > current_address[7:4])
                    req_l1_link1 = 4'b1111;
                else if (ip_link1_out_vc2[7:4] < current_address[7:4])
                    req_l2_link1 = 4'b1111;
                else if (ip_link1_out_vc2[3:0] > current_address[3:0])
                    req_l3_link1 = 4'b1111;
                else if (ip_link1_out_vc2[3:0] < current_address[3:0])
                    req_l4_link1 = 4'b1111;
                else
                    req_c_link1 = 4'b1111;
            end
            2'b10: begin
                if (ip_link1_out_vc2[7:4] > current_address[7:4])
                    req_l1_link1 = 4'b1111;
                else if (ip_link1_out_vc2[7:4] < current_address[7:4])
                    req_l2_link1 = 4'b1111;
                else if (ip_link1_out_vc2[3:0] > current_address[3:0])
                    req_l3_link1 = 4'b1111;
                else if (ip_link1_out_vc2[3:0] < current_address[3:0])
                    req_l4_link1 = 4'b1111;
                else
                    req_c_link1 = 4'b1111;
            end
            2'b11: begin
                req_c_link1 = 4'b1111;
            end
            default: begin
                req_c_link1 = 4'b1111;
            end
        endcase

        case (ip_link1_out_vc3[30:29])
            2'b01: begin
                if (ip_link1_out_vc3[7:4] > current_address[7:4])
                    req_l1_link1 = 4'b1111;
                else if (ip_link1_out_vc3[7:4] < current_address[7:4])
                    req_l2_link1 = 4'b1111;
                else if (ip_link1_out_vc3[3:0] > current_address[3:0])
                    req_l3_link1 = 4'b1111;
                else if (ip_link1_out_vc3[3:0] < current_address[3:0])
                    req_l4_link1 = 4'b1111;
                else
                    req_c_link1 = 4'b1111;
            end
            2'b10: begin
                if (ip_link1_out_vc3[7:4] > current_address[7:4])
                    req_l1_link1 = 4'b1111;
                else if (ip_link1_out_vc3[7:4] < current_address[7:4])
                    req_l2_link1 = 4'b1111;
                else if (ip_link1_out_vc3[3:0] > current_address[3:0])
                    req_l3_link1 = 4'b1111;
                else if (ip_link1_out_vc3[3:0] < current_address[3:0])
                    req_l4_link1 = 4'b1111;
                else
                    req_c_link1 = 4'b1111;
            end
            2'b11: begin
                req_c_link1 = 4'b1111;
            end
            default: begin
                req_c_link1 = 4'b1111;
            end
        endcase

        case (ip_link1_out_vc4[30:29])
            2'b01: begin
                if (ip_link1_out_vc4[7:4] > current_address[7:4])
                    req_l1_link1 = 4'b1111;
                else if (ip_link1_out_vc4[7:4] < current_address[7:4])
                    req_l2_link1 = 4'b1111;
                else if (ip_link1_out_vc4[3:0] > current_address[3:0])
                    req_l3_link1 = 4'b1111;
                else if (ip_link1_out_vc4[3:0] < current_address[3:0])
                    req_l4_link1 = 4'b1111;
                else
                    req_c_link1 = 4'b1111;
            end
            2'b10: begin
                if (ip_link1_out_vc4[7:4] > current_address[7:4])
                    req_l1_link1 = 4'b1111;
                else if (ip_link1_out_vc4[7:4] < current_address[7:4])
                    req_l2_link1 = 4'b1111;
                else if (ip_link1_out_vc4[3:0] > current_address[3:0])
                    req_l3_link1 = 4'b1111;
                else if (ip_link1_out_vc4[3:0] < current_address[3:0])
                    req_l4_link1 = 4'b1111;
                else
                    req_c_link1 = 4'b1111;
            end
            2'b11: begin
                req_c_link1 = 4'b1111;
            end
            default: begin
                req_c_link1 = 4'b1111;
            end
        endcase

        case (ip_link2_out_vc1[30:29])
            2'b01: begin
                if (ip_link2_out_vc1[7:4] > current_address[7:4])
                    req_l1_link2 = 4'b1111;
                else if (ip_link2_out_vc1[7:4] < current_address[7:4])
                    req_l2_link2 = 4'b1111;
                else if (ip_link2_out_vc1[3:0] > current_address[3:0])
                    req_l3_link2 = 4'b1111;
                else if (ip_link2_out_vc1[3:0] < current_address[3:0])
                    req_l4_link2 = 4'b1111;
                else
                    req_c_link2 = 4'b1111;
            end
            2'b10: begin
                if (ip_link2_out_vc1[7:4] > current_address[7:4])
                    req_l1_link2 = 4'b1111;
                else if (ip_link2_out_vc1[7:4] < current_address[7:4])
                    req_l2_link2 = 4'b1111;
                else if (ip_link2_out_vc1[3:0] > current_address[3:0])
                    req_l3_link2 = 4'b1111;
                else if (ip_link2_out_vc1[3:0] < current_address[3:0])
                    req_l4_link2 = 4'b1111;
                else
                    req_c_link2 = 4'b1111;
            end
            2'b11: begin
                req_c_link2 = 4'b1111;
            end
            default: begin
                req_c_link2 = 4'b1111;
            end
        endcase

        case (ip_link2_out_vc2[30:29])
            2'b01: begin
                if (ip_link2_out_vc2[7:4] > current_address[7:4])
                    req_l1_link2 = 4'b1111;
                else if (ip_link2_out_vc2[7:4] < current_address[7:4])
                    req_l2_link2 = 4'b1111;
                else if (ip_link2_out_vc2[3:0] > current_address[3:0])
                    req_l3_link2 = 4'b1111;
                else if (ip_link2_out_vc2[3:0] < current_address[3:0])
                    req_l4_link2 = 4'b1111;
                else
                    req_c_link2 = 4'b1111;
            end
            2'b10: begin
                if (ip_link2_out_vc2[7:4] > current_address[7:4])
                    req_l1_link2 = 4'b1111;
                else if (ip_link2_out_vc2[7:4] < current_address[7:4])
                    req_l2_link2 = 4'b1111;
                else if (ip_link2_out_vc2[3:0] > current_address[3:0])
                    req_l3_link2 = 4'b1111;
                else if (ip_link2_out_vc2[3:0] < current_address[3:0])
                    req_l4_link2 = 4'b1111;
                else
                    req_c_link2 = 4'b1111;
            end
            2'b11: begin
                req_c_link2 = 4'b1111;
            end
            default: begin
                req_c_link2 = 4'b1111;
            end
        endcase

        case (ip_link2_out_vc3[30:29])
            2'b01: begin
                if (ip_link2_out_vc3[7:4] > current_address[7:4])
                    req_l1_link2 = 4'b1111;
                else if (ip_link2_out_vc3[7:4] < current_address[7:4])
                    req_l2_link2 = 4'b1111;
                else if (ip_link2_out_vc3[3:0] > current_address[3:0])
                    req_l3_link2 = 4'b1111;
                else if (ip_link2_out_vc3[3:0] < current_address[3:0])
                    req_l4_link2 = 4'b1111;
                else
                    req_c_link2 = 4'b1111;
            end
            2'b10: begin
                if (ip_link2_out_vc3[7:4] > current_address[7:4])
                    req_l1_link2 = 4'b1111;
                else if (ip_link2_out_vc3[7:4] < current_address[7:4])
                    req_l2_link2 = 4'b1111;
                else if (ip_link2_out_vc3[3:0] > current_address[3:0])
                    req_l3_link2 = 4'b1111;
                else if (ip_link2_out_vc3[3:0] < current_address[3:0])
                    req_l4_link2 = 4'b1111;
                else
                    req_c_link2 = 4'b1111;
            end
            2'b11: begin
                req_c_link2 = 4'b1111;
            end
            default: begin
                req_c_link2 = 4'b1111;
            end
        endcase

        case (ip_link2_out_vc4[30:29])
            2'b01: begin
                if (ip_link2_out_vc4[7:4] > current_address[7:4])
                    req_l1_link2 = 4'b1111;
                else if (ip_link2_out_vc4[7:4] < current_address[7:4])
                    req_l2_link2 = 4'b1111;
                else if (ip_link2_out_vc4[3:0] > current_address[3:0])
                    req_l3_link2 = 4'b1111;
                else if (ip_link2_out_vc4[3:0] < current_address[3:0])
                    req_l4_link2 = 4'b1111;
                else
                    req_c_link2 = 4'b1111;
            end
            2'b10: begin
                if (ip_link2_out_vc4[7:4] > current_address[7:4])
                    req_l1_link2 = 4'b1111;
                else if (ip_link2_out_vc4[7:4] < current_address[7:4])
                    req_l2_link2 = 4'b1111;
                else if (ip_link2_out_vc4[3:0] > current_address[3:0])
                    req_l3_link2 = 4'b1111;
                else if (ip_link2_out_vc4[3:0] < current_address[3:0])
                    req_l4_link2 = 4'b1111;
                else
                    req_c_link2 = 4'b1111;
            end
            2'b11: begin
                req_c_link2 = 4'b1111;
            end
            default: begin
                req_c_link2 = 4'b1111;
            end
        endcase

        case (ip_link3_out_vc1[30:29])
            2'b01: begin
                if (ip_link3_out_vc1[7:4] > current_address[7:4])
                    req_l1_link3 = 4'b1111;
                else if (ip_link3_out_vc1[7:4] < current_address[7:4])
                    req_l2_link3 = 4'b1111;
                else if (ip_link3_out_vc1[3:0] > current_address[3:0])
                    req_l3_link3 = 4'b1111;
                else if (ip_link3_out_vc1[3:0] < current_address[3:0])
                    req_l4_link3 = 4'b1111;
                else
                    req_c_link3 = 4'b1111;
            end
            2'b10: begin
                if (ip_link3_out_vc1[7:4] > current_address[7:4])
                    req_l1_link3 = 4'b1111;
                else if (ip_link3_out_vc1[7:4] < current_address[7:4])
                    req_l2_link3 = 4'b1111;
                else if (ip_link3_out_vc1[3:0] > current_address[3:0])
                    req_l3_link3 = 4'b1111;
                else if (ip_link3_out_vc1[3:0] < current_address[3:0])
                    req_l4_link3 = 4'b1111;
                else
                    req_c_link3 = 4'b1111;
            end
            2'b11: begin
                req_c_link3 = 4'b1111;
            end
            default: begin
                req_c_link3 = 4'b1111;
            end
        endcase

        case (ip_link3_out_vc2[30:29])
            2'b01: begin
                if (ip_link3_out_vc2[7:4] > current_address[7:4])
                    req_l1_link3 = 4'b1111;
                else if (ip_link3_out_vc2[7:4] < current_address[7:4])
                    req_l2_link3 = 4'b1111;
                else if (ip_link3_out_vc2[3:0] > current_address[3:0])
                    req_l3_link3 = 4'b1111;
                else if (ip_link3_out_vc2[3:0] < current_address[3:0])
                    req_l4_link3 = 4'b1111;
                else
                    req_c_link3 = 4'b1111;
            end
            2'b10: begin
                if (ip_link3_out_vc2[7:4] > current_address[7:4])
                    req_l1_link3 = 4'b1111;
                else if (ip_link3_out_vc2[7:4] < current_address[7:4])
                    req_l2_link3 = 4'b1111;
                else if (ip_link3_out_vc2[3:0] > current_address[3:0])
                    req_l3_link3 = 4'b1111;
                else if (ip_link3_out_vc2[3:0] < current_address[3:0])
                    req_l4_link3 = 4'b1111;
                else
                    req_c_link3 = 4'b1111;
            end
            2'b11: begin
                req_c_link3 = 4'b1111;
            end
            default: begin
                req_c_link3 = 4'b1111;
            end
        endcase

        case (ip_link3_out_vc3[30:29])
            2'b01: begin
                if (ip_link3_out_vc3[7:4] > current_address[7:4])
                    req_l1_link3 = 4'b1111;
                else if (ip_link3_out_vc3[7:4] < current_address[7:4])
                    req_l2_link3 = 4'b1111;
                else if (ip_link3_out_vc3[3:0] > current_address[3:0])
                    req_l3_link3 = 4'b1111;
                else if (ip_link3_out_vc3[3:0] < current_address[3:0])
                    req_l4_link3 = 4'b1111;
                else
                    req_c_link3 = 4'b1111;
            end
            2'b10: begin
                if (ip_link3_out_vc3[7:4] > current_address[7:4])
                    req_l1_link3 = 4'b1111;
                else if (ip_link3_out_vc3[7:4] < current_address[7:4])
                    req_l2_link3 = 4'b1111;
                else if (ip_link3_out_vc3[3:0] > current_address[3:0])
                    req_l3_link3 = 4'b1111;
                else if (ip_link3_out_vc3[3:0] < current_address[3:0])
                    req_l4_link3 = 4'b1111;
                else
                    req_c_link3 = 4'b1111;
            end
            2'b11: begin
                req_c_link3 = 4'b1111;
            end
            default: begin
                req_c_link3 = 4'b1111;
            end
        endcase

        case (ip_link3_out_vc4[30:29])
            2'b01: begin
                if (ip_link3_out_vc4[7:4] > current_address[7:4])
                    req_l1_link3 = 4'b1111;
                else if (ip_link3_out_vc4[7:4] < current_address[7:4])
                    req_l2_link3 = 4'b1111;
                else if (ip_link3_out_vc4[3:0] > current_address[3:0])
                    req_l3_link3 = 4'b1111;
                else if (ip_link3_out_vc4[3:0] < current_address[3:0])
                    req_l4_link3 = 4'b1111;
                else
                    req_c_link3 = 4'b1111;
            end
            2'b10: begin
                if (ip_link3_out_vc4[7:4] > current_address[7:4])
                    req_l1_link3 = 4'b1111;
                else if (ip_link3_out_vc4[7:4] < current_address[7:4])
                    req_l2_link3 = 4'b1111;
                else if (ip_link3_out_vc4[3:0] > current_address[3:0])
                    req_l3_link3 = 4'b1111;
                else if (ip_link3_out_vc4[3:0] < current_address[3:0])
                    req_l4_link3 = 4'b1111;
                else
                    req_c_link3 = 4'b1111;
            end
            2'b11: begin
                req_c_link3 = 4'b1111;
            end
            default: begin
                req_c_link3 = 4'b1111;
            end
        endcase

        case (ip_link4_out_vc1[30:29])
            2'b01: begin
                if (ip_link4_out_vc1[7:4] > current_address[7:4])
                    req_l1_link4 = 4'b1111;
                else if (ip_link4_out_vc1[7:4] < current_address[7:4])
                    req_l2_link4 = 4'b1111;
                else if (ip_link4_out_vc1[3:0] > current_address[3:0])
                    req_l3_link4 = 4'b1111;
                else if (ip_link4_out_vc1[3:0] < current_address[3:0])
                    req_l4_link4 = 4'b1111;
                else
                    req_c_link4 = 4'b1111;
            end
            2'b10: begin
                if (ip_link4_out_vc1[7:4] > current_address[7:4])
                    req_l1_link4 = 4'b1111;
                else if (ip_link4_out_vc1[7:4] < current_address[7:4])
                    req_l2_link4 = 4'b1111;
                else if (ip_link4_out_vc1[3:0] > current_address[3:0])
                    req_l3_link4 = 4'b1111;
                else if (ip_link4_out_vc1[3:0] < current_address[3:0])
                    req_l4_link4 = 4'b1111;
                else
                    req_c_link4 = 4'b1111;
            end
            2'b11: begin
                req_c_link4 = 4'b1111;
            end
            default: begin
                req_c_link4 = 4'b1111;
            end
        endcase

        case (ip_link4_out_vc2[30:29])
            2'b01: begin
                if (ip_link4_out_vc2[7:4] > current_address[7:4])
                    req_l1_link4 = 4'b1111;
                else if (ip_link4_out_vc2[7:4] < current_address[7:4])
                    req_l2_link4 = 4'b1111;
                else if (ip_link4_out_vc2[3:0] > current_address[3:0])
                    req_l3_link4 = 4'b1111;
                else if (ip_link4_out_vc2[3:0] < current_address[3:0])
                    req_l4_link4 = 4'b1111;
                else
                    req_c_link4 = 4'b1111;
            end
            2'b10: begin
                if (ip_link4_out_vc2[7:4] > current_address[7:4])
                    req_l1_link4 = 4'b1111;
                else if (ip_link4_out_vc2[7:4] < current_address[7:4])
                    req_l2_link4 = 4'b1111;
                else if (ip_link4_out_vc2[3:0] > current_address[3:0])
                    req_l3_link4 = 4'b1111;
                else if (ip_link4_out_vc2[3:0] < current_address[3:0])
                    req_l4_link4 = 4'b1111;
                else
                    req_c_link4 = 4'b1111;
            end
            2'b11: begin
                req_c_link4 = 4'b1111;
            end
            default: begin
                req_c_link4 = 4'b1111;
            end
        endcase

        case (ip_link4_out_vc3[30:29])
            2'b01: begin
                if (ip_link4_out_vc3[7:4] > current_address[7:4])
                    req_l1_link4 = 4'b1111;
                else if (ip_link4_out_vc3[7:4] < current_address[7:4])
                    req_l2_link4 = 4'b1111;
                else if (ip_link4_out_vc3[3:0] > current_address[3:0])
                    req_l3_link4 = 4'b1111;
                else if (ip_link4_out_vc3[3:0] < current_address[3:0])
                    req_l4_link4 = 4'b1111;
                else
                    req_c_link4 = 4'b1111;
            end
            2'b10: begin
                if (ip_link4_out_vc3[7:4] > current_address[7:4])
                    req_l1_link4 = 4'b1111;
                else if (ip_link4_out_vc3[7:4] < current_address[7:4])
                    req_l2_link4 = 4'b1111;
                else if (ip_link4_out_vc3[3:0] > current_address[3:0])
                    req_l3_link4 = 4'b1111;
                else if (ip_link4_out_vc3[3:0] < current_address[3:0])
                    req_l4_link4 = 4'b1111;
                else
                    req_c_link4 = 4'b1111;
            end
            2'b11: begin
                req_c_link4 = 4'b1111;
            end
            default: begin
                req_c_link4 = 4'b1111;
            end
        endcase

        case (ip_link4_out_vc4[30:29])
            2'b01: begin
                if (ip_link4_out_vc4[7:4] > current_address[7:4])
                    req_l1_link4 = 4'b1111;
                else if (ip_link4_out_vc4[7:4] < current_address[7:4])
                    req_l2_link4 = 4'b1111;
                else if (ip_link4_out_vc4[3:0] > current_address[3:0])
                    req_l3_link4 = 4'b1111;
                else if (ip_link4_out_vc4[3:0] < current_address[3:0])
                    req_l4_link4 = 4'b1111;
                else
                    req_c_link4 = 4'b1111;
            end
            2'b10: begin
                if (ip_link4_out_vc4[7:4] > current_address[7:4])
                    req_l1_link4 = 4'b1111;
                else if (ip_link4_out_vc4[7:4] < current_address[7:4])
                    req_l2_link4 = 4'b1111;
                else if (ip_link4_out_vc4[3:0] > current_address[3:0])
                    req_l3_link4 = 4'b1111;
                else if (ip_link4_out_vc4[3:0] < current_address[3:0])
                    req_l4_link4 = 4'b1111;
                else
                    req_c_link4 = 4'b1111;
            end
            2'b11: begin
                req_c_link4 = 4'b1111;
            end
            default: begin
                req_c_link4 = 4'b1111;
            end
        endcase

        case (ip_core_out_vc1[30:29])
            2'b01: begin
                if (ip_core_out_vc1[7:4] > current_address[7:4])
                    req_l1_core = 4'b1111;
                else if (ip_core_out_vc1[7:4] < current_address[7:4])
                    req_l2_core = 4'b1111;
                else if (ip_core_out_vc1[3:0] > current_address[3:0])
                    req_l3_core = 4'b1111;
                else if (ip_core_out_vc1[3:0] < current_address[3:0])
                    req_l4_core = 4'b1111;
                else
                    req_c_core = 4'b1111;
            end
            2'b10: begin
                if (ip_core_out_vc1[7:4] > current_address[7:4])
                    req_l1_core = 4'b1111;
                else if (ip_core_out_vc1[7:4] < current_address[7:4])
                    req_l2_core = 4'b1111;
                else if (ip_core_out_vc1[3:0] > current_address[3:0])
                    req_l3_core = 4'b1111;
                else if (ip_core_out_vc1[3:0] < current_address[3:0])
                    req_l4_core = 4'b1111;
                else
                    req_c_core = 4'b1111;
            end
            2'b11: begin
                req_c_core = 4'b1111;
            end
            default: begin
                req_c_core = 4'b1111;
            end
        endcase

        case (ip_core_out_vc2[30:29])
            2'b01: begin
                if (ip_core_out_vc2[7:4] > current_address[7:4])
                    req_l1_core = 4'b1111;
                else if (ip_core_out_vc2[7:4] < current_address[7:4])
                    req_l2_core = 4'b1111;
                else if (ip_core_out_vc2[3:0] > current_address[3:0])
                    req_l3_core = 4'b1111;
                else if (ip_core_out_vc2[3:0] < current_address[3:0])
                    req_l4_core = 4'b1111;
                else
                    req_c_core = 4'b1111;
            end
            2'b10: begin
                if (ip_core_out_vc2[7:4] > current_address[7:4])
                    req_l1_core = 4'b1111;
                else if (ip_core_out_vc2[7:4] < current_address[7:4])
                    req_l2_core = 4'b1111;
                else if (ip_core_out_vc2[3:0] > current_address[3:0])
                    req_l3_core = 4'b1111;
                else if (ip_core_out_vc2[3:0] < current_address[3:0])
                    req_l4_core = 4'b1111;
                else
                    req_c_core = 4'b1111;
            end
            2'b11: begin
                req_c_core = 4'b1111;
            end
            default: begin
                req_c_core = 4'b1111;
            end
        endcase

        case (ip_core_out_vc3[30:29])
            2'b01: begin
                if (ip_core_out_vc3[7:4] > current_address[7:4])
                    req_l1_core = 4'b1111;
                else if (ip_core_out_vc3[7:4] < current_address[7:4])
                    req_l2_core = 4'b1111;
                else if (ip_core_out_vc3[3:0] > current_address[3:0])
                    req_l3_core = 4'b1111;
                else if (ip_core_out_vc3[3:0] < current_address[3:0])
                    req_l4_core = 4'b1111;
                else
                    req_c_core = 4'b1111;
            end
            2'b10: begin
                if (ip_core_out_vc3[7:4] > current_address[7:4])
                    req_l1_core = 4'b1111;
                else if (ip_core_out_vc3[7:4] < current_address[7:4])
                    req_l2_core = 4'b1111;
                else if (ip_core_out_vc3[3:0] > current_address[3:0])
                    req_l3_core = 4'b1111;
                else if (ip_core_out_vc3[3:0] < current_address[3:0])
                    req_l4_core = 4'b1111;
                else
                    req_c_core = 4'b1111;
            end
            2'b11: begin
                req_c_core = 4'b1111;
            end
            default: begin
                req_c_core = 4'b1111;
            end
        endcase

        case (ip_core_out_vc4[30:29])
            2'b01: begin
                if (ip_core_out_vc4[7:4] > current_address[7:4])
                    req_l1_core = 4'b1111;
                else if (ip_core_out_vc4[7:4] < current_address[7:4])
                    req_l2_core = 4'b1111;
                else if (ip_core_out_vc4[3:0] > current_address[3:0])
                    req_l3_core = 4'b1111;
                else if (ip_core_out_vc4[3:0] < current_address[3:0])
                    req_l4_core = 4'b1111;
                else
                    req_c_core = 4'b1111;
            end
            2'b10: begin
                if (ip_core_out_vc4[7:4] > current_address[7:4])
                    req_l1_core = 4'b1111;
                else if (ip_core_out_vc4[7:4] < current_address[7:4])
                    req_l2_core = 4'b1111;
                else if (ip_core_out_vc4[3:0] > current_address[3:0])
                    req_l3_core = 4'b1111;
                else if (ip_core_out_vc4[3:0] < current_address[3:0])
                    req_l4_core = 4'b1111;
                else
                    req_c_core = 4'b1111;
            end
            2'b11: begin
                req_c_core = 4'b1111;
            end
            default: begin
                req_c_core = 4'b1111;
            end
        endcase
    end
endmodule
