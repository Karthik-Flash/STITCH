# 3x3 ORFS hand-off: LLM-generated modules

These are 3x3 mesh routers (top `top_3x3_router`) in which some modules were written by an LLM (qwen2.5-coder:32b) and the rest are golden, plus the reference designs. We need their PPA, measured the same way as A1 and B in the 2x2 hand-off.

## How to run

1. Use your exact A1 ORFS setup: sky130hd, 10 ns clock, the same config.mk settings (keep A1's CORE_UTILIZATION and flow settings).
2. Per design, take `designs/<ID>/config.mk.template`: DESIGN_NAME (`top_3x3_router`) and VERILOG_FILES (the files in `designs/<ID>/VERILOG_FILES.txt`, under `designs/<ID>/rtl/`) are filled in; copy every other line from your A1 config.mk.
3. SDC: use your A1 constraint.sdc unchanged: `top_3x3_router` has the same clock port as `top_2x2_router` (`clk`; modules.csv, checked by pipeline/handoff_study.py).
4. Run in this order: C0_control_all_golden, P1_hybrid_signoff_oneshot, P2_hybrid_signoff_simloop; then, optional: A1_style_3x3, O1_hybrid_compile_oneshot, O2_hybrid_compile_stitch.

## Sanity check

C0 is the golden design through our assembly. It must reproduce B / 3x3 within flow noise (B: 2,312,740 um2, 98.0925 MHz, 429.068 mW; latch_study/PPA_SUMMARY.md). If it does not, stop and tell us before running the rest. A1 / 3x3 is already measured, so A1_style_3x3 is optional.

## Flow notes

- Size: Yosys counts 2.25x the cells of the 2x2 mesh for this study's C0 (reports/ASSEMBLY.md of both studies). With A1's CORE_UTILIZATION the floorplan scales by itself; keep it.
- If your A1 config.mk fixes DIE_AREA / CORE_AREA instead, scale each side by sqrt(2.25) = 1.5 and use the same DIE_AREA / CORE_AREA for every design of this hand-off. Write the values you used in PPA_TABLE.md (flow errors / notes).
- This is the only config change versus A1 besides DESIGN_NAME and VERILOG_FILES.

## What to fill in

PPA_TABLE.md, one row per design. Also run `check_setup -verbose` (OpenSTA) and report the number of unconstrained endpoints.

## What each design means

- A1_style_3x3: optional: the hand-written RTL with only the Yosys-aborting modules fixed; already measured as A1 / 3x3 (latch_study/PPA_SUMMARY.md, PPA_TABLE.md).
- C0_control_all_golden: every module golden, through our assembly: like-for-like reference (B-style RTL).
- P1_hybrid_signoff_oneshot: PRIMARY: oneshot LLM modules that pass their own sign-off checks (REUSED modules: the 2x2 result of the same arm), golden for the rest.
- P2_hybrid_signoff_simloop: PRIMARY: simloop LLM modules that pass their own sign-off checks (REUSED modules: the 2x2 result of the same arm), golden for the rest; byte-identical to hybrid_signoff_stitch.
- O1_hybrid_compile_oneshot: optional: every oneshot module that compiles, golden for the rest; fails the top tb, PPA indicative only.
- O2_hybrid_compile_stitch: optional: every stitch module that compiles, golden for the rest; fails the top tb, PPA indicative only.

- Not shipped: hybrid_compile_simloop: does not synthesise (Yosys: `ERROR: Multiple edge sensitive events found for this signal!`).

## Checklist

- [ ] A1_style_3x3 (optional)  [ ] C0  [ ] P1  [ ] P2  [ ] O1 (optional)  [ ] O2 (optional)
- [ ] PPA_TABLE.md filled
- [ ] ORFS reports/logs dir per design zipped and sent back
- [ ] A1 config.mk + constraint.sdc sent back if not sent with the 2x2 hand-off (we store them in latch_study/orfs_A1/)

## Return

Send the zip (filled PPA_TABLE.md, the reports/logs per design) back to Soumya.
