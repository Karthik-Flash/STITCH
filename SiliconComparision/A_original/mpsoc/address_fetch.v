`timescale 1ns / 1ps



















module address_fetch(
    input [31:0] next_pc,
    output reg [31:0] inst_address,
    input clock,
    input reset
    );	 
	
	 
	 always @(posedge clock)
	 begin
		if(reset == 1)
			begin
			inst_address = -4;
			
			end
			
		
		








		
	



		else
		inst_address = next_pc;
end
endmodule
