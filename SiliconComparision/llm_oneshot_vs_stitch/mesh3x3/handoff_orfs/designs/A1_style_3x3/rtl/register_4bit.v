module register_4bit(din, clk, clr, ce, dout);
    input [3:0] din ;
    input clk ;
    input clr ;
    input ce ;
    output [3:0] dout ;

	 reg [3:0] dout ;
    
	 always @( clr,ce )
	 begin
	 		if(clr)
			dout <= 4'b0000 ;

			else
			begin
					if (ce)
					
					
						dout<= din ;
			end












	 end






  
endmodule