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
    reg owner_valid;
    reg [1:0] current_owner;
    reg [1:0] popped_id;
    
    wire [3:0] gnt;
    wire [3:0] selected;
    wire advance;
    wire [31:0] muxed_flit;

    // Round-robin arbiter instantiation
    rr_arbiter arbiter_inst (
        .clk(clk),
        .reset(reset),
        .req(req),
        .advance(advance),
        .gnt(gnt)
    );

    // Flit multiplexer instantiation
    flit_mux mux_inst (
        .sel(pop),
        .in0(flit0),
        .in1(flit1),
        .in2(flit2),
        .in3(flit3),
        .out(muxed_flit)
    );

    // Selected requester logic
    assign selected = owner_valid ? (4'b0001 << current_owner) : gnt;

    // Pop signal logic: one-hot, indicates which flit will be sent
    assign pop = (selected & req) & (~full_in);

    // Advance signal for the arbiter: update L only when a new owner is granted
    assign advance = (!owner_valid && (pop != 4'b0000));

    // Combinational logic to determine the ID of the requester being popped
    always @(*) begin
        if (pop[0])
            popped_id = 2'b00;
        else if (pop[1])
            popped_id = 2'b01;
        else if (pop[2])
            popped_id = 2'b10;
        else if (pop[3])
            popped_id = 2'b11;
        else
            popped_id = 2'b00;
    end

    // Owner state update
    always @(posedge clk) begin
        if (reset) begin
            owner_valid <= 1'b0;
            current_owner <= 2'b00;
        end else if (pop != 4'b0000) begin
            // Check if the flit being sent is a tail flit (type 10)
            if (muxed_flit[31:30] == 2'b10) begin
                owner_valid <= 1'b0;
            end else begin
                owner_valid <= 1'b1;
                current_owner <= popped_id;
            end
        end else begin
            // Owner remains the same if no flit is sent
            owner_valid <= owner_valid;
            current_owner <= current_owner;
        end
    end

    // Data output register
    always @(posedge clk) begin
        if (reset) begin
            data_out_reg <= 32'h6000_0000;
        end else if (pop != 4'b0000) begin
            data_out_reg <= muxed_flit;
        end else begin
            data_out_reg <= 32'h6000_0000;
        end
    end

    assign data_out = data_out_reg;

endmodule
