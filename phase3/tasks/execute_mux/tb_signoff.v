`timescale 1ns / 1ps
module tb;
  reg [31:0] a, m; reg en; wire [31:0] y; integer i, err;
  execute_mux dut(.alu_result(a), .mul_result(m), .id_ex_enable(en), .result(y));
  initial begin
    err = 0;
    for (i = 0; i < 200; i = i + 1) begin
      a = $random; m = $random; en = i % 2; #5;
      if (y !== (en ? a : m)) begin err = err + 1; $display("FAIL en=%0d", en); end
    end
    if (err == 0) $display("ALL TESTS PASSED"); else $display("FAIL: %0d errors", err);
    $finish;
  end
endmodule
