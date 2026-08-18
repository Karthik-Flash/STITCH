`timescale 1ns/1ps
// Encodes index of HIGHEST-numbered active bit. valid=1 if any bit set.
module priority_enc_8_tb;
  reg  [7:0] in;
  wire [2:0] out;
  wire       valid;
  integer fail = 0;

  priority_enc_8 uut (.in(in), .out(out), .valid(valid));

  task check;
    input [7:0] ein;
    input [2:0] eout;
    input       evalid;
    begin
      in = ein; #10;
      if (out !== eout || valid !== evalid) begin
        $display("FAIL: in=8'b%b  expected out=%0d valid=%b  got out=%0d valid=%b",
                 ein, eout, evalid, out, valid);
        fail = fail + 1;
      end
    end
  endtask

  initial begin
    check(8'b0000_0000, 3'd0, 1'b0); // no bits set → valid=0
    check(8'b0000_0001, 3'd0, 1'b1); // only bit 0
    check(8'b0000_0010, 3'd1, 1'b1); // only bit 1
    check(8'b0000_0100, 3'd2, 1'b1); // only bit 2
    check(8'b0000_1000, 3'd3, 1'b1); // only bit 3
    check(8'b0001_0000, 3'd4, 1'b1); // only bit 4
    check(8'b0010_0000, 3'd5, 1'b1); // only bit 5
    check(8'b0100_0000, 3'd6, 1'b1); // only bit 6
    check(8'b1000_0000, 3'd7, 1'b1); // only bit 7
    check(8'b1111_1111, 3'd7, 1'b1); // all bits → highest = 7
    check(8'b0011_0010, 3'd5, 1'b1); // bits 5,4,1 → highest = 5
    check(8'b0000_0111, 3'd2, 1'b1); // bits 2,1,0 → highest = 2
    check(8'b1000_0001, 3'd7, 1'b1); // bits 7,0   → highest = 7
    check(8'b0110_0000, 3'd6, 1'b1); // bits 6,5   → highest = 6
    if (fail == 0) $display("ALL TESTS PASSED");
    $finish;
  end
endmodule
