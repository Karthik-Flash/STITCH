# P1_hybrid_signoff_oneshot preflight (pipeline/handoff.py)

PRIMARY: one-shot LLM modules that pass their own sign-off checks, golden for the rest. Required.

Source: `assembled/hybrid_signoff_oneshot` (pipeline/assemble.py); identical designs: none.
Modules: 34 (9 LLM-generated, 25 golden; see SOURCES.csv). Top: top_2x2_router.

| check | result |
|---|---|
| Icarus compile (whole mesh) | True |
| mesh tb (tasks/top_2x2_router/tb_signoff.v, cycle-exact against the golden mesh) | FAIL |
| Yosys synth (latch_study script) | True |
| Yosys cells | 118840 |
| Yosys latch cells | 0 |
| Yosys check problems | 144 |
| Yosys logic loops | 0 |
| Verilator errors / hard warnings | 0 / 0 |

First mesh tb failure: `FAIL t=309000 cycle 29: data_out_core_r3 = 22c06511, expected 60000000`

## Note

Fails the cycle-exact mesh tb only through dff_synch_clr, dff_synch_reset, memory. Each is formally equivalent to its golden module (Yosys equivalence check; a negative control fails). The mismatch comes from the golden's blocking-assignment flops (q = d) racing in simulation; the LLM modules use nonblocking (<=). With those swapped back to golden the mesh composes (diag_signoff_dropin_*).
