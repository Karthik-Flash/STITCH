# Assembly of the ni designs (pipeline/assemble_study.py)

Top `ni_pair` (wrapper `wrapper/ni_pair.v`, not golden, never generated; part of every design). 9 modules: 4 NEW (generated in this study: depack, new1, nidepack, rp1) and 5 REUSED (the 2x2 final file of the same arm, reports/REUSE.md). Golden replacements: tasks/<m>/golden.v (NEW), golden/reference (REUSED).

composes = Icarus compile of the whole design + `wrapper/ni_pair/tb_signoff.v` pass (property checks: the primary verdict for ni_pair, CP1). Yosys: the latch_study script (`synth -top`, `check`, `stat`). Verilator: `--lint-only -Wall`, p3_eval settings (hard = MULTIDRIVEN, UNOPTFLAT, LATCH, WIDTHTRUNC).

| design | golden modules | LLM modules (new / reused) | composes | Icarus compile | top tb | Yosys ok | cells | latch cells | check problems | logic loops | Verilator errors / hard | aliases |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| pure_oneshot | 0 | 4 / 5 | False | False | not run | False | None | None | None | 0 | 50 / 4 | - |
| hybrid_compile_oneshot | 4 | 2 / 3 | False | True | FAIL | True | 1580 | 0 | 0 | 0 | 0 / 4 | - |
| hybrid_signoff_oneshot | 7 | 0 / 2 | True | True | PASS | True | 1767 | 0 | 0 | 0 | 0 / 0 | hybrid_signoff_simloop, hybrid_signoff_stitch |
| pure_simloop | 0 | 4 / 5 | False | False | not run | False | None | None | None | 0 | 5 / 3 | - |
| hybrid_compile_simloop | 1 | 3 / 5 | False | True | FAIL | True | 1578 | 0 | 2 | 0 | 0 / 4 | - |
| pure_stitch | 0 | 4 / 5 | False | False | not run | False | None | None | None | 0 | 5 / 3 | - |
| hybrid_compile_stitch | 2 | 2 / 5 | False | True | FAIL | True | 1587 | 0 | 1 | 0 | 0 / 3 | - |
| control_all_golden | 9 | 0 / 0 | True | True | PASS | True | 1799 | 0 | 0 | 0 | 0 / 0 | A1_style_ni |

control_all_golden = every module golden. A1_style_ni = golden/A1 (reports/HANDWRITTEN.md). diag_signoff_dropin_<arm> = hybrid_signoff with the LLM modules that fail the drop-in test also replaced (diagnostic only).

## LLM modules kept by hybrid_signoff (so_clean in their task)

drop-in = golden design with only this module from the arm passes the top testbench. equivalent = Yosys formal equivalence with the golden module (clocks=True: clk2fflogic; golden children flattened). mutant rejected = the LLM module with one operator changed is not equivalent (control).

| arm | module | new / reused | drop-in | equivalent to golden | mutant rejected |
|---|---|---|---|---|---|
| oneshot | jk_ff | reused (2x2) | True | False | - |
| oneshot | memory | reused (2x2) | True | True | True |
| simloop | jk_ff | reused (2x2) | True | False | - |
| simloop | memory | reused (2x2) | True | True | True |
| stitch | jk_ff | reused (2x2) | True | False | - |
| stitch | memory | reused (2x2) | True | True | True |

Negative control: the 2x2 one-shot encoder (compiles, fails its tb) equivalent to golden: False.

First errors:

- pure_oneshot: Icarus: `design_renamed.v:183: error: 'j' is not a valid l-value for a procedural assignment.`; Yosys: `ERROR: Output port nidepack.router_fifo_inst.rd_dir (router_fifo) is connected to constants: 1'0`
- hybrid_compile_oneshot: top tb: `FAIL property: FIFO flag output rose without a write (t=139000)`
- pure_simloop: Icarus: `design_renamed.v:365: error: expression not valid in assign l-value: 1'd0`; Yosys: `ERROR: Output port nidepack.router_fifo_inst.rd_dir (router_fifo) is connected to constants: 1'0`
- hybrid_compile_simloop: top tb: `FAIL property: FIFO flag output rose without a write (t=199000)`
- pure_stitch: Icarus: `design_renamed.v:301: error: expression not valid in assign l-value: 3'd0`; Yosys: `ERROR: Output port nidepack.depack_inst.c_rd (depack) is connected to constants: 1'0`
- hybrid_compile_stitch: top tb: `FAIL property: FIFO flag output rose without a write (t=129000)`

Extra module definitions dropped from LLM files:

- pure_oneshot: none
- hybrid_compile_oneshot: none
- hybrid_signoff_oneshot: none
- pure_simloop: none
- hybrid_compile_simloop: none
- pure_stitch: none
- hybrid_compile_stitch: none
- control_all_golden: none
