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

    // State
    reg [2:0] owner; // 0-3: requester, 4: free
    reg [31:0] data_out_reg;

    // Internal signals
    wire [3:0] gnt;
    wire advance;
    wire [3:0] sel_vec;
    wire [31:0] mux_out;
    wire [3:0] pop_val;

    // Round-robin arbiter instantiation
    rr_arbiter arb (
        .clk(clk),
        .reset(reset),
        .req(req),
        .advance(advance),
        .gnt(gnt)
    );

    // Flit multiplexer instantiation
    flit_mux mux (
        .sel(pop_val),
        .in0(flit0),
        .in1(flit1),
        .in2(flit2),
        .in3(flit3),
        .out(mux_out)
    );

    // Combinational logic for selected requester
    reg [3:0] sel_vec_reg;
    always @(*) begin
        if (owner == 3'd4) begin
            sel_vec_reg = gnt;
        end else begin
            sel_vec_reg = 4'b0000;
            sel_vec_reg[owner] = 1'b1;
        end
    }

    assign sel_vec = sel_vec_reg;

    // pop is 1 if a requester is selected, they are requesting, and the output is not full
    assign pop_val = sel_vec & req & (full_in == 1'b0 ? 4'b1111 : 4'b0000);
    assign pop = pop_val;

    // advance is high when a new requester is granted the output
    assign advance = (owner == 3'd4) && (pop_val != 4'b0000);

    // Registered output and state updates
    always @(posedge clk) begin
        if (reset) begin
            owner <= 3'd4;
            data_out_reg <= 32'h6000_0000;
        end else begin
            if (pop_val != 4'b0000) begin
                data_out_reg <= mux_out;
                // Update owner based on flit type: 10 is tail
                if (mux_out[30:29] == 2'b10) begin
                    owner <= 3'd4;
                end else begin
                    if (pop_val[0]) begin
                        owner <= 3'd0;
                    end else if (pop_val[1]) begin
                        owner <= 3'd1;
                    end else if (pop_val[2]) begin
                        owner <= 3'd2;
                    end else if (pop_val[3]) begin
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
    end

    assign data_out = data_out_reg;

endmodule
