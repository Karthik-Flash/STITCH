`timescale 1ns/1ps
module full_adder_tb;
  reg a, b, cin;
  wire sum, cout;
  integer fail = 0;

  full_adder uut (.a(a), .b(b), .cin(cin), .sum(sum), .cout(cout));

  task check;
    input ea, eb, ecin, esum, ecout;
    begin
      a = ea; b = eb; cin = ecin; #10;
      if (sum !== esum || cout !== ecout) begin
        $display("FAIL: a=%b b=%b cin=%b  expected sum=%b cout=%b  got sum=%b cout=%b",
                 ea, eb, ecin, esum, ecout, sum, cout);
        fail = fail + 1;
      end
    end
  endtask

  initial begin
    // a b cin | sum cout
    check(0,0,0, 0,0);
    check(0,0,1, 1,0);
    check(0,1,0, 1,0);
    check(0,1,1, 0,1);
    check(1,0,0, 1,0);
    check(1,0,1, 0,1);
    check(1,1,0, 0,1);
    check(1,1,1, 1,1);
    if (fail == 0) $display("ALL TESTS PASSED");
    $finish;
  end
endmodule
