module dff_synch_clr (
    input d,
    input clr,
    input clk,
    output q
);

reg q_reg;

always @(posedge clk) begin
    if (clr == 1'b1) begin
        q_reg <= 1'b0;
    end else begin
        q_reg <= d;
    end
end

assign q = q_reg;

endmodule
