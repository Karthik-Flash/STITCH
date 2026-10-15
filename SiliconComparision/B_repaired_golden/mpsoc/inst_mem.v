



















`timescale 1ns / 1ps

module inst_mem (
    input [31:0]inst_add,
    input reset,
    
    output reg [31:0] inst_code
);


reg [7:0] Memory [55:0];



always @(reset)
    begin
        if(reset == 1)
        begin
        
        
        Memory[3] = 8'h02;    
                    Memory[2] = 8'h11;
                    Memory[1] = 8'h02;
                    Memory[0] = 8'hb3;
                    
                     Memory[7] = 8'h00;
                    Memory[6] = 8'h54;
                    Memory[5] = 8'ha0;
                    Memory[4] = 8'h23; 
                    
                   
                
                   









































































































 
				

				
        end
	end
	
	
    
    always @(inst_add )
    begin
	 
        case(inst_add)
		  
		   0: inst_code = {Memory[inst_add+3], Memory[inst_add+2], Memory[inst_add+1], Memory[inst_add]};
		4: inst_code = {Memory[inst_add+3], Memory[inst_add+2], Memory[inst_add+1], Memory[inst_add]};
		8: inst_code = {Memory[inst_add+3], Memory[inst_add+2], Memory[inst_add+1], Memory[inst_add]};
	
 12: inst_code = {Memory[inst_add+3], Memory[inst_add+2], Memory[inst_add+1], Memory[inst_add]};
		16: inst_code = {Memory[inst_add+3], Memory[inst_add+2], Memory[inst_add+1], Memory[inst_add]};
		20: inst_code = {Memory[inst_add+3], Memory[inst_add+2], Memory[inst_add+1], Memory[inst_add]}; 
	24: inst_code = {Memory[inst_add+3], Memory[inst_add+2], Memory[inst_add+1], Memory[inst_add]};
			28: inst_code = {Memory[inst_add+3], Memory[inst_add+2], Memory[inst_add+1], Memory[inst_add]};
		32: inst_code = {Memory[inst_add+3], Memory[inst_add+2], Memory[inst_add+1], Memory[inst_add]};
			36: inst_code = {Memory[inst_add+3], Memory[inst_add+2], Memory[inst_add+1], Memory[inst_add]}; 
			



			
			
		
	





















			
		


			
		





			
			
			  
			 
			
   		
			
			
			
		



				
		  endcase
	 end  	 

endmodule
