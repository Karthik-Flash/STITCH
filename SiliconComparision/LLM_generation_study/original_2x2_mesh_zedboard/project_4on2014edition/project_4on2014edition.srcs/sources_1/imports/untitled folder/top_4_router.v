 `timescale 1ns / 1ps

module top_4_router(
input clk, clr,
input [7:0] current_address_r1, current_address_r2, current_address_r3, current_address_r4,
input [31:0] data_in_core_r1, data_in_core_r2, data_in_core_r3, data_in_core_r4,
input full_in_core_vc1_r1, full_in_core_vc2_r1, full_in_core_vc3_r1, full_in_core_vc4_r1,
input full_in_core_vc1_r2, full_in_core_vc2_r2, full_in_core_vc3_r2, full_in_core_vc4_r2,
input full_in_core_vc1_r3, full_in_core_vc2_r3, full_in_core_vc3_r3, full_in_core_vc4_r3,
input full_in_core_vc1_r4, full_in_core_vc2_r4, full_in_core_vc3_r4, full_in_core_vc4_r4,

			
output reset,
output [31:0] data_out_core_r1, data_out_core_r2, data_out_core_r3, data_out_core_r4,
output full_out_core_vc1_r1, full_out_core_vc2_r1, full_out_core_vc3_r1, full_out_core_vc4_r1,
output full_out_core_vc1_r2, full_out_core_vc2_r2, full_out_core_vc3_r2, full_out_core_vc4_r2,
output full_out_core_vc1_r3, full_out_core_vc2_r3, full_out_core_vc3_r3, full_out_core_vc4_r3,
output full_out_core_vc1_r4, full_out_core_vc2_r4, full_out_core_vc3_r4, full_out_core_vc4_r4
);
wire gnd;
wire vdd;
assign gnd=0;
assign vdd=1;


/*
sc_in<bool> clk, clr;
sc_in<sc_uint<8> > current_address_r1, current_address_r2, current_address_r3, current_address_r4;
sc_in<sc_uint<32> >  data_in_core_r1, data_in_core_r2, data_in_core_r3, data_in_core_r4;
sc_signal<sc_uint<32> > temp_inval;
sc_in<bool> full_in_core_vc1_r1, full_in_core_vc2_r1, full_in_core_vc3_r1, full_in_core_vc4_r1;
sc_in<bool> full_in_core_vc1_r2, full_in_core_vc2_r2, full_in_core_vc3_r2, full_in_core_vc4_r2;
sc_in<bool> full_in_core_vc1_r3, full_in_core_vc2_r3, full_in_core_vc3_r3, full_in_core_vc4_r3;
sc_in<bool> full_in_core_vc1_r4, full_in_core_vc2_r4, full_in_core_vc3_r4, full_in_core_vc4_r4;

//sc_out<bool> reset_r1,reset_r2,reset_r3,reset_r4;
sc_signal<bool> reset_r1,reset_r2,reset_r3,reset_r4;
sc_out<sc_uint<32> > data_out_core_r1, data_out_core_r2, data_out_core_r3, data_out_core_r4;
sc_out<bool> full_out_core_vc1_r1, full_out_core_vc2_r1, full_out_core_vc3_r1, full_out_core_vc4_r1;
sc_out<bool> full_out_core_vc1_r2, full_out_core_vc2_r2, full_out_core_vc3_r2, full_out_core_vc4_r2;
sc_out<bool> full_out_core_vc1_r3, full_out_core_vc2_r3, full_out_core_vc3_r3, full_out_core_vc4_r3;
sc_out<bool> full_out_core_vc1_r4, full_out_core_vc2_r4, full_out_core_vc3_r4, full_out_core_vc4_r4;

sc_signal<bool> gnd,vdd;*/

wire [31:0]data_out_link1_r1, data_out_link3_r1, data_out_link1_r2, data_out_link4_r2,
				 data_out_link2_r3, data_out_link3_r3, data_out_link2_r4, data_out_link4_r4,
				 data_out_link3_r2,data_out_link1_r3,data_out_link3_r4;
			
wire [31:0]data_out_link1, data_out_link2, data_out_link3, data_out_link4;	
                 
    

wire full_out_link1_vc1_r1, full_out_link1_vc2_r1, full_out_link1_vc3_r1,full_out_link1_vc4_r1,
full_out_link3_vc1_r1, full_out_link3_vc2_r1, full_out_link3_vc3_r1, full_out_link3_vc4_r1,
full_out_link1_vc1_r2, full_out_link1_vc2_r2, full_out_link1_vc3_r2, full_out_link1_vc4_r2,
full_out_link4_vc1_r2, full_out_link4_vc2_r2, full_out_link4_vc3_r2, full_out_link4_vc4_r2,
full_out_link2_vc1_r3, full_out_link2_vc2_r3, full_out_link2_vc3_r3, full_out_link2_vc4_r3, 
full_out_link3_vc1_r3, full_out_link3_vc2_r3, full_out_link3_vc3_r3, full_out_link3_vc4_r3,
full_out_link2_vc1_r4, full_out_link2_vc2_r4, full_out_link2_vc3_r4, full_out_link2_vc4_r4,
full_out_link4_vc1_r4, full_out_link4_vc2_r4, full_out_link4_vc3_r4, full_out_link4_vc4_r4; 



/*sc_signal<sc_uint<32> >  data_out_link1_r1, data_out_link3_r1, data_out_link1_r2, data_out_link4_r2,
				 data_out_link2_r3, data_out_link3_r3, data_out_link2_r4, data_out_link4_r4;

//sc_out<sc_uint<32> >  data_out_link1_r1, data_out_link3_r1, data_out_link1_r2, data_out_link4_r2;
				 //data_out_link2_r3, data_out_link3_r3, data_out_link2_r4, data_out_link4_r4;    

sc_signal<bool> full_out_link1_vc1_r1, full_out_link1_vc2_r1, full_out_link1_vc3_r1,full_out_link1_vc4_r1,
		full_out_link3_vc1_r1, full_out_link3_vc2_r1, full_out_link3_vc3_r1, full_out_link3_vc4_r1,
		full_out_link1_vc1_r2, full_out_link1_vc2_r2, full_out_link1_vc3_r2, full_out_link1_vc4_r2,
		full_out_link4_vc1_r2, full_out_link4_vc2_r2, full_out_link4_vc3_r2, full_out_link4_vc4_r2,
		full_out_link2_vc1_r3, full_out_link2_vc2_r3, full_out_link2_vc3_r3, full_out_link2_vc4_r3, 
		full_out_link3_vc1_r3, full_out_link3_vc2_r3, full_out_link3_vc3_r3, full_out_link3_vc4_r3,
		full_out_link2_vc1_r4, full_out_link2_vc2_r4, full_out_link2_vc3_r4, full_out_link2_vc4_r4,
		full_out_link4_vc1_r4, full_out_link4_vc2_r4, full_out_link4_vc3_r4, full_out_link4_vc4_r4; 
//////////////////////////////////////////////////////////////////////////////////////////////////////
////extra..........................*/
wire temp_outval2_r1,temp_outval4_r1,temp_outval2_r2,temp_outval3_r2,temp_outval1_r3,temp_outval4_r3,temp_outval1_r4,temp_outval3_r4;

wire	false_val2_1_r1,false_val2_2_r1,false_val2_3_r1,false_val2_4_r1,
		false_val4_1_r1,false_val4_2_r1,false_val4_3_r1,false_val4_4_r1,		
		false_val2_1_r2,false_val2_2_r2,false_val2_3_r2,false_val2_4_r2,
		false_val3_1_r2,false_val3_2_r2,false_val3_3_r2,false_val3_4_r2,
		false_val1_1_r3,false_val1_2_r3,false_val1_3_r3,false_val1_4_r3,
		false_val4_1_r3,false_val4_2_r3,false_val4_3_r3,false_val4_4_r3,
		false_val1_1_r4,false_val1_2_r4,false_val1_3_r4,false_val1_4_r4,
		false_val3_1_r4,false_val3_2_r4,false_val3_3_r4,false_val3_4_r4;





assign gnd=0;
assign vdd =1;
assign temp_inval = 32'b01100000000000000000000000000000;
	


top_module r1(
    .data_in_link1(data_out_link2_r3), 
    .data_in_link2(32'b01100000000000000000000000000000), 
    .data_in_link3(data_out_link4_r2), 
    .data_in_link4(32'b01100000000000000000000000000000), 
    .data_in_core(data_in_core_r1), 
    .clk(clk), 
    .clr(clr), 
    .reset(reset), 
    .current_address(current_address_r1), 
    .full_in_link1_vc1(full_out_link2_vc1_r3), 
    .full_in_link1_vc2(full_out_link2_vc2_r3), 
    .full_in_link1_vc3(full_out_link2_vc3_r3), 
    .full_in_link1_vc4(full_out_link2_vc4_r3), 
    .full_in_link2_vc1(gnd), 
    .full_in_link2_vc2(gnd), 
    .full_in_link2_vc3(gnd), 
    .full_in_link2_vc4(gnd), 
    .full_in_link3_vc1(full_out_link4_vc1_r2), 
    .full_in_link3_vc2(full_out_link4_vc2_r2), 
    .full_in_link3_vc3(full_out_link4_vc3_r2), 
    .full_in_link3_vc4(full_out_link4_vc4_r2), 
    .full_in_link4_vc1(gnd), 
    .full_in_link4_vc2(gnd), 
    .full_in_link4_vc3(gnd), 
    .full_in_link4_vc4(gnd), 
    .full_in_core_vc1(full_in_core_vc1_r1), 
    .full_in_core_vc2(full_in_core_vc2_r1), 
    .full_in_core_vc3(full_in_core_vc3_r1), 
    .full_in_core_vc4(full_in_core_vc4_r1), 
    .data_out_link1(data_out_link1_r1), 
   .data_out_link2(data_out_link2), 
    .data_out_link3(data_out_link3_r1), 
  .data_out_link4(data_out_link4), 
    .data_out_core(data_out_core_r1), 
    .full_out_link1_vc1(full_out_link1_vc1_r1), 
    .full_out_link1_vc2(full_out_link1_vc2_r1), 
    .full_out_link1_vc3(full_out_link1_vc3_r1), 
    .full_out_link1_vc4(full_out_link1_vc4_r1), 
   .full_out_link2_vc1(full_out_link2_vc1), 
   .full_out_link2_vc2(full_out_link2_vc2), 
  .full_out_link2_vc3(full_out_link2_vc3), 
   .full_out_link2_vc4(full_out_link2_vc4), 
    .full_out_link3_vc1(full_out_link3_vc1_r1),
    .full_out_link3_vc2(full_out_link3_vc2_r1),
    .full_out_link3_vc3(full_out_link3_vc3_r1),
    .full_out_link3_vc4(full_out_link3_vc4_r1),
  .full_out_link4_vc1(full_out_link4_vc1), 
  .full_out_link4_vc2(full_out_link4_vc2), 
   .full_out_link4_vc3(full_out_link4_vc3), 
    .full_out_link4_vc4(full_out_link4_vc4), 
    .full_out_core_vc1(full_out_core_vc1_r1), 
    .full_out_core_vc2(full_out_core_vc2_r1), 
    .full_out_core_vc3(full_out_core_vc3_r1), 
    .full_out_core_vc4(full_out_core_vc4_r1)
    );


    /*r1(data_in_link1(data_out_link2_r3), 
    data_in_link2(temp_inval),
    data_in_link3(data_out_link4_r2),
    data_in_link4(temp_inval),
    data_in_core(data_in_core_r1),
    clk(clk),
    clr(clr),
    reset(reset_r1), // mod
    current_address(current_address_r1),
    full_in_link1_vc1(full_out_link2_vc1_r3), 
    full_in_link1_vc2(full_out_link2_vc2_r3), 
    full_in_link1_vc3(full_out_link2_vc3_r3), 
    full_in_link1_vc4(full_out_link2_vc4_r3), 
    full_in_link2_vc1(gnd), 
    full_in_link2_vc2(gnd), 
    full_in_link2_vc3(gnd), 
    full_in_link2_vc4(gnd), 
    full_in_link3_vc1(full_out_link4_vc1_r2), 
    full_in_link3_vc2(full_out_link4_vc2_r2), 
    full_in_link3_vc3(full_out_link4_vc3_r2), 
    full_in_link3_vc4(full_out_link4_vc4_r2), 
    full_in_link4_vc1(gnd), 
    full_in_link4_vc2(gnd), 
    full_in_link4_vc3(gnd), 
    full_in_link4_vc4(gnd), 
    full_in_core_vc1(full_in_core_vc1_r1), 
    full_in_core_vc2(full_in_core_vc2_r1), 
    full_in_core_vc3(full_in_core_vc3_r1), 
    full_in_core_vc4(full_in_core_vc4_r1), 
    data_out_link1(data_out_link1_r1),
    data_out_link2(temp_outval2_r1), // mod
    data_out_link3(data_out_link3_r1), 
    data_out_link4(temp_outval4_r1), // mod
    data_out_core(data_out_core_r1), 
    full_out_link1_vc1(full_out_link1_vc1_r1), 
    full_out_link1_vc2(full_out_link1_vc2_r1), 
    full_out_link1_vc3(full_out_link1_vc3_r1), 
    full_out_link1_vc4(full_out_link1_vc4_r1), 
    full_out_link2_vc1(false_val2_1_r1), // mod
    full_out_link2_vc2(false_val2_2_r1), // mod
    full_out_link2_vc3(false_val2_3_r1), // mod
    full_out_link2_vc4(false_val2_4_r1), // mod
    full_out_link3_vc1(full_out_link3_vc1_r1),
    full_out_link3_vc2(full_out_link3_vc2_r1),
    full_out_link3_vc3(full_out_link3_vc3_r1),
    full_out_link3_vc4(full_out_link3_vc4_r1),
    full_out_link4_vc1(false_val4_1_r1), // mod
    full_out_link4_vc2(false_val4_2_r1), // mod
    full_out_link4_vc3(false_val4_3_r1), // mod
    full_out_link4_vc4(false_val4_4_r1), // mod
    full_out_core_vc1(full_out_core_vc1_r1), 
    full_out_core_vc2(full_out_core_vc2_r1), 
    full_out_core_vc3(full_out_core_vc3_r1), 
    full_out_core_vc4(full_out_core_vc4_r1));*/
   
top_module r2(
    .data_in_link1(data_out_link2_r4), 
    .data_in_link2(32'b01100000000000000000000000000000), 
    .data_in_link3(32'b01100000000000000000000000000000), 
    .data_in_link4(data_out_link3_r1), 
    .data_in_core(data_in_core_r2), 
    .clk(clk), 
    .clr(clr), 
   .reset(reset), 
    .current_address(current_address_r2), 
    .full_in_link1_vc1(full_out_link2_vc1_r4), 
    .full_in_link1_vc2(full_out_link2_vc2_r4), 
    .full_in_link1_vc3(full_out_link2_vc3_r4), 
    .full_in_link1_vc4(full_out_link2_vc4_r4), 
    .full_in_link2_vc1(gnd), 
    .full_in_link2_vc2(gnd), 
    .full_in_link2_vc3(gnd), 
    .full_in_link2_vc4(gnd), 
    .full_in_link3_vc1(gnd), 
    .full_in_link3_vc2(gnd), 
    .full_in_link3_vc3(gnd), 
    .full_in_link3_vc4(gnd), 
    .full_in_link4_vc1(full_out_link3_vc1_r1), 
    .full_in_link4_vc2(full_out_link3_vc2_r1), 
    .full_in_link4_vc3(full_out_link3_vc3_r1), 
    .full_in_link4_vc4(full_out_link3_vc4_r1), 
    .full_in_core_vc1(full_in_core_vc1_r2), 
    .full_in_core_vc2(full_in_core_vc2_r2), 
    .full_in_core_vc3(full_in_core_vc3_r2), 
    .full_in_core_vc4(full_in_core_vc4_r2), 
    .data_out_link1(data_out_link1_r2), 
    .data_out_link2(data_out_link2), 
    .data_out_link3(data_out_link3_r2), 
    .data_out_link4(data_out_link4_r2), 
    .data_out_core(data_out_core_r2), 
    .full_out_link1_vc1(full_out_link1_vc1_r2), 
    .full_out_link1_vc2(full_out_link1_vc2_r2), 
    .full_out_link1_vc3(full_out_link1_vc3_r2), 
    .full_out_link1_vc4(full_out_link1_vc4_r2), 
    .full_out_link2_vc1(full_out_link2_vc1), 
  .full_out_link2_vc2(full_out_link2_vc2), 
   .full_out_link2_vc3(full_out_link2_vc3), 
    .full_out_link2_vc4(full_out_link2_vc4), 
   .full_out_link3_vc1(full_out_link3_vc1_r1),
    .full_out_link3_vc2(full_out_link3_vc2_r1),
    .full_out_link3_vc3(full_out_link3_vc3_r1),
    .full_out_link3_vc4(full_out_link3_vc4_r1),
     .full_out_link4_vc1(full_out_link4_vc1_r2), 
     .full_out_link4_vc2(full_out_link4_vc2_r2), 
     .full_out_link4_vc3(full_out_link4_vc3_r2), 
     .full_out_link4_vc4(full_out_link4_vc4_r2), 
    .full_out_core_vc1(full_out_core_vc1_r2), 
    .full_out_core_vc2(full_out_core_vc2_r2), 
    .full_out_core_vc3(full_out_core_vc3_r2), 
    .full_out_core_vc4(full_out_core_vc4_r2)
    );



    /*r2(data_in_link1(data_out_link2_r4), 
    data_in_link2(temp_inval), 
    data_in_link3(temp_inval),
    data_in_link4(data_out_link3_r1),
    data_in_core(data_in_core_r2),
    clk(clk), 
    clr(clr), 
    reset(reset_r2), // mod
    current_address(current_address_r2), 
    full_in_link1_vc1(full_out_link2_vc1_r4), 
    full_in_link1_vc2(full_out_link2_vc2_r4), 
    full_in_link1_vc3(full_out_link2_vc3_r4), 
    full_in_link1_vc4(full_out_link2_vc4_r4), 
    full_in_link2_vc1(gnd), 
    full_in_link2_vc2(gnd), 
    full_in_link2_vc3(gnd), 
    full_in_link2_vc4(gnd), 
    full_in_link3_vc1(gnd), 
    full_in_link3_vc2(gnd), 
    full_in_link3_vc3(gnd), 
    full_in_link3_vc4(gnd), 
    full_in_link4_vc1(full_out_link3_vc1_r1), 
    full_in_link4_vc2(full_out_link3_vc2_r1), 
    full_in_link4_vc3(full_out_link3_vc3_r1), 
    full_in_link4_vc4(full_out_link3_vc4_r1), 
    full_in_core_vc1(full_in_core_vc1_r2), 
    full_in_core_vc2(full_in_core_vc2_r2), 
    full_in_core_vc3(full_in_core_vc3_r2), 
    full_in_core_vc4(full_in_core_vc4_r2), 
    data_out_link1(data_out_link1_r2),
    data_out_link2(temp_outval2_r2), // mod
    data_out_link3(temp_outval3_r2), // mod
    data_out_link4(data_out_link4_r2),
    data_out_core(data_out_core_r2),
    full_out_link1_vc1(full_out_link1_vc1_r2),
    full_out_link1_vc2(full_out_link1_vc2_r2),
    full_out_link1_vc3(full_out_link1_vc3_r2),
    full_out_link1_vc4(full_out_link1_vc4_r2), 
    full_out_link2_vc1(false_val2_1_r2), // mod
    full_out_link2_vc2(false_val2_2_r2), // mod
    full_out_link2_vc3(false_val2_3_r2), // mod
    full_out_link2_vc4(false_val2_4_r2), // mod
    full_out_link3_vc1(false_val3_1_r2),// mod
    full_out_link3_vc2(false_val3_2_r2),// mod
    full_out_link3_vc3(false_val3_3_r2),// mod
    full_out_link3_vc4(false_val3_4_r2),// mod
    full_out_link4_vc1(full_out_link4_vc1_r2), 
    full_out_link4_vc2(full_out_link4_vc2_r2), 
    full_out_link4_vc3(full_out_link4_vc3_r2), 
    full_out_link4_vc4(full_out_link4_vc4_r2), 
    full_out_core_vc1(full_out_core_vc1_r2), 
    full_out_core_vc2(full_out_core_vc2_r2), 
    full_out_core_vc3(full_out_core_vc3_r2), 
    full_out_core_vc4(full_out_core_vc4_r2));*/
    
top_module r3(
    .data_in_link1(32'b01100000000000000000000000000000), 
    .data_in_link2(data_out_link1_r1), 
    .data_in_link3(data_out_link4_r4), 
    .data_in_link4(32'b01100000000000000000000000000000), 
    .data_in_core(data_in_core_r3), 
    .clk(clk), 
    .clr(clr), 
    .reset(reset), 
    .current_address(current_address_r3), 
    .full_in_link1_vc1(gnd), 
    .full_in_link1_vc2(gnd), 
    .full_in_link1_vc3(gnd), 
    .full_in_link1_vc4(gnd), 
    .full_in_link2_vc1(full_out_link1_vc1_r1), 
    .full_in_link2_vc2(full_out_link1_vc2_r1), 
    .full_in_link2_vc3(full_out_link1_vc3_r1), 
    .full_in_link2_vc4(full_out_link1_vc4_r1), 
    .full_in_link3_vc1(full_out_link4_vc1_r4), 
    .full_in_link3_vc2(full_out_link4_vc2_r4), 
    .full_in_link3_vc3(full_out_link4_vc3_r4), 
    .full_in_link3_vc4(full_out_link4_vc4_r4), 
    .full_in_link4_vc1(gnd), 
    .full_in_link4_vc2(gnd), 
    .full_in_link4_vc3(gnd), 
    .full_in_link4_vc4(gnd), 
    .full_in_core_vc1(full_in_core_vc1_r3), 
    .full_in_core_vc2(full_in_core_vc2_r3), 
    .full_in_core_vc3(full_in_core_vc3_r3), 
    .full_in_core_vc4(full_in_core_vc4_r3), 
  // .data_out_link1(data_out_link1_r3), 
  .data_out_link1(data_out_link1),
    .data_out_link2(data_out_link2_r3), 
    .data_out_link3(data_out_link3_r3), 
  .data_out_link4(data_out_link4), 
    .data_out_core(data_out_core_r3), 
    .full_out_link1_vc1(full_out_link1_vc1_r3), 
    .full_out_link1_vc2(full_out_link1_vc2_r3), 
    .full_out_link1_vc3(full_out_link1_vc3_r3), 
    .full_out_link1_vc4(full_out_link1_vc4_r3), 
    .full_out_link2_vc1(full_out_link2_vc1_r3), 
    .full_out_link2_vc2(full_out_link2_vc2_r3), 
    .full_out_link2_vc3(full_out_link2_vc3_r3), 
    .full_out_link2_vc4(full_out_link2_vc4_r3), 
    .full_out_link3_vc1(full_out_link3_vc1_r3),
    .full_out_link3_vc2(full_out_link3_vc2_r3),
    .full_out_link3_vc3(full_out_link3_vc3_r3),
    .full_out_link3_vc4(full_out_link3_vc4_r3),
    .full_out_link4_vc1(full_out_link4_vc1), 
    .full_out_link4_vc2(full_out_link4_vc2), 
    .full_out_link4_vc3(full_out_link4_vc3), 
    .full_out_link4_vc4(full_out_link4_vc4), 
    .full_out_core_vc1(full_out_core_vc1_r3), 
    .full_out_core_vc2(full_out_core_vc2_r3), 
    .full_out_core_vc3(full_out_core_vc3_r3), 
    .full_out_core_vc4(full_out_core_vc4_r3)
    );



    /*r3(data_in_link1(temp_inval), 
    data_in_link2(data_out_link1_r1), 
    data_in_link3(data_out_link4_r4), 
    data_in_link4(temp_inval),
    data_in_core(data_in_core_r3), 
    clk(clk), 
    clr(clr), 
    reset(reset_r3), // mod
    current_address(current_address_r3),
    full_in_link1_vc1(gnd), 
    full_in_link1_vc2(gnd), 
    full_in_link1_vc3(gnd), 
    full_in_link1_vc4(gnd), 
    full_in_link2_vc1(full_out_link1_vc1_r1), 
    full_in_link2_vc2(full_out_link1_vc2_r1), 
    full_in_link2_vc3(full_out_link1_vc3_r1), 
    full_in_link2_vc4(full_out_link1_vc4_r1), 
    full_in_link3_vc1(full_out_link4_vc1_r4), 
    full_in_link3_vc2(full_out_link4_vc2_r4), 
    full_in_link3_vc3(full_out_link4_vc3_r4), 
    full_in_link3_vc4(full_out_link4_vc4_r4), 
    full_in_link4_vc1(gnd), 
    full_in_link4_vc2(gnd), 
    full_in_link4_vc3(gnd), 
    full_in_link4_vc4(gnd), 
    full_in_core_vc1(full_in_core_vc1_r3), 
    full_in_core_vc2(full_in_core_vc2_r3), 
    full_in_core_vc3(full_in_core_vc3_r3), 
    full_in_core_vc4(full_in_core_vc4_r3), 
    data_out_link1(temp_outval1_r3), // mod
    data_out_link2(data_out_link2_r3), 
    data_out_link3(data_out_link3_r3), 
    data_out_link4(temp_outval4_r3), // mod
    data_out_core(data_out_core_r3), 
    full_out_link1_vc1(false_val1_1_r3), // mod
    full_out_link1_vc2(false_val1_2_r3), // mod
    full_out_link1_vc3(false_val1_3_r3), // mod
    full_out_link1_vc4(false_val1_4_r3), // mod
    full_out_link2_vc1(full_out_link2_vc1_r3), 
    full_out_link2_vc2(full_out_link2_vc2_r3), 
    full_out_link2_vc3(full_out_link2_vc3_r3), 
    full_out_link2_vc4(full_out_link2_vc4_r3), 
    full_out_link3_vc1(full_out_link3_vc1_r3),
    full_out_link3_vc2(full_out_link3_vc2_r3),
    full_out_link3_vc3(full_out_link3_vc3_r3),
    full_out_link3_vc4(full_out_link3_vc4_r3),
    full_out_link4_vc1(false_val4_1_r3), // mod
    full_out_link4_vc2(false_val4_2_r3), // mod
    full_out_link4_vc3(false_val4_3_r3), // mod
    full_out_link4_vc4(false_val4_4_r3), // mod
    full_out_core_vc1(full_out_core_vc1_r3), 
    full_out_core_vc2(full_out_core_vc2_r3), 
    full_out_core_vc3(full_out_core_vc3_r3), 
    full_out_core_vc4(full_out_core_vc4_r3));*/
   
top_module r4(
    .data_in_link1(32'b01100000000000000000000000000000), 
    .data_in_link2(data_out_link1_r2), 
    .data_in_link3(32'b01100000000000000000000000000000), 
    .data_in_link4(data_out_link3_r3), 
    .data_in_core(data_in_core_r4), 
    .clk(clk), 
    .clr(clr), 
    .reset(reset), 
    .current_address(current_address_r4), 
    .full_in_link1_vc1(gnd), 
    .full_in_link1_vc2(gnd), 
    .full_in_link1_vc3(gnd), 
    .full_in_link1_vc4(gnd), 
    .full_in_link2_vc1(full_out_link1_vc1_r2), 
    .full_in_link2_vc2(full_out_link1_vc2_r2), 
    .full_in_link2_vc3(full_out_link1_vc3_r2), 
    .full_in_link2_vc4(full_out_link1_vc4_r2), 
    .full_in_link3_vc1(gnd), 
    .full_in_link3_vc2(gnd), 
    .full_in_link3_vc3(gnd), 
    .full_in_link3_vc4(gnd), 
    .full_in_link4_vc1(full_out_link3_vc1_r3), 
    .full_in_link4_vc2(full_out_link3_vc2_r3), 
    .full_in_link4_vc3(full_out_link3_vc3_r3), 
    .full_in_link4_vc4(full_out_link3_vc4_r3), 
    .full_in_core_vc1(full_in_core_vc1_r4), 
    .full_in_core_vc2(full_in_core_vc2_r4), 
    .full_in_core_vc3(full_in_core_vc3_r4), 
    .full_in_core_vc4(full_in_core_vc4_r4), 
   //.data_out_link1(data_out_link1_r2), 
       .data_out_link1(data_out_link1),
        .data_out_link2(data_out_link2_r4), 
        //.data_out_link3(data_out_link3_r4),
         .data_out_link3(data_out_link3), 
    .data_out_link4(data_out_link4_r4), 
    .data_out_core(data_out_core_r4), 
    .full_out_link1_vc1(full_out_link1_vc1_r4), 
    .full_out_link1_vc2(full_out_link1_vc2_r4), 
    .full_out_link1_vc3(full_out_link1_vc3_r4), 
    .full_out_link1_vc4(full_out_link1_vc4_r4), 
    .full_out_link2_vc1(full_out_link2_vc1_r4), 
    .full_out_link2_vc2(full_out_link2_vc2_r4), 
    .full_out_link2_vc3(full_out_link2_vc3_r4), 
    .full_out_link2_vc4(full_out_link2_vc4_r4), 
   .full_out_link3_vc1(full_out_link3_vc1_r1),
   .full_out_link3_vc2(full_out_link3_vc2_r1),
    .full_out_link3_vc3(full_out_link3_vc3_r1),
    .full_out_link3_vc4(full_out_link3_vc4_r1),
     .full_out_link4_vc1(full_out_link4_vc1_r4), 
     .full_out_link4_vc2(full_out_link4_vc2_r4), 
     .full_out_link4_vc3(full_out_link4_vc3_r4), 
     .full_out_link4_vc4(full_out_link4_vc4_r4), 
    .full_out_core_vc1(full_out_core_vc1_r4), 
    .full_out_core_vc2(full_out_core_vc2_r4), 
    .full_out_core_vc3(full_out_core_vc3_r4), 
    .full_out_core_vc4(full_out_core_vc4_r4)
    );
				  



   /* r4(data_in_link1(temp_inval),
    r4.data_in_link2(data_out_link1_r2), 
    data_in_link3(temp_inval),
    data_in_link4(data_out_link3_r3), 
    data_in_core(data_in_core_r4),
    clk(clk), 
    clr(clr), 
    reset(reset_r4),  // mod 
    current_address(current_address_r4), 
    full_in_link1_vc1(gnd), 
    full_in_link1_vc2(gnd), 
    full_in_link1_vc3(gnd), 
    full_in_link1_vc4(gnd), 
    full_in_link2_vc1(full_out_link1_vc1_r2), 
    full_in_link2_vc2(full_out_link1_vc2_r2), 
    full_in_link2_vc3(full_out_link1_vc3_r2), 
    full_in_link2_vc4(full_out_link1_vc4_r2), 
    full_in_link3_vc1(gnd),
    full_in_link3_vc2(gnd),
    full_in_link3_vc3(gnd),
    full_in_link3_vc4(gnd),
    full_in_link4_vc1(full_out_link3_vc1_r3), 
    full_in_link4_vc2(full_out_link3_vc2_r3), 
    full_in_link4_vc3(full_out_link3_vc3_r3), 
    full_in_link4_vc4(full_out_link3_vc4_r3), 
    full_in_core_vc1(full_in_core_vc1_r4),
    full_in_core_vc2(full_in_core_vc2_r4), 
    full_in_core_vc3(full_in_core_vc3_r4), 
    full_in_core_vc4(full_in_core_vc4_r4), 
    data_out_link1(temp_outval1_r4), // mod
    data_out_link2(data_out_link2_r4),
    data_out_link3(temp_outval3_r4), // mod
    data_out_link4(data_out_link4_r4),
    data_out_core(data_out_core_r4), 
    full_out_link1_vc1(false_val1_1_r4),// mod 
    full_out_link1_vc2(false_val1_2_r4), // mod
    full_out_link1_vc3(false_val1_3_r4), // mod
    full_out_link1_vc4(false_val1_4_r4), // mod
    full_out_link2_vc1(full_out_link2_vc1_r4), 
    full_out_link2_vc2(full_out_link2_vc2_r4), 
    full_out_link2_vc3(full_out_link2_vc3_r4), 
    full_out_link2_vc4(full_out_link2_vc4_r4), 
    full_out_link3_vc1(false_val3_1_r4),// mod
    full_out_link3_vc2(false_val3_2_r4),// mod
    full_out_link3_vc3(false_val3_3_r4),// mod
    full_out_link3_vc4(false_val3_4_r4),// mod
     full_out_link4_vc1(full_out_link4_vc1_r4), 
     full_out_link4_vc2(full_out_link4_vc2_r4), 
     full_out_link4_vc3(full_out_link4_vc3_r4), 
     full_out_link4_vc4(full_out_link4_vc4_r4), 
    full_out_core_vc1(full_out_core_vc1_r4), 
    full_out_core_vc2(full_out_core_vc2_r4), 
    full_out_core_vc3(full_out_core_vc3_r4), 
    full_out_core_vc4(full_out_core_vc4_r4));*/
   
	endmodule		  



















