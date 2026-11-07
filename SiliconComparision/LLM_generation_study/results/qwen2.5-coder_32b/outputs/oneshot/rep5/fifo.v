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
    reg [1:0] count;

    wire full;
    wire not_empty;

    assign full = (count == 2'b100);
    assign not_empty = (count != 2'b000);
    assign dout = mem[rd_ptr];
    assign empty = ~not_empty;
    assign almost_full = (count >= 2'b11);

    always @(posedge clk) begin
        if (reset) begin
            wr_ptr <= 2'b00;
            rd_ptr <= 2'b00;
            count <= 2'b00;
        end else begin
            if (wr_en & ~full & ~rd_en) begin
                mem[wr_ptr] <= din;
                wr_ptr <= wr_ptr + 1;
                count <= count + 1;
            end else if (~wr_en & rd_en & not_empty) begin
                rd_ptr <= rd_ptr + 1;
                count <= count - 1;
            end else if (wr_en & ~full & rd_en & not_empty) begin
                mem[wr_ptr] <= din;
                wr_ptr <= wr_ptr + 1;
                rd_ptr <= rd_ptr + 1;
            end
        end
    end

endmodule
