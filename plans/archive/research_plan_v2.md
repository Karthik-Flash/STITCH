> **SUPERSEDED by research_plan_v4.md. Retained for history.**

# STITCHAdv Research Plan v2 — Journal Extension

**Supersedes:** `STITCHAdv_Extended_Research_Plan.md` (the original was written before the v20 results showed the interpreter is net-negative in aggregate, and before the competitive landscape check).

**Companion doc:** `STITCH_JOURNAL_HANDOFF.md` — read that first for context, competitive landscape, and what is already proven.

**Core reframe driving this version:** the original plan assumed the task was "broaden the benchmark and prove STITCH helps." The data says STITCH helps *conditionally* and hurts when applied unconditionally. The task is therefore to **change the architecture so the condition is enforced by design**, then prove that. Benchmark and model expansion are in service of that claim, not a substitute for it.

---

## 0. The thesis, stated once, precisely

> Semantic interpretation of EDA tool output is a high-value but high-variance intervention. Applied unconditionally it is net-negative. Applied as a conditional escalation — triggered only after the cheap feedback path has demonstrably failed — the same interpretation becomes net-positive while invoking heavyweight tooling on a minority of iterations.

Every experiment below exists to support, refute, or bound some part of that sentence. If an experiment does not, cut it.

**Explicitly not the thesis:** "STITCH achieves state-of-the-art RTL repair rates." Competitors report 90%+ (MAGE 95.7% VerilogEval-Human; VeriPilot 92.98% with GPT-5). That race is lost and entering it is a mistake. The unoccupied ground is *conditional, cost-bounded, zero-inference-cost* feedback — see handoff §3.

---

## Phase 1 — Build and validate the escalation architecture (the core result)

**Goal:** demonstrate that escalation-gated STITCH beats both baseline and unconditional STITCH on the *existing* v20 suite with the *existing* 5 local models. No new benchmark. No new models. No HPC.

### 1.1 Implementation

New runner, new folder. Conditions become:

| Condition | Behavior |
|---|---|
| `baseline` | iverilog only, plain error feedback (unchanged — this is the control) |
| `sem_always` | current unconditional STITCH (unchanged — this is what the conference paper did) |
| `sem_escalate_2` | plain iverilog feedback until 2 consecutive failures, then invoke Verilator+Yosys+interpreter |
| `sem_escalate_3` | same, threshold 3 |

Thresholds 2 and 3 both run because the right threshold is an empirical question, not an assumption. `STUCK_THRESHOLD=2` is already the existing rewrite-prompt trigger, so threshold 2 shares a natural boundary with existing behavior — worth noting whether escalation and rewrite-injection interact.

**Instrumentation required from day one** (the old runner lacked these and it cost real analysis time):
- Persist directive text per iteration (`feedback.txt`) — already fixed in `stitch_interpreter.py` era, keep it.
- Log `escalated: bool` and `escalation_iteration: int|null` per module-run.
- Log tool invocation counts separately: `verilator_invocations`, `yosys_invocations`, `interpreter_invocations`. **This is the cost metric — it is a headline number, not telemetry.**
- Log wall-clock and token cost per condition.

### 1.2 The resampling problem — handle it by design this time

The single biggest methodological hazard (handoff §6.1). `temperature=0.1`, no fixed seed → every run is an independent sample.

**Requirement: N≥3 independent samples per (model, module, condition) cell.** Report distributions, not points. With 5 models × 20 modules × 4 conditions × 3 samples = 1,200 module-runs. At observed local throughput this is large but tractable if staged; if it is not, reduce the model set before reducing N — **N=1 makes the entire result unfalsifiable and there is no point running it.**

Derived metrics per cell: pass rate across samples, mean iterations-to-pass, escalation rate, tool invocations.

### 1.3 The claims this phase can support

- **Primary:** `sem_escalate_k` pass rate ≥ `baseline` and ≥ `sem_always`, with confidence intervals from the N samples.
- **Cost:** tool invocations under `sem_escalate_k` as a fraction of `sem_always` — expect a large reduction, and this is arguably the more interesting number.
- **Regime:** harmful-bucket count under escalation should approach zero by construction. If it does not, that is a genuinely interesting negative result about *why* — investigate before proceeding.

### 1.4 Gate

If escalation does not beat unconditional STITCH here, **stop and reconsider the thesis** before spending anything on Phases 2–4. This phase is deliberately first and deliberately cheap for that reason.

---

## Phase 2 — Benchmark expansion, designed to be bias-proof

**The trap, stated plainly:** selecting new modules *because STITCH does well on them* is p-hacking with test cases, and a reviewer will catch it. The v20 aggregate (62.5%) is the honest number and a new suite showing 90% would be evidence of selection, not capability.

**The bias-proof design — three rules, all enforced before any module is run:**

### Rule 1 — Select by failure class, never by observed outcome
Modules are chosen to cover a *pre-registered* taxonomy of RTL defect classes, written down before generation. Target classes, derived from the interpreter's own warning vocabulary plus known gaps:

| Class | Why it is in the suite | Covered by v20? |
|---|---|---|
| Unused/unconnected port (`UNUSEDSIGNAL`) | The one confirmed enabling case class | Yes (decoder_3to8) |
| Multi-driver conflict (`MULTIDRIVEN`) | In interpreter vocabulary, thin coverage | Barely |
| Width truncation / sign extension (`WIDTHTRUNC`/`WIDTHEXPAND`) | Where extraction bugs concentrated | Yes, but as incidental warnings |
| Blocking-in-sequential (`BLKSEQ`) | Confirmed harmful-regime trigger — **include deliberately** | Yes (comb_sensitivity) |
| Inferred latch (Yosys) | Motivating example of the whole paper; almost no clean instance in v20 | **No — real gap** |
| Combinational loop (Yosys) | In interpreter vocabulary, zero coverage | **No — real gap** |
| Undeclared identifier vs. unassigned output (`UNDRIVEN` both paths) | The §5.2 disambiguation fix has no clean test case | **No — real gap** |
| Sequential reset-timing | Common real-world defect, no tool signal | Partial |
| Logic-only error, no tool signal | **Control class — STITCH must NOT help here** | Yes (alu_ops, lfsr_8bit) |

### Rule 2 — Include adversarial classes on purpose
The suite must contain modules where STITCH is *expected to fail or hurt*: the logic-only control class, and at least two `BLKSEQ`-style complex-restructuring cases. A suite that only contains classes STITCH handles is not a benchmark, it is a demo. **Reporting the classes where it does not help is what makes the classes where it does help credible.**

### Rule 3 — Freeze a held-out split before running anything
Generate ~2× the modules needed, randomly partition into development and held-out sets, and **do not run the held-out set until the final evaluation**. Any tuning of thresholds, directives, or interpreter logic happens on development only. This is the single cheapest defense against the reviewer question "did you tune on your test set."

### 2.1 Oracle validation gate (non-negotiable)

The conference paper already got burned by a mis-specified oracle (`pipeline_mult_4x4`, checked N+1 for a two-stage pipeline producing at N+2). Every new module must pass, in order:
1. Golden reference compiles and passes its own testbench.
2. Each injected bug variant *fails* that testbench.
3. The failure is attributable to one primary defect class (no multi-cause modules in the primary suite).
4. Independent re-derivation of the expected timing/behavior — for anything with pipeline latency or protocol timing, by a second method or second person.
5. No dependence on hidden state or waveform artifacts.

AI-assisted generation is fine for *proposing* modules and testbenches. Nothing enters the suite without passing all five gates. Record pass/fail against each gate per module in the manifest.

### 2.2 Size

8–14 new modules. Not 40. Every module costs N×conditions×models runs downstream, and coverage of the taxonomy matters far more than count.

---

## Phase 3 — Model expansion

Sequenced by cost and by what each model actually tests. **Nothing here starts until Phase 1 has a result.**

### 3.1 RTLCoder — highest value per unit cost, do first

RTLCoder-Deepseek-v1.1 is fine-tuned from `deepseek-coder-6.7b`, and you already have `deepseek-coder:6.7b` results across the full v20 suite. **Same base weights, same size, only difference is RTL-specific fine-tuning.** That is a controlled natural experiment nobody in the competitive set has run:

> Does domain fine-tuning make semantic tool feedback redundant, or complementary?

Both answers are publishable. If RTLCoder needs less escalation, that bounds STITCH's value as "for general-purpose models." If it needs the same escalation, that argues semantic feedback addresses something fine-tuning does not. Local, cheap, no API budget, and there is a GGUF 4-bit variant if VRAM is tight.

### 3.2 Frontier API models — Claude and Gemini

Purpose: establish the upper bound and test whether escalation still helps when the base model is strong. Hypothesis from existing data (gemma3:12b and qwen2.5-coder:14b showed *zero* regime movement) is that strong models rarely trigger escalation at all — which, if true, is itself a clean finding: **escalation cost scales inversely with model capability.** That is a good result and a cheap one to get, because if escalation rarely fires, the API spend is bounded.

Budget check before committing: N samples × modules × conditions × 2 models. Validate cost on 2–3 modules first.

### 3.3 Kimi K3 — coverage, with a specific caveat

2.8T-parameter open-weight MoE (Moonshot, July 2026), API-only — far beyond local hardware. OpenAI-SDK-compatible so integration is straightforward. **Specific risk to validate before committing:** always-on thinking mode produces verbose reasoning output that may break the regex-based code extraction step (Stage 2), the same class of failure as the `gemma3:27b` code-fence hypothesis that was never resolved. Run 2 modules first, inspect raw completions, then decide.

### 3.4 Explicitly deferred
`gemma3:27b` / `qwen2.5-coder:32b` HPC completion. The sweep is closed; R3 Major 2 is a stated limitation. Reopening it requires a freshly-scoped HPC session with a realistic time budget (observed: ~34/60 module-conditions in 11.5h under contention → budget 24h+, partition ceilings allow 3–5 days).

---

## Phase 4 — Head-to-head against a real baseline system

Currently missing and a reviewer will ask for it. Your paper positions RTLFixer as complementary but never benchmarks against it.

**Minimum viable comparison:** RTLFixer (or its published numbers on an overlapping benchmark) vs. escalation-STITCH, on whatever module subset both can address. If a direct run is infeasible, an honest structural comparison — what each system catches, what each costs per repair, what class of defect each is blind to — is still far better than the current silence.

**Comparison axes that favor an honest STITCH framing:**
- Tool invocations per successful repair (STITCH escalation should win decisively)
- Inference cost of the feedback mechanism itself (STITCH: zero — deterministic regex. LintLLM/VeriPilot: LLM calls)
- Determinism and reproducibility of the feedback (STITCH: exact. LLM-based: not)
- Whether a golden reference model is required (VeriPilot: yes. STITCH: no)

Do **not** compete on raw pass rate against MAGE/VeriPilot. Cite them, position against them on cost and determinism, and be explicit that they optimize a different objective.

---

## Phase 5 — Write-up structure

Suggested section skeleton, ordered by evidence strength:

1. **Motivation** — keep the latch/`decoder_3to8` example; it is concrete, auditable, and still the clearest illustration of the mechanism.
2. **The unconditional-application problem** — present the v20 aggregate honestly (65/65/62.5). *Leading with the negative result is the paper's credibility anchor and sets up everything after it.*
3. **Failure taxonomy** (contribution C2) — misdiagnosis / protective-regime failure / noise / extraction artifact, with the 24/197 quantification.
4. **Attribution methodology** (contribution C3) — the resampling-confound problem, the `semantic_fired`-gated regime definition, replay-vs-resample. Note that this critique applies broadly to before/after claims in this literature.
5. **Escalation architecture** (contribution C1) — the fix, and the Phase 1 results.
6. **Extended evaluation** — Phases 2–3 results, held-out split reported separately from development.
7. **Comparison and positioning** — Phase 4, on cost/determinism axes.
8. **Limitations** — n-per-cell, benchmark scale, `gemma3:27b` gap, the `"ambiguous"` UNDRIVEN fallback still not resolving cleanly, no formal verification of oracles.

---

## Phase 6 — Explicitly out of scope

Written down so it does not creep back in:

- Multi-agent orchestration (MAGE's territory; different objective, far more compute)
- CDFG/AST-based analysis (VeriPilot's territory; would abandon the zero-inference-cost differentiator)
- LLM-based linting (LintLLM's territory; directly contradicts the determinism claim)
- Fine-tuning any model (RTLCoder is *used*, not trained)
- PPA/timing optimization (the "proactive copilot" idea — genuinely interesting, entirely separate paper)
- Reopening the HPC sweep

---

## Immediate next actions

1. Create the new folder. Copy in `stitch_interpreter.py` (fixed version), the v20 baseline dataset, and the three evidence reports.
2. Implement the escalation runner with the §1.1 instrumentation. Threshold as a parameter, not a constant.
3. Smoke-test on `decoder_3to8`/`gemma3:4b` (known enabling) and `sync_fifo_8`/`llama3.1` (known harmful) — escalation should preserve the first and eliminate the second. If it does not, debug before scaling.
4. Run Phase 1 at N=3 on the 5 local models. Stage it; verify aggregation after each model.
5. Gate on §1.4 before touching Phase 2.

The pre-registered taxonomy in §2 should be written down *before* Phase 1 finishes, so module generation can start in parallel — but no module runs until Phase 1's gate clears.
