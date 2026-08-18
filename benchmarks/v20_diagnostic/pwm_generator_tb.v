`timescale 1ns/1ps
// pwm_out = 1 when counter < duty_cycle.
// Counter is 8-bit free-running 0..255.
// After reset: counter = 0.
module pwm_generator_tb;
  reg        clk = 0, rst = 1;
  reg  [7:0] duty_cycle;
  wire       pwm_out;
  integer fail = 0;
  integer high_count, i;

  pwm_generator uut (.clk(clk), .rst(rst), .duty_cycle(duty_cycle), .pwm_out(pwm_out));

  always #5 clk = ~clk;

  initial begin
    // ── Test 1: duty=0 → pwm always 0 for full 256-cycle window ──────────
    rst = 1; duty_cycle = 8'd0;
    @(negedge clk); // reset settles, counter=0
    rst = 0;
    for (i = 0; i < 256; i = i + 1) begin
      @(negedge clk);
      if (pwm_out !== 1'b0) begin
        $display("FAIL [duty=0]: pwm_out=1 at counter=%0d (expected always 0)", i);
        fail = fail + 1;
      end
    end

    // ── Test 2: duty=4 → high for first 4 cycles (0,1,2,3), low for rest ─
    rst = 1; duty_cycle = 8'd4;
    @(negedge clk); rst = 0;
    high_count = 0;
    for (i = 0; i < 256; i = i + 1) begin
      @(negedge clk);
      if (pwm_out) high_count = high_count + 1;
      // Check per-cycle correctness (counter == i since reset just released)
      if (i < 4 && pwm_out !== 1'b1) begin
        $display("FAIL [duty=4]: counter=%0d expected high, got low", i); fail = fail + 1;
      end
      if (i >= 4 && pwm_out !== 1'b0) begin
        $display("FAIL [duty=4]: counter=%0d expected low, got high", i); fail = fail + 1;
      end
    end
    if (high_count !== 4) begin
      $display("FAIL [duty=4]: counted %0d high cycles (expected 4)", high_count); fail = fail + 1;
    end

    // ── Test 3: duty=255 → high for 255 cycles, low for 1 cycle (cnt=255) ─
    rst = 1; duty_cycle = 8'd255;
    @(negedge clk); rst = 0;
    high_count = 0;
    for (i = 0; i < 256; i = i + 1) begin
      @(negedge clk);
      if (pwm_out) high_count = high_count + 1;
    end
    if (high_count !== 255) begin
      $display("FAIL [duty=255]: counted %0d high cycles (expected 255)", high_count); fail = fail + 1;
    end

    // ── Test 4: duty=128 → 128 high, 128 low ──────────────────────────────
    rst = 1; duty_cycle = 8'd128;
    @(negedge clk); rst = 0;
    high_count = 0;
    for (i = 0; i < 256; i = i + 1) begin
      @(negedge clk);
      if (pwm_out) high_count = high_count + 1;
    end
    if (high_count !== 128) begin
      $display("FAIL [duty=128]: counted %0d high cycles (expected 128)", high_count); fail = fail + 1;
    end

    if (fail == 0) $display("ALL TESTS PASSED");
    $finish;
  end
endmodule
