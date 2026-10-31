#!/usr/bin/env python3
"""One packet through the all-golden ni_pair (Icarus). Writes ni/reports/NI_PAIR_TRACE.md.

Reset for 4 cycles, then one core word 32'h1234_ABCD with wr_en for one cycle (dest 8'h11, source 8'h00, rd_en 0,
as in main.v), then 30 cycles sampled 4 ns after each rising edge: niout (rp1), depack's wr_en and data_out, and
the depacketiser FIFO's two flag nets (nidepack's full_int and empty, by hierarchical name).
Usage: python pipeline/ni_pair_trace.py   (needs iverilog, vvp)
"""
from __future__ import annotations

import glob
import os
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
NI = os.path.join(os.path.dirname(HERE), "ni")
WORD = "32'h1234_abcd"
TB = """`timescale 1ns / 1ps
module t;
  reg clk = 0, reset = 1, wr_en = 0, rd_en = 0; reg [31:0] data_in = %s;
  wire empty, full_int, wr_o; wire [31:0] niout, data_out;
  ni_pair u (.rd_clk(clk), .wr_clk(clk), .reset(reset), .data_in(data_in), .wr_en(wr_en), .dest(8'h11),
             .source(8'h00), .rd_en(rd_en), .empty(empty), .full_int(full_int), .niout(niout), .wr_o(wr_o),
             .data_out(data_out));
  always #5 clk = ~clk;
  integer i;
  initial begin
    repeat (4) @(negedge clk); #1 reset = 0; wr_en = 1; @(negedge clk); #1 wr_en = 0;
    for (i = 0; i < 30; i = i + 1) begin @(posedge clk); #4
      $display("| %%0d | %%h | %%b | %%h | %%b | %%b |", i, niout, u.D1.wr_en, u.D1.depack_out, u.D1.full_int,
               u.D1.empty); end
    $finish;
  end
endmodule
""" % WORD


def main() -> int:
    with tempfile.TemporaryDirectory() as d:
        open(os.path.join(d, "t.v"), "w").write(TB)
        files = [os.path.join(NI, "wrapper", "ni_pair.v"), *sorted(glob.glob(os.path.join(NI, "golden", "reference", "*.v")))]
        subprocess.run(["iverilog", "-g2012", "-o", os.path.join(d, "t.vvp"), "-s", "t", *files,
                        os.path.join(d, "t.v")], check=True)
        log = subprocess.run(["vvp", "-n", os.path.join(d, "t.vvp")], capture_output=True, text=True, check=True).stdout
    rows = [l for l in log.splitlines() if l.startswith("|")]
    md = ["# One packet through the all-golden ni_pair (pipeline/ni_pair_trace.py)", "",
          f"Core word {WORD} written once after reset; Icarus; samples 4 ns after each rising clock edge (cycle 0 = "
          "the edge after the write). depack wr_en / data_out and the FIFO flags are nidepack's internal nets "
          "(D1.wr_en, D1.depack_out, D1.full_int, D1.empty). The shifted connection (phase3/designs/SANITISATION.md "
          "item 3) puts router_fifo's full_ext (4 or more entries) on the net named full_int and its full_int (6 "
          "entries) on the net named empty.", "",
          "| cycle | niout | depack wr_en | depack data_out | net full_int = FIFO 4+ entries | "
          "net empty = FIFO full |", "|---|---|---|---|---|---|", *rows]
    out = os.path.join(NI, "reports", "NI_PAIR_TRACE.md")
    open(out, "w", encoding="utf-8", newline="\n").write("\n".join(md) + "\n")
    print("\n".join(md))
    return 0


if __name__ == "__main__":
    sys.exit(main())
