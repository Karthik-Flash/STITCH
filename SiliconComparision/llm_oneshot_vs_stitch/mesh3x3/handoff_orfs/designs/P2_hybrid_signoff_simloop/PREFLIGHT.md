# P2_hybrid_signoff_simloop preflight (pipeline/handoff_study.py)

PRIMARY: simloop LLM modules that pass their own sign-off checks (REUSED modules: the 2x2 result of the same arm), golden for the rest; byte-identical to hybrid_signoff_stitch. Required.

Source: `assembled/hybrid_signoff_simloop` (pipeline/assemble_study.py); identical designs: hybrid_signoff_stitch.
Modules: 34 (14 LLM-generated, 20 golden, 0 hand-written A1, 0 wrapper; see SOURCES.csv). Top: top_3x3_router.

| check | result |
|---|---|
| Icarus compile (whole design) | True |
| top tb (tasks/top_3x3_router/tb_signoff.v, cycle-exact against the golden design) | FAIL |
| Yosys synth (latch_study script) | True |
| Yosys cells | 268380 |
| Yosys latch cells | 0 |
| Yosys check problems | 0 |
| Yosys logic loops | 0 |
| Verilator errors / hard warnings | 0 / 0 |

First top tb failure: `FAIL t=269000 cycle 25: data_out_core_r2 = 60000000, expected 32c92d01`

## LLM modules in this design (pipeline/assemble_study.py)

| module | new / reused | drop-in | equivalent to golden (clocks=True) |
|---|---|---|---|
| dff_asynch_clr | reused (2x2) | False | True |
| dff_synch_clr | reused (2x2) | False | True |
| dff_synch_reset | reused (2x2) | False | True |
| dff_synch_set | reused (2x2) | True | True |
| encoder | reused (2x2) | True | False |
| final_op_data | reused (2x2) | True | True |
| jk_ff | reused (2x2) | True | False |
| memory | reused (2x2) | False | True |
| mux | reused (2x2) | True | True |
| priority_encoder | reused (2x2) | True | True |
| register_1bit | reused (2x2) | True | True |
| register_32bit | reused (2x2) | True | True |
| register_4bit | reused (2x2) | True | True |
| routing_algo_mesh | reused (2x2) | False | True |

## Note

Fails the top tb. PPA is indicative only unless the failure is explained above.
