module input_port (
    input clk,
    input reset,
    input [31:0] data_in,
    input [7:0] current_address,
    input rd_en,
    output full_out,
    output [31:0] flit,
    output reg [4:0] req
);

    wire [31:0] fifo_dout;
    wire fifo_empty;
    wire fifo_almost_full;
    wire [4:0] computed_req;
    wire wr_en_fifo;
    wire rd_en_fifo;
    reg [4:0] held_route;

    // Buffer write enable: store if flit type is not 11 (idle) and reset is not active
    assign wr_en_fifo = (!reset && (data_in[31:30] != 2'b11));
    
    // Buffer read enable: gated by reset as per specification
    assign rd_en_fifo = (!reset && rd_en);

    // Output assignments
    assign full_out = fifo_almost_full;
    assign flit = fifo_dout;

    // Instantiate FIFO buffer
    fifo fifo_inst (
        .clk(clk),
        .reset(reset),
        .wr_en(wr_en_fifo),
        .din(data_in),
        .rd_en(rd_en_fifo),
        .dout(fifo_dout),
        .empty(fifo_empty),
        .almost_full(fifo_almost_full)
    );

    // Instantiate Route Compute logic
    route_compute rc_inst (
        .flit(fifo_dout),
        .current_address(current_address),
        .req(computed_req)
    );

    // Held route update logic
    always @(posedge clk) begin
        if (reset) begin
            held_route <= 5'b00000;
        end else if (rd_en && !fifo_empty && (fifo_dout[31:30] == 2'b01)) begin
            held_route <= computed_req;
        end else begin
            held_route <= held_route;
        end
    end

    // Route request logic
    always @(*) begin
        if (fifo_empty) begin
            req = 5'b00000;
        end else if (fifo_dout[31:30] == 2'b01) begin
            req = computed_req;
        end else begin
            req = held_route;
        end
    end

endmodule
