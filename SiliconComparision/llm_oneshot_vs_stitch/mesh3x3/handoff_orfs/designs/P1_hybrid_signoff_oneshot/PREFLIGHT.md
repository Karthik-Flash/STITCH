# P1_hybrid_signoff_oneshot preflight (pipeline/handoff_study.py)

PRIMARY: oneshot LLM modules that pass their own sign-off checks (REUSED modules: the 2x2 result of the same arm), golden for the rest. Required.

Source: `assembled/hybrid_signoff_oneshot` (pipeline/assemble_study.py); identical designs: none.
Modules: 34 (9 LLM-generated, 25 golden, 0 hand-written A1, 0 wrapper; see SOURCES.csv). Top: top_3x3_router.

| check | result |
|---|---|
| Icarus compile (whole design) | True |
| top tb (tasks/top_3x3_router/tb_signoff.v, cycle-exact against the golden design) | FAIL |
| Yosys synth (latch_study script) | True |
| Yosys cells | 267390 |
| Yosys latch cells | 0 |
| Yosys check problems | 0 |
| Yosys logic loops | 0 |
| Verilator errors / hard warnings | 0 / 0 |

First top tb failure: `FAIL t=329000 cycle 31: data_out_core_r3 = 23351202, expected 60000000`

## LLM modules in this design (pipeline/assemble_study.py)

| module | new / reused | drop-in | equivalent to golden (clocks=True) |
|---|---|---|---|
| dff_synch_clr | reused (2x2) | False | True |
| dff_synch_reset | reused (2x2) | False | True |
| dff_synch_set | reused (2x2) | True | True |
| jk_ff | reused (2x2) | True | False |
| memory | reused (2x2) | False | True |
| mux | reused (2x2) | True | True |
| priority_encoder | reused (2x2) | True | True |
| register_32bit | reused (2x2) | True | True |
| register_4bit | reused (2x2) | True | True |

## Note

Fails the top tb. PPA is indicative only unless the failure is explained above.
