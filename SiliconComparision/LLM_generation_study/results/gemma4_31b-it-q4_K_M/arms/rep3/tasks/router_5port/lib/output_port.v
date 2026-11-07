// One router output. When free, it grants one of 4 requesters round-robin; the granted requester then
// holds the output until its tail flit has been sent (wormhole). The flit leaves on a register.
module output_port (
    input             clk,
    input             reset,
    input      [3:0]  req,       // bit i: requester i has a flit for this output
    input      [31:0] flit0,
    input      [31:0] flit1,
    input      [31:0] flit2,
    input      [31:0] flit3,
    input             full_in,   // the next router cannot take a flit
    output reg [31:0] data_out,
    output     [3:0]  pop        // one-hot: requester whose flit is sent this cycle
);
    reg  [3:0]  owner;           // requester holding the output; zero when the output is free
    wire        locked = (owner != 4'b0000);
    wire [3:0]  gnt;
    wire [3:0]  sel = locked ? owner : gnt;
    // a free output grants whenever any requester asks, so send does not wait for the arbiter
    wire        send = (locked ? ((owner & req) != 4'b0000) : (req != 4'b0000)) && !full_in;
    wire [31:0] sel_flit;

    rr_arbiter arb (
        .clk(clk),
        .reset(reset),
        .req(locked ? 4'b0000 : req),
        .advance(send),
        .gnt(gnt)
    );

    flit_mux mux (
        .sel(sel),
        .in0(flit0),
        .in1(flit1),
        .in2(flit2),
        .in3(flit3),
        .out(sel_flit)
    );

    assign pop = send ? sel : 4'b0000;

    always @(posedge clk) begin
        if (reset) begin
            owner    <= 4'b0000;
            data_out <= 32'h6000_0000;
        end else if (send) begin
            owner    <= (sel_flit[30:29] == 2'b10) ? 4'b0000 : sel;
            data_out <= sel_flit;
        end else begin
            data_out <= 32'h6000_0000;
        end
    end
endmodule
