`timescale 1ns/1ps
module ripple_carry_adder_tb;
  reg  [3:0] A, B;
  reg        cin;
  wire [3:0] Sum;
  wire       cout;
  integer fail = 0;

  ripple_carry_adder uut (.A(A), .B(B), .cin(cin), .Sum(Sum), .cout(cout));

  task check;
    input [3:0] ea, eb;
    input       ecin;
    input [3:0] esum;
    input       ecout;
    begin
      A = ea; B = eb; cin = ecin; #10;
      if (Sum !== esum || cout !== ecout) begin
        $display("FAIL: %0d + %0d + %0d  expected Sum=%0d cout=%b  got Sum=%0d cout=%b",
                 ea, eb, ecin, esum, ecout, Sum, cout);
        fail = fail + 1;
      end
    end
  endtask

  initial begin
    check(4'd0,  4'd0,  1'b0, 4'd0,  1'b0); // 0+0=0
    check(4'd1,  4'd1,  1'b0, 4'd2,  1'b0); // 1+1=2
    check(4'd7,  4'd8,  1'b0, 4'd15, 1'b0); // 7+8=15
    check(4'd8,  4'd8,  1'b0, 4'd0,  1'b1); // 8+8=16 → Sum=0, cout=1
    check(4'd15, 4'd15, 1'b0, 4'd14, 1'b1); // 15+15=30 → Sum=14, cout=1
    check(4'd15, 4'd15, 1'b1, 4'd15, 1'b1); // 15+15+1=31 → Sum=15, cout=1
    check(4'd5,  4'd3,  1'b0, 4'd8,  1'b0); // 5+3=8
    check(4'd9,  4'd6,  1'b1, 4'd0,  1'b1); // 9+6+1=16 → Sum=0, cout=1
    check(4'd0,  4'd0,  1'b1, 4'd1,  1'b0); // 0+0+1=1
    if (fail == 0) $display("ALL TESTS PASSED");
    $finish;
  end
endmodule
