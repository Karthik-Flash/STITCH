# O2_hybrid_compile_stitch preflight (pipeline/handoff.py)

optional: every STITCH module that compiles, golden for the rest; fails the mesh tb, PPA indicative only. Optional.

Source: `assembled/hybrid_compile_stitch` (pipeline/assemble.py); identical designs: none.
Modules: 34 (21 LLM-generated, 13 golden; see SOURCES.csv). Top: top_2x2_router.

| check | result |
|---|---|
| Icarus compile (whole mesh) | True |
| mesh tb (tasks/top_2x2_router/tb_signoff.v, cycle-exact against the golden mesh) | FAIL |
| Yosys synth (latch_study script) | True |
| Yosys cells | 119260 |
| Yosys latch cells | 0 |
| Yosys check problems | 8 |
| Yosys logic loops | 1 |
| Verilator errors / hard warnings | 0 / 102 |

First mesh tb failure: `FAIL t=239000 cycle 22: data_out_core_r1 = 60000000, expected 27660500`

## Note

Functionally incorrect: fails the mesh tb. PPA is indicative only.
