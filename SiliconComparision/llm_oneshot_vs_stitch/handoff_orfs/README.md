# 2x2 mesh ORFS hand-off: LLM-generated modules

These are 2x2 mesh routers (top `top_2x2_router`) in which some modules were written by an LLM (qwen2.5-coder:32b) and the rest are golden. We need their PPA, measured the same way as A1 and B.

## How to run

1. Use your exact A1 ORFS setup: sky130hd, 10 ns clock, the same config.mk settings and constraint.sdc.
2. Per design, take `designs/<ID>/config.mk.template`: copy every line from your A1 config.mk, keep its VERILOG_FILES (the files in `designs/<ID>/VERILOG_FILES.txt`, under `designs/<ID>/rtl/`). Top stays `top_2x2_router`. SDC: use your A1 constraint.sdc unchanged.
3. Run C0 first.

## Sanity check

C0 is the golden design through our assembly. It must match B within flow noise (B: 808,319 um2, 108.0 MHz, 151.1 mW). If it does not, stop and tell us before running the rest.

## What to fill in

PPA_TABLE.md, one row per design. Also run `check_setup -verbose` (OpenSTA) and report the number of unconstrained endpoints.

## What each design means

- C0_control_all_golden: every module golden, through our assembly: setup check, must reproduce B.
- P1_hybrid_signoff_oneshot: PRIMARY: one-shot LLM modules that pass their own sign-off checks, golden for the rest.
- P2_hybrid_signoff_retry: PRIMARY: same after the retry loops (simulation-only retry and STITCH give byte-identical designs).
- O1_hybrid_compile_oneshot: optional: every one-shot module that compiles, golden for the rest; fails the mesh tb, PPA indicative only.
- O2_hybrid_compile_stitch: optional: every STITCH module that compiles, golden for the rest; fails the mesh tb, PPA indicative only.

## Checklist

- [ ] C0  - [ ] P1  - [ ] P2  - [ ] O1 (optional)  - [ ] O2 (optional)
- [ ] PPA_TABLE.md filled
- [ ] ORFS reports/logs dir per design zipped and sent back
- [ ] A1 config.mk + constraint.sdc sent back (we store them in latch_study/orfs_A1/)

## Return

Send the zip (filled PPA_TABLE.md, the reports/logs per design, your A1 config.mk and constraint.sdc) back to Soumya.
