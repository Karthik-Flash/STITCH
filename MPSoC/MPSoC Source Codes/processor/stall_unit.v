`timescale 1ns / 1ps
//////////////////////////////////////////////////////////////////////////////////
// Company: 
// Engineer: 
// 
// Create Date:    16:42:32 03/27/2021 
// Design Name: 
// Module Name:    stall_unit 
// Project Name: 
// Target Devices: 
// Tool versions: 
// Description: 
//
// Dependencies: 
//
// Revision: 
// Revision 0.01 - File Created
// Additional Comments: 
//
//////////////////////////////////////////////////////////////////////////////////
module stall_unit(
    input id_ex_memread,
	 input [4:0]if_id_register_rs1,if_id_register_rs2,id_ex_register_rd,
	 output reg pc_write,if_id_write,control_sel
	 
	 );
always @(*) begin
	if (id_ex_memread==1 && (if_id_register_rs1==id_ex_register_rd) && id_ex_register_rd!=0 ) begin
		control_sel<=0;
		pc_write<=0;
		if_id_write<=0;
		end
	else if (id_ex_memread==1 && (if_id_register_rs2==id_ex_register_rd) && id_ex_register_rd!=0 ) begin
		control_sel<=0;
		pc_write<=0;
		if_id_write<=0;
		end
	 else
    begin
        control_sel<=1;
        pc_write<=1;
        if_id_write<=1;
    end
end
endmodule
