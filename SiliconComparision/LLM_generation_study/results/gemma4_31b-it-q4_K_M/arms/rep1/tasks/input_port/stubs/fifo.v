module fifo (
    input clk,
    input reset,
    input wr_en,
    input [31:0] din,
    input rd_en,
    output [31:0] dout,
    output empty,
    output almost_full
);
endmodule
