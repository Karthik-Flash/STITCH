module demux_16 (
    input ip,
    input [3:0] sel,
    output op1, op2, op3, op4, op5, op6, op7, op8, op9, op10, op11, op12, op13, op14, op15, op16
);

    wire op1, op2, op3, op4, op5, op6, op7, op8, op9, op10, op11, op12, op13, op14, op15, op16;

    assign op1 = (sel == 4'b0000) ? ip : 1'b0;
    assign op2 = (sel == 4'b0001) ? ip : 1'b0;
    assign op3 = (sel == 4'b0010) ? ip : 1'b0;
    assign op4 = (sel == 4'b0011) ? ip : 1'b0;
    assign op5 = (sel == 4'b0100) ? ip : 1'b0;
    assign op6 = (sel == 4'b0101) ? ip : 1'b0;
    assign op7 = (sel == 4'b0110) ? ip : 1'b0;
    assign op8 = (sel == 4'b0111) ? ip : 1'b0;
    assign op9 = (sel == 4'b1000) ? ip : 1'b0;
    assign op10 = (sel == 4'b1001) ? ip : 1'b0;
    assign op11 = (sel == 4'b1010) ? ip : 1'b0;
    assign op12 = (sel == 4'b1011) ? ip : 1'b0;
    assign op13 = (sel == 4'b1100) ? ip : 1'b0;
    assign op14 = (sel == 4'b1101) ? ip : 1'b0;
    assign op15 = (sel == 4'b1110) ? ip : 1'b0;
    assign op16 = (sel == 4'b1111) ? ip : 1'b0;

endmodule
