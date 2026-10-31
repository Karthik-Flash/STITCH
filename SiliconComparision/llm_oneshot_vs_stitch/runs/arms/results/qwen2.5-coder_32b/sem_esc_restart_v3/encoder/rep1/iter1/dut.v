module encoder (
    input g1, g2, g3, g4, g5, g6, g7, g8, g9, g10, g11, g12, g13, g14, g15, g16,
    output [3:0] encoded_addr
);

wire [3:0] encoded_addr_w;

assign encoded_addr_w[0] = g1 | g3 | g5 | g7 | g9 | g11 | g13 | g15;
assign encoded_addr_w[1] = g2 | g3 | g6 | g7 | g10 | g11 | g14 | g15;
assign encoded_addr_w[2] = g4 | g5 | g6 | g7 | g12 | g13 | g14 | g15;
assign encoded_addr_w[3] = g8 | g9 | g10 | g11 | g12 | g13 | g14 | g15;

assign encoded_addr = (g1) ? 4'b0000 :
                      (g2) ? 4'b0001 :
                      (g3) ? 4'b0010 :
                      (g4) ? 4'b0011 :
                      (g5) ? 4'b0100 :
                      (g6) ? 4'b0101 :
                      (g7) ? 4'b0110 :
                      (g8) ? 4'b0111 :
                      (g9) ? 4'b1000 :
                      (g10) ? 4'b1001 :
                      (g11) ? 4'b1010 :
                      (g12) ? 4'b1011 :
                      (g13) ? 4'b1100 :
                      (g14) ? 4'b1101 :
                      (g15) ? 4'b1110 :
                      (g16) ? 4'b1111 :
                      4'b0000;

endmodule
