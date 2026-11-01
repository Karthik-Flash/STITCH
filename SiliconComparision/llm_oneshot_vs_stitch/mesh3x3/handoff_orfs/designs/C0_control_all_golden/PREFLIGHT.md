# C0_control_all_golden preflight (pipeline/handoff_study.py)

every module golden, through our assembly: like-for-like reference (B-style RTL). Required.

Source: `assembled/control_all_golden` (pipeline/assemble_study.py); identical designs: none.
Modules: 34 (0 LLM-generated, 34 golden, 0 hand-written A1, 0 wrapper; see SOURCES.csv). Top: top_3x3_router.

| check | result |
|---|---|
| Icarus compile (whole design) | True |
| top tb (tasks/top_3x3_router/tb_signoff.v, cycle-exact against the golden design) | PASS |
| Yosys synth (latch_study script) | True |
| Yosys cells | 269370 |
| Yosys latch cells | 0 |
| Yosys check problems | 0 |
| Yosys logic loops | 0 |
| Verilator errors / hard warnings | 0 / 0 |
