 `timescale 1ns / 1ps

module dff_asynch_set(input clk, input d,input set,output reg q);

always@ (posedge clk, posedge set)
begin
if (set==1)
	begin
	q=1;
	end
else
	begin
	q=d;
	end

end
endmodule



