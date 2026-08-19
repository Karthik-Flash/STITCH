// Reference implementation for the alu_with_enable illustration candidate.
// Redesigned 2026-08-19 from the retired datapath_mux_alu (see
// illustrations/retired/retired_candidates.md section 1a): same top-level
// UNUSEDSIGNAL-on-'enable' mechanism, mode mux and bypass path dropped so the
// module stays within gemma3:4b's convergence horizon.
module alu_with_enable (
    input      [7:0] a,
    input      [7:0] b,
    input      [1:0] op,
    input            enable,
    output reg [7:0] out
);
    always @(*) begin
        if (enable) begin
            case (op)
                2'b00:   out = a + b;
                2'b01:   out = a - b;
                2'b10:   out = a & b;
                2'b11:   out = a | b;
                default: out = 8'b0;
            endcase
        end else begin
            out = 8'b0;
        end
    end
endmodule
