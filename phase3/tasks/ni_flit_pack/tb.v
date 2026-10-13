`timescale 1ns / 1ps
module tb;
  reg [1:0] t; reg [7:0] d, s; reg [31:0] p; wire [31:0] h, b; integer i, err;
  ni_flit_pack dut(.flit_type(t), .dest(d), .src(s), .payload(p), .head_flit(h), .body_flit(b));
  initial begin
    err = 0;
    for (i = 0; i < 300; i = i + 1) begin
      t = $random; d = $random; s = $random; p = $random; #5;
      if (h !== {t, d, s, 14'd0} || b !== {t, p[29:0]}) begin err = err + 1; $display("FAIL h=%h b=%h", h, b); end
    end
    if (err == 0) $display("ALL TESTS PASSED"); else $display("FAIL: %0d errors", err);
    $finish;
  end
endmodule
