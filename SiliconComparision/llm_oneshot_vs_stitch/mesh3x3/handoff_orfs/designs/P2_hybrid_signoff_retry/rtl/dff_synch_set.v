module dff_synch_set (
    input d,
    input set,
    input clk,
    output q
);

reg q_reg;

always @(posedge clk) begin
    if (set == 1'b1) begin
        q_reg <= 1'b1;
    end else begin
        q_reg <= d;
    end
end

assign q = q_reg;

endmodule
