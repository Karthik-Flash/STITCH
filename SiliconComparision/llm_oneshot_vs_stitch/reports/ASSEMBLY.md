# Assembly of the 2x2 mesh (pipeline/assemble.py)

Top `top_2x2_router` and the module set (34 modules) are A1's (`latch_study/A1_original_synthesisable/mesh2x2`; A1's ORFS config.mk is not in the repository, so the top is the one `latch_study/scripts/run_yosys_stat.sh` uses for mesh2x2). Golden replacements come from `golden/reference` (B-equivalent plus two declaration-only lines).

composes = Icarus compile of the whole mesh + `tasks/top_2x2_router/tb_signoff.v` pass. Yosys: the latch_study script (`synth -top`, `check`, `stat`). check problems = Yosys `check` count (0 = `check -assert` passes). Verilator: `--lint-only -Wall`, p3_eval settings (hard = MULTIDRIVEN, UNOPTFLAT, LATCH, WIDTHTRUNC).

| design | golden modules | composes | Icarus compile | top tb | Yosys ok | cells | latch cells | check problems | logic loops | Verilator errors / hard | aliases |
|---|---|---|---|---|---|---|---|---|---|---|---|
| pure_oneshot | 0 | False | False | not run | False | None | None | None | 0 | 7 / 0 | - |
| hybrid_compile_oneshot | 21 | False | True | FAIL | True | 120220 | 0 | 0 | 0 | 0 / 164 | - |
| hybrid_signoff_oneshot | 25 | False | True | FAIL | True | 118840 | 0 | 144 | 0 | 0 / 0 | - |
| pure_simloop | 0 | False | False | not run | False | None | None | None | 0 | 3 / 0 | - |
| hybrid_compile_simloop | 13 | False | True | FAIL | False | None | None | None | 0 | 0 / 166 | - |
| hybrid_signoff_simloop | 20 | False | True | FAIL | True | 119280 | 0 | 144 | 0 | 0 / 0 | hybrid_signoff_stitch |
| pure_stitch | 0 | False | False | not run | False | None | None | None | 0 | 5 / 0 | - |
| hybrid_compile_stitch | 13 | False | True | FAIL | True | 119260 | 0 | 8 | 1 | 0 / 102 | - |
| control_all_golden | 34 | True | True | PASS | True | 119720 | 0 | 144 | 0 | 0 / 0 | - |
| diag_signoff_dropin_oneshot | 28 | True | True | PASS | True | 118840 | 0 | 144 | 0 | 0 / 0 | - |
| diag_signoff_dropin_simloop | 25 | True | True | PASS | True | 119200 | 0 | 144 | 0 | 0 / 0 | diag_signoff_dropin_stitch |
| A1 (latch_study, sanity) | - | - | - | - | True | 119720 | 2880 | 144 | 0 | - | - |
| golden/reference (B-equivalent) | - | - | - | - | True | 119720 | 0 | 144 | 0 | - | - |

control_all_golden = every module golden through the same assembly and checks (tests the harness). diag_signoff_dropin_<arm> = hybrid_signoff with the LLM modules that fail the drop-in test also replaced (diagnostic only, not a hand-off design).

## LLM modules kept by hybrid_signoff (so_clean in their task)

drop-in = golden mesh with only this module from the arm: compiles and passes the top sign-off tb. equivalent = Yosys formal equivalence with the golden module (synthesis semantics).

| arm | module | drop-in | equivalent to golden |
|---|---|---|---|
| oneshot | dff_synch_clr | False | True |
| oneshot | dff_synch_reset | False | True |
| oneshot | dff_synch_set | True | True |
| oneshot | jk_ff | True | False |
| oneshot | memory | False | True |
| oneshot | mux | True | True |
| oneshot | priority_encoder | True | True |
| oneshot | register_32bit | True | True |
| oneshot | register_4bit | True | True |
| simloop | dff_asynch_clr | False | True |
| simloop | dff_synch_clr | False | True |
| simloop | dff_synch_reset | False | True |
| simloop | dff_synch_set | True | True |
| simloop | encoder | True | False |
| simloop | final_op_data | True | True |
| simloop | jk_ff | True | False |
| simloop | memory | False | True |
| simloop | mux | True | True |
| simloop | priority_encoder | True | True |
| simloop | register_1bit | True | True |
| simloop | register_32bit | True | True |
| simloop | register_4bit | True | True |
| simloop | routing_algo_mesh | False | True |
| stitch | dff_asynch_clr | False | True |
| stitch | dff_synch_clr | False | True |
| stitch | dff_synch_reset | False | True |
| stitch | dff_synch_set | True | True |
| stitch | encoder | True | False |
| stitch | final_op_data | True | True |
| stitch | jk_ff | True | False |
| stitch | memory | False | True |
| stitch | mux | True | True |
| stitch | priority_encoder | True | True |
| stitch | register_1bit | True | True |
| stitch | register_32bit | True | True |
| stitch | register_4bit | True | True |
| stitch | routing_algo_mesh | False | True |

Negative control: oneshot/encoder (compiles, fails its tb) equivalent to golden: False.

## PRIMARY designs (hybrid_signoff)

- hybrid_signoff_oneshot: Fails the cycle-exact mesh tb only through dff_synch_clr, dff_synch_reset, memory. Each is formally equivalent to its golden module (Yosys equivalence check; a negative control fails). The mismatch comes from the golden's blocking-assignment flops (q = d) racing in simulation; the LLM modules use nonblocking (<=). With those swapped back to golden the mesh composes (diag_signoff_dropin_*).
- hybrid_signoff_simloop: Fails the cycle-exact mesh tb only through dff_asynch_clr, dff_synch_clr, dff_synch_reset, memory, routing_algo_mesh. Each is formally equivalent to its golden module (Yosys equivalence check; a negative control fails). The mismatch comes from the golden's blocking-assignment flops (q = d) racing in simulation; the LLM modules use nonblocking (<=) (routing_algo_mesh is combinational: the golden uses nonblocking assignments in an explicit-list always block, the LLM module `always @(*)`). With those swapped back to golden the mesh composes (diag_signoff_dropin_*).

## Audit finding: golden RTL

The golden 2x2 mesh (tasks/top_2x2_router/tb_signoff.v reference) contains blocking-assignment flops that race in simulation; the mesh tb compares cycle-exact against it. The hybrid_signoff meshes fail it only through dff_asynch_clr, dff_synch_clr, dff_synch_reset, memory, routing_algo_mesh. Each is formally equivalent to its golden module (Yosys equivalence check; a negative control fails). The mismatch comes from the golden's blocking-assignment flops (q = d) racing in simulation; the LLM modules use nonblocking (<=) (routing_algo_mesh is combinational: the golden uses nonblocking assignments in an explicit-list always block, the LLM module `always @(*)`). With those swapped back to golden the mesh composes (diag_signoff_dropin_*).

Blocking assignments in the golden's clocked always blocks:

- dff_asynch_clr: tasks/dff_asynch_clr/golden.v:10, tasks/dff_asynch_clr/golden.v:12
- dff_synch_clr: tasks/dff_synch_clr/golden.v:10, tasks/dff_synch_clr/golden.v:12
- dff_synch_reset: tasks/dff_synch_reset/golden.v:8, tasks/dff_synch_reset/golden.v:10
- memory: tasks/memory/golden.v:44, tasks/memory/golden.v:50, tasks/memory/golden.v:54, tasks/memory/golden.v:57
- routing_algo_mesh: none (combinational)

First errors:

- pure_oneshot: Icarus: `design_renamed.v:13: error: 'gnt_or' has already been declared in this scope.`
- hybrid_compile_oneshot: top tb: `FAIL t=239000 cycle 22: data_out_core_r1 = 60000000, expected 27660500`
- hybrid_signoff_oneshot: top tb: `FAIL t=309000 cycle 29: data_out_core_r3 = 22c06511, expected 60000000`
- pure_simloop: Icarus: `design_renamed.v:179: error: 'op1' has already been declared in this scope.`; Yosys: `ERROR: Module `op_data_path' referenced in module `top_module' in cell `op_data_path_inst' does not have a port named 'reset'.`
- hybrid_compile_simloop: top tb: `FAIL t=239000 cycle 22: data_out_core_r1 = 60000000, expected 27660500`; Yosys: `ERROR: Multiple edge sensitive events found for this signal!`
- hybrid_signoff_simloop: top tb: `FAIL t=309000 cycle 29: data_out_core_r3 = 22c06511, expected 60000000`
- pure_stitch: Icarus: `design_renamed.v:176: error: 'op1' has already been declared in this scope.`; Yosys: `ERROR: Module `op_data_path' referenced in module `top_module' in cell `op_data_path_inst' does not have a port named 'data_to_core_ch4'.`
- hybrid_compile_stitch: top tb: `FAIL t=239000 cycle 22: data_out_core_r1 = 60000000, expected 27660500`

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
- diag_signoff_dropin_oneshot: none
- diag_signoff_dropin_simloop: none
