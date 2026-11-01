module nidepack (
    input [31:0] flit,
    input rd_clk, wr_clk, rd_en, reset,
    output [31:0] data_out
);

    wire [31:0] depack_data_out;
    wire depack_wr_en;

    // Tie unused ports to constants
    wire [2:0] rd_add_reg = 3'b000;
    wire [2:0] wr_add_reg = 3'b000;
    wire wr_dir_reg = 1'b0;
    wire rd_dir_reg = 1'b0;

    reg [31:0] data_out_reg;

    depack depack_inst (
        .flit(flit),
        .wr_clk(wr_clk),
        .reset(reset),
        .data_out(depack_data_out),
        .wr_en(depack_wr_en),
        .c_rd(1'b0) // c_rd is left open, so it can be tied to a constant value
    );

    router_fifo router_fifo_inst (
        .reset(reset),
        .rd_clk(rd_clk),
        .rd_en(rd_en),
        .data_in(depack_data_out),
        .wr_clk(wr_clk),
        .wr_en(depack_wr_en),
        .rd_add(rd_add_reg),
        .wr_add(wr_add_reg),
        .wr_dir(wr_dir_reg),
        .rd_dir(rd_dir_reg),
        .data_out(data_out_reg),
        .full_ext(), // Unused, can be left open
        .full_int(), // Unused, can be left open
        .empty()   // Unused, can be left open
    );

    assign data_out = data_out_reg;

endmodule
