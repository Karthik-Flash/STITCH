`timescale 1ns / 1ps
module tb;
  reg [1:0] sel; reg [31:0] a, e, m; wire [31:0] y; integer i, err;
  mux3 dut(.sel(sel), .id_ex_output_data1(a), .ex_forwarding(e), .mem_forwarding(m), .alu_in(y));
  initial begin
    err = 0;
    for (i = 0; i < 300; i = i + 1) begin
      a = $random; e = $random; m = $random; sel = i % 3; #5;
      if (y !== (sel == 0 ? a : sel == 1 ? e : m)) begin err = err + 1; $display("FAIL sel=%0d y=%h", sel, y); end
    end
    if (err == 0) $display("ALL TESTS PASSED"); else $display("FAIL: %0d errors", err);
    $finish;
  end
endmodule
