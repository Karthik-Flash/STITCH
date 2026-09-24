`timescale 1ns / 1ps
module tb;
  reg [31:0] a, b; reg [3:0] op; wire [31:0] r; wire z, n, c, v; integer i, err;
  reg [32:0] s; reg [31:0] er; reg ec, ev;
  riscv_alu_flags dut(.a(a), .b(b), .alu_ctrl(op), .result(r), .zero(z), .negative(n), .carry(c), .overflow(v));
  initial begin
    err = 0;
    for (i = 0; i < 1000; i = i + 1) begin
      a = $random; b = (i % 13 == 0) ? a : $random; op = i % 10; #5;
      ec = 0; ev = 0;
      case (op)
        0: begin s = {1'b0,a} + {1'b0,b}; er = s[31:0]; ec = s[32]; ev = (a[31]==b[31]) && (er[31]!=a[31]); end
        1: begin s = {1'b0,a} + {1'b0,~b} + 33'd1; er = s[31:0]; ec = s[32]; ev = (a[31]!=b[31]) && (er[31]!=a[31]); end
        2: er = a & b;  3: er = a | b;  4: er = a ^ b;
        5: er = a << b[4:0];  6: er = a >> b[4:0];  7: er = $signed(a) >>> b[4:0];
        8: er = ($signed(a) < $signed(b)) ? 1 : 0;  9: er = (a < b) ? 1 : 0;
      endcase
      if (r !== er || z !== (er == 0) || n !== er[31]) begin err = err + 1; $display("FAIL op=%0d r=%h exp=%h", op, r, er); end
      // carry/overflow are checked on ADD/SUB only (sim-silent latch benchmark)
      if (op < 2 && (c !== ec || v !== ev)) begin err = err + 1; $display("FAIL flags op=%0d", op); end
    end
    if (err == 0) $display("ALL TESTS PASSED"); else $display("FAIL: %0d errors", err);
    $finish;
  end
endmodule
