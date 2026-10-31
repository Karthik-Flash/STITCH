module demux_16 (
    input ip,
    input [3:0] sel,
    output op1, op2, op3, op4, op5, op6, op7, op8, op9, op10, op11, op12, op13, op14, op15, op16
);

    wire op1, op2, op3, op4, op5, op6, op7, op8, op9, op10, op11, op12, op13, op14, op15, op16;

    always @(*) begin
        case (sel)
            4'b0000: begin
                op1 = ip;
                op2 = 1'b0;
                op3 = 1'b0;
                op4 = 1'b0;
                op5 = 1'b0;
                op6 = 1'b0;
                op7 = 1'b0;
                op8 = 1'b0;
                op9 = 1'b0;
                op10 = 1'b0;
                op11 = 1'b0;
                op12 = 1'b0;
                op13 = 1'b0;
                op14 = 1'b0;
                op15 = 1'b0;
                op16 = 1'b0;
            end
            4'b0001: begin
                op1 = 1'b0;
                op2 = ip;
                op3 = 1'b0;
                op4 = 1'b0;
                op5 = 1'b0;
                op6 = 1'b0;
                op7 = 1'b0;
                op8 = 1'b0;
                op9 = 1'b0;
                op10 = 1'b0;
                op11 = 1'b0;
                op12 = 1'b0;
                op13 = 1'b0;
                op14 = 1'b0;
                op15 = 1'b0;
                op16 = 1'b0;
            end
            4'b0010: begin
                op1 = 1'b0;
                op2 = 1'b0;
                op3 = ip;
                op4 = 1'b0;
                op5 = 1'b0;
                op6 = 1'b0;
                op7 = 1'b0;
                op8 = 1'b0;
                op9 = 1'b0;
                op10 = 1'b0;
                op11 = 1'b0;
                op12 = 1'b0;
                op13 = 1'b0;
                op14 = 1'b0;
                op15 = 1'b0;
                op16 = 1'b0;
            end
            4'b0011: begin
                op1 = 1'b0;
                op2 = 1'b0;
                op3 = 1'b0;
                op4 = ip;
                op5 = 1'b0;
                op6 = 1'b0;
                op7 = 1'b0;
                op8 = 1'b0;
                op9 = 1'b0;
                op10 = 1'b0;
                op11 = 1'b0;
                op12 = 1'b0;
                op13 = 1'b0;
                op14 = 1'b0;
                op15 = 1'b0;
                op16 = 1'b0;
            end
            4'b0100: begin
                op1 = 1'b0;
                op2 = 1'b0;
                op3 = 1'b0;
                op4 = 1'b0;
                op5 = ip;
                op6 = 1'b0;
                op7 = 1'b0;
                op8 = 1'b0;
                op9 = 1'b0;
                op10 = 1'b0;
                op11 = 1'b0;
                op12 = 1'b0;
                op13 = 1'b0;
                op14 = 1'b0;
                op15 = 1'b0;
                op16 = 1'b0;
            end
            4'b0101: begin
                op1 = 1'b0;
                op2 = 1'b0;
                op3 = 1'b0;
                op4 = 1'b0;
                op5 = 1'b0;
                op6 = ip;
                op7 = 1'b0;
                op8 = 1'b0;
                op9 = 1'b0;
                op10 = 1'b0;
                op11 = 1'b0;
                op12 = 1'b0;
                op13 = 1'b0;
                op14 = 1'b0;
                op15 = 1'b0;
                op16 = 1'b0;
            end
            4'b0110: begin
                op1 = 1'b0;
                op2 = 1'b0;
                op3 = 1'b0;
                op4 = 1'b0;
                op5 = 1'b0;
                op6 = 1'b0;
                op7 = ip;
                op8 = 1'b0;
                op9 = 1'b0;
                op10 = 1'b0;
                op11 = 1'b0;
                op12 = 1'b0;
                op13 = 1'b0;
                op14 = 1'b0;
                op15 = 1'b0;
                op16 = 1'b0;
            end
            4'b0111: begin
                op1 = 1'b0;
                op2 = 1'b0;
                op3 = 1'b0;
                op4 = 1'b0;
                op5 = 1'b0;
                op6 = 1'b0;
                op7 = 1'b0;
                op8 = ip;
                op9 = 1'b0;
                op10 = 1'b0;
                op11 = 1'b0;
                op12 = 1'b0;
                op13 = 1'b0;
                op14 = 1'b0;
                op15 = 1'b0;
                op16 = 1'b0;
            end
            4'b1000: begin
                op1 = 1'b0;
                op2 = 1'b0;
                op3 = 1'b0;
                op4 = 1'b0;
                op5 = 1'b0;
                op6 = 1'b0;
                op7 = 1'b0;
                op8 = 1'b0;
                op9 = ip;
                op10 = 1'b0;
                op11 = 1'b0;
                op12 = 1'b0;
                op13 = 1'b0;
                op14 = 1'b0;
                op15 = 1'b0;
                op16 = 1'b0;
            end
            4'b1001: begin
                op1 = 1'b0;
                op2 = 1'b0;
                op3 = 1'b0;
                op4 = 1'b0;
                op5 = 1'b0;
                op6 = 1'b0;
                op7 = 1'b0;
                op8 = 1'b0;
                op9 = 1'b0;
                op10 = ip;
                op11 = 1'b0;
                op12 = 1'b0;
                op13 = 1'b0;
                op14 = 1'b0;
                op15 = 1'b0;
                op16 = 1'b0;
            end
            4'b1010: begin
                op1 = 1'b0;
                op2 = 1'b0;
                op3 = 1'b0;
                op4 = 1'b0;
                op5 = 1'b0;
                op6 = 1'b0;
                op7 = 1'b0;
                op8 = 1'b0;
                op9 = 1'b0;
                op10 = 1'b0;
                op11 = ip;
                op12 = 1'b0;
                op13 = 1'b0;
                op14 = 1'b0;
                op15 = 1'b0;
                op16 = 1'b0;
            end
            4'b1011: begin
                op1 = 1'b0;
                op2 = 1'b0;
                op3 = 1'b0;
                op4 = 1'b0;
                op5 = 1'b0;
                op6 = 1'b0;
                op7 = 1'b0;
                op8 = 1'b0;
                op9 = 1'b0;
                op10 = 1'b0;
                op11 = 1'b0;
                op12 = ip;
                op13 = 1'b0;
                op14 = 1'b0;
                op15 = 1'b0;
                op16 = 1'b0;
            end
            4'b1100: begin
                op1 = 1'b0;
                op2 = 1'b0;
                op3 = 1'b0;
                op4 = 1'b0;
                op5 = 1'b0;
                op6 = 1'b0;
                op7 = 1'b0;
                op8 = 1'b0;
                op9 = 1'b0;
                op10 = 1'b0;
                op11 = 1'b0;
                op12 = 1'b0;
                op13 = ip;
                op14 = 1'b0;
                op15 = 1'b0;
                op16 = 1'b0;
            end
            4'b1101: begin
                op1 = 1'b0;
                op2 = 1'b0;
                op3 = 1'b0;
                op4 = 1'b0;
                op5 = 1'b0;
                op6 = 1'b0;
                op7 = 1'b0;
                op8 = 1'b0;
                op9 = 1'b0;
                op10 = 1'b0;
                op11 = 1'b0;
                op12 = 1'b0;
                op13 = 1'b0;
                op14 = ip;
                op15 = 1'b0;
                op16 = 1'b0;
            end
            4'b1110: begin
                op1 = 1'b0;
                op2 = 1'b0;
                op3 = 1'b0;
                op4 = 1'b0;
                op5 = 1'b0;
                op6 = 1'b0;
                op7 = 1'b0;
                op8 = 1'b0;
                op9 = 1'b0;
                op10 = 1'b0;
                op11 = 1'b0;
                op12 = 1'b0;
                op13 = 1'b0;
                op14 = 1'b0;
                op15 = ip;
                op16 = 1'b0;
            end
            4'b1111: begin
                op1 = 1'b0;
                op2 = 1'b0;
                op3 = 1'b0;
                op4 = 1'b0;
                op5 = 1'b0;
                op6 = 1'b0;
                op7 = 1'b0;
                op8 = 1'b0;
                op9 = 1'b0;
                op10 = 1'b0;
                op11 = 1'b0;
                op12 = 1'b0;
                op13 = 1'b0;
                op14 = 1'b0;
                op15 = 1'b0;
                op16 = ip;
            end
            default: begin
                op1 = 1'b0;
                op2 = 1'b0;
                op3 = 1'b0;
                op4 = 1'b0;
                op5 = 1'b0;
                op6 = 1'b0;
                op7 = 1'b0;
                op8 = 1'b0;
                op9 = 1'b0;
                op10 = 1'b0;
                op11 = 1'b0;
                op12 = 1'b0;
                op13 = 1'b0;
                op14 = 1'b0;
                op15 = 1'b0;
                op16 = 1'b0;
            end
        endcase
    end

endmodule
