`timescale 1ns/1ps
// Expected Gray sequence for bin 0..15:
//  bin: 0  1  2  3  4  5  6  7  8  9 10 11 12 13 14 15
// gray: 0  1  3  2  6  7  5  4 12 13 15 14 10 11  9  8
module gray_counter_4bit_tb;
  reg  clk = 0, rst = 1;
  wire [3:0] gray_out;
  integer fail = 0;
  integer i;

  gray_counter_4bit uut (.clk(clk), .rst(rst), .gray_out(gray_out));

  always #5 clk = ~clk;

  // Expected gray code per step (bin 0..15)
  reg [3:0] expected_gray [0:15];

  initial begin
    expected_gray[0]  = 4'd0;
    expected_gray[1]  = 4'd1;
    expected_gray[2]  = 4'd3;
    expected_gray[3]  = 4'd2;
    expected_gray[4]  = 4'd6;
    expected_gray[5]  = 4'd7;
    expected_gray[6]  = 4'd5;
    expected_gray[7]  = 4'd4;
    expected_gray[8]  = 4'd12;
    expected_gray[9]  = 4'd13;
    expected_gray[10] = 4'd15;
    expected_gray[11] = 4'd14;
    expected_gray[12] = 4'd10;
    expected_gray[13] = 4'd11;
    expected_gray[14] = 4'd9;
    expected_gray[15] = 4'd8;

    // ── Reset: gray_out must be 0 ─────────────────────────────────────────
    rst = 1;
    @(negedge clk);
    if (gray_out !== 4'd0) begin
      $display("FAIL [reset]: expected gray=0 got %0d", gray_out); fail = fail + 1;
    end

    // ── Count through full 16-step Gray sequence ──────────────────────────
    @(negedge clk); rst = 0;
    // After rst=0 posedge, counter increments: first step = gray[1] = 1
    for (i = 1; i <= 16; i = i + 1) begin
      @(negedge clk);
      if (gray_out !== expected_gray[i % 16]) begin
        $display("FAIL: step %0d  expected gray=%0d (4'b%b)  got %0d (4'b%b)",
                 i, expected_gray[i%16], expected_gray[i%16], gray_out, gray_out);
        fail = fail + 1;
      end
    end

    // ── Mid-count reset returns to gray=0 ────────────────────────────────
    @(negedge clk); rst = 1;
    @(negedge clk);
    if (gray_out !== 4'd0) begin
      $display("FAIL [mid-reset]: expected 0 got %0d", gray_out); fail = fail + 1;
    end

    if (fail == 0) $display("ALL TESTS PASSED");
    $finish;
  end
endmodule
