// Reference implementation for the priority_encoder_valid illustration
// candidate. Every branch assigns BOTH outputs, so no path leaves either
// output unassigned and no latch is inferred.
module priority_encoder_valid (
    input      [7:0] req,
    output reg [2:0] pos,
    output reg       valid
);
    always @(*) begin
        casez (req)
            8'b1???????: begin pos = 3'd7; valid = 1'b1; end
            8'b01??????: begin pos = 3'd6; valid = 1'b1; end
            8'b001?????: begin pos = 3'd5; valid = 1'b1; end
            8'b0001????: begin pos = 3'd4; valid = 1'b1; end
            8'b00001???: begin pos = 3'd3; valid = 1'b1; end
            8'b000001??: begin pos = 3'd2; valid = 1'b1; end
            8'b0000001?: begin pos = 3'd1; valid = 1'b1; end
            8'b00000001: begin pos = 3'd0; valid = 1'b1; end
            default:     begin pos = 3'd0; valid = 1'b0; end
        endcase
    end
endmodule
