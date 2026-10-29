`timescale 1ns / 1ps





















module multiply(input [31:0] in1,in2, 
    input id_ex_enable,
    input[3:0] id_ex_alu_control,
    output reg [31:0] mul_result
   
    );
    wire  [31:0]mulhsu;
wire  [31:0]mulhu;
wire  [31:0]mul;
wire  [31:0]mulh;
wire [31:0] div;
wire [31:0] divu;
wire [31:0] rem;
wire [31:0] remu;

mult_signed_unsigned m1( in1,in2,mulhsu); 
mult_unsigned_unsigned m2(in1,in2,mulhu,mul);
mult_signed m3(in1,in2,mulh);
div d1( in1,in2,divu,remu); 
div_signed d2(in1,in2,div,rem);


always @(*)
begin
if(id_ex_enable==0)
    begin
        case(id_ex_alu_control)
          4'd0: mul_result = mul;   
          4'd1:  mul_result = mulh ; 
          4'd2:  mul_result = mulhsu;
          4'd3:  mul_result = mulhu ; 
          4'd4:  mul_result = divu ; 
          4'd5:  mul_result = remu ; 
          4'd6:  mul_result = div ; 
          4'd7:  mul_result = rem ; 
        endcase
         end
         
        



  else
     mul_result = 32'hz;   
 end
endmodule

module mult_signed_unsigned(
input signed [31:0]in1,
input  [31:0]in2,
output signed [31:0]mulhsu);
wire signed [63:0] prod;
assign prod = in1*$signed({1'b0,in2});
assign mulhsu = prod[63:32];
endmodule

module mult_unsigned_unsigned(
input  [31:0]in1,
input  [31:0]in2,
output  [31:0]mulhu,
output  [31:0] mul);

wire [63:0] prod;
assign prod = in1*in2;
assign mulhu = prod[63:32];
assign mul=prod[31:0];

endmodule

module mult_signed(input signed [31:0]in1, 
input signed [31:0]in2,
output signed [31:0]mulh);
wire signed [63:0] prod;
assign prod = in1*in2;
assign mulh = prod[63:32];
endmodule

module div( 
input  [31:0]in1,
input  [31:0]in2,
output  [31:0]divu,
output  [31:0] remu);


assign divu = in1/in2;
assign remu = in1%in2;



endmodule

module div_signed(input signed [31:0]in1, 
input signed [31:0]in2,
output signed [31:0]div,
output signed  [31:0] rem);

assign div = in1/in2;
assign rem = in1%in2;

endmodule


