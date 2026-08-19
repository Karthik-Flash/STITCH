// The DEFECT this candidate targets: 'enable' is declared at the top level
// and never read. All four ALU ops are correct; only the enable gating is
// missing. Same mechanism as mux4_oe, on ALU-shaped logic instead of a mux.
//
// Expected from Verilator: "Signal is not used: 'enable'" (UNUSEDSIGNAL)
// iverilog:  every enable=0 vector returns the ALU result instead of 0
//
// Hand-written for the pre-screen. Defect shape the spec is designed to
// elicit, not a captured model response.
module alu_with_enable (
    input      [7:0] a,
    input      [7:0] b,
    input      [1:0] op,
    input            enable,
    output reg [7:0] out
);
    always @(*) begin
        case (op)
            2'b00:   out = a + b;
            2'b01:   out = a - b;
            2'b10:   out = a & b;
            2'b11:   out = a | b;
            default: out = 8'b0;
        endcase
    end
endmodule
