module jk_ff (
    input j, k, reset, en, clk,
    output q, qbar
);

    reg q_reg;

    assign q = q_reg;
    assign qbar = ~q_reg;

    always @(posedge clk) begin
        if (reset == 1'b1) begin
            q_reg <= 1'b0;
        end else if (en == 1'b1) begin
            case ({j, k})
                2'b00: begin
                    q_reg <= q_reg;
                end
                2'b01: begin
                    q_reg <= 1'b0;
                end
                2'b10: begin
                    q_reg <= 1'b1;
                end
                2'b11: begin
                    q_reg <= ~q_reg;
                end
            endcase
        end else begin
            q_reg <= q_reg;
        end
    end

endmodule
