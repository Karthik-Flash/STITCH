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
    wire [31:0] fifo_dout;
    wire fifo_empty;
    wire fifo_almost_full;
    wire [4:0] route_compute_out;
    wire wr_en_fifo;
    wire rd_en_fifo;

    // Internal registers
    reg [4:0] held_route;
    reg [4:0] req_reg;

    // FIFO control signals
    // Store data_in if type is not 11 (idle) and not in reset.
    // Flit type is bits [30:29].
    assign wr_en_fifo = (data_in[30:29] != 2'b11) && !reset;
    // Read from FIFO if rd_en is high and not in reset.
    assign rd_en_fifo = rd_en && !reset;

    // Output assignments
    assign flit = fifo_dout;
    assign full_out = fifo_almost_full;

    // Instantiate FIFO
    fifo u_fifo (
        .clk(clk),
        .reset(reset),
        .wr_en(wr_en_fifo),
        .din(data_in),
        .rd_en(rd_en_fifo),
        .dout(fifo_dout),
        .empty(fifo_empty),
        .almost_full(fifo_almost_full)
    );

    // Instantiate Route Compute
    route_compute u_route_compute (
        .flit(fifo_dout),
        .current_address(current_address),
        .req(route_compute_out)
    );

    // Held route update logic
    // The held route is set at a rising clk edge where rd_en = 1, 
    // the buffer is not empty and the front flit is a head flit (type 01).
    always @(posedge clk) begin
        if (reset) begin
            held_route <= 5'b0;
        end else if (rd_en && !fifo_empty && (fifo_dout[30:29] == 2'b01)) begin
            held_route <= route_compute_out;
        end else begin
            held_route <= held_route;
        end
    end

    // Request logic
    // Buffer empty: req = 0.
    // Front flit is a head flit: req is the route of that head flit.
    // Front flit is a body or tail flit: req is the held route.
    always @(*) begin
        if (fifo_empty) begin
            req_reg = 5'b0;
        end else if (fifo_dout[30:29] == 2'b01) begin
            req_reg = route_compute_out;
        end else begin
            req_reg = held_route;
        end
    end

    // Assign the internal request register to the output port
    assign req = req_reg;

endmodule
