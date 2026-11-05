// Row-first routing of a head flit, as routing_algo_mesh in the MPSoC router.
// req is one-hot: [0] link1, [1] link2, [2] link3, [3] link4, [4] core. Zero unless flit is a head flit.
module route_compute (
    input  [31:0] flit,
    input  [7:0]  current_address,
    output [4:0]  req
);
    wire       is_head = (flit[30:29] == 2'b01);
    wire [3:0] dest_row = flit[7:4];
    wire [3:0] dest_col = flit[3:0];
    wire [3:0] curr_row = current_address[7:4];
    wire [3:0] curr_col = current_address[3:0];

    assign req = !is_head              ? 5'b00000 :
                 (dest_row > curr_row) ? 5'b00001 :
                 (dest_row < curr_row) ? 5'b00010 :
                 (dest_col > curr_col) ? 5'b00100 :
                 (dest_col < curr_col) ? 5'b01000 :
                                         5'b10000;
endmodule
