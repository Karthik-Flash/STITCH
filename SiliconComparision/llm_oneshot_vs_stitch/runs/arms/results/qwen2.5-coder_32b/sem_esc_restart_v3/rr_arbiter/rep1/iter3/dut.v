module rr_arbiter (
    input req1, req2, req3, req4, reset,
    output gnt1, gnt2, gnt3, gnt4,
    input clk
);

    wire [1:0] priority;
    wire [3:0] req;
    wire [3:0] gnt;
    wire [3:0] gnt_q0;
    wire [3:0] dff_out;
    wire [3:0] dff_clr;
    wire [3:0] dff_clk;
    wire [3:0] dff_q;

    assign req = {req4, req3, req2, req1};
    assign gnt = {gnt4, gnt3, gnt2, gnt1};

    // Instantiate priority encoder
    priority_encoder pe (
        .reset(reset),
        .en(1'b1),
        .in0(req[0]),
        .in1(req[1]),
        .in2(req[2]),
        .in3(req[3]),
        .out0(priority[0]),
        .out1(priority[1]),
        .out2(),
        .out3(),
        .clk(clk)
    );

    // Instantiate falling edge pulse generators
    falling_edge_pulse_generator fepg1 (
        .reset(reset),
        .gnt(gnt[0]),
        .clk(clk),
        .q0(gnt_q0[0])
    );

    falling_edge_pulse_generator fepg2 (
        .reset(reset),
        .gnt(gnt[1]),
        .clk(clk),
        .q0(gnt_q0[1])
    );

    falling_edge_pulse_generator fepg3 (
        .reset(reset),
        .gnt(gnt[2]),
        .clk(clk),
        .q0(gnt_q0[2])
    );

    falling_edge_pulse_generator fepg4 (
        .reset(reset),
        .gnt(gnt[3]),
        .clk(clk),
        .q0(gnt_q0[3])
    );

    // Instantiate DFFs for grant signals
    dff_asynch_clr dff1 (
        .d(dff_out[0]),
        .clr(dff_clr[0]),
        .clk(clk),
        .q(dff_q[0])
    );

    dff_asynch_clr dff2 (
        .d(dff_out[1]),
        .clr(dff_clr[1]),
        .clk(clk),
        .q(dff_q[1])
    );

    dff_asynch_clr dff3 (
        .d(dff_out[2]),
        .clr(dff_clr[2]),
        .clk(clk),
        .q(dff_q[2])
    );

    dff_asynch_clr dff4 (
        .d(dff_out[3]),
        .clr(dff_clr[3]),
        .clk(clk),
        .q(dff_q[3])
    );

    // Instantiate DFF for priority state
    reg [1:0] priority_reg;
    dff_asynch_clr dff_priority (
        .d(priority),
        .clr(reset),
        .clk(clk),
        .q(priority_reg)
    );

    // Combinational logic for grant signals
    always @(*) begin
        case (priority_reg)
            2'b00: begin
                dff_out[0] = req[0];
                dff_out[1] = 1'b0;
                dff_out[2] = 1'b0;
                dff_out[3] = 1'b0;
            end
            2'b01: begin
                dff_out[0] = 1'b0;
                dff_out[1] = req[1];
                dff_out[2] = 1'b0;
                dff_out[3] = 1'b0;
            end
            2'b10: begin
                dff_out[0] = 1'b0;
                dff_out[1] = 1'b0;
                dff_out[2] = req[2];
                dff_out[3] = 1'b0;
            end
            2'b11: begin
                dff_out[0] = 1'b0;
                dff_out[1] = 1'b0;
                dff_out[2] = 1'b0;
                dff_out[3] = req[3];
            end
            default: begin
                dff_out[0] = 1'b0;
                dff_out[1] = 1'b0;
                dff_out[2] = 1'b0;
                dff_out[3] = 1'b0;
            end
        endcase
    end

    // Combinational logic for clear signals
    always @(*) begin
        if (reset) begin
            dff_clr[0] = 1'b1;
            dff_clr[1] = 1'b1;
            dff_clr[2] = 1'b1;
            dff_clr[3] = 1'b1;
        end else begin
            dff_clr[0] = gnt_q0[0];
            dff_clr[1] = gnt_q0[1];
            dff_clr[2] = gnt_q0[2];
            dff_clr[3] = gnt_q0[3];
        end
    end

    // Assign outputs
    assign gnt1 = dff_q[0];
    assign gnt2 = dff_q[1];
    assign gnt3 = dff_q[2];
    assign gnt4 = dff_q[3];

endmodule
