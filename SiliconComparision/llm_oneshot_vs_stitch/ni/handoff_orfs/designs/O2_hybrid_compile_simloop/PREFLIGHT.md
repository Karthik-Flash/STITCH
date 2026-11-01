# O2_hybrid_compile_simloop preflight (pipeline/handoff_study.py)

optional: every simloop module that compiles, golden for the rest; fails the top tb, PPA indicative only. Optional.

Source: `assembled/hybrid_compile_simloop` (pipeline/assemble_study.py); identical designs: none.
Modules: 10 (8 LLM-generated, 1 golden, 0 hand-written A1, 1 wrapper; see SOURCES.csv). Top: ni_pair.

| check | result |
|---|---|
| Icarus compile (whole design) | True |
| top tb (wrapper/ni_pair/tb_signoff.v, property checks) | FAIL |
| Yosys synth (latch_study script) | True |
| Yosys cells | 1578 |
| Yosys latch cells | 0 |
| Yosys check problems | 2 |
| Yosys logic loops | 0 |
| Verilator errors / hard warnings | 0 / 4 |

First top tb failure: `FAIL property: FIFO flag output rose without a write (t=199000)`

## Note

Fails the top tb. PPA is indicative only unless the failure is explained above.
