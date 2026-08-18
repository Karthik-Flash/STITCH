`timescale 1ns/1ps
// 8-entry x 8-bit synchronous FIFO.
// full  = (wr_ptr[2:0]==rd_ptr[2:0]) && (wr_ptr[3]!=rd_ptr[3])
// empty = (wr_ptr == rd_ptr)
module sync_fifo_8_tb;
  reg        clk = 0, rst = 1;
  reg        wr_en = 0, rd_en = 0;
  reg  [7:0] din;
  wire [7:0] dout;
  wire       full, empty;
  integer fail = 0;
  integer i;
  reg [7:0] ref_data [0:7]; // expected readback

  sync_fifo_8 uut (
    .clk(clk), .rst(rst), .wr_en(wr_en), .rd_en(rd_en),
    .din(din), .dout(dout), .full(full), .empty(empty)
  );

  always #5 clk = ~clk;

  task tick; begin @(posedge clk); #1; end endtask

  initial begin
    // ── Reset ──────────────────────────────────────────────────────────────
    rst = 1; wr_en = 0; rd_en = 0; din = 8'h00;
    tick; tick;
    rst = 0; tick;
    if (!empty) begin
      $display("FAIL [reset]: empty should be 1 after reset"); fail = fail + 1;
    end
    if (full) begin
      $display("FAIL [reset]: full should be 0 after reset"); fail = fail + 1;
    end

    // ── Write 8 entries ───────────────────────────────────────────────────
    wr_en = 1;
    for (i = 0; i < 8; i = i + 1) begin
      din = 8'hA0 + i; ref_data[i] = din;
      tick;
      if (i < 7 && full) begin
        $display("FAIL [write]: full asserted too early at i=%0d", i); fail = fail + 1;
      end
    end
    wr_en = 0; tick;
    if (!full) begin
      $display("FAIL [write]: full should be 1 after 8 writes"); fail = fail + 1;
    end
    if (empty) begin
      $display("FAIL [write]: empty should be 0 after writes"); fail = fail + 1;
    end

    // ── Write when full must not change state ─────────────────────────────
    wr_en = 1; din = 8'hFF; tick; wr_en = 0;

    // ── Read 8 entries and verify data ───────────────────────────────────
    rd_en = 1;
    for (i = 0; i < 8; i = i + 1) begin
      tick;
      // dout updates on posedge when rd_en=1; after #1 it's settled
      if (dout !== ref_data[i]) begin
        $display("FAIL [read %0d]: expected 8'h%h got 8'h%h", i, ref_data[i], dout);
        fail = fail + 1;
      end
      if (i < 7 && empty) begin
        $display("FAIL [read]: empty asserted too early at i=%0d", i); fail = fail + 1;
      end
    end
    rd_en = 0; tick;
    if (!empty) begin
      $display("FAIL [read]: empty should be 1 after 8 reads"); fail = fail + 1;
    end
    if (full) begin
      $display("FAIL [read]: full should be 0 after all reads"); fail = fail + 1;
    end

    // ── Simultaneous read+write (count stays same) ────────────────────────
    // Write 4 entries first
    wr_en = 1;
    for (i = 0; i < 4; i = i + 1) begin
      din = 8'hB0 + i; tick;
    end
    wr_en = 0; tick;
    // Now do simultaneous wr+rd for 4 cycles
    wr_en = 1; rd_en = 1;
    for (i = 0; i < 4; i = i + 1) begin
      din = 8'hC0 + i; tick;
      if (full || empty) begin
        $display("FAIL [simult]: full=%b empty=%b during simultaneous rw at i=%0d",
                 full, empty, i);
        fail = fail + 1;
      end
    end
    wr_en = 0; rd_en = 0;

    // ── Wrap-around: write 8 and read 8 to verify pointer wrap ───────────
    rst = 1; tick; tick; rst = 0; tick;
    // Write 4, read 4 (moves ptrs to middle of ring)
    wr_en = 1;
    for (i = 0; i < 4; i = i + 1) begin din = 8'hD0+i; tick; end
    wr_en = 0; rd_en = 1;
    for (i = 0; i < 4; i = i + 1) begin tick; end
    rd_en = 0; tick;
    // Now write 8 to fill across the pointer wrap boundary
    wr_en = 1;
    for (i = 0; i < 8; i = i + 1) begin din = 8'hE0+i; ref_data[i]=din; tick; end
    wr_en = 0; tick;
    if (!full) begin
      $display("FAIL [wrap fill]: not full after 8 writes across wrap"); fail = fail + 1;
    end
    // Read all 8 and verify
    rd_en = 1;
    for (i = 0; i < 8; i = i + 1) begin
      tick;
      if (dout !== ref_data[i]) begin
        $display("FAIL [wrap read %0d]: expected 8'h%h got 8'h%h", i, ref_data[i], dout);
        fail = fail + 1;
      end
    end
    rd_en = 0; tick;
    if (!empty) begin
      $display("FAIL [wrap read]: not empty after draining all entries"); fail = fail + 1;
    end

    if (fail == 0) $display("ALL TESTS PASSED");
    $finish;
  end
endmodule
