module rr_arbiter (
    input clk,
    input reset,
    input [3:0] req,
    input advance,
    output [3:0] gnt
);

    reg [3:0] gnt_reg;
    reg [1:0] last;
    reg [1:0] gnt_idx;

    assign gnt = gnt_reg;

    // Combinational logic to determine the grant based on the last requester
    always @(*) begin
        gnt_reg = 4'b0000;
        case (last)
            2'b00: begin
                if (req[1]) 
                    gnt_reg = 4'b0010;
                else if (req[2]) 
                    gnt_reg = 4'b0100;
                else if (req[3]) 
                    gnt_reg = 4'b1000;
                else if (req[0]) 
                    gnt_reg = 4'b0001;
                else 
                    gnt_reg = 4'b0000;
            end
            2'b01: begin
                if (req[2]) 
                    gnt_reg = 4'b0100;
                else if (req[3]) 
                    gnt_reg = 4'b1000;
                else if (req[0]) 
                    gnt_reg = 4'b0001;
                else if (req[1]) 
                    gnt_reg = 4'b0010;
                else 
                    gnt_reg = 4'b0000;
            end
            2'b10: begin
                if (req[3]) 
                    gnt_reg = 4'b1000;
                else if (req[0]) 
                    gnt_reg = 4'b0001;
                else if (req[1]) 
                    gnt_reg = 4'b0010;
                else if (req[2]) 
                    gnt_reg = 4'b0100;
                else 
                    gnt_reg = 4'b0000;
            end
            2'b11: begin
                if (req[0]) 
                    gnt_reg = 4'b0001;
                else if (req[1]) 
                    gnt_reg = 4'b0010;
                else if (req[2]) 
                    gnt_reg = 4'b0100;
                else if (req[3]) 
                    gnt_reg = 4'b1000;
                else 
                    gnt_reg = 4'b0000;
            end
            default: begin
                gnt_reg = 4'b0000;
            end
        end
    end

    // Combinational logic to convert one-hot grant to index
    always @(*) begin
        case (gnt_reg)
            4'b0001: gnt_idx = 2'b00;
            4'b0010: gnt_idx = 2'b01;
            4'b0100: gnt_idx = 2'b10;
            4'b1000: gnt_idx = 2'b11;
            default: gnt_idx = 2'b00;
        end
    end

    // Sequential logic to update the last requester
    always @(posedge clk) begin
        if (reset) begin
            last <= 2'b11;
        end else if (advance && (gnt_reg != 4'b0000)) begin
            last <= gnt_idx;
        end
    end

endmodule
