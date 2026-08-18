`timescale 1ns/1ps
module alu_8bit_tb;
  reg  [7:0] A, B;
  reg  [2:0] op;
  wire [7:0] result;
  wire       zero;
  integer fail = 0;

  alu_8bit uut (.A(A), .B(B), .op(op), .result(result), .zero(zero));

  task check;
    input [7:0] ea, eb;
    input [2:0]  eop;
    input [7:0]  eres;
    input        ezero;
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
    // ADD (000)
    check(8'd10,  8'd20,  3'b000, 8'd30,  1'b0);
    check(8'd0,   8'd0,   3'b000, 8'd0,   1'b1); // zero flag
    check(8'd255, 8'd1,   3'b000, 8'd0,   1'b1); // overflow → 0, zero=1
    // SUB (001)
    check(8'd20,  8'd10,  3'b001, 8'd10,  1'b0);
    check(8'd10,  8'd10,  3'b001, 8'd0,   1'b1); // zero flag
    check(8'd0,   8'd1,   3'b001, 8'd255, 1'b0); // underflow → 255
    // AND (010)
    check(8'hFF,  8'h0F,  3'b010, 8'h0F,  1'b0);
    check(8'hAA,  8'h55,  3'b010, 8'h00,  1'b1); // zero flag
    // OR (011)
    check(8'hAA,  8'h55,  3'b011, 8'hFF,  1'b0);
    check(8'h00,  8'h00,  3'b011, 8'h00,  1'b1); // zero flag
    // XOR (100)
    check(8'hFF,  8'hFF,  3'b100, 8'h00,  1'b1); // zero flag
    check(8'hAA,  8'h55,  3'b100, 8'hFF,  1'b0);
    // NOT_A (101) — B ignored
    check(8'h00,  8'hXX,  3'b101, 8'hFF,  1'b0);
    check(8'hFF,  8'hXX,  3'b101, 8'h00,  1'b1); // zero flag
    // SHL (110) — A << 1
    check(8'h01,  8'hXX,  3'b110, 8'h02,  1'b0);
    check(8'h80,  8'hXX,  3'b110, 8'h00,  1'b1); // MSB shifted out → 0, zero=1
    // SHR (111) — A >> 1
    check(8'h80,  8'hXX,  3'b111, 8'h40,  1'b0);
    check(8'h01,  8'hXX,  3'b111, 8'h00,  1'b1); // LSB shifted out → 0, zero=1
    if (fail == 0) $display("ALL TESTS PASSED");
    $finish;
  end
endmodule
