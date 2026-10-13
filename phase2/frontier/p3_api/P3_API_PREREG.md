# Phase 3 API point: pre-registration

Written before any paid Part A call. The SHA-256 of this file and the time are recorded in
`P3_API_REPORT.md`. Changes after hashing go in dated amendments at the end.

## Purpose and reading

A top-of-ladder point for Phase 3's main contrasts: the Phase 3 final-batch protocol run unchanged on two
commercial non-reasoning API models. It is **descriptive at N=3**. The API models are reported as their own
rows and are **never pooled into the six-model headline** of `phase3/evidence/PREREG_FINAL.md`.

## Protocol (identical to the Phase 3 final batch)

- Runner: `phase3/runner/stitch_runner_p3.py`, unmodified and imported read-only. `phase2/frontier/p3_api/p3_api_runner.py`
  swaps only the model transport (its `Ollama` class → the `backends.py` API adapter) and the model digest, which
  becomes `api:<model>`. Mock parity (A3b) verified that the (system, user) texts sent are byte-identical to the Ollama
  path for all 6 conditions on mux3, register_4bit and register_1bit (96 of 96 requests, both providers).
- 11 tasks × 6 conditions (baseline, raw_adv, sem_adv_v2, sem_adv_v3, sem_esc_restart_v3, baseline_gate) × N=3 =
  198 runs per model.
- Protocol `feedback_first_v2`; budget 6 LLM calls (`--max-iters 6`); `--max-directives 3`; `--sem-include-raw 1`;
  production system prompt `phase3/runner/system_prompt.txt`; tb.v in the loop only (sign-off scoring is done
  offline later, by the Phase 3 agent).
- T=0.1; max_tokens 8192; no reasoning (any reasoning token or reasoning content stops the provider).
- Models: `gpt-4.1-mini-2025-04-14`, `claude-haiku-4-5-20251001`.
- Toolchain: oss-cad-suite 20260917 (Yosys 0.69+71 150c32b03, Verilator 5.053 v5.052-103-g1aa87913c, Icarus 14.0
  s20260301-451-gc9ed76463), matching the HPC. Gates G0–G5 passed locally on it (G0 44/0, G1 11/11, G2, G3 198/model,
  G4, G5), run on a copy so that nothing under `phase3/` is written.

## Metrics (as defined in PREREG_FINAL.md §2)

`loop_pass` (= func_pass, tb.v), `signoff_func`, **`signoff_clean` (primary)**, `signed_off_defective`,
`silent structural pass`, `clean_pass` (as run). **This run produces the as-run metrics** (func_pass, clean_pass,
silent structural pass). `signoff_clean` needs `tb_signoff.v`, which is applied offline by the Phase 3 agent.
On 9 of the 11 tasks `tb_signoff.v` is byte-identical to `tb.v`, so `clean_pass` = `signoff_clean` there; the two
tasks that differ are mem_wb_mux and Address_select. Contrasts here are reported on `clean_pass` (as run), labelled
as such, until sign-off scoring is available. Strata: sim-silent (MuxPC, execute_mux, mem_wb_mux, mux3,
register_1bit, riscv_alu_flags), sim-visible (Address_select, ni_flit_pack, noc_xbar4, register_32bit, register_4bit).

## Primary contrasts (copied from PREREG_FINAL.md §4), per API model, pooled over tasks, sim-silent, sim-visible

1. sem_esc_restart_v3 − baseline_gate
2. sem_adv_v3 − baseline_gate
3. baseline_gate − raw_adv
4. baseline_gate − baseline (sim-visible only; sim-silent is fixed by protocol)

Statistics as PREREG_FINAL.md §3: runs paired on (model, task, rep), cells (model, task); the effect is the mean over
cells of the within-cell rate difference in points; 95% CI by cell bootstrap (10,000) and cell sign-flip p (20,000),
seeded with SEED 20260925 + CRC of the label (`phase2/frontier/stats_set4.py`, verified against the published Set 1 /
Set 3 numbers). With 11 cells per model (5 or 6 per stratum) these are descriptive.

## Also reported

Per model × condition × stratum: func_pass, clean_pass, silent structural pass, LLM calls and tokens per run;
baseline_gate runs that failed while `would_fire` = 1; INR per clean pass (96/USD + 18% GST).

## Pilot and budget

- Pilot: 2 tasks × 6 conditions × N=1 per model. The tasks are the most expensive of each stratum for the 14B model in
  Phase 3 (mean calls/run): Address_select (sim-visible, 2.17) and riscv_alu_flags (sim-silent, 2.06). Choosing
  high-cost tasks avoids the Set 4b underestimate.
- Projection per model: the higher of (i) pilot USD per run × 198 and (ii) 14B Phase 3 mean calls per run per
  condition × the pilot's USD per call × 33 runs per condition, plus a 90% bootstrap upper bound.
- Part A cap per provider: min(sub-cap, 1.5 × projection); sub-caps OpenAI USD 1.5, Anthropic USD 3.5. Hard provider
  caps for Parts A+B together: OpenAI USD 5, Anthropic USD 10 (new spend, one shared ledger directory
  `phase2/results/p3_api/ledgers/`). Caps are never raised.
- Stop a provider on: reasoning tokens > 0, model-ID mismatch, auth failure, ledger not updating, a gate failure,
  `scan_secrets` > 0, or its cap.
