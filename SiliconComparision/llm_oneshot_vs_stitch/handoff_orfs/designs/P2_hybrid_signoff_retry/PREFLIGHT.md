# P2_hybrid_signoff_retry preflight (pipeline/handoff.py)

PRIMARY: same after the retry loops (simulation-only retry and STITCH give byte-identical designs). Required.

Source: `assembled/hybrid_signoff_simloop` (pipeline/assemble.py); identical designs: hybrid_signoff_stitch.
Modules: 34 (14 LLM-generated, 20 golden; see SOURCES.csv). Top: top_2x2_router.

| check | result |
|---|---|
| Icarus compile (whole mesh) | True |
| mesh tb (tasks/top_2x2_router/tb_signoff.v, cycle-exact against the golden mesh) | FAIL |
| Yosys synth (latch_study script) | True |
| Yosys cells | 119280 |
| Yosys latch cells | 0 |
| Yosys check problems | 144 |
| Yosys logic loops | 0 |
| Verilator errors / hard warnings | 0 / 0 |

First mesh tb failure: `FAIL t=309000 cycle 29: data_out_core_r3 = 22c06511, expected 60000000`

## Note

Fails the cycle-exact mesh tb only through dff_asynch_clr, dff_synch_clr, dff_synch_reset, memory, routing_algo_mesh. Each is formally equivalent to its golden module (Yosys equivalence check; a negative control fails). The mismatch comes from the golden's blocking-assignment flops (q = d) racing in simulation; the LLM modules use nonblocking (<=) (routing_algo_mesh is combinational: the golden uses nonblocking assignments in an explicit-list always block, the LLM module `always @(*)`). With those swapped back to golden the mesh composes (diag_signoff_dropin_*).
