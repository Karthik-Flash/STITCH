module mux4_oe (
    input            oe,
    input      [1:0] sel,
    input      [7:0] a,
    input      [7:0] b,
    input      [7:0] c,
    input      [7:0] d,
    output reg [7:0] out
);
    always @(*) begin
        if (oe) begin
            case (sel)
                2'd0:    out = a;
                2'd1:    out = b;
                2'd2:    out = c;
                2'd3:    out = d;
                default: out = 8'b0;
            endcase
        end else begin
            out = 8'b0;
        end
    end
endmodule
