# C0_control_all_golden preflight (pipeline/handoff_study.py)

every module golden, through our assembly: like-for-like reference (B-style RTL); byte-identical to A1_style_ni (the hand-written NI RTL synthesises without latches, nothing to fix), so it is also the A1-style reference. Optional.

Source: `assembled/control_all_golden` (pipeline/assemble_study.py); identical designs: A1_style_ni.
Modules: 10 (0 LLM-generated, 9 golden, 0 hand-written A1, 1 wrapper; see SOURCES.csv). Top: ni_pair.

| check | result |
|---|---|
| Icarus compile (whole design) | True |
| top tb (wrapper/ni_pair/tb_signoff.v, property checks) | PASS |
| Yosys synth (latch_study script) | True |
| Yosys cells | 1799 |
| Yosys latch cells | 0 |
| Yosys check problems | 0 |
| Yosys logic loops | 0 |
| Verilator errors / hard warnings | 0 / 0 |
