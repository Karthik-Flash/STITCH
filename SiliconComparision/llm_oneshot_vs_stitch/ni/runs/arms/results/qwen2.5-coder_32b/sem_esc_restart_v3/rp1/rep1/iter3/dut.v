module rp1 (
    input [31:0] data_in,
    input [7:0] dest, source,
    input rd_clk, wr_clk, wr_en, reset,
    output [31:0] niout,
    output rd_en, wr_o
);

    parameter N = 1;
    parameter header = 1;
    parameter idle = 0;
    parameter last = 5;
    parameter payload1 = 2;
    parameter payload2 = 3;
    parameter tailer = 4;

    reg [31:0] niout_reg;
    reg [1:0] state_reg;
    reg [3:0] i;
    reg [3:0] j;
    reg rd_en_reg;
    reg wr_o_reg;

    always @(posedge rd_clk or posedge reset) begin
        if (reset) begin
            niout_reg <= 32'h6000_0000;
            state_reg <= 2'b00; // Explicitly set to 2 bits
            i <= 0;
            wr_o_reg <= 0;
        end else begin
            case (state_reg)
                idle: begin
                    if (wr_en) begin
                        niout_reg <= {1'b0, 2'b01, 2'b00, 11'd0, source, dest};
                        state_reg <= 2'b01; // Explicitly set to 2 bits
                    end else begin
                        niout_reg <= niout_reg;
                        state_reg <= 2'b00; // Explicitly set to 2 bits
                    end
                end
                header: begin
                    niout_reg <= {1'b0, 2'b00, 2'b00, 11'd0, data_in[15:0]};
                    state_reg <= 2'b10; // Explicitly set to 2 bits
                end
                payload1: begin
                    niout_reg <= {1'b0, 2'b00, 2'b00, 11'd0, data_in[31:16]};
                    state_reg <= 2'b11; // Explicitly set to 2 bits
                    j <= j + 1;
                end
                payload2: begin
                    niout_reg <= {1'b0, 2'b00, 2'b00, 11'd0, data_in[31:16]};
                    i <= i + 1;
                    if (i == N) begin
                        if (j == N) begin
                            wr_o_reg <= 1;
                            state_reg <= 2'b100; // Explicitly set to 2 bits
                        end else begin
                            wr_o_reg <= 0;
                            state_reg <= 2'b10; // Explicitly set to 2 bits
                        end
                    end else begin
                        wr_o_reg <= 0;
                        state_reg <= 2'b11; // Explicitly set to 2 bits
                    end
                end
                tailer: begin
                    niout_reg <= 32'h4000_0000;
                    state_reg <= 2'b101; // Explicitly set to 2 bits
                end
                last: begin
                    niout_reg <= 32'h7FFF_FFFF;
                    state_reg <= 2'b101; // Explicitly set to 2 bits
                end
                default: begin
                    niout_reg <= 32'h6000_0000;
                    state_reg <= 2'b00; // Explicitly set to 2 bits
                end
            endcase
        end
    end

    always @(negedge rd_clk or posedge reset) begin
        if (reset) begin
            rd_en_reg <= 0;
        end else begin
            case (state_reg)
                2'b01: rd_en_reg <= 1; // Explicitly set to 2 bits
                2'b11: rd_en_reg <= 1; // Explicitly set to 2 bits
                default: rd_en_reg <= 0;
            endcase
        end
    end

    assign niout = niout_reg;
    assign rd_en = rd_en_reg;
    assign wr_o = wr_o_reg;

endmodule
