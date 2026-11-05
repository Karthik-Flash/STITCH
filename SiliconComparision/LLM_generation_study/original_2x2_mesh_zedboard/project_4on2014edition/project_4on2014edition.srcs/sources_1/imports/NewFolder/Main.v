`timescale 1ns / 1ps
//////////////////////////////////////////////////////////////////////////////////
// Company: 
// Engineer: 
// 
// Create Date: 11/28/2018 04:55:48 PM
// Design Name: 
// Module Name: Main
// Project Name: 
// Target Devices: 
// Tool Versions: 
// Description: 
// 
// Dependencies: 
// 
// Revision:
// Revision 0.01 - File Created
// Additional Comments:
// 
//////////////////////////////////////////////////////////////////////////////////


module main(input clk);


wire reset,clr;
wire[7:0] current_address_r1, current_address_r2, current_address_r3, current_address_r4;
wire[31:0] data_in_core_r1, data_in_core_r2, data_in_core_r3, data_in_core_r4,
           data_out_core_r1, data_out_core_r2, data_out_core_r3, data_out_core_r4;
           
wire full_in_core_vc1_r1, full_in_core_vc2_r1, full_in_core_vc3_r1, full_in_core_vc4_r1,
     full_in_core_vc1_r2, full_in_core_vc2_r2, full_in_core_vc3_r2, full_in_core_vc4_r2,
     full_in_core_vc1_r3, full_in_core_vc2_r3, full_in_core_vc3_r3, full_in_core_vc4_r3,
     full_in_core_vc1_r4, full_in_core_vc2_r4, full_in_core_vc3_r4, full_in_core_vc4_r4,
     
     
     full_out_core_vc1_r1, full_out_core_vc2_r1, full_out_core_vc3_r1, full_out_core_vc4_r1,
     full_out_core_vc1_r2, full_out_core_vc2_r2, full_out_core_vc3_r2, full_out_core_vc4_r2,
     full_out_core_vc1_r3, full_out_core_vc2_r3, full_out_core_vc3_r3, full_out_core_vc4_r3,
     full_out_core_vc1_r4, full_out_core_vc2_r4, full_out_core_vc3_r4, full_out_core_vc4_r4;
                     


top_4_router m1(clk, clr,
current_address_r1, current_address_r2, current_address_r3, current_address_r4,
data_in_core_r1, data_in_core_r2, data_in_core_r3, data_in_core_r4,
full_in_core_vc1_r1, full_in_core_vc2_r1, full_in_core_vc3_r1, full_in_core_vc4_r1,
full_in_core_vc1_r2, full_in_core_vc2_r2, full_in_core_vc3_r2, full_in_core_vc4_r2,
full_in_core_vc1_r3, full_in_core_vc2_r3, full_in_core_vc3_r3, full_in_core_vc4_r3,
full_in_core_vc1_r4, full_in_core_vc2_r4, full_in_core_vc3_r4, full_in_core_vc4_r4,
reset,
data_out_core_r1, data_out_core_r2, data_out_core_r3, data_out_core_r4,
full_out_core_vc1_r1, full_out_core_vc2_r1, full_out_core_vc3_r1, full_out_core_vc4_r1,
full_out_core_vc1_r2, full_out_core_vc2_r2, full_out_core_vc3_r2, full_out_core_vc4_r2,
full_out_core_vc1_r3, full_out_core_vc2_r3, full_out_core_vc3_r3, full_out_core_vc4_r3,
full_out_core_vc1_r4, full_out_core_vc2_r4, full_out_core_vc3_r4, full_out_core_vc4_r4
);


vio_0 m2(clk,
reset,
data_out_core_r1, data_out_core_r2, data_out_core_r3, data_out_core_r4,
full_out_core_vc1_r1, full_out_core_vc2_r1, full_out_core_vc3_r1, full_out_core_vc4_r1,
full_out_core_vc1_r2, full_out_core_vc2_r2, full_out_core_vc3_r2, full_out_core_vc4_r2,
full_out_core_vc1_r3, full_out_core_vc2_r3, full_out_core_vc3_r3, full_out_core_vc4_r3,
full_out_core_vc1_r4, full_out_core_vc2_r4, full_out_core_vc3_r4, full_out_core_vc4_r4,
clr,
current_address_r1, current_address_r2, current_address_r3, current_address_r4,
data_in_core_r1, data_in_core_r2, data_in_core_r3, data_in_core_r4,
full_in_core_vc1_r1, full_in_core_vc2_r1, full_in_core_vc3_r1, full_in_core_vc4_r1,
full_in_core_vc1_r2, full_in_core_vc2_r2, full_in_core_vc3_r2, full_in_core_vc4_r2,
full_in_core_vc1_r3, full_in_core_vc2_r3, full_in_core_vc3_r3, full_in_core_vc4_r3,
full_in_core_vc1_r4, full_in_core_vc2_r4, full_in_core_vc3_r4, full_in_core_vc4_r4
);




ila_0 m3(clk,
clr,
current_address_r1, current_address_r2, current_address_r3, current_address_r4,
data_in_core_r1, data_in_core_r2, data_in_core_r3, data_in_core_r4,
full_in_core_vc1_r1, full_in_core_vc2_r1, full_in_core_vc3_r1, full_in_core_vc4_r1,
full_in_core_vc1_r2, full_in_core_vc2_r2, full_in_core_vc3_r2, full_in_core_vc4_r2,
full_in_core_vc1_r3, full_in_core_vc2_r3, full_in_core_vc3_r3, full_in_core_vc4_r3,
full_in_core_vc1_r4, full_in_core_vc2_r4, full_in_core_vc3_r4, full_in_core_vc4_r4,
reset,
data_out_core_r1, data_out_core_r2, data_out_core_r3, data_out_core_r4,
full_out_core_vc1_r1, full_out_core_vc2_r1, full_out_core_vc3_r1, full_out_core_vc4_r1,
full_out_core_vc1_r2, full_out_core_vc2_r2, full_out_core_vc3_r2, full_out_core_vc4_r2,
full_out_core_vc1_r3, full_out_core_vc2_r3, full_out_core_vc3_r3, full_out_core_vc4_r3,
full_out_core_vc1_r4, full_out_core_vc2_r4, full_out_core_vc3_r4, full_out_core_vc4_r4
);

endmodule
