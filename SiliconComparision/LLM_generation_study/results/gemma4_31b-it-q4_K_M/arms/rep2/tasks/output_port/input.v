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
    wire [3:0] pop_comb;
    wire advance;
    wire [31:0] mux_out;

    // Selected requester logic
    assign selected = (owner == 3'd4) ? gnt : (1 << owner);

    // Pop logic: one-hot, indicates which flit will be sent
    assign pop_comb = (selected & req) & {4{~full_in}};
    assign pop = pop_comb;

    // Advance signal for round-robin arbiter
    assign advance = (pop_comb != 4'b0000) && (owner == 3'd4);

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
        .sel(pop_comb),
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
        end else if (pop_comb != 4'b0000) begin
            data_out_reg <= mux_out;
            if (mux_out[31:30] == 2'b10) begin
                owner <= 3'd4;
            end else begin
                if (pop_comb[0]) begin
                    owner <= 3'd0;
                end else if (pop_comb[1]) begin
                    owner <= 3'd1;
                end else if (pop_comb[2]) begin
                    owner <= 3'd2;
                end else if (pop_comb[3]) begin
                    owner <= 3'd3;
                end else begin
                    owner <= owner;
                end
            end
        end else begin
            data_out_reg <= 32'h6000_0000;
            owner <= owner;
        end
    end

    assign data_out = data_out_reg;

endmodule
