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
    reg [2:0] owner; // 0-3: requester, 4: free
    wire [3:0] gnt;
    wire [3:0] selected;
    wire advance;
    wire [31:0] mux_out;

    // Selected requester logic:
    // If the output has an owner, the selected requester is the owner.
    // If the output is free, the selected requester is chosen round-robin among requesters with req=1.
    assign selected = (owner == 3'd4) ? gnt : (4'b0001 << owner);

    // Pop logic: one-hot, indicates which flit will be sent.
    // A flit is sent when a requester is selected, that requester's req bit is 1, and full_in = 0.
    assign pop = (selected & req) & (full_in ? 4'b0000 : 4'b1111);

    // Advance signal for round-robin arbiter:
    // If the output was free before the edge and a flit is sent, the selected requester becomes the last granted.
    assign advance = (pop != 4'b0000) && (owner == 3'd4);

    // Instantiate rr_arbiter
    rr_arbiter arbiter_inst (
        .clk(clk),
        .reset(reset),
        .req(req),
        .advance(advance),
        .gnt(gnt)
    );

    // Instantiate flit_mux
    flit_mux mux_inst (
        .sel(pop),
        .in0(flit0),
        .in1(flit1),
        .in2(flit2),
        .in3(flit3),
        .out(mux_out)
    );

    // State updates
    always @(posedge clk) begin
        if (reset) begin
            data_out_reg <= 32'h6000_0000;
            owner <= 3'd4;
        end else if (pop != 4'b0000) begin
            data_out_reg <= mux_out;
            // If that flit is a tail flit (type 10), the output becomes free; otherwise the selected requester becomes/stays owner.
            if (mux_out[31:30] == 2'b10) begin
                owner <= 3'd4;
            end else begin
                if (pop[0]) begin
                    owner <= 3'd0;
                end else if (pop[1]) begin
                    owner <= 3'd1;
                end else if (pop[2]) begin
                    owner <= 3'd2;
                end else if (pop[3]) begin
                    owner <= 3'd3;
                end else begin
                    owner <= owner;
                end
            end
        end else begin
            // At an edge where no flit is sent, data_out becomes the idle flit and the owner does not change.
            data_out_reg <= 32'h6000_0000;
            owner <= owner;
        end
    end

    assign data_out = data_out_reg;

endmodule
