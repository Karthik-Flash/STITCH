`timescale 1ns/1ps
// Default: N=4 registers, W=8 bits wide. wr_addr/rd_addr are 2-bit ($clog2(4)=2).
// Read is combinational. Write is clocked (posedge).
// No reset — this is intentional per spec.
module param_register_file_tb;
  reg        clk = 0, wr_en = 0;
  reg  [1:0] wr_addr, rd_addr;
  reg  [7:0] wr_data;
  wire [7:0] rd_data;
  integer fail = 0;
  integer i;

  param_register_file uut (
    .clk(clk), .wr_en(wr_en),
    .wr_addr(wr_addr), .rd_addr(rd_addr),
    .wr_data(wr_data), .rd_data(rd_data)
  );

  always #5 clk = ~clk;

  task tick; begin @(posedge clk); #1; end endtask

  // Write data to an address (synchronous)
  task write_reg;
    input [1:0] addr;
    input [7:0] data;
    begin
      wr_en = 1; wr_addr = addr; wr_data = data;
      tick;
      wr_en = 0;
    end
  endtask

  // Read data from an address (combinational — just set rd_addr and check)
  task read_check;
    input [1:0]  addr;
    input [7:0]  expected;
    begin
      rd_addr = addr; #5; // combinational settle
      if (rd_data !== expected) begin
        $display("FAIL: rd_addr=%0d  expected 8'h%h  got 8'h%h", addr, expected, rd_data);
        fail = fail + 1;
      end
    end
  endtask

  initial begin
    wr_en = 0; wr_addr = 2'd0; rd_addr = 2'd0; wr_data = 8'h00;
    tick; // let sim settle

    // ── Write distinct values to all 4 registers ─────────────────────────
    write_reg(2'd0, 8'hDE);
    write_reg(2'd1, 8'hAD);
    write_reg(2'd2, 8'hBE);
    write_reg(2'd3, 8'hEF);

    // ── Read them back and verify ─────────────────────────────────────────
    read_check(2'd0, 8'hDE);
    read_check(2'd1, 8'hAD);
    read_check(2'd2, 8'hBE);
    read_check(2'd3, 8'hEF);

    // ── Overwrite register 2 and verify others are unchanged ──────────────
    write_reg(2'd2, 8'h42);
    read_check(2'd0, 8'hDE); // unchanged
    read_check(2'd1, 8'hAD); // unchanged
    read_check(2'd2, 8'h42); // updated
    read_check(2'd3, 8'hEF); // unchanged

    // ── wr_en=0: write must NOT change register ───────────────────────────
    wr_en = 0; wr_addr = 2'd0; wr_data = 8'hFF; tick;
    read_check(2'd0, 8'hDE); // must still be 0xDE

    // ── Combinational read follows rd_addr immediately ────────────────────
    wr_en = 0;
    rd_addr = 2'd1; #2;
    if (rd_data !== 8'hAD) begin
      $display("FAIL [comb read]: rd_addr=1 expected 8'hAD got 8'h%h", rd_data); fail = fail + 1;
    end
    rd_addr = 2'd3; #2;
    if (rd_data !== 8'hEF) begin
      $display("FAIL [comb read]: rd_addr=3 expected 8'hEF got 8'h%h", rd_data); fail = fail + 1;
    end

    // ── Fill all 4 registers with sequential pattern ──────────────────────
    for (i = 0; i < 4; i = i + 1) begin
      write_reg(i[1:0], 8'h10 * (i+1));
    end
    for (i = 0; i < 4; i = i + 1) begin
      read_check(i[1:0], 8'h10 * (i+1));
    end

    if (fail == 0) $display("ALL TESTS PASSED");
    $finish;
  end
endmodule
