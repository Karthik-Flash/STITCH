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

    reg [31:0] mem [3:0];
    reg [1:0] wr_ptr;
    reg [1:0] rd_ptr;
    reg [2:0] count;

    wire full = (count == 3'b100);
    wire almost_full_w = (count >= 3'b11);

    assign dout = (empty) ? 32'hxxxxxxxx : mem[rd_ptr];
    assign empty = (count == 3'b000);
    assign almost_full = almost_full_w;

    always @(posedge clk) begin
        if (reset) begin
            wr_ptr <= 2'b00;
            rd_ptr <= 2'b00;
            count <= 3'b000;
        end else begin
            case ({wr_en, rd_en, full, empty})
                3'b100: begin // Write only, not full
                    mem[wr_ptr] <= din;
                    wr_ptr <= wr_ptr + 1;
                    count <= count + 1;
                end
                3'b010: begin // Read only, not empty
                    rd_ptr <= rd_ptr + 1;
                    count <= count - 1;
                end
                3'b110: begin // Write and read, not full, not empty
                    mem[wr_ptr] <= din;
                    wr_ptr <= wr_ptr + 1;
                    rd_ptr <= rd_ptr + 1;
                end
                default: begin // No operation or invalid conditions
                    // Do nothing
                end
            endcase
        end
    end

endmodule
