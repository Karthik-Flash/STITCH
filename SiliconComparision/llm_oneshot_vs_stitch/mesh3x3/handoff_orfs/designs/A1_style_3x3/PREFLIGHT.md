# A1_style_3x3 preflight (pipeline/handoff_study.py)

optional: the hand-written RTL with only the Yosys-aborting modules fixed; already measured as A1 / 3x3 (latch_study/PPA_SUMMARY.md, PPA_TABLE.md). Optional.

Source: `assembled/A1_style_3x3` (pipeline/assemble_study.py); identical designs: none.
Modules: 34 (0 LLM-generated, 0 golden, 34 hand-written A1, 0 wrapper; see SOURCES.csv). Top: top_3x3_router.

| check | result |
|---|---|
| Icarus compile (whole design) | False |
| top tb (tasks/top_3x3_router/tb_signoff.v, cycle-exact against the golden design) | not run |
| Yosys synth (latch_study script) | True |
| Yosys cells | 269370 |
| Yosys latch cells | 6480 |
| Yosys check problems | 0 |
| Yosys logic loops | 0 |
| Verilator errors / hard warnings | 0 / 0 |

## Note

Fails the top tb. PPA is indicative only unless the failure is explained above.
