module memory (
    input reset, rd_clk,
    input [2:0] rd_add,
    input wr_clk,
    input [2:0] wr_add,
    input [31:0] data_in,
    input wr_en, rd_en,
    output [31:0] data_out
);

    reg [31:0] mem [0:7];
    reg [31:0] data_out_reg;

    always @(posedge wr_clk) begin
        if (wr_en) begin
            mem[wr_add] <= data_in;
        end
    end

    always @(posedge rd_clk) begin
        if (reset) begin
            data_out_reg <= 32'h6000_0000;
        end else if (rd_en) begin
            data_out_reg <= mem[rd_add];
        end
    end

    assign data_out = data_out_reg;

endmodule
