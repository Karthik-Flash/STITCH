module router_fifo (
    input reset, rd_clk, rd_en,
    input [31:0] data_in,
    input wr_clk, wr_en,
    output [2:0] rd_add, wr_add,
    output wr_dir, rd_dir,
    output [31:0] data_out,
    output full_ext, full_int, empty
);

    wire [2:0] rd_ptr, wr_ptr;
    wire rd_dir_int, wr_dir_int;
    wire [31:0] data_out_int;

    gray_mod6 rd_gray_mod (
        .clk(rd_clk),
        .reset(reset),
        .en(rd_en),
        .gray_out(rd_add),
        .dir(rd_dir_int)
    );

    gray_mod6 wr_gray_mod (
        .clk(wr_clk),
        .reset(reset),
        .en(wr_en),
        .gray_out(wr_add),
        .dir(wr_dir_int)
    );

    memory mem (
        .reset(reset),
        .rd_clk(rd_clk),
        .rd_add(rd_ptr),
        .wr_clk(wr_clk),
        .wr_add(wr_ptr),
        .data_in(data_in),
        .wr_en(wr_en),
        .rd_en(rd_en),
        .data_out(data_out_int)
    );

    asynch_comparator comp (
        .rd_ptr(rd_ptr),
        .wr_ptr(wr_ptr),
        .rd_dir(rd_dir_int),
        .wr_dir(wr_dir_int),
        .full_ext(full_ext),
        .full_int(full_int),
        .empty(empty)
    );

    reg [2:0] rd_ptr_reg;
    reg [2:0] wr_ptr_reg;
    reg [31:0] data_out_reg;
    reg rd_dir_reg;
    reg wr_dir_reg;

    always @(posedge rd_clk or posedge reset) begin
        if (reset) begin
            rd_ptr_reg <= 3'b000;
            data_out_reg <= 32'h6000_0000;
            rd_dir_reg <= 1'b0;
        end else begin
            if (rd_en && !empty) begin
                rd_ptr_reg <= rd_ptr_reg + 1; // Increment rd_ptr_reg directly
                data_out_reg <= data_out_int;
            end
            rd_dir_reg <= rd_dir_int;
        end
    end

    always @(posedge wr_clk or posedge reset) begin
        if (reset) begin
            wr_ptr_reg <= 3'b000;
            wr_dir_reg <= 1'b0;
        end else begin
            if (wr_en && !full_int) begin
                wr_ptr_reg <= wr_ptr_reg + 1; // Increment wr_ptr_reg directly
            end
            wr_dir_reg <= wr_dir_int;
        end
    end

    assign rd_ptr = rd_ptr_reg;
    assign wr_ptr = wr_ptr_reg;
    assign data_out = data_out_reg;
    assign rd_dir = rd_dir_reg;
    assign wr_dir = wr_dir_reg;

endmodule
