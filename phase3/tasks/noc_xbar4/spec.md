Module `noc_xbar4` -- one output port of a NoC router crossbar (combinational).
Ports (keep exactly): input [3:0] gnt (one-hot grant from the arbiter, or all-zero); input [31:0] in0..in3;
output [31:0] out_data; output out_valid.
out_data = in_k when gnt[k]==1 (gnt is one-hot); out_data = 0 when gnt == 0. out_valid = |gnt.
Every output must have exactly ONE driver.
