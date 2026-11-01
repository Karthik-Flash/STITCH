module falling_edge_pulse_generator(reset,gnt,clk,q0);

input reset,gnt;
input clk;
output q0;
	
	wire q1;
	wire  high;
reg not_gnt;
reg d0_reset;
	







always@(*)
begin	
d0_reset=(reset|q1);
not_gnt=(!gnt);
end





            
                    dff_asynch_clr d00 (.d(1'b1),
                    .clr(d0_reset),
                    .clk(not_gnt),
                    .q(q0));
                    
                    dff_asynch_clr d11(.d(q0),
                    .clr(reset),
                    .clk(clk),
                    .q(q1));
                                	
	
	
endmodule