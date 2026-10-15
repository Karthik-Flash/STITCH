module ni_flit_pack(input [1:0] flit_type, input [7:0] dest, input [7:0] src, input [31:0] payload,
                    output [31:0] head_flit, output [31:0] body_flit);
  assign head_flit = {flit_type, dest, src, 14'b0};
  assign body_flit = {flit_type, payload[29:0]};
endmodule
