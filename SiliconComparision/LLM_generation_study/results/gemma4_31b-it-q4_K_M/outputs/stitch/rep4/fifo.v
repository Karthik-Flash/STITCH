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
    reg [1:0] wr_ptr;
    reg [1:0] rd_ptr;
    reg [2:0] count;

    assign dout = buffer[rd_ptr];
    assign empty = (count == 3'd0);
    assign almost_full = (count >= 3'd3);

    always @(posedge clk) begin
        if (reset) begin
            wr_ptr <= 2'b00;
            rd_ptr <= 2'b00;
            count <= 3'd0;
        end else begin
            // Write logic
            if (wr_en && (count < 3'd4)) begin
                buffer[wr_ptr] <= din;
                wr_ptr <= wr_ptr + 2'b01;
            end

            // Read logic
            if (rd_en && (count > 3'd0)) begin
                rd_ptr <= rd_ptr + 2'b01;
            end

            // Count logic
            if (wr_en && (count < 3'd4) && rd_en && (count > 3'd0)) begin
                count <= count;
            end else if (wr_en && (count < 3'd4)) begin
                count <= count + 3'd1;
            end else if (rd_en && (count > 3'd0)) begin
                count <= count - 3'd1;
            end else begin
                count <= count;
            end
        end
    end

endmodule
