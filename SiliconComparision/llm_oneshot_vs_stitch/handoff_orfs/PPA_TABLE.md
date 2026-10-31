# PPA table (fill in the empty cells)

A1 and B: ORFS, SKY130HD, 10 ns clock, from latch_study/PPA_SUMMARY.md. Yosys latch cells and functionally correct are prefilled by pipeline/handoff.py (Yosys: the latch_study script, reports/ASSEMBLY.md; the B row uses golden/reference, the B-equivalent RTL; functionally correct = passes the cycle-exact mesh tb).

| design | area um2 | fmax MHz | total power mW | check_setup unconstrained endpoints | flow errors / notes | Yosys latch cells | functionally correct |
|---|---|---|---|---|---|---|---|
| A1 (primary ref) | 780685 | 106.84 | 138.308 | not measured | - | 2880 | reference (original RTL, with latches) |
| B (like-for-like ref) | 808319 | 108.0 | 151.1 | not measured | - | 0 | yes (golden) |
| C0_control_all_golden |  |  |  |  |  | 0 | yes (passes the mesh tb) |
| P1_hybrid_signoff_oneshot |  |  |  |  |  | 0 | no: fails the cycle-exact mesh tb only through 3 formally equivalent modules (PREFLIGHT.md) |
| P2_hybrid_signoff_retry |  |  |  |  |  | 0 | no: fails the cycle-exact mesh tb only through 5 formally equivalent modules (PREFLIGHT.md) |
| O1_hybrid_compile_oneshot |  |  |  |  |  | 0 | no (fails the mesh tb) |
| O2_hybrid_compile_stitch |  |  |  |  |  | 0 | no (fails the mesh tb) |
