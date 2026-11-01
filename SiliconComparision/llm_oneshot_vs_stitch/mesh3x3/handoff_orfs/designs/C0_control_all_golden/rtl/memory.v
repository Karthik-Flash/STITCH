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
        reg [31:0] mem [7:0] ;    
   
       
     
   
   
        always @ (posedge wr_clk)
        begin
               if (wr_en)
                   mem [wr_add] = data_in ;            
        end 
   
        always @ (posedge rd_clk)
        begin
            if (reset)
                data_out = 32'b01100000000000000000000000000000 ; 
         else
           begin
               if (rd_en)
                   data_out = mem[rd_add] ;
            else
                
                data_out=data_out;
           end
           
           
         
       end 

endmodule