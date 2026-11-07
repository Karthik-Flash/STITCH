module input_port (
    input         clk,
    input         reset,
    input  [31:0] data_in,
    input  [7:0]  current_address,
    input         rd_en,      // the head flit is taken this cycle
    output        full_out,   // to the sender: stop sending
    output [31:0] flit,       // flit at the head of the buffer
    output [4:0]  req         // one-hot output wanted by that flit; zero when the buffer is empty
);
    wire       empty;
    wire [4:0] head_route;
    reg  [4:0] route;
    wire       is_head = (flit[30:29] == 2'b01);

    fifo buffer (
        .clk(clk),
        .reset(reset),
        .wr_en(data_in[30:29] != 2'b11),
        .din(data_in),
        .rd_en(rd_en),
        .dout(flit),
        .empty(empty),
        .almost_full(full_out)
    );

    route_compute rc (
        .flit(flit),
        .current_address(current_address),
        .req(head_route)
    );

    always @(posedge clk) begin
        if (reset)
            route <= 5'b00000;
        else if (rd_en && !empty && is_head)
            route <= head_route;
    end

    assign req = empty   ? 5'b00000 :
                 is_head ? head_route :
                           route;
endmodule
