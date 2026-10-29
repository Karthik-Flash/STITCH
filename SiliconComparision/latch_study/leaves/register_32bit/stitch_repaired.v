module register_32bit(din, clk, clr, ce, dout);
    input   [31:0] din;
    input         clk;
    input         clr;
    input         ce;
    output  [31:0] dout;

    reg    [31:0] dout_reg;

    always @(posedge clk)
    begin
        if(clr)
            dout_reg <= 32'h60000000;
        else if(ce)
            dout_reg <= din;
    end

    assign dout = dout_reg;

endmodule
