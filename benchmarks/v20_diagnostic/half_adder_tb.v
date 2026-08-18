`timescale 1ns/1ps
module half_adder_tb;
  reg a, b;
  wire sum, cout;
  integer fail = 0;

  half_adder uut (.a(a), .b(b), .sum(sum), .cout(cout));

  task check;
    input ea, eb, esum, ecout;
    begin
      a = ea; b = eb; #10;
      if (sum !== esum || cout !== ecout) begin
        $display("FAIL: a=%b b=%b  expected sum=%b cout=%b  got sum=%b cout=%b",
                 ea, eb, esum, ecout, sum, cout);
        fail = fail + 1;
      end
    end
  endtask

  initial begin
    check(1'b0, 1'b0, 1'b0, 1'b0);
    check(1'b0, 1'b1, 1'b1, 1'b0);
    check(1'b1, 1'b0, 1'b1, 1'b0);
    check(1'b1, 1'b1, 1'b0, 1'b1);
    if (fail == 0) $display("ALL TESTS PASSED");
    $finish;
  end
endmodule
