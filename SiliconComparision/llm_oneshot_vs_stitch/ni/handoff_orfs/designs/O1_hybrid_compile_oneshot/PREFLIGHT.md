# O1_hybrid_compile_oneshot preflight (pipeline/handoff_study.py)

optional: every oneshot module that compiles, golden for the rest; fails the top tb, PPA indicative only. Optional.

Source: `assembled/hybrid_compile_oneshot` (pipeline/assemble_study.py); identical designs: none.
Modules: 10 (5 LLM-generated, 4 golden, 0 hand-written A1, 1 wrapper; see SOURCES.csv). Top: ni_pair.

| check | result |
|---|---|
| Icarus compile (whole design) | True |
| top tb (wrapper/ni_pair/tb_signoff.v, property checks) | FAIL |
| Yosys synth (latch_study script) | True |
| Yosys cells | 1580 |
| Yosys latch cells | 0 |
| Yosys check problems | 0 |
| Yosys logic loops | 0 |
| Verilator errors / hard warnings | 0 / 4 |

First top tb failure: `FAIL property: FIFO flag output rose without a write (t=139000)`

## Note

Fails the top tb. PPA is indicative only unless the failure is explained above.
