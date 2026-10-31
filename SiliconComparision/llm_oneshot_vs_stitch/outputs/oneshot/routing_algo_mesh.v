module routing_algo_mesh (
    input [31:0] header_in,
    input [7:0] current_address,
    input reset,
    output req_link1, req_link2, req_core, req_link3, req_link4
);

    wire req_link1, req_link2, req_core, req_link3, req_link4;

    always @(*) begin
        if (reset || (header_in[29] != 1'b1 || header_in[30] != 1'b0)) begin
            req_link1 = 1'b0;
            req_link2 = 1'b0;
            req_core = 1'b0;
            req_link3 = 1'b0;
            req_link4 = 1'b0;
        end else begin
            case (1'b1)
                (header_in[7:4] > current_address[7:4]): begin
                    req_link1 = 1'b1;
                    req_link2 = 1'b0;
                    req_core = 1'b0;
                    req_link3 = 1'b0;
                    req_link4 = 1'b0;
                end
                (header_in[7:4] < current_address[7:4]): begin
                    req_link1 = 1'b0;
                    req_link2 = 1'b1;
                    req_core = 1'b0;
                    req_link3 = 1'b0;
                    req_link4 = 1'b0;
                end
                default: begin
                    case (1'b1)
                        (header_in[3:0] > current_address[3:0]): begin
                            req_link1 = 1'b0;
                            req_link2 = 1'b0;
                            req_core = 1'b0;
                            req_link3 = 1'b1;
                            req_link4 = 1'b0;
                        end
                        (header_in[3:0] < current_address[3:0]): begin
                            req_link1 = 1'b0;
                            req_link2 = 1'b0;
                            req_core = 1'b0;
                            req_link3 = 1'b0;
                            req_link4 = 1'b1;
                        end
                        default: begin
                            req_link1 = 1'b0;
                            req_link2 = 1'b0;
                            req_core = 1'b1;
                            req_link3 = 1'b0;
                            req_link4 = 1'b0;
                        end
                    endcase
                end
            endcase
        end
    end

endmodule
