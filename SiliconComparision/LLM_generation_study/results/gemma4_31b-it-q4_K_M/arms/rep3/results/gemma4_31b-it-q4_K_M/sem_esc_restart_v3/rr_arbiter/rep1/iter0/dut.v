module rr_arbiter (
    input clk,
    input reset,
    input [3:0] req,
    input advance,
    output reg [3:0] gnt
);

    reg [1:0] last_granted;

    always @(*) begin
        gnt = 4'b0000;
        case (last_granted)
            2'b00: begin
                if (req[1]) 
                    gnt = 4'b0010;
                else if (req[2]) 
                    gnt = 4'b0100;
                else if (req[3]) 
                    gnt = 4'b1000;
                else if (req[0]) 
                    gnt = 4'b0001;
                else 
                    gnt = 4'b0000;
            end
            2'b01: begin
                if (req[2]) 
                    gnt = 4'b0100;
                else if (req[3]) 
                    gnt = 4'b1000;
                else if (req[0]) 
                    gnt = 4'b0001;
                else if (req[1]) 
                    gnt = 4'b0010;
                else 
                    gnt = 4'b0000;
            end
            2'b10: begin
                if (req[3]) 
                    gnt = 4'b1000;
                else if (req[0]) 
                    gnt = 4'b0001;
                else if (req[1]) 
                    gnt = 4'b0010;
                else if (req[2]) 
                    gnt = 4'b0100;
                else 
                    gnt = 4'b0000;
            end
            2'b11: begin
                if (req[0]) 
                    gnt = 4'b0001;
                else if (req[1]) 
                    gnt = 4'b0010;
                else if (req[2]) 
                    gnt = 4'b0100;
                else if (req[3]) 
                    gnt = 4'b1000;
                else 
                    gnt = 4'b0000;
            end
            default: begin
                gnt = 4'b0000;
            end
        endcase
    end

    always @(posedge clk) begin
        if (reset) begin
            last_granted <= 2'b11;
        end else if (advance && (gnt != 4'b0000)) begin
            if (gnt[0]) begin
                last_granted <= 2'b00;
            end else if (gnt[1]) begin
                last_granted <= 2'b01;
            end else if (gnt[2]) begin
                last_granted <= 2'b10;
            end else if (gnt[3]) begin
                last_granted <= 2'b11;
            end else begin
                last_granted <= last_granted;
            end
        end
    end

endmodule
