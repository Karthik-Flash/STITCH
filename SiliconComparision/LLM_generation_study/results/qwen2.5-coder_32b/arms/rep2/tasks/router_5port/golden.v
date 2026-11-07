module router_5port (
    input         clk,
    input         reset,
    input  [7:0]  current_address,
    input  [31:0] data_in_link1,
    input  [31:0] data_in_link2,
    input  [31:0] data_in_link3,
    input  [31:0] data_in_link4,
    input  [31:0] data_in_core,
    input         full_in_link1,
    input         full_in_link2,
    input         full_in_link3,
    input         full_in_link4,
    input         full_in_core,
    output [31:0] data_out_link1,
    output [31:0] data_out_link2,
    output [31:0] data_out_link3,
    output [31:0] data_out_link4,
    output [31:0] data_out_core,
    output        full_out_link1,
    output        full_out_link2,
    output        full_out_link3,
    output        full_out_link4,
    output        full_out_core
);
    wire [31:0] flit_l1, flit_l2, flit_l3, flit_l4, flit_c;
    wire [4:0]  req_l1, req_l2, req_l3, req_l4, req_c;
    wire [3:0]  pop_l1, pop_l2, pop_l3, pop_l4, pop_c;

    // An input's head flit is taken by whichever output pops it.
    wire rd_l1 = pop_l2[0] | pop_l3[0] | pop_l4[0] | pop_c[0];
    wire rd_l2 = pop_l1[0] | pop_l3[1] | pop_l4[1] | pop_c[1];
    wire rd_l3 = pop_l1[1] | pop_l2[1] | pop_l4[2] | pop_c[2];
    wire rd_l4 = pop_l1[2] | pop_l2[2] | pop_l3[2] | pop_c[3];
    wire rd_c  = pop_l1[3] | pop_l2[3] | pop_l3[3] | pop_l4[3];

    input_port in_link1 (.clk(clk), .reset(reset), .data_in(data_in_link1), .current_address(current_address),
                         .rd_en(rd_l1), .full_out(full_out_link1), .flit(flit_l1), .req(req_l1));
    input_port in_link2 (.clk(clk), .reset(reset), .data_in(data_in_link2), .current_address(current_address),
                         .rd_en(rd_l2), .full_out(full_out_link2), .flit(flit_l2), .req(req_l2));
    input_port in_link3 (.clk(clk), .reset(reset), .data_in(data_in_link3), .current_address(current_address),
                         .rd_en(rd_l3), .full_out(full_out_link3), .flit(flit_l3), .req(req_l3));
    input_port in_link4 (.clk(clk), .reset(reset), .data_in(data_in_link4), .current_address(current_address),
                         .rd_en(rd_l4), .full_out(full_out_link4), .flit(flit_l4), .req(req_l4));
    input_port in_core  (.clk(clk), .reset(reset), .data_in(data_in_core), .current_address(current_address),
                         .rd_en(rd_c), .full_out(full_out_core), .flit(flit_c), .req(req_c));

    output_port out_link1 (.clk(clk), .reset(reset),
                           .req({req_c[0], req_l4[0], req_l3[0], req_l2[0]}),
                           .flit0(flit_l2), .flit1(flit_l3), .flit2(flit_l4), .flit3(flit_c),
                           .full_in(full_in_link1), .data_out(data_out_link1), .pop(pop_l1));
    output_port out_link2 (.clk(clk), .reset(reset),
                           .req({req_c[1], req_l4[1], req_l3[1], req_l1[1]}),
                           .flit0(flit_l1), .flit1(flit_l3), .flit2(flit_l4), .flit3(flit_c),
                           .full_in(full_in_link2), .data_out(data_out_link2), .pop(pop_l2));
    output_port out_link3 (.clk(clk), .reset(reset),
                           .req({req_c[2], req_l4[2], req_l2[2], req_l1[2]}),
                           .flit0(flit_l1), .flit1(flit_l2), .flit2(flit_l4), .flit3(flit_c),
                           .full_in(full_in_link3), .data_out(data_out_link3), .pop(pop_l3));
    output_port out_link4 (.clk(clk), .reset(reset),
                           .req({req_c[3], req_l3[3], req_l2[3], req_l1[3]}),
                           .flit0(flit_l1), .flit1(flit_l2), .flit2(flit_l3), .flit3(flit_c),
                           .full_in(full_in_link4), .data_out(data_out_link4), .pop(pop_l4));
    output_port out_core  (.clk(clk), .reset(reset),
                           .req({req_l4[4], req_l3[4], req_l2[4], req_l1[4]}),
                           .flit0(flit_l1), .flit1(flit_l2), .flit2(flit_l3), .flit3(flit_l4),
                           .full_in(full_in_core), .data_out(data_out_core), .pop(pop_c));
endmodule
