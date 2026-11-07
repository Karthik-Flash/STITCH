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

    reg [31:0] buffer [0:3];
    reg [1:0] head;
    reg [1:0] tail;
    reg [2:0] count;

    assign dout = buffer[head];
    assign empty = (count == 3'd0);
    assign almost_full = (count >= 3'd3);

    always @(posedge clk) begin
        if (reset) begin
            head <= 2'b00;
            tail <= 2'b00;
            count <= 3'd0;
        end else begin
            if (rd_en && (count > 3'd0)) begin
                head <= head + 2'b01;
            end

            if (wr_en && (count < 3'd4)) begin
                buffer[tail] <= din;
                tail <= tail + 2'b01;
            end

            if (rd_en && (count > 3'd0) && wr_en && (count < 3'd4)) begin
                count <= count;
            end else if (rd_en && (count > 3'd0)) begin
                count <= count - 3'd1;
            end else if (wr_en && (count < 3'd4)) begin
                count <= count + 3'd1;
            end else begin
                count <= count;
            end
        end
    end

endmodule
