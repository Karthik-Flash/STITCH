module register_1bit (
    input din, reset, clk, clr, ce,
    output reg dout
);

always @(posedge clk or posedge reset) begin
    if (reset) begin
        dout <= 1'b0;
    end else begin
        if (clr) begin
            dout <= 1'b0;
        end else if (ce) begin
            dout <= din;
        end
    end
end

endmodule
