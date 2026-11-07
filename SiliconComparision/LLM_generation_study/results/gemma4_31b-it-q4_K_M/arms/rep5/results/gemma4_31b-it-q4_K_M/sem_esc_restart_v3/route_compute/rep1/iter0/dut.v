module route_compute (
    input [31:0] flit,
    input [7:0] current_address,
    output reg [4:0] req
);

    wire [3:0] dest_row;
    wire [3:0] dest_col;
    wire [3:0] curr_row;
    wire [3:0] curr_col;

    assign dest_row = flit[7:4];
    assign dest_col = flit[3:0];
    assign curr_row = current_address[7:4];
    assign curr_col = current_address[3:0];

    always @(*) begin
        if (flit[30:29] == 2'b01) begin
            if (dest_row > curr_row) begin
                req = 5'b00001;
            end else if (dest_row < curr_row) begin
                req = 5'b00010;
            end else begin
                if (dest_col > curr_col) begin
                    req = 5'b00100;
                end else if (dest_col < curr_col) begin
                    req = 5'b01000;
                end else begin
                    req = 5'b10000;
                end
            end
        end else begin
            req = 5'b00000;
        end
    end

endmodule
