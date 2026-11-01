# O1_hybrid_compile_oneshot preflight (pipeline/handoff_study.py)

optional: every oneshot module that compiles, golden for the rest; fails the top tb, PPA indicative only. Optional.

Source: `assembled/hybrid_compile_oneshot` (pipeline/assemble_study.py); identical designs: none.
Modules: 34 (13 LLM-generated, 21 golden, 0 hand-written A1, 0 wrapper; see SOURCES.csv). Top: top_3x3_router.

| check | result |
|---|---|
| Icarus compile (whole design) | True |
| top tb (tasks/top_3x3_router/tb_signoff.v, cycle-exact against the golden design) | FAIL |
| Yosys synth (latch_study script) | True |
| Yosys cells | 270495 |
| Yosys latch cells | 0 |
| Yosys check problems | 1440 |
| Yosys logic loops | 0 |
| Verilator errors / hard warnings | 0 / 13 |

First top tb failure: `FAIL t=14000 cycle 0: data_out_core_r1 = xxxxxxxx, expected 60000000`

## Note

Fails the top tb. PPA is indicative only unless the failure is explained above.
