# O2_hybrid_compile_stitch preflight (pipeline/handoff_study.py)

optional: every stitch module that compiles, golden for the rest; fails the top tb, PPA indicative only. Optional.

Source: `assembled/hybrid_compile_stitch` (pipeline/assemble_study.py); identical designs: none.
Modules: 34 (20 LLM-generated, 14 golden, 0 hand-written A1, 0 wrapper; see SOURCES.csv). Top: top_3x3_router.

| check | result |
|---|---|
| Icarus compile (whole design) | True |
| top tb (tasks/top_3x3_router/tb_signoff.v, cycle-exact against the golden design) | FAIL |
| Yosys synth (latch_study script) | True |
| Yosys cells | 268335 |
| Yosys latch cells | 0 |
| Yosys check problems | 8 |
| Yosys logic loops | 1 |
| Verilator errors / hard warnings | 0 / 202 |

First top tb failure: `FAIL t=179000 cycle 16: data_out_core_r2 = 60000000, expected 248ce301`

## Note

Fails the top tb. PPA is indicative only unless the failure is explained above.
