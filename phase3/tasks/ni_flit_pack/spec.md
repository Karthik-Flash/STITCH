Module `ni_flit_pack` -- network-interface flit packetiser (combinational).
Ports (keep exactly): input [1:0] flit_type; input [7:0] dest, src; input [31:0] payload;
output [31:0] head_flit, body_flit.
head_flit = {flit_type (bits 31:30), dest (29:22), src (21:14), 14'b0 (13:0)}.
body_flit = {flit_type (31:30), payload[29:0] (29:0)}.
