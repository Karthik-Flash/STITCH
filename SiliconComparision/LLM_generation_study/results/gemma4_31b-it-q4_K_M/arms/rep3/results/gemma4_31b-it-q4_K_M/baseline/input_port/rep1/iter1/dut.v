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

    wire [4:0] computed_req;
    wire fifo_empty;
    wire wr_en_fifo;
    wire rd_en_fifo;
    reg [4:0] held_route;

    // Route computation for the front flit
    // route_compute is combinational and takes the front flit and current_address
    route_compute u_route_compute (
        .flit(flit),
        .current_address(current_address),
        .req(computed_req)
    );

    // FIFO buffer for flits
    // dout is the oldest word (first-word fall-through)
    fifo u_fifo (
        .clk(clk),
        .reset(reset),
        .wr_en(wr_en_fifo),
        .din(data_in),
        .rd_en(rd_en_fifo),
        .dout(flit),
        .empty(fifo_empty),
        .almost_full(full_out)
    );

    // FIFO control signals
    // Idle flits (type 11 at bits [30:29]) are never stored.
    // Reset ignores data_in and rd_en.
    assign wr_en_fifo = (!reset && (data_in[30:29] != 2'b11));
    assign rd_en_fifo = (!reset && rd_en);

    // Held route register: updated when a head flit (type 01 at bits [30:29]) is read from the buffer
    always @(posedge clk) begin
        if (reset) begin
            held_route <= 5'b00000;
        end else if (rd_en && !fifo_empty && flit[30:29] == 2'b01) begin
            held_route <= computed_req;
        end else begin
            held_route <= held_route;
        end
    end

    // Combinational logic for the route request (req)
    always @(*) begin
        if (fifo_empty) begin
            req = 5'b00000;
        end else if (flit[30:29] == 2'b01) begin
            // Front flit is a head flit: use computed route
            req = computed_req;
        end else begin
            // Front flit is a body or tail flit: use held route
            req = held_route;
        end
    end

endmodule
