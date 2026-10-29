`timescale 1ns / 1ps





















module Branch_Cal(
input [31:0] if_id_PC,
input [31:0] sign_extend,
output reg [31:0] B_addr
    );
 always @(*)
 begin
 B_addr= if_id_PC+sign_extend;
 end
endmodule
