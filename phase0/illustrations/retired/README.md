# `illustrations/retired/` — the failure landscape at a glance

Every candidate designed, probed, or run for this project and then dropped.
This file is an index only — one line per candidate, enough to see the shape
of what's been tried without opening every subdirectory. Full reasoning,
data, and per-sample tables live in `retired_candidates.md`, which this file
points into section by section. Read `retired_candidates.md` before designing
anything new; it defines the recipe these failures collectively established.

**Paper-ready synthesis of the three most-cited findings:**
`../../evidence/phase0_illustration_hunt_findings.md`.

## Index

| Module | Target mechanism | Samples | Retirement reason (one line) | Detail |
|---|---|---|---|---|
| `adder_with_overflow` | `UNDRIVEN` on a forgotten output | 1 (real run, spec v1) | Target output assigned unprompted on iteration 1 in every condition — the defect class does not occur | §1 |
| `fsm_next_state_error` | `UNDRIVEN` on a forgotten output | 1 (real run) | Same — forgotten-output class unreachable | §1 |
| `datapath_mux_alu` | `UNUSEDSIGNAL` on a forgotten top-level gate | 1 (gemma3:4b) + N=3 (llama3.1) | Too large for gemma3:4b's convergence horizon; llama3.1 N=3 passes 2/3 but `semantic_fired=0` in all three — not attributable | §1a |
| `instr_decode_unit` | `UNUSEDSIGNAL` on a forgotten top-level gate | 1 + N=3 (gemma3:4b, 4 total) | Mechanism fires cleanly when reached (confirmed once), but `sem_adv` never passes across the 3 fresh samples — NOISY | §1b |
| `alu_with_enable` | `UNUSEDSIGNAL` on a forgotten top-level gate | 1 (each model) | Redesign over-corrected: `PASS\|1` on gemma3:4b with `semantic_fired=0` — too easy, same shape as `cmp8_en` | §1c |
| `counter_with_enable` | `UNUSEDSIGNAL` | 1 | Spec stated the gate-off behaviour outright — handed over the answer | §2 |
| `counter_with_enable_dir` | `UNUSEDSIGNAL` | 1 | Same | §2 |
| `register_with_load` | `UNUSEDSIGNAL` | 1 | Same | §2 |
| `cmp8_en` | `UNUSEDSIGNAL` | 1 | Too easy — model used `en` correctly, `PASS\|1` all conditions | §2 |
| `seg7_blank` | `UNUSEDSIGNAL` | 1 | Mechanism fires correctly; ten 7-segment patterns introduce unrelated errors it never converges past | §2 |
| `mode_mux_latch` | Yosys latch (missing `case` default) | 3 sweeps | `SYSTEM_PROMPT` rule 3 pre-empts the bug before any tool runs — confirmed across all three | §3 |
| `priority_chain_comb` | Combinational loop | 1 (each model) | Model's actual defect was a wrong priority order — a logic error, no structural fingerprint | §3 |
| `arbiter_two_writers` | `MULTIDRIVEN` | 0 (tool-level only, no LLM run) | Two hand-written RTL designs, neither triggers `MULTIDRIVEN` from Verilator | §5 |
| `traffic_light_fsm` | Yosys latch | 0 (failed pre-screen) | Registered `state` inside a clocked block — Yosys correctly declines to infer a latch there | §6 |
| `shift_reg_with_enable` | `UNUSEDSIGNAL` | 0 (never built) | Superseded before being written — same shape as `counter_with_enable` | §6 |

## Two proven, for contrast

`decoder_3to8` and `mux4_oe` are the only candidates that cleared this bar —
**3/3 N=3 replication**, not a single draw. They live in `../proven/`, not
here. See `../proven/README.md` for what "proven" requires.

## What this list is for

Every retirement reason above traces back to one of a small number of causes,
laid out in full in `retired_candidates.md` §2's recipe and
`../../evidence/phase0_illustration_hunt_findings.md`'s consolidated
findings:

- The spec handed the model the answer (states the gate-off behaviour).
- The target defect is one `SYSTEM_PROMPT` already pre-empts.
- The module is too complex to converge within the iteration budget.
- The model doesn't reliably produce the target defect at all (forgotten
  **outputs**, as opposed to forgotten **inputs** — a whole class, not a
  one-off).
- A single-draw result that looked clean did not survive N=3 replication.

Read `retired_candidates.md`'s §2 recipe table and
`phase0_illustration_hunt_findings.md` §3 before starting a new candidate —
both exist specifically so the next attempt doesn't re-discover one of these
the expensive way.
