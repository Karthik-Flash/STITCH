module register_32bit (
    input [31:0] din,
    input clk, clr, ce,
    output [31:0] dout
);

reg [31:0] dout_reg;

always @(posedge clk) begin
    if (clr == 1'b1) begin
        dout_reg <= 32'h60000000;
    end else if (ce == 1'b1) begin
        dout_reg <= din;
    end
end

assign dout = dout_reg;

endmodule
