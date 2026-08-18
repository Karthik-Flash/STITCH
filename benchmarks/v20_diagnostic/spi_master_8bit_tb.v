`timescale 1ns/1ps
// SPI mode 0: CPOL=0 CPHA=0.
// CLK_DIV=4: each SCLK half-period = 4 system clocks.
// MOSI: MSB-first, driven when CS goes active (bit7) then on each falling sclk edge.
// MISO: sampled by master on rising sclk edge.
// Slave (in testbench) drives MISO[7:0] = 8'hA5 MSB-first.
// Master sends mosi_data = 8'hB4.
// After done: check miso_capture == 8'hA5, and verify MOSI bits matched 8'hB4.
module spi_master_8bit_tb;
  localparam CLK_DIV = 4;

  reg        clk = 0, rst = 1, start = 0, miso = 0;
  reg  [7:0] mosi_data;
  wire       sclk, cs_n, mosi, done;
  wire [7:0] miso_capture;
  integer fail = 0;

  spi_master_8bit #(.CLK_DIV(CLK_DIV)) uut (
    .clk(clk), .rst(rst), .start(start),
    .mosi_data(mosi_data), .miso(miso),
    .sclk(sclk), .cs_n(cs_n), .mosi(mosi),
    .miso_capture(miso_capture), .done(done)
  );

  always #5 clk = ~clk;

  // ── MISO slave: drives 8'hA5 MSB-first ────────────────────────────────
  // Mode 0: slave drives MISO before rising edge.
  // Drive bit[7] when cs_n falls, then each bit on falling sclk edge.
  reg [7:0] slave_byte;
  integer   sbit;
  reg       slave_done;

  initial begin
    slave_byte = 8'hA5; // 10100101
    slave_done = 0;
    miso = 1'b0;
    @(negedge cs_n);          // CS active
    miso = slave_byte[7];     // drive MSB before first rising edge
    for (sbit = 6; sbit >= 0; sbit = sbit - 1) begin
      @(negedge sclk);        // master drives MOSI on falling; slave also updates
      miso = slave_byte[sbit];
    end
    @(posedge cs_n);          // CS released
    miso = 1'b0;
    slave_done = 1;
  end

  // ── MOSI capture: sample on each rising sclk edge ────────────────────
  reg [7:0] mosi_captured;
  integer   mosi_bit;
  initial begin
    mosi_captured = 8'hxx;
    @(negedge cs_n);
    for (mosi_bit = 7; mosi_bit >= 0; mosi_bit = mosi_bit - 1) begin
      @(posedge sclk);
      mosi_captured[mosi_bit] = mosi;
    end
  end

  // ── Main test ─────────────────────────────────────────────────────────
  integer timeout;
  integer done_seen;
  initial begin
    rst = 1; start = 0; mosi_data = 8'hB4;
    repeat(4) @(posedge clk); #1;
    rst = 0;
    repeat(2) @(posedge clk); #1;

    // Verify idle state
    if (cs_n !== 1'b1) begin
      $display("FAIL [idle]: cs_n should be 1 in idle, got %b", cs_n); fail = fail + 1;
    end
    if (sclk !== 1'b0) begin
      $display("FAIL [idle]: sclk should be 0 in idle (mode 0), got %b", sclk); fail = fail + 1;
    end

    // Start transfer
    @(negedge clk); start = 1;
    @(posedge clk); #1; start = 0;

    // Check cs_n went active
    repeat(2) @(posedge clk); #1;
    if (cs_n !== 1'b0) begin
      $display("FAIL [start]: cs_n should go low after start"); fail = fail + 1;
    end

    // Wait for done with timeout (max 8 bits * 8 clocks/bit * 2 = 128 + margin)
    done_seen = 0;
    timeout = 200;
    while (!done_seen && timeout > 0) begin
      @(posedge clk); #1;
      if (done) done_seen = 1;
      timeout = timeout - 1;
    end

    if (!done_seen) begin
      $display("FAIL: done never asserted within timeout"); fail = fail + 1;
    end

    // Allow one more cycle for outputs to settle
    @(posedge clk); #1;

    // Verify MISO capture
    if (miso_capture !== 8'hA5) begin
      $display("FAIL [miso]: expected miso_capture=8'hA5 got 8'h%h", miso_capture); fail = fail + 1;
    end

    // Verify MOSI bits (captured on rising sclk edges)
    if (mosi_captured !== 8'hB4) begin
      $display("FAIL [mosi]: expected mosi_captured=8'hB4 got 8'h%h", mosi_captured); fail = fail + 1;
    end

    // Verify cs_n is deasserted after done
    if (cs_n !== 1'b1) begin
      $display("FAIL [cs_n]: cs_n should be high after transfer done, got %b", cs_n); fail = fail + 1;
    end

    // Verify sclk is low (idle) after done
    if (sclk !== 1'b0) begin
      $display("FAIL [sclk]: sclk should be 0 in idle after done, got %b", sclk); fail = fail + 1;
    end

    if (fail == 0) $display("ALL TESTS PASSED");
    $finish;
  end

  // Safety timeout
  initial begin
    #100000;
    $display("FAIL: global simulation timeout");
    $finish;
  end
endmodule
