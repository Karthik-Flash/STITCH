// The DEFECT this candidate targets: 'enable' is declared at the top level
// and never read. The ALU case and the mode mux are both entirely correct, so
// the only failing vectors are the enable=0 ones -- the mux4_oe defect scaled
// up into a module with real internal structure.
//
// Expected from Verilator: "Signal is not used: 'enable'" (UNUSEDSIGNAL)
// iverilog:  every enable=0 vector returns the datapath result instead of 0
//
// Hand-written for the pre-screen. Defect shape the spec is designed to
// elicit, not a captured model response.
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
        case (op)
            2'b00:   alu_result = a + b;
            2'b01:   alu_result = a - b;
            2'b10:   alu_result = a & b;
            2'b11:   alu_result = a | b;
            default: alu_result = 8'b0;
        endcase

        if (mode) out = bypass;
        else      out = alu_result;
    end
endmodule
