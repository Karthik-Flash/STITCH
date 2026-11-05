`timescale 1ns / 1ps
//////////////////////////////////////////////////////////////////////////////////
// Company: 
// Engineer: 
// 
// Create Date: 01/30/2018 07:20:36 PM
// Design Name: 
// Module Name: memory
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


module memory(reset, rd_clk, rd_add, wr_clk, wr_add, data_in, wr_en, rd_en, data_out);
 input reset ;
       input rd_clk ;
       input [2:0] rd_add ;
       input rd_en ;
       input wr_clk ;
       input [2:0] wr_add ;
       input wr_en ;
        input [31:0] data_in ;
       output [31:0] data_out ;
        
        reg [31:0] data_out ;
        reg [31:0] mem [7:0] ;    // memory width 32 bit, depth 6.
   
       ///////////////////////////
     // output [31:0] l,m,n,o,w,z ;
               
               assign l=mem[0];
               assign m=mem[1];
               assign n=mem[2];
               assign o=mem[3];
               assign w=mem[4];
               assign z=mem[5];
   
   
        always @ (posedge wr_clk)
        begin
               if (wr_en)
                   mem [wr_add] = data_in ;            
        end // end of always (wr_clk)
   
        always @ (posedge rd_clk)
        begin
            if (reset)
                data_out = 32'b01100000000000000000000000000000 ; 
         else
           begin
               if (rd_en)
                   data_out = mem[rd_add] ;
            else
                  data_out = 32'b01100000000000000000000000000000 ; 
           end
       end // end always (rd_clk)    
    
endmodule
