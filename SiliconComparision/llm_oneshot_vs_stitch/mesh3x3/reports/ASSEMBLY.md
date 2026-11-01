# Assembly of the mesh3x3 designs (pipeline/assemble_study.py)

Top `top_3x3_router`. 34 modules: 1 NEW (generated in this study: top_3x3_router) and 33 REUSED (the 2x2 final file of the same arm, reports/REUSE.md). Golden replacements: tasks/<m>/golden.v (NEW), golden/reference (REUSED).

composes = Icarus compile of the whole design + `tasks/top_3x3_router/tb_signoff.v` pass (cycle-exact against the golden design). Yosys: the latch_study script (`synth -top`, `check`, `stat`). Verilator: `--lint-only -Wall`, p3_eval settings (hard = MULTIDRIVEN, UNOPTFLAT, LATCH, WIDTHTRUNC).

| design | golden modules | LLM modules (new / reused) | composes | Icarus compile | top tb | Yosys ok | cells | latch cells | check problems | logic loops | Verilator errors / hard | aliases |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| pure_oneshot | 0 | 1 / 33 | False | False | not run | False | None | None | None | 0 | 7 / 0 | - |
| hybrid_compile_oneshot | 21 | 1 / 12 | False | True | FAIL | True | 270495 | 0 | 1440 | 0 | 0 / 13 | - |
| hybrid_signoff_oneshot | 25 | 0 / 9 | False | True | FAIL | True | 267390 | 0 | 0 | 0 | 0 / 0 | - |
| pure_simloop | 0 | 1 / 33 | False | False | not run | False | None | None | None | 0 | 3 / 0 | - |
| hybrid_compile_simloop | 13 | 1 / 20 | False | True | FAIL | False | None | None | None | 0 | 0 / 15 | - |
| hybrid_signoff_simloop | 20 | 0 / 14 | False | True | FAIL | True | 268380 | 0 | 0 | 0 | 0 / 0 | hybrid_signoff_stitch |
| pure_stitch | 0 | 1 / 33 | False | False | not run | False | None | None | None | 0 | 5 / 0 | - |
| hybrid_compile_stitch | 14 | 0 / 20 | False | True | FAIL | True | 268335 | 0 | 8 | 1 | 0 / 202 | - |
| control_all_golden | 34 | 0 / 0 | True | True | PASS | True | 269370 | 0 | 0 | 0 | 0 / 0 | - |
| A1_style_3x3 | 0 | 0 / 0 | False | False | not run | True | 269370 | 6480 | 0 | 0 | 0 / 0 | - |
| diag_signoff_dropin_oneshot | 28 | 0 / 6 | True | True | PASS | True | 267390 | 0 | 0 | 0 | 0 / 0 | - |
| diag_signoff_dropin_simloop | 25 | 0 / 9 | True | True | PASS | True | 268200 | 0 | 0 | 0 | 0 / 0 | diag_signoff_dropin_stitch |
| golden/reference (sanity) | - | - | - | - | - | True | 269370 | 0 | 0 | 0 | - | - |

control_all_golden = every module golden. A1_style_3x3 = golden/A1 (reports/HANDWRITTEN.md). diag_signoff_dropin_<arm> = hybrid_signoff with the LLM modules that fail the drop-in test also replaced (diagnostic only).

## LLM modules kept by hybrid_signoff (so_clean in their task)

drop-in = golden design with only this module from the arm passes the top testbench. equivalent = Yosys formal equivalence with the golden module (clocks=True: clk2fflogic; golden children flattened). mutant rejected = the LLM module with one operator changed is not equivalent (control).

| arm | module | new / reused | drop-in | equivalent to golden | mutant rejected |
|---|---|---|---|---|---|
| oneshot | dff_synch_clr | reused (2x2) | False | True | True |
| oneshot | dff_synch_reset | reused (2x2) | False | True | True |
| oneshot | dff_synch_set | reused (2x2) | True | True | True |
| oneshot | jk_ff | reused (2x2) | True | False | - |
| oneshot | memory | reused (2x2) | False | True | True |
| oneshot | mux | reused (2x2) | True | True | True |
| oneshot | priority_encoder | reused (2x2) | True | True | True |
| oneshot | register_32bit | reused (2x2) | True | True | True |
| oneshot | register_4bit | reused (2x2) | True | True | True |
| simloop | dff_asynch_clr | reused (2x2) | False | True | True |
| simloop | dff_synch_clr | reused (2x2) | False | True | True |
| simloop | dff_synch_reset | reused (2x2) | False | True | True |
| simloop | dff_synch_set | reused (2x2) | True | True | True |
| simloop | encoder | reused (2x2) | True | False | - |
| simloop | final_op_data | reused (2x2) | True | True | True |
| simloop | jk_ff | reused (2x2) | True | False | - |
| simloop | memory | reused (2x2) | False | True | True |
| simloop | mux | reused (2x2) | True | True | True |
| simloop | priority_encoder | reused (2x2) | True | True | True |
| simloop | register_1bit | reused (2x2) | True | True | True |
| simloop | register_32bit | reused (2x2) | True | True | True |
| simloop | register_4bit | reused (2x2) | True | True | True |
| simloop | routing_algo_mesh | reused (2x2) | False | True | True |
| stitch | dff_asynch_clr | reused (2x2) | False | True | True |
| stitch | dff_synch_clr | reused (2x2) | False | True | True |
| stitch | dff_synch_reset | reused (2x2) | False | True | True |
| stitch | dff_synch_set | reused (2x2) | True | True | True |
| stitch | encoder | reused (2x2) | True | False | - |
| stitch | final_op_data | reused (2x2) | True | True | True |
| stitch | jk_ff | reused (2x2) | True | False | - |
| stitch | memory | reused (2x2) | False | True | True |
| stitch | mux | reused (2x2) | True | True | True |
| stitch | priority_encoder | reused (2x2) | True | True | True |
| stitch | register_1bit | reused (2x2) | True | True | True |
| stitch | register_32bit | reused (2x2) | True | True | True |
| stitch | register_4bit | reused (2x2) | True | True | True |
| stitch | routing_algo_mesh | reused (2x2) | False | True | True |

Negative control: the 2x2 one-shot encoder (compiles, fails its tb) equivalent to golden: False.

First errors:

- pure_oneshot: Icarus: `design_renamed.v:13: error: 'gnt_or' has already been declared in this scope.`
- hybrid_compile_oneshot: top tb: `FAIL t=14000 cycle 0: data_out_core_r1 = xxxxxxxx, expected 60000000`
- hybrid_signoff_oneshot: top tb: `FAIL t=329000 cycle 31: data_out_core_r3 = 23351202, expected 60000000`
- pure_simloop: Icarus: `design_renamed.v:179: error: 'op1' has already been declared in this scope.`; Yosys: `ERROR: Module `op_data_path' referenced in module `top_module' in cell `op_data_path_inst' does not have a port named 'reset'.`
- hybrid_compile_simloop: top tb: `FAIL t=14000 cycle 0: data_out_core_r1 = xxxxxxxx, expected 60000000`; Yosys: `ERROR: Multiple edge sensitive events found for this signal!`
- hybrid_signoff_simloop: top tb: `FAIL t=269000 cycle 25: data_out_core_r2 = 60000000, expected 32c92d01`
- pure_stitch: Icarus: `design_renamed.v:176: error: 'op1' has already been declared in this scope.`; Yosys: `ERROR: Module `op_data_path' referenced in module `top_module' in cell `op_data_path_inst' does not have a port named 'data_to_core_ch4'.`
- hybrid_compile_stitch: top tb: `FAIL t=179000 cycle 16: data_out_core_r2 = 60000000, expected 248ce301`
- A1_style_3x3: Icarus: `design_renamed.v:723: error: Unable to bind wire/reg/memory `rd_en_out' in `tb.dut.r5.ip_link1.vc1'`

Extra module definitions dropped from LLM files:

- pure_oneshot: none
- hybrid_compile_oneshot: none
- hybrid_signoff_oneshot: none
- pure_simloop: none
- hybrid_compile_simloop: none
- hybrid_signoff_simloop: none
- pure_stitch: none
- hybrid_compile_stitch: none
- control_all_golden: none
- A1_style_3x3: none
- diag_signoff_dropin_oneshot: none
- diag_signoff_dropin_simloop: none
