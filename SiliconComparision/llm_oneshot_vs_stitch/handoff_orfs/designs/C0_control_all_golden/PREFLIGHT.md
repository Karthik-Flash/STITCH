# C0_control_all_golden preflight (pipeline/handoff.py)

every module golden, through our assembly: setup check, must reproduce B. Required.

Source: `assembled/control_all_golden` (pipeline/assemble.py); identical designs: none.
Modules: 34 (0 LLM-generated, 34 golden; see SOURCES.csv). Top: top_2x2_router.

| check | result |
|---|---|
| Icarus compile (whole mesh) | True |
| mesh tb (tasks/top_2x2_router/tb_signoff.v, cycle-exact against the golden mesh) | PASS |
| Yosys synth (latch_study script) | True |
| Yosys cells | 119720 |
| Yosys latch cells | 0 |
| Yosys check problems | 144 |
| Yosys logic loops | 0 |
| Verilator errors / hard warnings | 0 / 0 |
