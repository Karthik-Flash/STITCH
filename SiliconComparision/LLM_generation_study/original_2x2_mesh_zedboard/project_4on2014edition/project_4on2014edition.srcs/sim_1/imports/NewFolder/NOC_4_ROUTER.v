`timescale 1ns / 1ps

////////////////////////////////////////////////////////////////////////////////
// Company: 
// Engineer:
//
// Create Date:   22:38:38 04/24/2017
// Design Name:   top_4_router
// Module Name:   C:/cms/NOC/converted/converted/NOC_PROJECT/NOC_4_ROUTER.v
// Project Name:  NOC_PROJECT
// Target Device:  
// Tool versions:  
// Description: 
//
// Verilog Test Fixture created by ISE for module: top_4_router
//
// Dependencies:
// 
// Revision:
// Revision 0.01 - File Created
// Additional Comments:
// 
////////////////////////////////////////////////////////////////////////////////

module NOC_4_ROUTER;

	// Inputs
	reg clk;
	reg clr;
	reg [7:0] current_address_r1;
	reg [7:0] current_address_r2;
	reg [7:0] current_address_r3;
	reg [7:0] current_address_r4;
	reg [31:0] data_in_core_r1;
	reg [31:0] data_in_core_r2;
	reg [31:0] data_in_core_r3;
	reg [31:0] data_in_core_r4;
	reg full_in_core_vc1_r1;
	reg full_in_core_vc2_r1;
	reg full_in_core_vc3_r1;
	reg full_in_core_vc4_r1;
	reg full_in_core_vc1_r2;
	reg full_in_core_vc2_r2;
	reg full_in_core_vc3_r2;
	reg full_in_core_vc4_r2;
	reg full_in_core_vc1_r3;
	reg full_in_core_vc2_r3;
	reg full_in_core_vc3_r3;
	reg full_in_core_vc4_r3;
	reg full_in_core_vc1_r4;
	reg full_in_core_vc2_r4;
	reg full_in_core_vc3_r4;
	reg full_in_core_vc4_r4;

	// Outputs
	wire reset;
	wire [31:0] data_out_core_r1;
	wire [31:0] data_out_core_r2;
	wire [31:0] data_out_core_r3;
	wire [31:0] data_out_core_r4;
	wire full_out_core_vc1_r1;
	wire full_out_core_vc2_r1;
	wire full_out_core_vc3_r1;
	wire full_out_core_vc4_r1;
	wire full_out_core_vc1_r2;
	wire full_out_core_vc2_r2;
	wire full_out_core_vc3_r2;
	wire full_out_core_vc4_r2;
	wire full_out_core_vc1_r3;
	wire full_out_core_vc2_r3;
	wire full_out_core_vc3_r3;
	wire full_out_core_vc4_r3;
	wire full_out_core_vc1_r4;
	wire full_out_core_vc2_r4;
	wire full_out_core_vc3_r4;
	wire full_out_core_vc4_r4;

	// Instantiate the Unit Under Test (UUT)
	top_4_router uut (
		.clk(clk), 
		.clr(clr), 
		.current_address_r1(current_address_r1), 
		.current_address_r2(current_address_r2), 
		.current_address_r3(current_address_r3), 
		.current_address_r4(current_address_r4), 
		.data_in_core_r1(data_in_core_r1), 
		.data_in_core_r2(data_in_core_r2), 
		.data_in_core_r3(data_in_core_r3), 
		.data_in_core_r4(data_in_core_r4), 
		.full_in_core_vc1_r1(full_in_core_vc1_r1), 
		.full_in_core_vc2_r1(full_in_core_vc2_r1), 
		.full_in_core_vc3_r1(full_in_core_vc3_r1), 
		.full_in_core_vc4_r1(full_in_core_vc4_r1), 
		.full_in_core_vc1_r2(full_in_core_vc1_r2), 
		.full_in_core_vc2_r2(full_in_core_vc2_r2), 
		.full_in_core_vc3_r2(full_in_core_vc3_r2), 
		.full_in_core_vc4_r2(full_in_core_vc4_r2), 
		.full_in_core_vc1_r3(full_in_core_vc1_r3), 
		.full_in_core_vc2_r3(full_in_core_vc2_r3), 
		.full_in_core_vc3_r3(full_in_core_vc3_r3), 
		.full_in_core_vc4_r3(full_in_core_vc4_r3), 
		.full_in_core_vc1_r4(full_in_core_vc1_r4), 
		.full_in_core_vc2_r4(full_in_core_vc2_r4), 
		.full_in_core_vc3_r4(full_in_core_vc3_r4), 
		.full_in_core_vc4_r4(full_in_core_vc4_r4), 
		.reset(reset), 
		.data_out_core_r1(data_out_core_r1), 
		.data_out_core_r2(data_out_core_r2), 
		.data_out_core_r3(data_out_core_r3), 
		.data_out_core_r4(data_out_core_r4), 
		.full_out_core_vc1_r1(full_out_core_vc1_r1), 
		.full_out_core_vc2_r1(full_out_core_vc2_r1), 
		.full_out_core_vc3_r1(full_out_core_vc3_r1), 
		.full_out_core_vc4_r1(full_out_core_vc4_r1), 
		.full_out_core_vc1_r2(full_out_core_vc1_r2), 
		.full_out_core_vc2_r2(full_out_core_vc2_r2), 
		.full_out_core_vc3_r2(full_out_core_vc3_r2), 
		.full_out_core_vc4_r2(full_out_core_vc4_r2), 
		.full_out_core_vc1_r3(full_out_core_vc1_r3), 
		.full_out_core_vc2_r3(full_out_core_vc2_r3), 
		.full_out_core_vc3_r3(full_out_core_vc3_r3), 
		.full_out_core_vc4_r3(full_out_core_vc4_r3), 
		.full_out_core_vc1_r4(full_out_core_vc1_r4), 
		.full_out_core_vc2_r4(full_out_core_vc2_r4), 
		.full_out_core_vc3_r4(full_out_core_vc3_r4), 
		.full_out_core_vc4_r4(full_out_core_vc4_r4)
	);

        
    always #5 
        clk = ~clk;

	initial begin
		// Initialize Inputs
		clk=1;
		 clr = 1;
		
		current_address_r1 = 8'b00000000;
		current_address_r2 = 8'b00000001;
		current_address_r3 = 8'b00010000;
		current_address_r4 = 8'b00010001;
		data_in_core_r1 = 32'b001100000000000000000000000000000;
		data_in_core_r2 = 32'b001100000000000000000000000000000;
		data_in_core_r3 = 32'b001100000000000000000000000000000;
		data_in_core_r4 = 32'b001100000000000000000000000000000;
		full_in_core_vc1_r1 = 0;
		full_in_core_vc2_r1 = 0;
		full_in_core_vc3_r1 = 0;
		full_in_core_vc4_r1 = 0;
		full_in_core_vc1_r2 = 0;
		full_in_core_vc2_r2 = 0;
		full_in_core_vc3_r2 = 0;
		full_in_core_vc4_r2 = 0;
		full_in_core_vc1_r3 = 0;
		full_in_core_vc2_r3 = 0;
		full_in_core_vc3_r3 = 0;
		full_in_core_vc4_r3 = 0;
		full_in_core_vc1_r4 = 0;
		full_in_core_vc2_r4 = 0;
		full_in_core_vc3_r4 = 0;
		full_in_core_vc4_r4 = 0;

		// Wait 100 ns for global reset to finish
		#100;
		
		clr=0;
		#50;
		//data_in_core_r1 = 32'b00010001000000000000000000010100;
		data_in_core_r1 = 32'b00101000000000000000000000010001;
	//	data_in_core_r2 = 32'b000110000000000000000000000010001;
	//	data_in_core_r3 = 32'b000100000000000000000011100000000;
	//	data_in_core_r4 = 32'b000100000000000000000111100010000;
#20;


clr=0;
  data_in_core_r1=32'b00001000000010000000000000010001;
//data_in_core_r2=32'b000010000000000000000000000001000;
//data_in_core_r3=32'b000000000000000000000000000010001;
//data_in_core_r4=32'b000000000000000000000000000011101;

#10;
clr=0;
  data_in_core_r1=32'b01001000000000000000000000010001;
//data_in_core_r2=32'b000010000000000000000000000001001;
//data_in_core_r3=32'b000000000000000000000000000000010;
//data_in_core_r4=32'b000000000000000000000000000000010;
#10;
clr=0;
data_in_core_r1=32'b1111111111111111111111111111111;
#50;
		//data_in_core_r1 = 32'b00010001000000000000000000010100;
		data_in_core_r1 = 32'b00110000000000000000000000010001;
	//	data_in_core_r2 = 32'b000110000000000000000000000010001;
	//	data_in_core_r3 = 32'b000100000000000000000011100000000;
	//	data_in_core_r4 = 32'b000100000000000000000111100010000;
#20;


clr=0;
  data_in_core_r1=32'b00010000000010000000000000010001;
//data_in_core_r2=32'b000010000000000000000000000001000;
//data_in_core_r3=32'b000000000000000000000000000010001;
//data_in_core_r4=32'b000000000000000000000000000011101;

#10;
clr=0;
  data_in_core_r1=32'b01010000000000000000000000010001;
//data_in_core_r2=32'b000010000000000000000000000001001;
//data_in_core_r3=32'b000000000000000000000000000000010;
//data_in_core_r4=32'b000000000000000000000000000000010;

#10;
//clr=0;
//data_in_core_r1=32'b1111111111111111111111111111111;
//data_in_core_r1=32'b000001000000000000000000000000011;
//data_in_core_r2=32'b000010000000000000000000000001010;
//data_in_core_r3=32'b000000000000000000000000000000011;
//data_in_core_r4=32'b000000000000000000000000000000011;

//#10
//clr=0;
//data_in_core_r1=32'b000001000000000000000000000000100;
//data_in_core_r2=32'b000010000000000000000000000001011;
//data_in_core_r3=32'b000000000000000000000000000000100;
//data_in_core_r4=32'b000000000000000000000000000000100;

///#10

//data_in_core_r1=32'b000001000000000000000000000000101;
//data_in_core_r2=32'b000010000000000000000000000000101;
//data_in_core_r3=32'b000000000000000000000000000000101;
//data_in_core_r4=32'b000000000000000000000000000000101;

//#10

//data_in_core_r1=32'b000001000000000000000000000000110;
//data_in_core_r2=32'b000010000000000000000000000000110;
//data_in_core_r3=32'b000000000000000000000000000000110;
//data_in_core_r4=32'b000000000000000000000000000000110;

//#10

//data_in_core_r1=32'b000001000000000000000000000000111;
//data_in_core_r2=32'b000010000000000000000000000000111;
//data_in_core_r3=32'b000000000000000000000000000000111;
//data_in_core_r4=32'b000000000000000000000000000000111;


        
		// Add stimulus here

end
      
endmodule


