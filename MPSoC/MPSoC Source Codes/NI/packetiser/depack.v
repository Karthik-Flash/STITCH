`timescale 1ns / 1ps
//////////////////////////////////////////////////////////////////////////////////
// Company: 
// Engineer: 
// 
// Create Date:    19:12:05 04/20/2021 
// Design Name: 
// Module Name:    depack 
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
module depack(
input [31:0] flit,
input wr_clk,
input reset,
output reg [31:0]data_out,
output reg wr_en,c_rd

    );
reg [15:0]data1;
parameter state0=0,header=1,firsthalf=2,secondhalf=3,nextstate=4;
reg [2:0] currentstate;
integer i;



always@(posedge wr_clk)
begin
if(reset==1'b1)
begin
currentstate=state0;
wr_en=0;
i=0;
end
else
begin

case(currentstate)
state0:
begin
if({flit[30],flit[29]}==2'b01)
begin 
wr_en=0;
currentstate=header;
end
else
begin
currentstate=state0;
data_out=data_out;
wr_en=0;
end
end


header:
begin
if({flit[30],flit[29]}==2'b00)
begin
wr_en=0;
data1=flit[15:0];
 currentstate=firsthalf;
end
else
currentstate=header;
end


firsthalf:
begin
if({flit[30],flit[29]}==2'b10)
begin
currentstate=state0;
wr_en=0;
end
else
begin
wr_en=1;
c_rd=1;
data_out={flit[15:0],data1};
currentstate=header;
end
end 

default:
currentstate=state0;

endcase
end
end

endmodule






/*if({flit[30],flit[29]}==2'b01)
begin
currentstate=header;
wr_en=0;
end

else if({flit[30],flit[29]}==2'b00)
begin
if(i%2==0)
currentstate=firsthalf;
else
currentstate=secondhalf;
end

else if({flit[30],flit[29]}==2'b11)
begin
currentstate=state0;
wr_en=0;
end


if(i==4)
begin
currentstate=nextstate;
wr_en=0;
end

case(currentstate)
header:
begin
//data_out=flit;
currentstate=firsthalf;
wr_en=0;
end
firsthalf:
begin
data1=flit;
wr_en=0;
//currentstate=secondhalf;
i=i+1;
end
secondhalf:
begin
data_out={flit[15:0],data1[15:0]};
i=i+1;
wr_en=1;
end*/


