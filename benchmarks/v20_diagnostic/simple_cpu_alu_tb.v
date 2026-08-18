`timescale 1ns/1ps
module simple_cpu_alu_tb;
  reg  [3:0] A, B;
  reg  [1:0] op;
  wire [3:0] result;
  wire       zero;
  integer fail = 0;

  simple_cpu_alu uut (.A(A), .B(B), .op(op), .result(result), .zero(zero));

  task check;
    input [3:0] ea, eb;
    input [1:0] eop;
    input [3:0] eres;
    input       ezero;
    begin
      A = ea; B = eb; op = eop; #10;
      if (result !== eres || zero !== ezero) begin
        $display("FAIL: A=%0d B=%0d op=%0d  expected result=%0d zero=%b  got result=%0d zero=%b",
                 ea, eb, eop, eres, ezero, result, zero);
        fail = fail + 1;
      end
    end
  endtask

  initial begin
    // ADD (00)
    check(4'd3,  4'd5,  2'b00, 4'd8,  1'b0);
    check(4'd15, 4'd1,  2'b00, 4'd0,  1'b1); // overflow → 0, zero=1
    check(4'd0,  4'd0,  2'b00, 4'd0,  1'b1); // zero flag
    // SUB (01)
    check(4'd8,  4'd3,  2'b01, 4'd5,  1'b0);
    check(4'd5,  4'd5,  2'b01, 4'd0,  1'b1); // zero flag
    check(4'd0,  4'd1,  2'b01, 4'd15, 1'b0); // underflow wraps
    // AND (10)
    check(4'hF,  4'h5,  2'b10, 4'h5,  1'b0);
    check(4'hA,  4'h5,  2'b10, 4'h0,  1'b1); // 1010 & 0101 = 0000, zero=1
    // OR (11)
    check(4'hA,  4'h5,  2'b11, 4'hF,  1'b0); // 1010 | 0101 = 1111
    check(4'h0,  4'h0,  2'b11, 4'h0,  1'b1); // zero flag
    if (fail == 0) $display("ALL TESTS PASSED");
    $finish;
  end
endmodule
