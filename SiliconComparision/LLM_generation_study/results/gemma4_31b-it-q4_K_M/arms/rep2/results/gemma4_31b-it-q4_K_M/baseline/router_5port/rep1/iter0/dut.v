module router_5port (
    input clk,
    input reset,
    input [7:0] current_address,
    input [31:0] data_in_link1,
    input [31:0] data_in_link2,
    input [31:0] data_in_link3,
    input [31:0] data_in_link4,
    input [31:0] data_in_core,
    input full_in_link1,
    input full_in_link2,
    input full_in_link3,
    input full_in_link4,
    input full_in_core,
    output [31:0] data_out_link1,
    output [31:0] data_out_link2,
    output [31:0] data_out_link3,
    output [31:0] data_out_link4,
    output [31:0] data_out_core,
    output full_out_link1,
    output full_out_link2,
    output full_out_link3,
    output full_out_link4,
    output full_out_core
);

    wire [31:0] flit_link1, flit_link2, flit_link3, flit_link4, flit_core;
    wire [4:0] req_link1, req_link2, req_link3, req_link4, req_core;
    wire rd_en_link1, rd_en_link2, rd_en_link3, rd_en_link4, rd_en_core;

    wire [3:0] req_op1, req_op2, req_op3, req_op4, req_op_core;
    wire [3:0] pop_op1, pop_op2, pop_op3, pop_op4, pop_op_core;

    // Input Port Instantiations
    input_port ip1 (
        .clk(clk), .reset(reset), .data_in(data_in_link1), .current_address(current_address),
        .rd_en(rd_en_link1), .full_out(full_out_link1), .flit(flit_link1), .req(req_link1)
    );
    input_port ip2 (
        .clk(clk), .reset(reset), .data_in(data_in_link2), .current_address(current_address),
        .rd_en(rd_en_link2), .full_out(full_out_link2), .flit(flit_link2), .req(req_link2)
    );
    input_port ip3 (
        .clk(clk), .reset(reset), .data_in(data_in_link3), .current_address(current_address),
        .rd_en(rd_en_link3), .full_out(full_out_link3), .flit(flit_link3), .req(req_link3)
    );
    input_port ip4 (
        .clk(clk), .reset(reset), .data_in(data_in_link4), .current_address(current_address),
        .rd_en(rd_en_link4), .full_out(full_out_link4), .flit(flit_link4), .req(req_link4)
    );
    input_port ip_core (
        .clk(clk), .reset(reset), .data_in(data_in_core), .current_address(current_address),
        .rd_en(rd_en_core), .full_out(full_out_core), .flit(flit_core), .req(req_core)
    );

    // Output Port Request Mapping
    // Output link1: {link2, link3, link4, core}
    assign req_op1 = {req_core[0], req_link4[0], req_link3[0], req_link2[0]};
    // Output link2: {link1, link3, link4, core}
    assign req_op2 = {req_core[1], req_link4[1], req_link3[1], req_link1[1]};
    // Output link3: {link1, link2, link4, core}
    assign req_op3 = {req_core[2], req_link4[2], req_link2[2], req_link1[2]};
    // Output link4: {link1, link2, link3, core}
    assign req_op4 = {req_core[3], req_link3[3], req_link2[3], req_link1[3]};
    // Output core: {link1, link2, link3, link4}
    assign req_op_core = {req_link4[4], req_link3[4], req_link2[4], req_link1[4]};

    // Output Port Instantiations
    output_port op1 (
        .clk(clk), .reset(reset), .req(req_op1), 
        .flit0(flit_link2), .flit1(flit_link3), .flit2(flit_link4), .flit3(flit_core),
        .full_in(full_in_link1), .data_out(data_out_link1), .pop(pop_op1)
    );
    output_port op2 (
        .clk(clk), .reset(reset), .req(req_op2), 
        .flit0(flit_link1), .flit1(flit_link3), .flit2(flit_link4), .flit3(flit_core),
        .full_in(full_in_link2), .data_out(data_out_link2), .pop(pop_op2)
    );
    output_port op3 (
        .clk(clk), .reset(reset), .req(req_op3), 
        .flit0(flit_link1), .flit1(flit_link2), .flit2(flit_link4), .flit3(flit_core),
        .full_in(full_in_link3), .data_out(data_out_link3), .pop(pop_op3)
    );
    output_port op4 (
        .clk(clk), .reset(reset), .req(req_op4), 
        .flit0(flit_link1), .flit1(flit_link2), .flit2(flit_link3), .flit3(flit_core),
        .full_in(full_in_link4), .data_out(data_out_link4), .pop(pop_op4)
    );
    output_port op_core (
        .clk(clk), .reset(reset), .req(req_op_core), 
        .flit0(flit_link1), .flit1(flit_link2), .flit2(flit_link3), .flit3(flit_link4),
        .full_in(full_in_core), .data_out(data_out_core), .pop(pop_op_core)
    );

    // Input Port Read Enable Logic
    assign rd_en_link1 = pop_op2[0] | pop_op3[0] | pop_op4[0] | pop_op_core[0];
    assign rd_en_link2 = pop_op1[0] | pop_op3[1] | pop_op4[1] | pop_op_core[1];
    assign rd_en_link3 = pop_op1[1] | pop_op2[1] | pop_op4[2] | pop_op_core[2];
    assign rd_en_link4 = pop_op1[2] | pop_op2[2] | pop_op3[2] | pop_op_core[3];
    assign rd_en_core  = pop_op1[3] | pop_op2[3] | pop_op3[3] | pop_op4[3];

endmodule
