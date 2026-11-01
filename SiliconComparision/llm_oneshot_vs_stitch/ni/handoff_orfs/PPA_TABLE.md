# PPA table (fill in the empty cells)

ni hand-off. Yosys latch cells and functionally correct are prefilled by pipeline/handoff_study.py (Yosys: the latch_study script, reports/ASSEMBLY.md; functionally correct = passes wrapper/ni_pair/tb_signoff.v).

| design | area um2 | fmax MHz | total power mW | check_setup unconstrained endpoints | flow errors / notes | Yosys latch cells | functionally correct |
|---|---|---|---|---|---|---|---|
| C0_control_all_golden |  |  |  |  |  | 0 | yes (passes the top tb) |
| P1_hybrid_signoff_oneshot |  |  |  |  |  | 0 | yes (passes the top tb) |
| O1_hybrid_compile_oneshot |  |  |  |  |  | 0 | no (fails the top tb) |
| O2_hybrid_compile_simloop |  |  |  |  |  | 0 | no (fails the top tb) |
| O3_hybrid_compile_stitch |  |  |  |  |  | 0 | no (fails the top tb) |
