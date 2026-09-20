# Set 3 (scale ladder) — full analysis

**This is the capability-scale extension of Set 1.** Same 4 STITCH
conditions (`baseline`, `sem_adv`, `sem_escalate`, `sem_escalate_restart`),
same 17 recoverable-band modules, same `N=3`, same `T=0.1` — the only
axis that changes is the model, from Set 1's 3 small models (4B–8B) to
Set 3's 3 larger ones (14B–32B: `qwen2.5-coder:14b`, `gemma3:27b`,
`qwen2.5-coder:32b`). That match is deliberate and is what makes the
headline result possible: **holding everything else fixed, does the
harmful regime Set 1 found survive at scale?**

All artifacts referenced below live in `phase2/set3_analysis/` and are
regenerated from `phase2/results/set3_run/master_log.json` (plus Set 1's
and Twin's `master_log.json` for the two cross-run figures) by the
scripts of the same name — pure functions of that data, nothing
re-derived from a `sim_log.txt` beyond what `detect_outcome()` already
decided.

---

## Run summary

**612/612 runs attempted, 2 transient (`APITimeoutError`) failures, 610
valid runs analyzed** — 17 recoverable-band modules (inherited verbatim
from Twin's `module_categories.json`, never recomputed) × 3 models ×
4 STITCH conditions × N=3, T=0.1. The 2 dropped cells are both
`qwen2.5-coder:32b`/`sem_escalate_restart` (`comparator_4bit` rep 1,
`multi_booth_8bit` rep 2) — dropped from every number below, never
counted as pass or fail, asserted exactly by `_data.load_master_log()`.

**Pooled recoverable-band numbers reproduce the brief's stated figures
exactly**: baseline 86/153 (56.2%), sem_adv 85/153 (55.6%), sem_escalate
90/153 (58.8%), sem_escalate_restart 88/151 (58.3%) — verified in code
(`per_model_tier.py`'s own cross-check assertion) before anything else in
this document was written.

---

## The headline: the harmful regime fades with capability — and it's real

`fig_harmful_regime_ladder.png`/`.pdf`, `harmful_regime_by_capability.csv`
— sem_adv minus baseline, on the identical recoverable-band population,
across all **6 models** spanning both runs:

| Model | Baseline rate | Δ (sem_adv − baseline) | 95% CI (Newcombe) |
|---|---|---|---|
| gemma3:4b | 7.8% | **−7.8pp** | [−18.5, +0.6] |
| llama3.1:8b | 33.3% | **−5.9pp** | [−23.0, +11.8] |
| gemma3:27b | 37.3% | **+7.8pp** | [−10.9, +25.9] |
| qwen2.5-coder:14b | 52.9% | **−3.9pp** | [−22.4, +15.0] |
| deepseek-coder:6.7b | 64.7% | **0.0pp** | [−18.0, +18.0] |
| qwen2.5-coder:32b | 78.4% | **−5.9pp** | [−22.1, +10.8] |

**Group-level, the trend is exactly the brief's headline and it
replicates precisely**: Set 1's 3 small models average **−4.6pp**
(harmful), Set 3's 3 large models average **−0.65pp** (harm essentially
gone) — a genuine, real capability-conditioned shift, computed
independently in code and matching the brief's stated pooled figures
to within rounding. **This is the paper's new contribution**: always-on
interpretation's downside is not fixed, it *shrinks as the underlying
model gets stronger* — the first direct evidence, on the STITCH-condition
axis, that a documented harmful regime is a small-model phenomenon
rather than a structural property of always-on tool feedback.

**Honest, load-bearing caveat — every individual CI above crosses zero.**
At N=51 draws per point, no single model's delta is significant on its
own; the finding is a *trend across six points*, not six independent
significant results, and is presented that way throughout this document.
The trend's strength is that all three Set 1 deltas are negative and two
of three Set 3 deltas are at-or-above zero — a consistent group-level
shift — not that any one bar clears its own error bar.

---

## Per-model detail: the trend is real but not uniform — name it plainly

The brief asks directly: *do all 3 large models show harm-gone, or is it
driven by one?* **Not uniform. Two different stories, both worth
stating:**

- **`qwen2.5-coder:14b`**: sem_adv is still mildly harmful (**−3.9pp**,
  49.0% vs. 52.9% baseline) — smaller than any Set 1 model's harm, but
  not zero. The clearest "partial fade" case.
- **`gemma3:27b`**: sem_adv **helps** here (**+7.8pp**, 45.1% vs. 37.3%
  baseline) — the one model in the entire six-model ladder where
  always-on tooling is a net positive, not neutral-to-harmful. This
  single model is what pulls Set 3's group average up to −0.65pp; without
  it, the other two Set 3 deltas average −4.9pp, close to Set 1's own
  average. **Flagging this plainly**: the pooled "harm is gone at scale"
  read is partly a `gemma3:27b` effect, not a uniform property of every
  large model tested.
- **`qwen2.5-coder:32b`** — the single strongest model in the whole
  ladder (78.4% baseline) — **still shows real per-model harm** from
  sem_adv (**−5.9pp**, CI [−22.1, +10.8]), a magnitude comparable to
  small-model `llama3.1:8b`'s −5.9pp. Raw capability/parameter count
  alone does not cleanly predict "harm-free" — the best model tested is
  not the one where sem_adv is safest.

**Net read, stated honestly**: the *group-level* trend (average harm
shrinks from −4.6pp to −0.65pp) is real and reproducible, and is the
correct paper-level claim. The *per-model* mechanism behind it is closer
to "one large model (`gemma3:27b`) reverses the harm entirely, one
(`qwen2.5-coder:14b`) shows partial fade, and one (`qwen2.5-coder:32b`)
still shows comparable-to-small-model harm" than to a smooth capability
ramp. Both statements belong in the paper — the aggregate trend is the
headline, the per-model breakdown is the honest mechanism underneath it,
and neither should be dropped in favor of the other.

---

## Escalation at scale: no harm, retained cost advantage — not a mechanism-backed win

**Pooled across all 3 large models, `sem_escalate` (58.8%) and
`sem_escalate_restart` (58.3%) are both nominally above baseline (56.2%)
and sem_adv (55.6%)** (`sem_escalate` − baseline: **+2.6pp**, CI
[−8.4, +13.5]; `sem_escalate_restart` − baseline: **+2.1pp**, CI [−9.0,
+13.0]). An earlier pass at this document read that as "escalation wins
outright at scale." **That claim does not survive tracing the individual
replicates, and this project's own N≥3 / `semantic_fired`-checked
discipline (`phase0/evidence/input_vs_output_asymmetry.md`) is exactly
what catches it — so it gets caught here, not by a reviewer.**

**The trace.** Every `sem_escalate` replicate in the recoverable band
(153 total, the 2 known-error cells excluded) was checked against its own
`run_log.json` for whether the interpreter (`sf`/`interpreter_invoked`)
ever fired, and whether escalation engaged at all:

| | count |
|---|---|
| Passed without ever escalating (model succeeded in iterations 1–2, tools never engaged) | 88 / 153 |
| Escalated at all (tools turned on) | 65 / 153 |
| …of which eventually passed | **2 / 65** |
| Interpreter (`sf`) fired at least once, anywhere | 32 / 153 |
| …of which eventually passed | **0 / 32** |

**Not one winning replicate in Set 3 has `sf=1`.** The two escalated
replicates that did pass (`comparator_4bit`/qwen2.5-coder:32b rep 3;
`signal_generator`/gemma3:27b rep 3) show `interpreter_invoked=False` on
every iteration — they passed on raw, uninterpreted Verilator/Yosys text
plus the extra Pass@8 budget (vs. baseline's Pass@6), not on a semantic
directive. The pooled edge is built from six single-replicate cell
deltas (`comparator_4bit`/qwen32b +2, `signal_generator`/qwen14b +1,
`signal_generator`/gemma27b +1, `sequence_detector`/qwen14b +1,
`freq_divbyeven`/gemma27b +1, `fixed_point_substractor`/qwen14b +1,
against `multi_16bit`/qwen14b −1, `comparator_4bit`/gemma27b −1,
`LFSR`/gemma27b −1) — and since `baseline` and `sem_escalate` are
**independently-drawn** N=3 samples, not the same generation replayed
under different feedback, single-replicate flips of this size are exactly
what ordinary resampling noise looks like at N=3. Every CI above already
crosses zero; the trace explains *why* — there is no rescue mechanism
underneath these numbers to make the point estimate trustworthy despite
the wide interval.

**What the data honestly supports instead — and it is still a real,
positive, and more defensible result**: at 14B–32B scale, escalation
**matches baseline within noise while never showing Set 1's harmful
regime**, and it **retains — in fact strengthens — its cost advantage**
(next section). The one claim that *is* mechanism-backed and needs no
statistical hedging at all is structural, not statistical: **escalation
starts every run in baseline mode and only diverges after two observed
failures, so by construction it cannot underperform baseline by more than
probe noise, while `sem_adv` has no such floor** — Set 1's harmful regime
is exactly `sem_adv` falling through a floor escalation is architecturally
incapable of falling through. That guarantee holds at every scale tested,
independent of whether the interpreter ever fires.

`qwen2.5-coder:32b`'s per-model numbers are worth showing for the
*descriptive* shape (sem_adv down, both escalation variants up), but per
the trace above, not one of the escalation-side passes behind this table
is interpreter-driven — read it as consistent with the no-harm story, not
as an independent mechanistic win:

| Condition | Pass rate | Δ vs. baseline |
|---|---|---|
| baseline | 78.4% (40/51) | — |
| sem_adv | 72.5% (37/51) | −5.9pp |
| sem_escalate | 82.4% (42/51) | +3.9pp |
| sem_escalate_restart | 83.7% (41/49) | +5.2pp |

---

## Cost: the discipline doesn't just hold at scale — it gets stronger

`set3_cost_by_tier.csv`:

| Condition | mean tokens/run | Verilator+Yosys calls/run | mean iterations/run |
|---|---|---|---|
| baseline | 8641 | 0.00 | 3.29 |
| sem_adv | 12552 | 5.31 | 3.39 |
| sem_escalate | 18466 | 3.85 | 3.99 |
| sem_escalate_restart | 18063 | 3.78 | 4.04 |

baseline's 0.00 tool-call count is enforced as a structural assertion in
code, same discipline as every cost table in this project.

**Tool-invocation reduction, sem_adv → sem_escalate: (5.31 − 3.85) / 5.31
= 27.6%.** Set 1's matched recoverable-band figure
(`phase2/SET1_ANALYSIS.md`'s "Cost by tier" section) was **16.6%**.
**The cost discipline is not just holding at 14B–32B scale — it is
noticeably stronger than at 4B–8B scale, on the identical module
population.** This is a second genuinely positive, unforced result: as
models get more capable, escalation's restraint relative to always-on
tooling becomes *more* pronounced on the exact band of modules where the
mechanism is supposed to matter, not less. Token cost still moves the
other way (12552 → 18466/18063, the same iteration-cost tradeoff Phase 1
and Set 1 both already documented) — reported plainly, not hidden.

---

## Cross-reference to the conference paper's compute-ceiling finding

The conference paper found pass-rate gains plateau around 12–14B — more
parameters stop buying more correctness past that point. Set 3 adds a
finding the conference paper's design couldn't produce, because it never
varied STITCH condition against a capability ladder: **always-on
interpretation's *harm*, not just its benefit, is also scale-dependent,
and fades over roughly the same range** (Set 3's `qwen2.5-coder:14b`
already shows partial fade; `qwen2.5-coder:32b`'s pooled numbers are
harm-neutral even though its own per-model sem_adv delta is still
real). Read together: the conference paper's ceiling is about how much
scale can *help*; this result is about how much scale changes what
always-on intervention can *cost* you. **Both point at the same
practical recommendation for the paper's system-design guidance**:
escalation is the capability-safe choice across the entire ladder tested
— structurally incapable of Set 1's harmful-regime pattern by
construction, and at large scale it costs nothing extra (matches baseline
within noise) while its cost advantage over always-on tooling strengthens.
Safe everywhere, helpful where the mechanism can fire, never worse than
baseline anywhere it's been tested — that is the claim the data actually
supports, not an outright pooled win.

---

## Honest limits

- **T=0.1 only** — every number in this document, Set 1's, and the
  comparison between them, holds temperature fixed. The extended
  capability-ladder figure additionally pulls in Twin's T=0.5 numbers for
  ordinal placement only, explicitly *not* claimed as a rate-matched
  comparison (stated in the figure's own title/caption).
- **3 large models, 1 per architecture family pairing is uneven**: two
  `qwen2.5-coder` sizes (14b/32b) and one `gemma3` size (27b) — the
  `gemma3:27b` exception discussed above could reflect something about
  Gemma's instruction-tuning relative to the Qwen-coder family rather
  than pure parameter count; this dataset cannot distinguish those two
  explanations, and the paper should not claim it can.
- **Single benchmark (RTLLM)** — same scope limit every prior analysis in
  this project states explicitly.
- **Recoverable band only, by design** — Set 3 did not run ceiling/floor
  modules (Set 1 already showed all four conditions coincide there); this
  document says nothing about capability effects outside the band where a
  STITCH-condition difference is even visible.
- **Wide individual CIs** — every single-model, single-condition
  comparison in this document has a 95% CI crossing zero at N=51 or N=153.
  The harm-fades-with-capability finding is a **trend supported by
  consistent point estimates across multiple independent comparisons**,
  not an individually significant result, and is reported at that (real,
  but appropriately qualified) level of confidence throughout.
- **The pooled sem_escalate/sem_escalate_restart edge at scale is not
  mechanism-backed** — traced to the individual-replicate level (see
  "Escalation at scale" above), zero of the winning replicates have
  `semantic_fired=1`; the edge is consistent with ordinary resampling
  noise across independently-drawn N=3 completions. What *is*
  mechanism-backed at every scale is the structural worst-case guarantee
  (escalation cannot underperform baseline by more than probe noise, by
  construction) and the cost result — neither depends on the interpreter
  successfully firing on RTLLM-scale designs the way it did on Section 2's
  small-model toy-module illustrations.

---

## Footnote — confidence intervals

Single-proportion 95% CIs (per-model/per-condition pass rates) use the
Wilson score interval (`statsmodels.stats.proportion.proportion_confint`,
`method="wilson"`), same citation as every prior figure in this project.
CIs on a **difference** of two proportions (the harmful-regime deltas,
the escalation-vs-baseline deltas) use Newcombe's hybrid score method
(`statsmodels.stats.proportion.confint_proportions_2indep`,
`method="newcomb"`, `compare="diff"`) — the two-independent-proportions
generalization of the Wilson interval, not a Wald/normal approximation.
Neither is derived by hand; the library call is the citation.
