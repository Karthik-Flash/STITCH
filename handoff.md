# STITCH Phase 1 — Handoff

## Where phase 0 ended

- Two proven illustrations (`phase0/illustrations/proven/`), replicated 3/3.
- Five documented retirement causes across 15 candidates, in
  `phase0/illustrations/retired/`, with three secondary methodology findings
  that came out of the larger-module hunt specifically.
- Interpreter hardened (50 tests), runner canonical at
  `src/runner/stitch_runner.py`, all five original defects fixed.
- See `phase0/README.md` for the full phase 0 summary, and
  `plans/research_plan_v4.md` for the plan of record.

## Phase 1 goal

Build and evaluate the conditional escalation architecture from
`plans/research_plan_v4.md` §4. Same interpreter, applied only after N
consecutive baseline failures instead of on every iteration. Target:
net-positive on aggregate, with a bounded tool-invocation cost story.

## Benchmark decision — resolved

Primary benchmark for Phase 1 is **RTLLM v2**
(https://github.com/hkust-zhiyao/RTLLM), **not** VerilogEval-Human.

Rationale: RTLLM v2 is Verilog-2001-compatible, so the current
`SYSTEM_PROMPT` works unchanged and results are directly comparable to the
MLCAD paper's v20 baseline. VerilogEval-Human uses SystemVerilog constructs
(`logic`, `always_comb`, `always_ff`, the `TopModule` convention)
incompatible with the current prompt — using it requires either relaxing the
prompt (losing MLCAD comparability) or building a translation layer.
Deferred to Phase 2.

**Note for whoever picks this up:** `plans/research_plan_v4.md` §3 still
reads "VerilogEval-Human is the likely primary benchmark" — that line
predates this decision and was not edited as part of this handoff. Treat
this section of `handoff.md` as authoritative over plan v4 §3 until §3 is
updated to match.

## Model set for Phase 1

Same as phase 0 proven runs, extended:

- `gemma3:4b` — already benchmarked, enabling regime confirmed
  (`decoder_3to8`, `mux4_oe`)
- `llama3.1:latest` — already benchmarked, efficiency regime confirmed
  (`mux4_oe`)
- `deepseek-coder:6.7b` — already in Ollama, benchmarked in the MLCAD paper
- `deepseek-coder-v2:16b` — pulled, not yet used
- RTL-specific models to add: RTLCoder (fine-tuned instruction format, may
  need prompt adaptation), VeriPilot (expects structured input)

Prompting adaptation for RTL-specific models is a known Phase 1 design
question, not a solved problem — see `plans/research_plan_v4.md` §7 for open
questions.

## First tasks for the new chat

1. Design the escalation runner spec (thresholds N=2 vs N=3, cost
   accounting, when to escalate on syntax vs logic errors).
2. Adapter for RTLLM v2 module loading (their format vs the `BENCHMARK`
   dict convention in `src/runner/stitch_runner.py`).
3. Baseline pass — run `baseline` + unconditional-STITCH (`sem_adv`) on
   RTLLM v2 across the 5 non-specialized models before touching escalation.

## Constraints carried over from phase 0

- Temperature 0.1, no seed → runs are reproducibility, not variance (see
  `plans/research_plan_v4.md` §2).
- `sem_adv` can beat `baseline` via resampling variance with the
  interpreter completely inert (phase 0 finding §2a,
  `phase0/evidence/phase0_illustration_hunt_findings.md`) — **every Phase 1
  claim needs N=3 before it counts, and `semantic_fired` must be checked and
  reported alongside any pass-rate number, not separately from it.**
- Correct directives don't guarantee recovery from a degenerate generation
  state (phase 0 finding §2b) — escalation logic must account for
  generation-state instability, not just error class, when deciding whether
  to escalate again or give up.
- Raw tool text alone helps in some cases, symmetrically across `raw_adv`
  and `sem_adv` (phase 0 finding §2c) — the three conditions still separate
  `baseline` / `raw_adv` / `sem_adv`; do not collapse `raw_adv` into
  `sem_adv`'s framing, the split is still doing real work.

## Files a Phase 1 chat should open with

- `handoff.md` (this file)
- `plans/research_plan_v4.md`
- `phase0/evidence/phase0_illustration_hunt_findings.md`
- `phase0/evidence/input_vs_output_asymmetry.md`
- `src/interpreter/stitch_interpreter.py` (canonical interpreter)
- `src/runner/stitch_runner.py` (canonical runner)
- `phase0/illustrations/proven/decoder_3to8/` and `mux4_oe/` — reference
  behavior for regression checks; any escalation-runner change must still
  pass both.

## Long-term direction (not phase 1 work, for context)

- Kimi K3 and Claude API benchmarking (Phase 2).
- HPC runs on larger open-weight models (Phase 2).
- VerilogEval adapter (Phase 2).
- Chip Design LLM Zoo-style comparison graph with pass@k across models
  (Phase 3).
