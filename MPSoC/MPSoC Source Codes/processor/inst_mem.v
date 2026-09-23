
//////////////////////////////////////////////////////////////////////////////////
// Company: 
// Engineer: 
// 
// Create Date:    16:18:15 03/27/2021 
// Design Name: 
// Module Name:    inst_mem 
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
`timescale 1ns / 1ps

module inst_mem (
    input [31:0]inst_add,
    input reset,
    
    output reg [31:0] inst_code
);

// byte addressable memory with 32 locations
reg [7:0] Memory [55:0];
//wire [4:0] shamt = imm_val;

// r-type instructions: add, sub, sll, slt, sltu, xor, srl, sra, or, and
always @(reset)
    begin
        if(reset == 1)
        begin
        
        
        Memory[3] = 8'h02;    //multiply rs1 and rs2 and result rs5
                    Memory[2] = 8'h11;
                    Memory[1] = 8'h02;
                    Memory[0] = 8'hb3;
                    
                     Memory[7] = 8'h00;
                    Memory[6] = 8'h54;
                    Memory[5] = 8'ha0;
                    Memory[4] = 8'h23; 
                    
                   
                // Setting 32-bit instruction: addi s0,zero,10
                   /* Memory[3] = 8'h00;
                    Memory[2] = 8'hA0;
                    Memory[1] = 8'h04;
                    Memory[0] = 8'h13;
       /*  Memory[3] = 8'h00;
            Memory[2] = 8'hA0;
            Memory[1] = 8'h04;
            Memory[0] = 8'h13;
            
             Memory[7] = 8'h00;
            Memory[6] = 8'h04;
            Memory[5] = 8'h10;
            Memory[4] = 8'h63; 
        // Setting 32-bit instruction: addi s0,zero,10
            Memory[3] = 8'h00;
            Memory[2] = 8'hA0;
            Memory[1] = 8'h04;
            Memory[0] = 8'h13; 
          // Setting 32-bit instruction: addi s1,s1,1
            Memory[7] = 8'h00;
            Memory[6] = 8'h14;
            Memory[5] = 8'h84;
            Memory[4] = 8'h93;
           // Setting 32-bit instruction : lw t0, 0(s1)
            Memory[11] = 8'h00;
            Memory[10] = 8'h04;
            Memory[9] = 8'ha2;
            Memory[8] = 8'h83;
            // beq s0,zero,exit
            Memory[15] = 8'h00;
            Memory[14] = 8'h80;
            Memory[13] = 8'h06;
            Memory[12] = 8'h63; 
            // addi t0,t0,5
            Memory[19] = 8'h00;
				Memory[18] = 8'h52;
				Memory[17] = 8'h82;
				Memory[16] = 8'h93;
				//sw t0,0(s1)
				Memory[23] = 8'h00;
            Memory[22] = 8'h54;
            Memory[21] = 8'ha0;
            Memory[20] = 8'h23;
			
      // Setting 32-bit instruction:  addi, s1,s1,1
            Memory[27] = 8'h00;
            Memory[26] = 8'h14;
            Memory[25] = 8'h84;
            Memory[24] = 8'h93; 
            //addi s0,s0,-1
				Memory[31] = 8'hff;
				Memory[30] = 8'hf4;
				Memory[29] = 8'h04;
				Memory[28] = 8'h13;
				//bne zero,s0,loop
				Memory[35] = 8'hfe;
				Memory[34] = 8'h04;
				Memory[33] = 8'h1a;
				Memory[32] = 8'he3;
				//beq s0,s0,exit
				Memory[39] = 8'h04;
				Memory[38] = 8'h84;
				Memory[37] = 8'h04;
				Memory[36] = 8'h63;
				
				//end of program 
          // Setting 32-bit instruction: 13: addi t0,t0,5
            Memory[19] = 8'h00;
            Memory[18] = 8'h52;
            Memory[17] = 8'h82;
            Memory[16] = 8'h93;  
           // Setting 32-bit instruction: 15: sw t0,0(s1)
            Memory[19] = 8'h00;
            Memory[18] = 8'h54;
            Memory[17] = 8'ha0;
            Memory[16] = 8'h23;
           
			                  // 16 addi s1,s1,1
				Memory[23] = 8'h00;
            Memory[22] = 8'h14;
            Memory[21] = 8'ha4;
            Memory[20] = 8'h93;
            // 17 addi s0,s0,-1
            Memory[31] = 8'hff;
            Memory[30] = 8'hf4;
            Memory[29] = 8'h04;
            Memory[28] = 8'h13;
	    // 18 bne zero,s0,loop
				Memory[35] = 8'h00;
				Memory[34] = 8'h80;
				Memory[33] = 8'h18;
				Memory[32] = 8'h63;
				//19 exit : beq s0,s0,exit
				Memory[15] = 8'h00;
				Memory[14] = 8'h84;
				Memory[13] = 8'h0c;
				Memory[12] = 8'h63;
				//21 bne zero,s0,loop
				Memory[43] = 8'hfe;
				Memory[42] = 8'h80;
				Memory[41] = 8'h14;
				Memory[40] = 8'he3;
				// 22 exit:ecall
				Memory[47] = 8'h00;
				Memory[46] = 8'h00;
				Memory[45] = 8'h00;
				Memory[44] = 8'h73; */ 
				

				
        end
	end
	
	
    // making instruction code
    always @(inst_add )
    begin
	 //extend[20:1] <= {{8{imm_val[11]}},imm_val[11:0]}; 
        case(inst_add)
		  // R-type instructions
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
			/* 40: inst_code = {Memory[inst_add+3], Memory[inst_add+2], Memory[inst_add+1], Memory[inst_add]};
			44: inst_code = {Memory[inst_add+3], Memory[inst_add+2], Memory[inst_add+1], Memory[inst_add]}; 
			//48: inst_code = {Memory[inst_add+3], Memory[inst_add+2], Memory[inst_add+1], Memory[inst_add]};
			//52: inst_code = {Memory[inst_add+3], Memory[inst_add+2], Memory[inst_add+1], Memory[inst_add]}; */
			
			
		
	/*	//I-type instructions
			  140: inst_code = {imm_val,5'b01000,3'b000,5'b00101,7'b0010011}; //addi t0, s0, imm 
			  144: inst_code = {imm_val,5'b00101,3'b010,5'b00110,7'b0010011}; //slti t1, s1, imm
			  148: inst_code = {imm_val,5'b10010,3'b011,5'b00111,7'b0010011}; //sltiu t2, s2, imm 
			  152: inst_code = {imm_val,5'b10011,3'b100,5'b11100,7'b0010011}; //ori t3, s3, imm
			  56: inst_code = {imm_val,5'b10100,3'b110,5'b11101,7'b0010011}; //xori t4, s4, imm
			  60: inst_code = {imm_val,5'b10101,3'b111,5'b11110,7'b0010011}; //andi t5, s5, imm
			  64: inst_code = {7'b0000000,shamt,5'b01010,3'b001,5'b10111,7'b0010011}; //slli s7, a0
			  68: inst_code = {7'b0000000,shamt,5'b01011,3'b101,5'b11000,7'b0010011}; //srli s8, a1
			  72: inst_code = {7'b0100000,shamt,5'b01100,3'b101,5'b11001,7'b0010011}; //srai s9, a2
			  
			  
			 76: inst_code = {imm_val[11:5],5'b00101,5'b00100,3'b010,imm_val[4:0],7'b0100011}; //sw t0, s3, imm = 12
			  80: inst_code = {imm_val,5'b00100,3'b010,5'b00110,7'b0000011}; // lw t1, s3, imm = 12
			
			
			  84: inst_code = {imm_val[11],imm_val[10:5],5'b00110,5'b00101,3'b001,imm_val[4:1],imm_val[11],7'b1100011}; //bne t1,s1,imm  */
/*			  
			//S-type instructions
			  76: inst_code = {imm_val[11:5],5'b11100,5'b10011,3'b010,imm_val[4:0],7'b0100011};//sw s3, t3, imm
			  80: inst_code = {imm_val[11:5],5'b11100,5'b10011,3'b001,imm_val[4:0],7'b0100011}; //sh s3, t3, imm
			  84: inst_code = {imm_val[11:5],5'b11100,5'b10011,3'b000,imm_val[4:0],7'b0100011}; //sb s3, t3, imm */
			
		/*	//Jump instructions
			  88: inst_code = {imm_val, 5'b00111, 3'b000, 5'b10010, 7'b1100111}; //jalr t2, s2, imm
			  92: inst_code = {imm_20[20],imm_20[10:1],imm_20[11],imm_20[19:12],5'b00111,7'b1101111}; //jal t2, imm */
			
		/*	//Load instructions
			  96: inst_code = {imm_val,5'b00101,3'b000,5'b00100,7'b0000011}; // lb 
			  100: inst_code = {imm_val,5'b00101,3'b001,5'b00100,7'b0000011}; // lh
			  104: inst_code = {imm_val,5'b00101,3'b010,5'b00100,7'b0000011}; // lw
			  108: inst_code = {imm_val,5'b00101,3'b100,5'b00100,7'b0000011}; // lbu
			  112: inst_code = {imm_val,5'b00101,3'b101,5'b00100,7'b0000011}; // lhu */
			
			// branch instructions
			  //0: inst_code = {imm_val[11],imm_val[9:4],5'b00110,5'b00101,3'b000,imm_val[3:0],imm_val[10],7'b1100011}; //beq t1,s1,imm
			 // 120: inst_code = {imm_val[11],imm_val[9:4],5'b00110,5'b00101,3'b001,imm_val[3:0],imm_val[10],7'b1100011}; //bne t1,s1,imm
			//  124: inst_code = {imm_val[11],imm_val[9:4],5'b00110,5'b00101,3'b010,imm_val[3:0],imm_val[10],7'b1100011}; //blt t1,s1,imm
   		//  128: inst_code = {imm_val[11],imm_val[9:4],5'b00110,5'b00101,3'b100,imm_val[3:0],imm_val[10],7'b1100011}; //bge t1,s1,imm
			//  132: inst_code = {imm_val[11],imm_val[9:4],5'b00110,5'b00101,3'b101,imm_val[3:0],imm_val[10],7'b1100011}; //bltu t1,s1,imm
			//  136: inst_code = {imm_val[11],imm_val[9:4],5'b00110,5'b00101,3'b110,imm_val[3:0],imm_val[10],7'b1100011}; //bgeu t1,s1,imm
			
		/*	// U-type instructions
			  140: inst_code = {imm_32[31:12],5'b00111,7'b0110111}; //lui t2, imm
			  144: inst_code = {imm_32[31:12],5'b00111,7'b0010111}; //auipc t2, imm
	*/
				
		  endcase
	 end  	 

endmodule
