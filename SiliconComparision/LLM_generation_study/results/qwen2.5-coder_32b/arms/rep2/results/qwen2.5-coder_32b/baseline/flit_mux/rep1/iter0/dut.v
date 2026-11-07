module flit_mux (
    input [3:0] sel,
    input [31:0] in0,
    input [31:0] in1,
    input [31:0] in2,
    input [31:0] in3,
    output [31:0] out
);

wire [31:0] out;

assign out = (sel == 4'b0001) ? in0 :
             (sel == 4'b0010) ? in1 :
             (sel == 4'b0100) ? in2 :
             (sel == 4'b1000) ? in3 :
             32'h6000_0000;

endmodule
