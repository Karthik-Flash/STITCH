module final_op_data (
    input [31:0] data_in,
    input [1:0] vc_id,
    input gnt_or,
    output [31:0] data_out
);

wire [31:0] data_out;

assign data_out[31] = data_in[31];
assign data_out[30] = data_in[30] | (~gnt_or);
assign data_out[29] = data_in[29] | (~gnt_or);
assign data_out[28:27] = vc_id;
assign data_out[26:0] = gnt_or ? data_in[26:0] : 27'b0;

endmodule
