`timescale 1ns / 1ps

module control(
    input [6:0] funct7,
    input [2:0] funct3,
    input [6:0] opcode,
    input control_sel,
	 
    output reg [3:0] if_id_alu_control,
	 output reg [10:0]control,
	 output reg enable,
    output reg if_id_regwrite_control,if_id_memtoreg,if_id_alusrc,if_id_memread,if_id_memwrite,if_id_branch,if_id_branch2,if_id_jump
    );
	
	
	 
always @(funct3 or funct7 or opcode )
    begin
   
     if(control_sel==0)
    begin
    if_id_regwrite_control = 0;
				if_id_memtoreg=0;
				if_id_alusrc=0;
				if_id_memread=0;
				if_id_memwrite=0;
				if_id_branch=0;
				if_id_branch2=0;
				if_id_alu_control =0;
				
				enable=0;
    end
    
    else if(control_sel)
    begin
        if (opcode == 7'b0110011 && funct7 == 7'b0000001 ) 
            begin
            if_id_regwrite_control = 1;
				if_id_memtoreg=0;
				if_id_alusrc=0;
				if_id_memread=0;
				if_id_memwrite=0;
				if_id_branch=0;
				if_id_branch2=0;
                 enable =0;
				      
				      if(funct3 ==3'b000)
                         if_id_alu_control = 4'b0000; 
                      else if(funct3 == 3'b001)
                         if_id_alu_control = 4'b0001; 
                      else if(funct3 == 3'b010)
                        if_id_alu_control = 4'b0010; 
                      else if(funct3 == 3'b011)
                         if_id_alu_control = 4'b0011; 
                      else if(funct3 == 3'b100)
                         if_id_alu_control = 4'b0100; 
                      else if(funct3 == 3'b101)
                         if_id_alu_control = 4'b0101; 
                       else if(funct3 == 3'b110)
                         if_id_alu_control = 4'b0110; 
                        else if(funct3 == 3'b111)
                         if_id_alu_control = 4'b0111; 
			  end
		
		 if (opcode == 7'b0110011 && funct7 != 7'b0000001) begin 
             
		     enable=1;
            if_id_regwrite_control = 1;
				if_id_memtoreg=0;
				if_id_alusrc=0;
				if_id_memread=0;
				if_id_memwrite=0;
				if_id_branch=0;	    
				if_id_branch2=0;
				if_id_jump =0;  
				
            case (funct3)
                0: begin
                    if(funct7 == 0)
                    if_id_alu_control = 4'b0000; 
                    else if(funct7 == 32)
                    if_id_alu_control = 4'b0001; 
                end
                6: if_id_alu_control = 4'b0010; 
                7: if_id_alu_control = 4'b0011; 
                1: if_id_alu_control = 4'b0101; 
                5: begin 
							if(funct7==0)
							if_id_alu_control = 4'b0110; 
							else if(funct7==32)
							if_id_alu_control = 4'b0110	;  
					    end
				2: if_id_alu_control = 4'b0100; 
				3: if_id_alu_control = 4'b0100; 
				4: if_id_alu_control = 4'b1000; 
				default: if_id_alu_control=4'b1111;
            endcase
			end
			
			if (opcode==7'b0010011) begin 
				 
		     enable=1;
				if_id_regwrite_control=1;
				if_id_memtoreg=0;
				if_id_alusrc=1;
				if_id_memread=0;
				if_id_memwrite=0;
				if_id_branch=0;
				if_id_branch2=0;
				if_id_jump =0;
				
				case (funct3)
					0: if_id_alu_control = 4'b0000; 
					2: if_id_alu_control = 4'b0100; 
					3: if_id_alu_control = 4'b0100; 
					4: if_id_alu_control = 4'b1000; 
					6: if_id_alu_control = 4'b0010; 
					7: if_id_alu_control = 4'b0011; 
					1: if_id_alu_control = 4'b0101; 
					5: begin
						if (funct7==0)
						if_id_alu_control = 4'b0110; 
					   else if (funct7==32)
						if_id_alu_control = 4'b0110; 
						end
					default: if_id_alu_control=4'b1111;
				endcase
         end
			
			if (opcode==7'b0000011) begin 
		      
		     enable=1;
				if_id_regwrite_control=1;	
				if_id_memtoreg=1;
				if_id_alusrc=1;
				if_id_memread=1;
				if_id_memwrite=0;
				if_id_branch=0;
				if_id_branch2=0;
				if_id_jump=0;
				if_id_alu_control = 4'b0000; 
					
			end
			
			if (opcode==7'b0100011) begin 
				
		    enable=1;
				if_id_regwrite_control=0;
				if_id_memtoreg=1'bx;
				if_id_alusrc=1;
				if_id_memread=0;
				if_id_memwrite=1;
				if_id_branch=0;
				if_id_branch2=0;
				if_id_jump=0;
				if_id_alu_control = 4'b0000; 
					
			end
			
			if (opcode==7'b1100011) begin 
				
		     enable=1;
				if_id_regwrite_control=0;
				if_id_memtoreg=1'b0;
				if_id_alusrc=0;
				if_id_memread=0;
				if_id_memwrite=0;
			
				if_id_jump=0;
				
				case (funct3)
					0: begin if_id_alu_control = 4'b0001; if_id_branch=1;  if_id_branch2=0; end 
					
					1: begin if_id_alu_control = 4'b0001; if_id_branch=0;if_id_branch2=1; end 
					4: if_id_alu_control = 4'b0100; 
					5: if_id_alu_control = 4'b0111; 
					6: if_id_alu_control = 4'b0100; 
					7: if_id_alu_control = 4'b0111; 
					default: if_id_alu_control=4'b1111;
				endcase
			end
			
			if (opcode==7'b1001111)begin
			     
		     enable=1;
				if_id_regwrite_control=1;
				if_id_memtoreg=1'bx;
				if_id_alusrc=1;
				if_id_memread=1;
				if_id_memwrite=0;
				if_id_branch=0;
				if_id_branch2=0;
				if_id_jump=1;
				if_id_alu_control = 4'b0000; 
				end
			if (opcode==7'b1101111) begin
			    
		     enable=1;
				if_id_regwrite_control=1;
				if_id_memtoreg=1'bx;
				if_id_alusrc=1;
				if_id_memread=1;
				if_id_memwrite=0;
				if_id_branch=0;
				if_id_branch2=0;
				if_id_jump=1;
				if_id_alu_control = 4'b0000; 
				end
			
				
			if (opcode==7'b0010111) begin
			    
		     enable=1;
				if_id_regwrite_control=1;
				if_id_memtoreg=1'bx;
				if_id_alusrc=1;
				if_id_memread=1;
				if_id_memwrite=0;
				if_id_branch=0;
				if_id_branch2=0;
				if_id_jump=0;
				if_id_alu_control = 4'b0000; 
				end
				if (opcode==7'b1110011) begin
			    
		     enable=1;
				if_id_regwrite_control=0;
				if_id_memtoreg=1'b0;
				if_id_alusrc=0;
				if_id_memread=0;
				if_id_memwrite=0;
				if_id_branch=0;
				if_id_jump=0;
				if_id_branch2=0;
				if_id_alu_control = 4'b0000; 
				end
			control={enable,if_id_regwrite_control,if_id_alu_control,if_id_alusrc,if_id_memread,if_id_memwrite,if_id_branch,if_id_memtoreg};
    end
 end  

endmodule