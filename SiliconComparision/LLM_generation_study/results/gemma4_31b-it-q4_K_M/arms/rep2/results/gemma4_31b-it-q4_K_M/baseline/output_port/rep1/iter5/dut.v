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

    // State registers
    reg [1:0] owner_id;
    reg has_owner;
    reg [31:0] data_out_reg;

    // Internal wires
    wire [3:0] current_gnt;
    wire [3:0] selected_mask;
    wire [31:0] muxed_flit;
    wire pop_any;
    wire advance;

    // Selected requester logic:
    // If the output has an owner, the selected requester is the owner.
    // If the output is free, the selected requester is chosen round-robin among requesters with req=1.
    assign selected_mask = has_owner ? (4'b0001 << owner_id) : current_gnt;

    // pop is one-hot and shows which requester's flit will be sent.
    // A flit is sent if a requester is selected, their req bit is 1, and full_in is 0.
    // Nothing is sent during the reset cycle.
    assign pop = (~reset) ? (selected_mask & req & (~full_in)) : 4'b0000;
    assign pop_any = |pop;

    // The arbiter advances its priority pointer only when a new requester is granted the output.
    // This happens if the output was free before the edge and a flit is sent.
    assign advance = (!has_owner) && pop_any;

    // Instantiate the round-robin arbiter
    rr_arbiter arb_inst (
        .clk(clk),
        .reset(reset),
        .req(req),
        .advance(advance),
        .gnt(current_gnt)
    );

    // Instantiate the flit multiplexer
    flit_mux mux_inst (
        .sel(selected_mask),
        .in0(flit0),
        .in1(flit1),
        .in2(flit2),
        .in3(flit3),
        .out(muxed_flit)
    );

    // Registered output data
    always @(posedge clk) begin
        if (reset) begin
            data_out_reg <= 32'h6000_0000;
        end else if (pop_any) begin
            data_out_reg <= muxed_flit;
        end else begin
            data_out_reg <= 32'h6000_0000;
        end
    end

    // Owner state management
    always @(posedge clk) begin
        if (reset) begin
            has_owner <= 1'b0;
            owner_id <= 2'b00;
        end else if (pop_any) begin
            // If the flit sent is a tail flit (type 10), the output becomes free.
            if (muxed_flit[30:29] == 2'b10) begin
                has_owner <= 1'b0;
                owner_id <= owner_id;
            end else begin
                // Otherwise, the selected requester becomes or stays the owner.
                has_owner <= 1'b1;
                // Convert one-hot selected_mask to ID for state update
                if (selected_mask[0]) begin
                    owner_id <= 2'b00;
                end else if (selected_mask[1]) begin
                    owner_id <= 2'b01;
                end else if (selected_mask[2]) begin
                    owner_id <= 2'b10;
                end else if (selected_mask[3]) begin
                    owner_id <= 2'b11;
                end else begin
                    owner_id <= owner_id;
                end
            end
        end else begin
            // If no flit is sent, the owner does not change.
            has_owner <= has_owner;
            owner_id <= owner_id;
        end
    end

    // Assign registered data to output port
    assign data_out = data_out_reg;

endmodule
