`timescale 1ns / 1ps
module tb;
  reg [1:0] s; reg [31:0] n, b, j; wire [31:0] y; integer i, err;
  MuxPC dut(.next_address(n), .B_addr(b), .J_addr(j), .PCsrc(s), .input_to_ifu(y));
  initial begin
    err = 0;
    for (i = 0; i < 300; i = i + 1) begin
      n = $random; b = $random; j = $random; s = i % 3; #5;
      if (y !== (s == 0 ? n : s == 1 ? j : b)) begin err = err + 1; $display("FAIL s=%0d", s); end
    end
    if (err == 0) $display("ALL TESTS PASSED"); else $display("FAIL: %0d errors", err);
    $finish;
  end
endmodule
