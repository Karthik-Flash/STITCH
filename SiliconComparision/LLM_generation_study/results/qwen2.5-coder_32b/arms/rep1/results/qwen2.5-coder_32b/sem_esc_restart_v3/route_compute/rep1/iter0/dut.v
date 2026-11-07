module route_compute (
    input [31:0] flit,
    input [7:0] current_address,
    output [4:0] req
);

    wire [1:0] flit_type;
    wire [3:0] dest_column;
    wire [3:0] dest_row;
    wire [3:0] current_column;
    wire [3:0] current_row;

    assign flit_type = flit[30:29];
    assign dest_column = flit[3:0];
    assign dest_row = flit[7:4];
    assign current_column = current_address[3:0];
    assign current_row = current_address[7:4];

    reg [4:0] req_reg;

    always @(*) begin
        case (flit_type)
            2'b01: begin // Head flit
                if (dest_row > current_row) begin
                    req_reg = 5'b00001; // link1
                end else if (dest_row < current_row) begin
                    req_reg = 5'b00010; // link2
                end else begin // same row
                    if (dest_column > current_column) begin
                        req_reg = 5'b00100; // link3
                    end else if (dest_column < current_column) begin
                        req_reg = 5'b01000; // link4
                    end else begin // same column
                        req_reg = 5'b10000; // core
                    end
                end
            end
            default: begin // Not a head flit
                req_reg = 5'b00000;
            end
        endcase
    end

    assign req = req_reg;

endmodule
