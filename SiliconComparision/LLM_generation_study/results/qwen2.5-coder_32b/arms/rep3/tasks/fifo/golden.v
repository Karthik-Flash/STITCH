module fifo (
    input         clk,
    input         reset,
    input         wr_en,
    input  [31:0] din,
    input         rd_en,
    output [31:0] dout,
    output        empty,
    output        almost_full
);
    reg [31:0] mem [0:3];
    reg [1:0]  wr_ptr;
    reg [1:0]  rd_ptr;
    reg [2:0]  count;

    wire do_wr = wr_en && (count != 3'd4);
    wire do_rd = rd_en && (count != 3'd0);

    always @(posedge clk) begin
        if (reset) begin
            wr_ptr <= 2'd0;
            rd_ptr <= 2'd0;
            count  <= 3'd0;
        end else begin
            if (do_wr) wr_ptr <= wr_ptr + 2'd1;
            if (do_rd) rd_ptr <= rd_ptr + 2'd1;
            if (do_wr && !do_rd)
                count <= count + 3'd1;
            else if (do_rd && !do_wr)
                count <= count - 3'd1;
        end
    end

    always @(posedge clk)
        if (do_wr)
            mem[wr_ptr] <= din;

    assign dout        = mem[rd_ptr];
    assign empty       = (count == 3'd0);
    assign almost_full = (count >= 3'd3);
endmodule
