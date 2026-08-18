`timescale 1ns/1ps
// alu_accumulator_top instantiates alu_8bit internally.
// ALU A-input = acc_out (feedback).  ALU B-input = data_in.
// load_acc=1 → acc <= data_in  (bypass ALU).
// load_acc=0 → acc <= alu_result.
// zero = alu zero flag (combinational from acc vs data_in).
module alu_accumulator_top_tb;
  reg        clk = 0, rst = 1;
  reg  [7:0] data_in;
  reg  [2:0] op;
  reg        load_acc;
  wire [7:0] acc_out;
  wire       zero;
  integer fail = 0;

  alu_accumulator_top uut (
    .clk(clk), .rst(rst), .data_in(data_in), .op(op),
    .load_acc(load_acc), .acc_out(acc_out), .zero(zero)
  );

  always #5 clk = ~clk;

  task tick; begin @(posedge clk); #1; end endtask

  task check_acc;
    input [7:0] expected;
    input [63:0] label;
    begin
      if (acc_out !== expected) begin
        $display("FAIL [%s]: expected acc=8'h%h got 8'h%h", label, expected, acc_out);
        fail = fail + 1;
      end
    end
  endtask

  initial begin
    rst = 1; load_acc = 0; data_in = 8'h00; op = 3'b000;
    tick; tick;
    // After reset acc = 0
    if (acc_out !== 8'h00) begin
      $display("FAIL [rst]: expected acc=0 got 8'h%h", acc_out); fail = fail + 1;
    end

    rst = 0;

    // ── load_acc=1: acc ← data_in directly ──────────────────────────────
    load_acc = 1; data_in = 8'h10; op = 3'b000; tick;
    check_acc(8'h10, "load 0x10");

    load_acc = 1; data_in = 8'h05; tick;
    check_acc(8'h05, "load 0x05");

    // ── ADD: acc = acc + data_in = 5 + 3 = 8 ────────────────────────────
    load_acc = 0; data_in = 8'h03; op = 3'b000; tick;
    check_acc(8'h08, "add 5+3=8");

    // ── ADD again: 8 + 4 = 12 ────────────────────────────────────────────
    data_in = 8'h04; tick;
    check_acc(8'h0C, "add 8+4=12");

    // ── SUB: acc = acc - data_in = 12 - 2 = 10 ──────────────────────────
    data_in = 8'h02; op = 3'b001; tick;
    check_acc(8'h0A, "sub 12-2=10");

    // ── AND: acc = acc & data_in = 0x0A & 0x0F = 0x0A ──────────────────
    data_in = 8'h0F; op = 3'b010; tick;
    check_acc(8'h0A, "and 0x0A&0x0F=0x0A");

    // ── OR: acc = acc | data_in = 0x0A | 0x50 = 0x5A ───────────────────
    data_in = 8'h50; op = 3'b011; tick;
    check_acc(8'h5A, "or 0x0A|0x50=0x5A");

    // ── Zero flag: load 0, then ADD 0 → zero=1 ──────────────────────────
    load_acc = 1; data_in = 8'h00; tick;       // acc=0
    load_acc = 0; data_in = 8'h00; op = 3'b000; // acc+0=0
    #1; // combinational settle (zero is combinational from ALU)
    // zero is based on alu_result = acc_out + data_in = 0+0 = 0 → zero should be 1
    // We check zero before the clock edge (it's combinational)
    if (zero !== 1'b1) begin
      $display("FAIL [zero]: expected zero=1 for 0+0, got %b", zero); fail = fail + 1;
    end
    tick;
    check_acc(8'h00, "acc=0 after ADD 0+0");

    // ── Non-zero: acc=5+3=8 → zero=0 ────────────────────────────────────
    load_acc = 1; data_in = 8'h05; tick; // acc=5
    load_acc = 0; data_in = 8'h03; op = 3'b000; #1;
    if (zero !== 1'b0) begin
      $display("FAIL [zero]: expected zero=0 for 5+3=8, got %b", zero); fail = fail + 1;
    end
    tick;
    check_acc(8'h08, "accumulate 5+3=8");

    // ── Reset mid-run ────────────────────────────────────────────────────
    rst = 1; tick;
    if (acc_out !== 8'h00) begin
      $display("FAIL [mid-rst]: acc should be 0 after reset, got 8'h%h", acc_out); fail = fail + 1;
    end

    if (fail == 0) $display("ALL TESTS PASSED");
    $finish;
  end
endmodule
