# O1_hybrid_compile_oneshot preflight (pipeline/handoff.py)

optional: every one-shot module that compiles, golden for the rest; fails the mesh tb, PPA indicative only. Optional.

Source: `assembled/hybrid_compile_oneshot` (pipeline/assemble.py); identical designs: none.
Modules: 34 (13 LLM-generated, 21 golden; see SOURCES.csv). Top: top_2x2_router.

| check | result |
|---|---|
| Icarus compile (whole mesh) | True |
| mesh tb (tasks/top_2x2_router/tb_signoff.v, cycle-exact against the golden mesh) | FAIL |
| Yosys synth (latch_study script) | True |
| Yosys cells | 120220 |
| Yosys latch cells | 0 |
| Yosys check problems | 0 |
| Yosys logic loops | 0 |
| Verilator errors / hard warnings | 0 / 164 |

First mesh tb failure: `FAIL t=239000 cycle 22: data_out_core_r1 = 60000000, expected 27660500`

## Note

Functionally incorrect: fails the mesh tb. PPA is indicative only.
