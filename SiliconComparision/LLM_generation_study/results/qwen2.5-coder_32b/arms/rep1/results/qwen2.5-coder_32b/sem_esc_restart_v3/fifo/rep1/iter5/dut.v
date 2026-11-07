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
    wire almost_full_int;

    assign full = (count == 3'b100);
    assign almost_full_int = (count >= 3'b10);
    assign almost_full = almost_full_int;
    assign empty = (count == 3'b000);
    assign dout = mem[rd_ptr];

    always @(posedge clk) begin
        if (reset) begin
            wr_ptr <= 2'b00;
            rd_ptr <= 2'b00;
            count <= 3'b000;
        end else begin
            if (wr_en && !full && !(rd_en && !empty)) begin
                mem[wr_ptr] <= din;
                wr_ptr <= wr_ptr + 1;
                count <= count + 1;
            end else if (rd_en && !empty) begin
                rd_ptr <= rd_ptr + 1;
                count <= count - 1;
            end
        end
    end

endmodule
