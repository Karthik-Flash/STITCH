module input_port (
    input clk,
    input reset,
    input [31:0] data_in,
    input [7:0] current_address,
    input rd_en,
    output full_out,
    output [31:0] flit,
    output [4:0] req
);

    // Internal wires for FIFO and route_compute
    wire [31:0] flit_out;
    wire empty_out;
    wire almost_full_out;
    wire [4:0] computed_req;
    wire wr_en_fifo;
    wire rd_en_fifo;

    // Internal registers
    reg [4:0] held_route;
    reg [4:0] req_reg;

    // FIFO write enable: store if not idle and not resetting
    assign wr_en_fifo = (!reset && (data_in[31:30] != 2'b11));
    
    // FIFO read enable: read if requested and not resetting
    assign rd_en_fifo = (!reset && rd_en);

    // Instantiate FIFO
    fifo u_fifo (
        .clk(clk),
        .reset(reset),
        .wr_en(wr_en_fifo),
        .din(data_in),
        .rd_en(rd_en_fifo),
        .dout(flit_out),
        .empty(empty_out),
        .almost_full(almost_full_out)
    );

    // Instantiate Route Compute
    route_compute u_route_compute (
        .flit(flit_out),
        .current_address(current_address),
        .req(computed_req)
    );

    // Output assignments
    assign full_out = almost_full_out;
    assign flit = flit_out;
    assign req = req_reg;

    // Held route update logic
    always @(posedge clk) begin
        if (reset) begin
            held_route <= 5'b00000;
        end else if (rd_en && !empty_out && (flit_out[31:30] == 2'b01)) begin
            held_route <= computed_req;
        end else begin
            held_route <= held_route;
        end
    end

    // Request logic
    always @(*) begin
        if (empty_out) begin
            req_reg = 5'b00000;
        end else if (flit_out[31:30] == 2'b01) begin
            req_reg = computed_req;
        end else begin
            req_reg = held_route;
        end
    end

endmodule
