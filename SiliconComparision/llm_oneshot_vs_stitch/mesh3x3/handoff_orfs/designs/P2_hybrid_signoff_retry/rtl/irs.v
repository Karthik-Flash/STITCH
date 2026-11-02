module irs (reset, empty, rd_en, rd_clk, tailer, tailer_org, header, 
 				 rd_en_out, data_sel,en1,en2,en4,en5,en6 );
    
	 input reset, empty, rd_clk, rd_en;
    input header, tailer, tailer_org ;

    output rd_en_out, data_sel; 

	 supply1 H ;
	 
	 output en1, en2, en4, en5, en6;
	 wire  w1, w2, w3, nxt_reset;	 
	 wire gated_rd_en, gate_rd, gate_rd_synch, d_w;	

	 assign en1 = (!empty);	 
	 assign en2 = (rd_en); 

	 dff_asynch_clr d1(.d(H),   .clk(header), .q(en4), .clr(reset | en5));
	 dff_asynch_clr d2(.d(en4), .clk(tailer), .q(en5), .clr(reset | en6));
	 dff_asynch_clr d3(.d(en5), .clk(rd_clk), .q(en6), .clr(reset));
					
	 assign rd_en_out = (en4 == 1'b 0) ?  en1 : en2 ;


	  
dff_asynch_clr dff_data3(.d(H), .clk(rd_en), .clr(reset | w2 | w3), .q(data_sel));
dff_asynch_clr dff_data4(.d(data_sel), .clk(rd_clk), .clr(reset), .q(w2));
dff_asynch_clr dff_data5(.d(H), .clk(!data_sel), .clr(reset | tailer), .q(w3));
		  	
endmodule