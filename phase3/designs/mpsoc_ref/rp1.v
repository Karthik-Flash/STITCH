`timescale 1ns / 1ps





















module rp1(
    input [31:0] data_in,
   input [7:0] dest,
    input [7:0] source,
    input rd_clk,
    input wr_clk,
    input wr_en,
	input reset,
    output reg [31:0] niout,
    output reg rd_en,
    output reg wr_o
    );


integer i;
integer j=0;
integer k;
parameter N=1;
parameter idle=0,header=1,payload1=2,payload2=3,tailer=4,last=5;
reg [2:0]currentstate,nextstate;
reg [31:0] data;

always@(negedge rd_clk)
begin
if(reset==1'b1) begin
rd_en=0;

end
else
begin
if((currentstate==header) || (currentstate==payload2))
begin
rd_en=1;
end
else
rd_en=0;
end
end

always@(posedge rd_clk)
begin
if(reset==1'b1)
begin
niout={1'b0,2'b11,29'd0};
currentstate=idle;
i=0;
k=0;
wr_o=0;
end
else

begin
case(currentstate)
idle:
begin
if(wr_en)
begin
currentstate=header;
end
else
currentstate=idle;
end


header:
begin
niout={1'b0,2'b01,2'b00,11'd0,source,dest};
currentstate=payload1;
end

payload1:
begin
niout={1'b0,2'b00,2'b00,11'd0,data_in[15:0]};
currentstate=payload2;
j=j+1;
end

payload2:
begin
niout={1'b0,2'b00,2'b00,11'd0,data_in[31:16]};
i=i+1;
if(i==N)
currentstate=tailer;
if(j==N)
wr_o=1;
else 
currentstate=payload1;
end


tailer:
begin
niout={1'b0,2'b10,29'd0};
currentstate=last;
end

last:
begin
niout=32'h7fffffff;
currentstate=last;
end

endcase
end
end
endmodule
