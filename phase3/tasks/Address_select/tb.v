`timescale 1ns / 1ps
module tb;
  reg [31:0] ic, pc; reg fl; wire [31:0] ja; wire [1:0] ps; integer i, err;
  reg [19:0] imm, sh; reg [31:0] x;
  Address_select dut(.Instruction_code(ic), .IF_Flush(fl), .PC(pc), .J_addr(ja), .PCsrc(ps));
  initial begin
    err = 0;
    for (i = 0; i < 400; i = i + 1) begin
      ic = $random; if (i % 2) ic[6:0] = 7'b1101111; fl = (i % 7 == 0); pc = $random & 32'hFFFFFFFC; #5;
      imm = {ic[31], ic[19:12], ic[20], ic[30:21]}; sh = imm << 2; x = {{12{sh[19]}}, sh};
      if (fl) begin if (ps !== 2'b10) begin err = err + 1; $display("FAIL flush"); end end
      else if (ic[6:0] == 7'b1101111) begin
        if (ps !== 2'b01 || ja !== x + pc) begin err = err + 1; $display("FAIL jal ja=%h exp=%h", ja, x + pc); end
      end else if (ps !== 2'b00) begin err = err + 1; $display("FAIL pcsrc"); end
    end
    if (err == 0) $display("ALL TESTS PASSED"); else $display("FAIL: %0d errors", err);
    $finish;
  end
endmodule
