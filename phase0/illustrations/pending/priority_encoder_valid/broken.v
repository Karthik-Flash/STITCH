// The DEFECT this candidate targets: the casez HAS a default branch, so
// SYSTEM_PROMPT rule 3 ("EVERY combinational always block MUST have a
// 'default' branch") is satisfied -- and 'valid' is STILL left unassigned on
// eight of the nine paths. Rule 3 constrains branch coverage, not output
// coverage, and that gap is what this module occupies.
//
// Yosys infers a latch on 'valid'. Verilator has nothing to say: the case is
// complete, so CASEINCOMPLETE does not apply, and 'valid' is both driven
// (in default) and read (at the port), so neither UNDRIVEN nor UNUSEDSIGNAL
// applies either.
//
// Hand-written for the pre-screen. Defect shape the spec is designed to
// elicit, not a captured model response.
module priority_encoder_valid (
    input      [7:0] req,
    output reg [2:0] pos,
    output reg       valid
);
    always @(*) begin
        casez (req)
            8'b1???????: pos = 3'd7;
            8'b01??????: pos = 3'd6;
            8'b001?????: pos = 3'd5;
            8'b0001????: pos = 3'd4;
            8'b00001???: pos = 3'd3;
            8'b000001??: pos = 3'd2;
            8'b0000001?: pos = 3'd1;
            8'b00000001: pos = 3'd0;
            default:     begin pos = 3'd0; valid = 1'b0; end
        endcase
    end
endmodule
