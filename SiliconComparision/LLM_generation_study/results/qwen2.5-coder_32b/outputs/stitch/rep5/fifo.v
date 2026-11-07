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

    wire full;
    wire not_empty;

    assign full = (count == 3'b100);
    assign not_empty = (count != 3'b000);
    assign dout = mem[rd_ptr];
    assign empty = ~not_empty;
    assign almost_full = (count >= 3'b11);

    always @(posedge clk) begin
        if (reset) begin
            wr_ptr <= 2'b00;
            rd_ptr <= 2'b00;
            count <= 3'b000;
        end else begin
            case ({wr_en, rd_en, full, not_empty})
                4'b1110: begin // wr_en & rd_en & full & ~not_empty
                    // Do nothing, both operations are ignored
                end
                4'b1101: begin // wr_en & rd_en & ~full & not_empty
                    mem[wr_ptr] <= din;
                    wr_ptr <= wr_ptr + 1;
                    rd_ptr <= rd_ptr + 1;
                    // count remains the same
                end
                4'b1010: begin // wr_en & ~rd_en & full & ~not_empty
                    // Do nothing, write is ignored
                end
                4'b1001: begin // wr_en & ~rd_en & ~full & not_empty
                    mem[wr_ptr] <= din;
                    wr_ptr <= wr_ptr + 1;
                    count <= count + 1;
                end
                4'b0110: begin // ~wr_en & rd_en & full & ~not_empty
                    // Do nothing, read is ignored
                end
                4'b0101: begin // ~wr_en & rd_en & ~full & not_empty
                    rd_ptr <= rd_ptr + 1;
                    count <= count - 1;
                end
                4'b0010: begin // ~wr_en & ~rd_en & full & ~not_empty
                    // Do nothing, no operation
                end
                4'b0001: begin // ~wr_en & ~rd_en & ~full & not_empty
                    // Do nothing, no operation
                end
                default: begin
                    // Do nothing, invalid combination
                end
            endcase
        end
    end

endmodule
