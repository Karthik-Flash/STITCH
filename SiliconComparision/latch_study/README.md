# Latch study (closed)

**Closed on 2026-11-05.**

Question: what does removing the inferred latches of the MPSoC mesh cost in silicon? Answer, from one ORFS run per
variant (SKY130HD, 10 ns clock) on the 2x2 and 3x3 meshes: about 3.5% more area and an estimated 9% more power,
because the repaired registers are real clocked flip-flops. The gain is timing analysability and sign-off
correctness, not lower PPA (`PPA_SUMMARY.md`).

Not done: variant C (STITCH's own repair) in ORFS, and the checks listed in `PPA_SUMMARY.md` section 6 (untimed
endpoints, clock sinks, cell-type histograms, several placement seeds).

The silicon work continues in `../LLM_generation_study/` (Vivado, ZedBoard). Contents of this folder: the
latch_study section of `../README.md`, and `COWORKER_BRIEF.md`.
