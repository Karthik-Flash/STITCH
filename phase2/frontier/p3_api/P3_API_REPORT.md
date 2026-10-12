# Phase 3 API point: report (Part A) and final-run completion audit

Written 2026-09-29. Every number comes from a script in `phase2/frontier/p3_api/` or `phase2/frontier/`
(`p3_api_analysis.py`, `p3_project.py`, `b_plan.py`, `analysis_set4b.py`, `spend_summary.py`); raw outputs are in
the gitignored `phase2/results/p3_api/`. INR = USD × 96 × 1.18.

**LEAK STATUS: clean** (see the final line of the completion audit).

**New spend (this batch):** OpenAI $0.7344 (INR 83.2), Anthropic $2.6568 (INR 301.0), total $3.3912 (INR 384.2).
**Running total since Set 4:** $13.0345 (INR 1,476.5): Set 4 $1.5905, Set 4b $8.0527, this batch $3.3912.

Pre-registration: `P3_API_PREREG.md`, SHA-256 `680F24F5B63A7125299549603BC3AC1B3A6B5D24E37FFA59830C415B8516C130`,
2026-09-29 20:10:44 UTC, before any Part A paid call.

## Pre-flight (A3), no paid calls

- Toolchain: oss-cad-suite 20260917 = HPC (Yosys 0.69+71 150c32b03, Verilator 5.053 v5.052-103-g1aa87913c,
  Icarus 14.0 s20260301-451-gc9ed76463).
- Gates, same commands as `phase3/hpc/phase3_gate.slurm`, run on a `/tmp` copy of phase3/ (G1 writes into
  phase3/evidence): G0 44 passed / 0 failed; G1 11/11 tasks OK; G2 mock smoke + summarize OK; G5 PASS (11
  baseline_gate runs, no tool text in prompts); G4 PASS; G3 198 runs/model. ALL GATES PASSED.
- Mock parity: a fake model answering Ollama, OpenAI and Anthropic endpoints identically. For all 6 conditions on
  mux3, register_4bit and register_1bit, the prompt sequence hashes of the API wrapper equal the Ollama path's (18 of 18
  condition × task runs) and the (system, user) texts on the wire are identical (96 of 96 requests, both providers).

## Pilot (A4)

Address_select + riscv_alu_flags × 6 conditions × N=1 (the most expensive task of each stratum for 14B). 24 runs,
0 errors, 0 reasoning tokens, 0 truncations. Projection (higher of pilot-based and 14B-call-count-based): OpenAI
$0.25 (90% UB $0.31), Anthropic $0.81 (90% UB $0.89); Part A caps 1.5× = $0.38 and $1.22 (below the $1.5 / $3.5
sub-caps). Actual Part A full runs: OpenAI $0.1411, Anthropic $0.3957 (0.56× and 0.49× projection).

## Part A results: 198/198 runs per model, 0 errored, 0 truncated, 0 reasoning tokens

As-run metrics (tb.v): func_pass, clean_pass, silent structural pass (func_pass and not structurally clean).
`signoff_clean` (primary in PREREG_FINAL) needs tb_signoff.v and is scored offline by the Phase 3 agent; it equals
clean_pass on 9 of 11 tasks.

### GPT-4.1 mini (`gpt-4.1-mini-2025-04-14`)

| condition | stratum | n | func | clean | silent SP | calls/run | tokens/run | INR / clean |
|---|---|---|---|---|---|---|---|---|
| baseline | silent | 18 | 18 | 0 | 18 | 0.00 | 0 | – |
| baseline | visible | 15 | 15 | 15 | 0 | 1.00 | 969 | 0.069 |
| raw_adv | silent | 18 | 18 | 18 | 0 | 1.06 | 1118 | 0.080 |
| raw_adv | visible | 15 | 15 | 15 | 0 | 1.00 | 1220 | 0.076 |
| sem_adv_v2 | silent | 18 | 18 | 18 | 0 | 1.00 | 1124 | 0.073 |
| sem_adv_v2 | visible | 15 | 15 | 15 | 0 | 1.00 | 1413 | 0.071 |
| sem_adv_v3 | silent | 18 | 18 | 18 | 0 | 1.00 | 1152 | 0.072 |
| sem_adv_v3 | visible | 15 | 15 | 15 | 0 | 1.00 | 1383 | 0.069 |
| sem_esc_restart_v3 | silent | 18 | 18 | 18 | 0 | 1.44 | 1772 | 0.146 |
| sem_esc_restart_v3 | visible | 15 | 15 | 15 | 0 | 1.00 | 964 | 0.068 |
| baseline_gate | silent | 18 | 17 | 16 | 1 | 1.61 | 1998 | 0.186 |
| baseline_gate | visible | 15 | 15 | 15 | 0 | 1.00 | 967 | 0.069 |

### Claude Haiku 4.5 (`claude-haiku-4-5-20251001`)

| condition | stratum | n | func | clean | silent SP | calls/run | tokens/run | INR / clean |
|---|---|---|---|---|---|---|---|---|
| baseline | silent | 18 | 18 | 0 | 18 | 0.00 | 0 | – |
| baseline | visible | 15 | 15 | 15 | 0 | 1.00 | 1136 | 0.212 |
| raw_adv | silent | 18 | 18 | 18 | 0 | 1.00 | 1219 | 0.260 |
| raw_adv | visible | 15 | 15 | 15 | 0 | 1.00 | 1472 | 0.254 |
| sem_adv_v2 | silent | 18 | 18 | 18 | 0 | 1.00 | 1364 | 0.266 |
| sem_adv_v2 | visible | 15 | 15 | 15 | 0 | 1.00 | 1701 | 0.280 |
| sem_adv_v3 | silent | 18 | 18 | 18 | 0 | 1.00 | 1402 | 0.270 |
| sem_adv_v3 | visible | 15 | 15 | 15 | 0 | 1.00 | 1669 | 0.275 |
| sem_esc_restart_v3 | silent | 18 | 18 | 18 | 0 | 1.00 | 1071 | 0.246 |
| sem_esc_restart_v3 | visible | 15 | 15 | 15 | 0 | 1.00 | 1136 | 0.212 |
| baseline_gate | silent | 18 | 18 | 18 | 0 | 1.00 | 1068 | 0.244 |
| baseline_gate | visible | 15 | 15 | 15 | 0 | 1.00 | 1136 | 0.212 |

### Primary contrasts (clean_pass as run; points; cell bootstrap 95% CI; sign-flip p; descriptive)

| contrast | GPT-4.1 mini | Claude Haiku 4.5 |
|---|---|---|
| 1. sem_esc_restart_v3 − baseline_gate, pooled (11 cells) | +6.1 [+0.0, +18.2], p=1.000 | +0.0 [+0.0, +0.0], p=1.000 |
|   sim-silent (6) | +11.1 [+0.0, +33.3], p=1.000 | +0.0 |
|   sim-visible (5) | +0.0 | +0.0 |
| 2. sem_adv_v3 − baseline_gate, pooled | +6.1 [+0.0, +18.2], p=1.000 | +0.0 |
|   sim-silent | +11.1 [+0.0, +33.3], p=1.000 | +0.0 |
|   sim-visible | +0.0 | +0.0 |
| 3. baseline_gate − raw_adv, pooled | −6.1 [−18.2, +0.0], p=1.000 | +0.0 |
|   sim-silent | −11.1 [−33.3, +0.0], p=1.000 | +0.0 |
|   sim-visible | +0.0 | +0.0 |
| 4. baseline_gate − baseline, sim-visible (5) | +0.0 | +0.0 |

The whole GPT-4.1 mini effect is 2 runs: baseline_gate on riscv_alu_flags, reps 1 and 3.

### baseline_gate runs not clean while would_fire = 1

- GPT-4.1 mini: riscv_alu_flags rep1 and rep3, both with would_class ['LATCH'] (the v3 interpreter would have named
  the latch; the bare gate verdict did not get the model there within the budget). One of them also failed tb.v
  (func 17/18 on sim-silent).
- Claude Haiku 4.5: none.

## Reading (Part A)

At the top of the ladder, Phase 3 is at ceiling. Every tool-feedback condition reaches clean_pass on all 33 runs for
both models, mostly in one call. Baseline stays at 0/18 on sim-silent tasks by protocol (it stops at func_pass,
which the defective input already has) and 15/15 on sim-visible. So the sim-silent structural gap is entirely a
protocol property at this tier, not a capability gap. The only discriminating cells are baseline_gate on
riscv_alu_flags for GPT-4.1 mini: there the bare "fails synthesis sign-off" verdict failed twice (would_fire = LATCH),
while every condition that feeds tool detail succeeded. That is a +6.1-point, non-significant (p=1.000) pooled edge
for interpreter-bearing arms over the gate. For Claude Haiku 4.5 the verdict alone is enough on every task (all
contrasts 0).

So, of the two outcomes set out before the run: for strong models the verdict carries nearly all of the effect, and
the interpreter's margin is confined to one latch task on one of two models, at N=3. That supports the design rule
"the gate matters for everyone; the interpreter matters most for small models". It gives no evidence that STITCH's
detail still helps strong models in general. Costs are INR 0.07–0.19 per clean pass (GPT-4.1 mini) and
INR 0.21–0.28 (Haiku).

## Completion audit (all planned runs in this batch)

| Part | Provider | Planned | Completed | Errored (reason) | Not run (cap) |
|---|---|---|---|---|---|
| A pilot | OpenAI | 12 | 12 | 0 | 0 |
| A pilot | Anthropic | 12 | 12 | 0 | 0 |
| A full | OpenAI | 198 | 198 | 0 | 0 |
| A full | Anthropic | 198 | 198 | 0 | 0 |
| B (Set 4b) | OpenAI | 48 | 48 | 0 | 0 |
| B (Set 4b) | Anthropic | 123 | 38 | 85 (HTTP 400 "credit balance is too low"; one resume pass, same error) | 0 |

Anthropic Part B completed alu (12), freq_divbyfrac (12), parallel2serial (12), float_multi (2 of 3 remaining). The
85 errored runs: float_multi 1, traffic_light 12, barrel_shifter 12, pulse_detect 12, LIFObuffer 12, fsm 12,
serial2parallel 12, counter_12 12. They cost $0 and remain excluded. **The Anthropic account ran out of credit** at a
cumulative ledger spend of $6.69 across Set 4, Set 4b and this batch (well under the reported $20 prepaid and under
the $10 runner cap). Please check the console balance; the ledger and the account disagree.

Final `scan_secrets.py`: 0 matches; `leak_audit.py`: clean (see the SET4_REPORT.md update for the exact line).

## Deviations

1. **The Anthropic billing failure was not an automatic stop.** The stop rules cover auth failure (401/403);
   "credit balance too low" is an HTTP 400, so each run errored and the driver moved to the next module. It cost $0,
   but 85 runs are recorded as errored instead of the provider stopping at the first one.
2. **Gates run on a copy of phase3/**, because G1 (`validate_tasks.py`) writes into phase3/evidence/; same commands,
   same toolchain.
3. **Model digest** is `api:<model>` (no Ollama digest); returned model IDs, response IDs and fingerprints are in the
   ledger.
4. **Pilot tasks** were the two most expensive per stratum for 14B, not arbitrary, to avoid the Set 4b underestimate.
5. **Contrasts on clean_pass (as run)**, pending offline signoff_clean scoring by the Phase 3 agent.
