module asynch_comparator (
    input [2:0] rd_ptr, wr_ptr,
    input rd_dir, wr_dir,
    output full_ext, full_int, empty
);

    wire [2:0] rd_pos, wr_pos;
    wire [2:0] diff;
    wire [2:0] occupancy;

    // Convert Gray code to binary position
    always @(*) begin
        case (rd_ptr)
            3'b000: rd_pos = 3'b000;
            3'b001: rd_pos = 3'b001;
            3'b011: rd_pos = 3'b010;
            3'b010: rd_pos = 3'b011;
            3'b110: rd_pos = 3'b100;
            3'b100: rd_pos = 3'b101;
            3'b101: rd_pos = 3'b101; // Treat 101 as position 5
            3'b111: rd_pos = 3'b101; // Treat 111 as position 5
            default: rd_pos = 3'b000; // Default case
        endcase
    end

    always @(*) begin
        case (wr_ptr)
            3'b000: wr_pos = 3'b000;
            3'b001: wr_pos = 3'b001;
            3'b011: wr_pos = 3'b010;
            3'b010: wr_pos = 3'b011;
            3'b110: wr_pos = 3'b100;
            3'b100: wr_pos = 3'b101;
            3'b101: wr_pos = 3'b101; // Treat 101 as position 5
            3'b111: wr_pos = 3'b101; // Treat 111 as position 5
            default: wr_pos = 3'b000; // Default case
        endcase
    end

    // Calculate the difference between positions
    always @(*) begin
        diff = wr_pos - rd_pos;
    end

    // Calculate occupancy
    always @(*) begin
        if (rd_dir == wr_dir) begin
            occupancy = diff;
        end else begin
            occupancy = diff + 3'b110; // Add 6 to the difference
        end
    end

    // Determine full_int, full_ext, and empty
    always @(*) begin
        if (rd_ptr == wr_ptr) begin
            if (rd_dir == wr_dir) begin
                empty = 1'b1;
                full_int = 1'b0;
            end else begin
                empty = 1'b0;
                full_int = 1'b1;
            end
        end else begin
            empty = 1'b0;
            full_int = 1'b0;
        end

        if (occupancy >= 3'b100) begin // 4 or more entries
            full_ext = 1'b1;
        end else begin
            full_ext = 1'b0;
        end
    end

endmodule
