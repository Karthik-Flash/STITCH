`timescale 1ns / 1ps
module register_1bit(din, reset, clk, clr, ce, dout);
    input din ;
    input clk ;
    input clr ;
    input ce ;
    input reset;
    output reg dout ;

always @(posedge clk,posedge reset)
	 begin
	 		if(clr | reset)
			dout <= 1'b0;

			else if ( ce )
                                       dout <= din ;

	 end

endmodule
