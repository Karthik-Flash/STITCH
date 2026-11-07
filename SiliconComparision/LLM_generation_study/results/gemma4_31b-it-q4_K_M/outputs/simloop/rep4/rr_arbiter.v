module rr_arbiter (
    input clk,
    input reset,
    input [3:0] req,
    input advance,
    output [3:0] gnt
);

    reg [1:0] last;
    reg [3:0] gnt_comb;

    assign gnt = gnt_comb;

    always @(*) begin
        case (last)
            2'b00: begin
                if (req[1]) 
                    gnt_comb = 4'b0010;
                else if (req[2]) 
                    gnt_comb = 4'b0100;
                else if (req[3]) 
                    gnt_comb = 4'b1000;
                else if (req[0]) 
                    gnt_comb = 4'b0001;
                else 
                    gnt_comb = 4'b0000;
            end
            2'b01: begin
                if (req[2]) 
                    gnt_comb = 4'b0100;
                else if (req[3]) 
                    gnt_comb = 4'b1000;
                else if (req[0]) 
                    gnt_comb = 4'b0001;
                else if (req[1]) 
                    gnt_comb = 4'b0010;
                else 
                    gnt_comb = 4'b0000;
            end
            2'b10: begin
                if (req[3]) 
                    gnt_comb = 4'b1000;
                else if (req[0]) 
                    gnt_comb = 4'b0001;
                else if (req[1]) 
                    gnt_comb = 4'b0010;
                else if (req[2]) 
                    gnt_comb = 4'b0100;
                else 
                    gnt_comb = 4'b0000;
            end
            2'b11: begin
                if (req[0]) 
                    gnt_comb = 4'b0001;
                else if (req[1]) 
                    gnt_comb = 4'b0010;
                else if (req[2]) 
                    gnt_comb = 4'b0100;
                else if (req[3]) 
                    gnt_comb = 4'b1000;
                else 
                    gnt_comb = 4'b0000;
            end
            default: begin
                gnt_comb = 4'b0000;
            end
        endcase
    end

    always @(posedge clk) begin
        if (reset) begin
            last <= 2'b11;
        end else if (advance && (gnt != 4'b0000)) begin
            if (gnt[0]) 
                last <= 2'b00;
            else if (gnt[1]) 
                last <= 2'b01;
            else if (gnt[2]) 
                last <= 2'b10;
            else if (gnt[3]) 
                last <= 2'b11;
            else 
                last <= last;
        end else begin
            last <= last;
        end
    end

endmodule
