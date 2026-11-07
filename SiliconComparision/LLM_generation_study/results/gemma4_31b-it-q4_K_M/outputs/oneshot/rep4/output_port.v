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

    reg [2:0] owner;
    reg [31:0] data_out_reg;
    reg [3:0] selected;
    wire [3:0] gnt;
    wire [31:0] mux_out;
    wire advance;

    assign data_out = data_out_reg;

    // Selected requester logic
    always @(*) begin
        if (owner == 3'd4) begin
            selected = gnt;
        end else if (owner == 3'd0) begin
            selected = 4'b0001;
        end else if (owner == 3'd1) begin
            selected = 4'b0010;
        end else if (owner == 3'd2) begin
            selected = 4'b0100;
        end else if (owner == 3'd3) begin
            selected = 4'b1000;
        end else begin
            selected = 4'b0000;
        end
    end

    // Pop signal: one-hot, indicates which flit will be sent
    assign pop = selected & req & (~full_in);

    // Advance signal for round-robin arbiter
    assign advance = (pop != 4'b0000) && (owner == 3'd4);

    // Instantiate round-robin arbiter
    rr_arbiter arbiter_inst (
        .clk(clk),
        .reset(reset),
        .req(req),
        .advance(advance),
        .gnt(gnt)
    );

    // Instantiate flit multiplexer
    flit_mux mux_inst (
        .sel(pop),
        .in0(flit0),
        .in1(flit1),
        .in2(flit2),
        .in3(flit3),
        .out(mux_out)
    );

    // State updates on rising clock edge
    always @(posedge clk) begin
        if (reset) begin
            owner <= 3'd4;
            data_out_reg <= 32'h6000_0000;
        end else if (pop != 4'b0000) begin
            data_out_reg <= mux_out;
            if (pop[0]) begin
                if (flit0[31:30] == 2'b10) begin
                    owner <= 3'd4;
                end else begin
                    owner <= 3'd0;
                end
            end else if (pop[1]) begin
                if (flit1[31:30] == 2'b10) begin
                    owner <= 3'd4;
                end else begin
                    owner <= 3'd1;
                end
            end else if (pop[2]) begin
                if (flit2[31:30] == 2'b10) begin
                    owner <= 3'd4;
                end else begin
                    owner <= 3'd2;
                end
            end else if (pop[3]) begin
                if (flit3[31:30] == 2'b10) begin
                    owner <= 3'd4;
                end else begin
                    owner <= 3'd3;
                end
            end else begin
                owner <= owner;
            end
        end else begin
            data_out_reg <= 32'h6000_0000;
            owner <= owner;
        end
    end

endmodule
