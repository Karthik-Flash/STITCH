module rr_comb_new (
    input reset, clk, r1, r2, r3, r4,
    output g1, g2, g3, g4, l1, l2, l3, l4, mux_out1, mux_out2, mux_out3, mux_out4, and_out1, and_out2, and_out3,
           and_out4, or_out, b1, b0, b1_logic, b0_logic
);

    wire g1_w, g2_w, g3_w, g4_w;
    wire and_out1_w, and_out2_w, and_out3_w, and_out4_w;
    wire or_out_w;
    wire b1_w, b0_w;
    wire l1_w, l2_w, l3_w, l4_w;
    wire mux_out1_w, mux_out2_w, mux_out3_w, mux_out4_w;

    // Instantiate DFFs
    dff_synch_clr dff_g1 (g1_w, reset, clk, g1);
    dff_synch_clr dff_g2 (g2_w, reset, clk, g2);
    dff_synch_clr dff_g3 (g3_w, reset, clk, g3);
    dff_synch_clr dff_g4 (g4_w, reset, clk, g4);

    // Combinational logic
    assign g1_w = r1 & g1;
    assign g2_w = r2 & g2;
    assign g3_w = r3 & g3;
    assign g4_w = r4 & g4;

    assign and_out1_w = g1_w & ~g2_w & ~g3_w & ~g4_w;
    assign and_out2_w = g2_w & ~g1_w & ~g3_w & ~g4_w;
    assign and_out3_w = g3_w & ~g2_w & ~g1_w & ~g4_w;
    assign and_out4_w = g4_w & ~g2_w & ~g3_w & ~g1_w;

    assign or_out_w = g1_w | g2_w | g3_w | g4_w;

    assign b1_w = and_out3_w | and_out4_w;
    assign b0_w = and_out2_w | and_out4_w;

    assign l1_w = r1 & ~g2_w & ~g3_w & ~g4_w & ((~r3 & ~r4 & (b0_w | (~b1_w & ~r2_w))) | (b1_w & (b0_w | ~r4_w)));
    assign l2_w = r2 & ~g1_w & ~g3_w & ~g4_w & ((~b0_w & ~r1_w & ~r4_w) | (~r1_w & ~r3_w & ~r4_w) | (b1_w & b0_w & ~r1_w) | (~b1_w & ~b0_w));
    assign l3_w = r3 & ~g2_w & ~g1_w & ~g4_w & ((~r1_w & ~r2_w & ~r4_w) | (b0_w & ~r1_w & ~r2_w) | (~b1_w & ~r2_w) | (~b1_w & b0_w));
    assign l4_w = r4 & ~g2_w & ~g3_w & ~g1_w & ((~b1_w & ~r2_w & ~r3_w) | (~r1_w & ~r2_w & ~r3_w) | (~b1_w & b0_w & ~r3_w) | (b1_w & ~b0_w));

    assign mux_out1_w = and_out1_w ? r1 : l1_w;
    assign mux_out2_w = and_out2_w ? r2 : l2_w;
    assign mux_out3_w = and_out3_w ? r3 : l3_w;
    assign mux_out4_w = and_out4_w ? r4 : l4_w;

    // Drive outputs
    assign g1 = g1_w;
    assign g2 = g2_w;
    assign g3 = g3_w;
    assign g4 = g4_w;
    assign and_out1 = and_out1_w;
    assign and_out2 = and_out2_w;
    assign and_out3 = and_out3_w;
    assign and_out4 = and_out4_w;
    assign or_out = or_out_w;
    assign b1 = b1_w;
    assign b0 = b0_w;
    assign l1 = l1_w;
    assign l2 = l2_w;
    assign l3 = l3_w;
    assign l4 = l4_w;
    assign mux_out1 = mux_out1_w;
    assign mux_out2 = mux_out2_w;
    assign mux_out3 = mux_out3_w;
    assign mux_out4 = mux_out4_w;

endmodule
