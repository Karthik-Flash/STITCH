`timescale 1ns / 1ps
module tb;
  reg [3:0] g; reg [31:0] i0, i1, i2, i3; wire [31:0] y; wire v; integer i, err; reg [31:0] e;
  noc_xbar4 dut(.gnt(g), .in0(i0), .in1(i1), .in2(i2), .in3(i3), .out_data(y), .out_valid(v));
  initial begin
    err = 0;
    for (i = 0; i < 300; i = i + 1) begin
      i0 = $random; i1 = $random; i2 = $random; i3 = $random; g = (i % 5 == 4) ? 4'b0 : (4'b1 << (i % 5)); #5;
      e = g[0] ? i0 : g[1] ? i1 : g[2] ? i2 : g[3] ? i3 : 32'd0;
      if (y !== e || v !== |g) begin err = err + 1; $display("FAIL g=%b y=%h e=%h", g, y, e); end
    end
    if (err == 0) $display("ALL TESTS PASSED"); else $display("FAIL: %0d errors", err);
    $finish;
  end
endmodule
