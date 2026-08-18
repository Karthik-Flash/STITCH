`timescale 1ns/1ps
// 2-stage pipeline: product valid 2 posedges after inputs presented.
// Stage 1: a_r <= a; b_r <= b
// Stage 2: product <= a_r * b_r
// A 1-stage (combinational) implementation will FAIL because output appears at cycle 1, not 2.
module pipeline_mult_4x4_tb;
  reg        clk = 0;
  reg  [3:0] a, b;
  wire [7:0] product;
  integer fail = 0;

  pipeline_mult_4x4 uut (.clk(clk), .a(a), .b(b), .product(product));

  always #5 clk = ~clk;

  task tick; begin @(posedge clk); #1; end endtask

  initial begin
    a = 4'd0; b = 4'd0;
    tick; tick; // pipeline flush / settle

    // ── Test 1: apply (3,4) at cycle 0; expect product=12 at cycle 2 ─────
    a = 4'd3; b = 4'd4;
    tick; // T1: stage1 latches a_r=3, b_r=4.  stage2: product = 0 (old)
    tick; // T2: stage1: a_r=3, b_r=4.         stage2: product = 3*4 = 12
    if (product !== 8'd12) begin
      $display("FAIL [3*4]: expected product=12 after 2 cycles, got %0d", product); fail = fail + 1;
    end

    // ── Test 2: change input to (5,6); expect 30 two cycles later ─────────
    // NOTE: a=5,b=6 are assigned 1 ns AFTER posedge T2, so stage1 only
    //       sees them starting at T3.  Two full ticks are needed.
    a = 4'd5; b = 4'd6;
    tick; // T3: stage1 latches a_r=5, b_r=6.  stage2: product = 3*4 = 12 (still old)
    tick; // T4: stage1: a_r=5, b_r=6.         stage2: product = 5*6 = 30  <-- FIX: was missing this tick
    if (product !== 8'd30) begin
      $display("FAIL [5*6]: expected product=30 after 2 cycles, got %0d", product); fail = fail + 1;
    end

    // ── Test 3: back-to-back inputs, verify each result appears 2 cycles later ──
    // Apply (2,3) → expect 6 two cycles later
    a = 4'd2; b = 4'd3; tick;  // T5: stage1 latches 2,3.  stage2: product=5*6=30
    a = 4'd7; b = 4'd7; tick;  // T6: stage1 latches 7,7.  stage2: product=2*3=6
    if (product !== 8'd6) begin
      $display("FAIL [2*3]: expected 6 at T6, got %0d", product); fail = fail + 1;
    end
    a = 4'd1; b = 4'd1; tick;  // T7: stage1 latches 1,1.  stage2: product=7*7=49
    if (product !== 8'd49) begin
      $display("FAIL [7*7]: expected 49 at T7, got %0d", product); fail = fail + 1;
    end
    tick;                       // T8: stage1: a_r=1,b_r=1. stage2: product=1*1=1
    if (product !== 8'd1) begin
      $display("FAIL [1*1]: expected 1 at T8, got %0d", product); fail = fail + 1;
    end

    // ── Test 4: max input 15*15=225 ──────────────────────────────────────
    a = 4'd15; b = 4'd15; tick; // T9:  stage1 latches 15,15. stage2: product=1*1=1
    a = 4'd0;  b = 4'd0;  tick; // T10: stage1 latches 0,0.   stage2: product=15*15=225
    if (product !== 8'd225) begin
      $display("FAIL [15*15]: expected 225, got %0d", product); fail = fail + 1;
    end

    if (fail == 0) $display("ALL TESTS PASSED");
    $finish;
  end
endmodule
