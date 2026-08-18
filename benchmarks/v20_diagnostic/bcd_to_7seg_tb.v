`timescale 1ns/1ps
// seg[6:0] = {a,b,c,d,e,f,g}  active HIGH
// Encoding (standard common-cathode, active-high segments):
//  0->7'b1111110  1->7'b0110000  2->7'b1101101  3->7'b1111001
//  4->7'b0110011  5->7'b1011011  6->7'b1011111  7->7'b1110000
//  8->7'b1111111  9->7'b1111011  default->7'b0000000
module bcd_to_7seg_tb;
  reg  [3:0] bcd;
  wire [6:0] seg;
  integer fail = 0;

  bcd_to_7seg uut (.bcd(bcd), .seg(seg));

  task check;
    input [3:0] digit;
    input [6:0] expected;
    begin
      bcd = digit; #10;
      if (seg !== expected) begin
        $display("FAIL: bcd=%0d  expected seg=7'b%b  got seg=7'b%b",
                 digit, expected, seg);
        fail = fail + 1;
      end
    end
  endtask

  initial begin
    check(4'd0,  7'b1111110);
    check(4'd1,  7'b0110000);
    check(4'd2,  7'b1101101);
    check(4'd3,  7'b1111001);
    check(4'd4,  7'b0110011);
    check(4'd5,  7'b1011011);
    check(4'd6,  7'b1011111);
    check(4'd7,  7'b1110000);
    check(4'd8,  7'b1111111);
    check(4'd9,  7'b1111011);
    check(4'd10, 7'b0000000); // default (invalid BCD)
    check(4'd15, 7'b0000000); // default (invalid BCD)
    if (fail == 0) $display("ALL TESTS PASSED");
    $finish;
  end
endmodule
