# PPA table (fill in the empty cells)

3x3 hand-off. A1 / 3x3 and B / 3x3: ORFS, SKY130HD, 10 ns clock, from latch_study/PPA_SUMMARY.md (already measured). Yosys latch cells and functionally correct are prefilled by pipeline/handoff_study.py (Yosys: the latch_study script, reports/ASSEMBLY.md; functionally correct = passes tasks/top_3x3_router/tb_signoff.v).

| design | area um2 | fmax MHz | total power mW | check_setup unconstrained endpoints | flow errors / notes | Yosys latch cells | functionally correct |
|---|---|---|---|---|---|---|---|
| A1 / 3x3 (reference) | 2235731 | 99.2363 | 392.244 | not measured | - | 6480 | reference (original RTL, with latches) |
| B / 3x3 (reference) | 2312740 | 98.0925 | 429.068 | not measured | - | 0 | yes (golden) |
| A1_style_3x3 |  |  |  |  |  | 6480 | reference (hand-written RTL, with latches); not simulated: the design does not compile in Icarus (PREFLIGHT.md) |
| C0_control_all_golden |  |  |  |  |  | 0 | yes (passes the top tb) |
| P1_hybrid_signoff_oneshot |  |  |  |  |  | 0 | no: fails the top tb only through 3 formally equivalent modules (PREFLIGHT.md) |
| P2_hybrid_signoff_simloop |  |  |  |  |  | 0 | no: fails the top tb only through 5 formally equivalent modules (PREFLIGHT.md) |
| O1_hybrid_compile_oneshot |  |  |  |  |  | 0 | no (fails the top tb) |
| O2_hybrid_compile_stitch |  |  |  |  |  | 0 | no (fails the top tb) |

Every value latch_study/PPA_SUMMARY.md has for the 3x3 references (copied by the script):

| Variant / design | Final std-cell area (um^2) | Area / total power change (%) | Fmax (MHz) | Setup WNS / TNS (ns) | Dynamic split: internal / switching / dynamic (W) | Leakage (W) | Total power (W) | D_NET cap (pF) | Wire length (um) | Vias | DRC / antenna nets/pins; max-slew/max-cap |
|---|---|---|---|---|---|---|---|---|---|---|---|
| A1 / 3x3 | 2235731 | reference / reference | 99.2363 | -0.0769544 / -0.322059 | 0.3 / 0.0922 / 0.3922 | 7.44e-07 | 0.392244 | 1543.319526 | 9122103.0 | 1245396.0 | 0.0 / 2.0/2.0; not measured |
| B / 3x3 | 2312740 | 3.4444662618177233 / 9.388033978849906 | 98.0925 | -0.194461 / -0.718273 | 0.32814 / 0.100927 / 0.429067 | 7.60921e-07 | 0.429068 | 1667.661449 | 9739427.0 | 1342265.0 | 0.0 / 1.0/1.0; 124.0 / 31.0 |

For context only, 2x2 mesh (not this design): ORFS, SKY130HD, 10 ns, latch_study/PPA_SUMMARY.md.

| design (2x2 mesh) | area um2 | fmax MHz | total power mW |
|---|---|---|---|
| A1 / 2x2 | 780685 | 106.84 | 138.308 |
| B / 2x2 | 808319 | 108.0 | 151.1 |
