# ni ORFS hand-off: LLM-generated modules

Optional. No newly generated NI module signed off, so no design here measures LLM output; P1 differs from C0 only by two reused 2x2 leaves.

These are network-interface pairs (top `ni_pair`: the packetiser new1 driving the depacketiser nidepack directly, a wrapper we wrote; every design includes it) in which some modules were written by an LLM (qwen2.5-coder:32b) and the rest are golden, plus the reference designs. If you run them, measure them the same way as A1 and B in the 2x2 hand-off.

## How to run

1. Use your exact A1 ORFS setup: sky130hd, 10 ns clock, the same config.mk settings (keep A1's CORE_UTILIZATION and flow settings).
2. Per design, take `designs/<ID>/config.mk.template`: DESIGN_NAME (`ni_pair`) and VERILOG_FILES (the files in `designs/<ID>/VERILOG_FILES.txt`, under `designs/<ID>/rtl/`) are filled in; copy every other line from your A1 config.mk.
3. SDC: use `constraint.sdc` from this folder. It is the only SDC change versus A1: one 10 ns clock on each clock port of `ni_pair` (`rd_clk`, `wr_clk`, read from wrapper/ni_pair.v by the script) and `set_clock_groups -asynchronous` between them (the FIFOs between the two clocks are asynchronous). If your A1 constraint.sdc has further lines (I/O delays, ...), keep them and point them at these clocks.
4. Nothing is required. Optional, in this order: C0_control_all_golden, P1_hybrid_signoff_oneshot, O1_hybrid_compile_oneshot, O2_hybrid_compile_simloop, O3_hybrid_compile_stitch.

## Flow notes

- Size: Yosys counts 0.015x the cells of the 2x2 mesh for this study's C0 (reports/ASSEMBLY.md of both studies). With A1's CORE_UTILIZATION the floorplan scales by itself; keep it.
- If your A1 config.mk fixes DIE_AREA / CORE_AREA instead, scale each side by sqrt(0.015) = 0.123 and use the same DIE_AREA / CORE_AREA for every design of this hand-off. Write the values you used in PPA_TABLE.md (flow errors / notes).
- `ni_pair` has 120 I/O pins. If the scaled die cannot place them, use the smallest die that does, the same for every design of this hand-off, and note it.
- This is the only config change versus A1 besides DESIGN_NAME and VERILOG_FILES. The SDC change is in step 3.

## What to fill in

PPA_TABLE.md, one row per design. Also run `check_setup -verbose` (OpenSTA) and report the number of unconstrained endpoints.

## What each design means

- C0_control_all_golden: every module golden, through our assembly: like-for-like reference (B-style RTL); byte-identical to A1_style_ni (the hand-written NI RTL synthesises without latches, nothing to fix), so it is also the A1-style reference.
- P1_hybrid_signoff_oneshot: PRIMARY: oneshot LLM modules that pass their own sign-off checks (REUSED modules: the 2x2 result of the same arm), golden for the rest; byte-identical to hybrid_signoff_simloop, hybrid_signoff_stitch.
- O1_hybrid_compile_oneshot: optional: every oneshot module that compiles, golden for the rest; fails the top tb, PPA indicative only.
- O2_hybrid_compile_simloop: optional: every simloop module that compiles, golden for the rest; fails the top tb, PPA indicative only.
- O3_hybrid_compile_stitch: optional: every stitch module that compiles, golden for the rest; fails the top tb, PPA indicative only.

## Checklist

- [ ] C0 (optional)  [ ] P1 (optional)  [ ] O1 (optional)  [ ] O2 (optional)  [ ] O3 (optional)
- [ ] PPA_TABLE.md filled
- [ ] ORFS reports/logs dir per design zipped and sent back
- [ ] A1 config.mk + constraint.sdc sent back if not sent with the 2x2 hand-off (we store them in latch_study/orfs_A1/)

## Return

Send the zip (filled PPA_TABLE.md, the reports/logs per design) back to Soumya.
