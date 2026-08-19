// Reference implementation for the datapath_mux_alu illustration candidate.
// Internal structure is decoder/mux-shaped -- a case-based ALU feeding a
// mode-selected mux -- but the gating port 'enable' is at the TOP level,
// which is the only place the interpreter can see it.
module datapath_mux_alu (
    input      [7:0] a,
    input      [7:0] b,
    input      [7:0] bypass,
    input      [1:0] op,
    input            mode,
    input            enable,
    output reg [7:0] out
);
    reg [7:0] alu_result;

    always @(*) begin
        if (enable) begin
            case (op)
                2'b00:   alu_result = a + b;
                2'b01:   alu_result = a - b;
                2'b10:   alu_result = a & b;
                2'b11:   alu_result = a | b;
                default: alu_result = 8'b0;
            endcase

            if (mode) out = bypass;
            else      out = alu_result;
        end else begin
            alu_result = 8'b0;
            out        = 8'b0;
        end
    end
endmodule
