`timescale 1ns / 1ps





















module alu(
input [31:0] in1,in2, 
input id_ex_enable,
input[3:0] id_ex_alu_control,

output reg [31:0] alu_result,
    output reg zero_flag
    );
    always @(*)
    
    begin
    
    if(id_ex_enable)
    begin
        
        case(id_ex_alu_control)

        4'b0000: alu_result = in1+in2; 
        4'b0001: alu_result = in1-in2; 
        4'b0010: alu_result = in1|in2; 
        4'b0011: alu_result = in1&in2; 
        4'b0100: begin 
            if(in1<in2) 					  
            alu_result = 1;
            else
            alu_result = 0;
        end
        4'b0101: alu_result = in1<<in2; 
        4'b0110: alu_result = in1>>in2; 
		  4'b0111: begin 
            if(in1>in2) 					  
            alu_result = 1;
            else
            alu_result = 0;
        end
        4'b1000: alu_result = in1^in2;  
		  default: alu_result=1'bz;

        endcase

        
        if (alu_result == 0)
            zero_flag = 1'b1;
        else
            zero_flag = 1'b0;
        
    end
else
begin
alu_result = 32'hz;
zero_flag = 1'bz;
end
end


endmodule

    

