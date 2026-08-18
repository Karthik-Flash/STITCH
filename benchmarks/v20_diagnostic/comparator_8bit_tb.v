`timescale 1ns/1ps
module comparator_8bit_tb;
  reg  [7:0] A, B;
  wire       gt, eq, lt;
  integer fail = 0;

  comparator_8bit uut (.A(A), .B(B), .gt(gt), .eq(eq), .lt(lt));

  task check;
    input [7:0] ea, eb;
    input       egt, eeq, elt;
    begin
      A = ea; B = eb; #10;
      if (gt !== egt || eq !== eeq || lt !== elt) begin
        $display("FAIL: A=%0d B=%0d  expected gt=%b eq=%b lt=%b  got gt=%b eq=%b lt=%b",
                 ea, eb, egt, eeq, elt, gt, eq, lt);
        fail = fail + 1;
      end
      // Sanity: exactly one flag must be set
      if ((gt+eq+lt) !== 1) begin
        $display("FAIL: exactly one flag must be set (A=%0d B=%0d  gt=%b eq=%b lt=%b)",
                 ea, eb, gt, eq, lt);
        fail = fail + 1;
      end
    end
  endtask

  initial begin
    check(8'd0,   8'd0,   1'b0, 1'b1, 1'b0); // equal
    check(8'd1,   8'd0,   1'b1, 1'b0, 1'b0); // A > B
    check(8'd0,   8'd1,   1'b0, 1'b0, 1'b1); // A < B
    check(8'd255, 8'd254, 1'b1, 1'b0, 1'b0);
    check(8'd254, 8'd255, 1'b0, 1'b0, 1'b1);
    check(8'd255, 8'd255, 1'b0, 1'b1, 1'b0);
    check(8'd128, 8'd127, 1'b1, 1'b0, 1'b0);
    check(8'd127, 8'd128, 1'b0, 1'b0, 1'b1);
    check(8'd100, 8'd100, 1'b0, 1'b1, 1'b0);
    if (fail == 0) $display("ALL TESTS PASSED");
    $finish;
  end
endmodule
