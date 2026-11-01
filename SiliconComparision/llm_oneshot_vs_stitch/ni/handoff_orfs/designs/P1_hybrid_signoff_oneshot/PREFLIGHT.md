# P1_hybrid_signoff_oneshot preflight (pipeline/handoff_study.py)

PRIMARY: oneshot LLM modules that pass their own sign-off checks (REUSED modules: the 2x2 result of the same arm), golden for the rest; byte-identical to hybrid_signoff_simloop, hybrid_signoff_stitch. Optional.

Source: `assembled/hybrid_signoff_oneshot` (pipeline/assemble_study.py); identical designs: hybrid_signoff_simloop, hybrid_signoff_stitch.
Modules: 10 (2 LLM-generated, 7 golden, 0 hand-written A1, 1 wrapper; see SOURCES.csv). Top: ni_pair.

| check | result |
|---|---|
| Icarus compile (whole design) | True |
| top tb (wrapper/ni_pair/tb_signoff.v, property checks) | PASS |
| Yosys synth (latch_study script) | True |
| Yosys cells | 1767 |
| Yosys latch cells | 0 |
| Yosys check problems | 0 |
| Yosys logic loops | 0 |
| Verilator errors / hard warnings | 0 / 0 |

## LLM modules in this design (pipeline/assemble_study.py)

| module | new / reused | drop-in | equivalent to golden (clocks=True) |
|---|---|---|---|
| jk_ff | reused (2x2) | True | False |
| memory | reused (2x2) | True | True |
