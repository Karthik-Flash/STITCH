module output_port (
    input clk,
    input reset,
    input [3:0] req,
    input [31:0] flit0,
    input [31:0] flit1,
    input [31:0] flit2,
    input [31:0] flit3,
    input full_in,
    output [31:0] data_out,
    output [3:0] pop
);

    reg [31:0] data_out_reg;
    reg [3:0] owner_vec;
    wire [3:0] gnt;
    wire [3:0] selected_req;
    wire [3:0] pop_wire;
    wire advance;
    wire [31:0] mux_out;

    assign data_out = data_out_reg;
    assign pop = pop_wire;

    // Selected requester: owner if exists, otherwise the arbiter's grant
    assign selected_req = (owner_vec != 4'b0000) ? owner_vec : gnt;

    // pop is one-hot and combinational. 
    // A flit is sent if a requester is selected, that requester's req is 1, and full_in is 0.
    assign pop_wire = (!full_in) ? (selected_req & req) : 4'b0000;

    // advance is 1 if the output was free and a flit is now being sent.
    assign advance = (owner_vec == 4'b0000) && (pop_wire != 4'b0000);

    // Instantiate the round-robin arbiter
    rr_arbiter arb (
        .clk(clk),
        .reset(reset),
        .req(req),
        .advance(advance),
        .gnt(gnt)
    );

    // Instantiate the flit multiplexer
    flit_mux mux (
        .sel(pop_wire),
        .in0(flit0),
        .in1(flit1),
        .in2(flit2),
        .in3(flit3),
        .out(mux_out)
    );

    always @(posedge clk) begin
        if (reset) begin
            data_out_reg <= 32'h6000_0000;
            owner_vec <= 4'b0000;
        end else if (pop_wire != 4'b0000) begin
            data_out_reg <= mux_out;
            // Flit type: bits [30:29]. 10 = tail.
            if (mux_out[30:29] == 2'b10) begin
                owner_vec <= 4'b0000;
            end else begin
                owner_vec <= selected_req;
            end
        end else begin
            data_out_reg <= 32'h6000_0000;
            // Owner does not change when no flit is sent.
            owner_vec <= owner_vec;
        end
    end

endmodule
