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

    reg [31:0] mem [0:3];
    reg [1:0] wr_ptr;
    reg [1:0] rd_ptr;
    reg [2:0] count;

    wire write_possible = (wr_en && (count < 3'd4));
    wire read_possible = (rd_en && (count > 3'd0));

    always @(posedge clk) begin
        if (reset) begin
            wr_ptr <= 2'b00;
            rd_ptr <= 2'b00;
            count <= 3'd0;
        end else begin
            if (write_possible) begin
                mem[wr_ptr] <= din;
                wr_ptr <= wr_ptr + 2'b01;
            end

            if (read_possible) begin
                rd_ptr <= rd_ptr + 2'b01;
            end

            if (write_possible && !read_possible) begin
                count <= count + 3'd1;
            end else if (!write_possible && read_possible) begin
                count <= count - 3'd1;
            end else begin
                count <= count;
            end
        end
    end

    assign dout = mem[rd_ptr];
    assign empty = (count == 3'd0);
    assign almost_full = (count >= 3'd3);

endmodule
