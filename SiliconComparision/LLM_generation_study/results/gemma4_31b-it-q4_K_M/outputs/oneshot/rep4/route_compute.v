module route_compute (
    input [31:0] flit,
    input [7:0] current_address,
    output reg [4:0] req
);

    always @(*) begin
        if (flit[30:29] == 2'b01) begin
            if (flit[7:4] > current_address[7:4]) begin
                req = 5'b00001;
            end else if (flit[7:4] < current_address[7:4]) begin
                req = 5'b00010;
            end else begin
                if (flit[3:0] > current_address[3:0]) begin
                    req = 5'b00100;
                end else if (flit[3:0] < current_address[3:0]) begin
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
