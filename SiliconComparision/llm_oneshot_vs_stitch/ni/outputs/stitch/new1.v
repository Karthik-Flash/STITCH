module new1 (
    input rd_clk, wr_clk,
    input [31:0] data_in,
    input reset, wr_en,
    input [7:0] dest, source,
    output empty, full_int,
    output [31:0] niout,
    output wr_o
);

    wire rd_en;
    wire [31:0] data_out;
    wire full_ext, full_int_fifo, empty_fifo;

    router_fifo router_fifo_inst (
        .reset(reset),
        .rd_clk(rd_clk),
        .rd_en(rd_en),
        .data_in(data_in),
        .wr_clk(wr_clk),
        .wr_en(wr_en),
        .rd_add(3'b000), // Unused, tied to 0
        .wr_add(3'b000), // Unused, tied to 0
        .wr_dir(1'b0),  // Unused, tied to 0
        .rd_dir(1'b0),  // Unused, tied to 0
        .data_out(data_out),
        .full_ext(full_ext),
        .full_int(full_int_fifo),
        .empty(empty_fifo)
    );

    rp1 rp1_inst (
        .data_in(data_out),
        .dest(dest),
        .source(source),
        .rd_clk(rd_clk),
        .wr_clk(wr_clk),
        .wr_en(wr_en),
        .reset(reset),
        .niout(niout),
        .rd_en(rd_en),
        .wr_o(wr_o)
    );

    reg rd_en_reg;
    reg empty_reg;
    reg full_int_reg;

    always @(posedge rd_clk or posedge reset) begin
        if (reset) begin
            rd_en_reg <= 1'b0;
        end else begin
            rd_en_reg <= wr_en;
        end
    end

    assign rd_en = rd_en_reg;

    always @(*) begin
        if (full_int_fifo) begin
            empty_reg = 1'b1;
            full_int_reg = 1'b1;
        end else begin
            empty_reg = empty_fifo;
            full_int_reg = full_ext;
        end
    end

    assign empty = empty_reg;
    assign full_int = full_int_reg;

endmodule
