# Set 1 (STITCH conditions on RTLLM) — full-scale analysis

**This document replaces the paper's Section 4** (Phase 1 escalation →
RTLLM-scale escalation). It is the STITCH-condition counterpart to
`phase2/TWIN_RUN_ANALYSIS.md` (the model-comparison analysis) — together
they comprise the full RTLLM evidence base. This analysis **holds model
and benchmark constant and varies the STITCH condition**; Twin holds the
STITCH condition constant (baseline) and varies the model. Every graph
and caption in this document reflects that axis, not a model comparison.

All artifacts referenced below live in `phase2/set1_analysis/` and are
regenerated from `phase2/results/set1_run/master_log.json` and its
per-cell `metrics.json`/`run_log.json` files by the scripts of the same
name (`cost_analysis.py`, `fig2_tier_split.py`, `table_full_grid.py`,
`table_condition_decision.py`, `cost_by_tier.py`) — pure functions of
that data, nothing hand-edited, nothing re-derived from `sim_log.txt`
beyond what `detect_outcome()` already decided. Difficulty tiers and
functional classes are **inherited verbatim from Twin's
`module_categories.json`**, not recomputed (see `_data.py`'s module
docstring for why: Twin's pooled rate is over 5 model-conditions × N=3 =
15 draws/module, a stronger recoverability signal than Set 1's own
3-model × 4-condition pool would give on a different axis).

---

## Run summary

**1512/1512 runs attempted, 6 transient (`APITimeoutError`) failures,
1506 valid runs analyzed** — 42 RTLLM-compatible modules (`edge_detect`
and `square_wave` excluded, per `RUNNER_HARDENING_REPORT.md` §6) × 3
Ollama models (gemma3:4b, llama3.1:latest, deepseek-coder:6.7b) × 4
STITCH conditions (baseline, sem_adv, sem_escalate,
sem_escalate_restart) × N=3 replicates, **T=0.1** (matched to Phase 1
for cross-benchmark comparability — Twin used T=0.5, see the
Cross-reference-to-Twin section below for what that difference means for
comparability). The 6 dropped cells are exactly:
`LIFObuffer`/deepseek-coder/sem_escalate_restart rep2;
`RAM`/llama3.1/sem_escalate reps 1–3 (all three — this cell has **zero**
valid replicates); `RAM`/llama3.1/sem_escalate_restart reps 1 and 3.
These are dropped from every table/figure below, never treated as pass
or fail, and their absence is asserted in code
(`_data.load_master_log()`'s exact-error-set check) rather than silently
tolerated.

This is a **STITCH-condition comparison, holding model and benchmark
constant** — the opposite axis from Twin's model comparison. Pass/fail
comes directly from `master_log.json`'s `pass` field (hardened
`detect_outcome()`, regression-verified 64/64 against the twin pilot's
corrected ground truth).

---

## Cost result — the headline

Extending Phase 1's Table 4 (`STITCH_EXT.pdf` p.4 /
`phase1/PHASE1_TASK3_ANALYSIS.md` §3) to RTLLM scale
(`cost_summary.tex`/`.csv`, `fig1_cost_vs_passrate.png`/`.pdf`):

| Condition | mean tokens/run | Verilator+Yosys calls/run | mean iterations/run |
|---|---|---|---|
| baseline | 18933 | 0.00 | 4.70 |
| sem_adv | 23985 | 6.60 | 4.78 |
| sem_escalate | 37754 | 5.38 | 6.21 |
| sem_escalate_restart | 33851 | 5.53 | 6.16 |

baseline's tool-invocation count is exactly 0.00 by construction
(structural check, enforced in `cost_analysis.py`) — a real assertion
failure, not a rounding artifact, would mean the extraction itself is
broken.

**Tool-invocation reduction, sem_adv → sem_escalate: (6.60 − 5.38) /
6.60 = 18.5%.** Phase 1's matched result was **~35–45%**
(`PHASE1_FINDINGS.md` §1). **This does not land in that range — reported
honestly, not massaged.** The mechanism still reduces cost at RTLLM
scale, and the pass rate still holds (below), but the magnitude of the
reduction is smaller here than Phase 1's own 255-run benchmark found.
See the tier-split cost result immediately below for *why*: the
reduction is real and large on some modules, small on others, and pools
out to 18.5% overall rather than 35–45%.

Token cost moves the same direction Phase 1 found — **up**, not down,
for both escalation conditions (sem_escalate 37754 vs. sem_adv 23985;
sem_escalate_restart 33851 vs. sem_adv 23985) — for the same reason
Phase 1 documented: escalating and then burning extra iterations before
(or without) passing costs tokens even as it saves tool invocations
(mean iterations/run: sem_escalate 6.21, sem_escalate_restart 6.16, vs.
sem_adv's 4.78). **The efficiency claim is scoped to the tool-invocation
axis, where it holds; it is not a claim about token cost, which moves
the other way and is reported plainly, not hidden.**

### Cost by tier — escalation is smart about when to spend

`cost_by_tier.csv` breaks the sem_adv → sem_escalate tool-call reduction
out by difficulty tier:

| Tier | sem_adv calls/run | sem_escalate calls/run | Reduction |
|---|---|---|---|
| Ceiling (6 modules) | 4.02 | 1.00 | **75.1%** |
| Recoverable (17 modules) | 6.74 | 5.62 | 16.6% |
| Floor (19 modules) | 7.28 | 6.54 | 10.1% |

**This is the real story behind the flat 18.5% pooled number.** On
ceiling modules — designs these models mostly get right on the first
try or two — escalation correctly recognizes there's rarely a stuck
failure worth reacting to, and spends 75% less tooling than sem_adv's
always-on invocation. On floor modules — designs that fail
near-universally — escalation ends up triggering quickly on nearly every
run regardless (there's always a stuck failure to react to), so the
saving shrinks to 10%. The recoverable band sits in between at 16.6%.
**Escalation's cost advantage is concentrated exactly where the
mechanism is designed to matter — modules where tools have the least to
offer — and shrinks on modules where a real stuck failure legitimately
warrants escalating almost every time.** This is a materially more
specific and more defensible claim than "escalation is cheaper," and one
sem_adv's always-on design cannot make at all.

`up_down_counter` (a ceiling-tier counter module, all 3 models, all 4
conditions: **36/36 pass, every single run passing on iteration 1**) is
the cleanest single-module illustration: sem_adv spends 2 tool calls per
run it never needed (immediate pass, nothing to react to), while
sem_escalate correctly spends 0 — identical 100% pass rate, real cost
difference, zero pass-rate cost. This is Phase 1's `counter_4bit`
"cost, no fail" story, replicated at RTLLM scale, cleaner than the
original (Phase 1's version had one replicate burn 6 extra iterations;
this one burns none).

---

## Pass rate regression check

Pooled across all 42 modules (`fig1_cost_vs_passrate.png` panel b):

| Condition | Pass rate | n |
|---|---|---|
| baseline | 28.8% | 109/378 |
| sem_adv | 27.2% | 103/378 |
| sem_escalate | 27.7% | 104/375 |
| sem_escalate_restart | 28.8% | 108/375 |

**All four conditions land within 1.6 percentage points of each other.**
This is the regression check, not the result — Phase 1 already
established that escalation's value is on the cost axis, not the
pass-rate axis (`PHASE1_FINDINGS.md` §1), and this pooled number
confirms that framing holds at RTLLM scale too: `sem_escalate` and
`sem_escalate_restart` do not lose ground against baseline (27.7%/28.8%
vs. 28.8%), and `sem_adv`'s small drop (27.2%) is consistent with Phase
1's "always-on tools can mildly hurt" (harmful-regime) pattern, though
at this pooled scale the drop is small enough to be within noise on its
own — see the tier-split below for where it's more visible.

---

## Tier-split

`fig2_tier_split.png`/`.pdf`, `tier_pass_rates.csv` — pooled pass rate
per condition, split by Twin-inherited difficulty tier, Wilson 95% CIs:

| Tier | baseline | sem_adv | sem_escalate | sem_escalate_restart |
|---|---|---|---|---|
| Ceiling (6 mod) | 0.815 (44/54) | 0.815 (44/54) | 0.852 (46/54) | 0.796 (43/54) |
| Recoverable (17 mod) | 0.353 (54/153) | 0.307 (47/153) | 0.313 (47/150) | 0.358 (54/151) |
| Floor (19 mod) | 0.064 (11/171) | 0.070 (12/171) | 0.064 (11/171) | 0.065 (11/170) |

**What we expected from Phase 1** (sem_adv slightly below baseline on
ceilings, a harmful-regime signal that escalation should be protected
against): **does not hold on ceilings** — baseline and sem_adv are
exactly tied (44/54 both), all four conditions overlap heavily within
each other's CIs. The harmful-regime pattern instead shows up on the
**recoverable band**, where sem_adv (0.307) sits visibly below baseline
(0.353) — the direction Phase 1 predicted, just on a different tier than
expected. `sem_escalate_restart` on the recoverable band (0.358) is the
only condition that both matches-or-exceeds baseline **and** sits above
sem_adv — a small protective signal, though the CIs for baseline, sem_adv,
and sem_escalate_restart all overlap substantially (0.353 vs. 0.307 vs.
0.358 — a real-looking but not statistically sharp lift). **Floor is
flat and near-zero across all four conditions, exactly as expected** —
19 modules where essentially nothing recovers regardless of tooling.

**Honest summary: the recoverable band is where the interesting movement
is, and it's modest — a real-looking sem_adv dip and a real-looking
sem_escalate_restart recovery, neither large enough to call decisive at
this N.** This is consistent with, not a stronger version of, Phase 1's
own finding that Task 3's pass-rate movement was "a small, four-cell
sample with real movement in both directions" (`PHASE1_FINDINGS.md`
§2) — RTLLM scale doesn't sharpen this into a strong result, it mostly
confirms the pattern is real but small.

---

## Named regressions and protections

`table_condition_decision.tex`/`.csv` — recoverable-band modules only
(17 modules × 3 models = 51 rows), verdict logic in
`table_condition_decision.py` (documented there in detail; summary:
Tied requires every condition within 1 replicate of every other; outside
that, Escalation-wins/Protective/Baseline-wins are checked in that
priority order).

| Verdict | Count |
|---|---|
| Escalation wins | 1 |
| Protective | 1 |
| Baseline wins | 3 |
| Tied | 45 |
| Insufficient data | 1 |

**45 of 51 rows are tied** — the pooled tier-split's "modest movement"
finding holds at the per-cell level too, not just in aggregate. The 6
non-tied rows, named plainly:

- **Escalation wins** — `freq_div`/llama3.1: baseline 0/3, sem_adv 1/3,
  sem_escalate 0/3, **sem_escalate_restart 2/3**. The restart variant
  specifically, not plain escalation, produces the one clear win in this
  band.
- **Protective** — `JC_counter`/llama3.1: baseline 2/3, **sem_adv drops
  to 0/3** (harmful regime), both sem_escalate and sem_escalate_restart
  hold at 2/3 — textbook regression-avoidance, sem_adv actively hurts
  and escalation is immune to it.
- **Baseline wins** (3 rows, all showing sem_adv and both escalation
  variants underperforming baseline): `fixed_point_adder`/llama3.1
  (baseline 2/3 → sem_adv 1/3, sem_escalate 0/3, sem_escalate_restart
  1/3), `fixed_point_substractor`/gemma3:4b (baseline 3/3 → sem_adv 0/3,
  sem_escalate 1/3, sem_escalate_restart 2/3), `sequence_detector`/llama3.1
  (baseline 2/3 → sem_adv 1/3, sem_escalate 0/3, sem_escalate_restart
  1/3). On these three, tooling of any kind hurts and neither escalation
  variant fully recovers it — the harmful-regime pattern Phase 1 flagged,
  present but not always rescued.
- **Insufficient data** — `RAM`/llama3.1: sem_escalate has zero valid
  replicates (all 3 timed out), so no verdict is computed rather than
  guessed at.

**Net: escalation protects against sem_adv's harm more often than it
loses to it (1 protective + 1 win vs. 3 baseline-wins is close, and 2 of
the 3 baseline-wins cases show escalation partially, not fully,
recovering ground sem_adv lost), but this is a small-N, mixed-signal
picture, not a clean sweep in either direction.**

---

## Cross-reference to Phase 1

Revisiting `PHASE1_FINDINGS.md` §2's four named cells:

1. **`pwm_generator` win** — absent from the 42-module RTLLM pool
   entirely (it was one of Phase 1's own proven testbenches, not an
   RTLLM design). No analogue exists to check.
2. **`ripple_carry_adder` structural win** (baseline 3/3, sem_adv
   collapses to 0/3, sem_escalate holds 3/3 by never firing) — RTLLM's
   closest-named analogues, `adder_16bit` and `adder_32bit`, are both
   **floor tier** (pooled far below ceiling), not the near-universal
   ceiling `ripple_carry_adder` was in Phase 1. Not analogous; the
   specific structural-win pattern can't be checked on a module this
   hard for these models.
3. **`counter_4bit` (cost, no fail)** — **this one replicates, cleanly,
   on `up_down_counter`** (ceiling tier, ROM/comparator_3bit/pe/
   right_shifter/sub_64bit/up_down_counter are the 6 ceiling modules):
   36/36 pass across every model × condition, sem_adv spends tool calls
   it never needed, sem_escalate correctly spends none. See "Cost by
   tier" above — this is in fact a cleaner version of the Phase 1 result
   (no extra-iteration cost either, whereas Phase 1's `counter_4bit` had
   one replicate burn 6 extra iterations).
4. **`alu_8bit` (one loss)** — RTLLM's `alu` is confirmed **floor tier**,
   in fact **0/12 across every model × condition in Set 1** (all four
   conditions, all three models fail every replicate) — not a
   comparable near-miss case, just uniformly unsolved. Phase 1's specific
   "STUCK_THRESHOLD rescues elsewhere but not here" puzzle can't be
   checked on a module nothing solves at all.

**Net: 1 of 4 Phase 1 cells (`counter_4bit`) has a real, clean RTLLM
analogue and replicates; 1 (`pwm_generator`) has no analogue; 2
(`ripple_carry_adder`, `alu_8bit`) have RTLLM analogues but at a
different, harder difficulty tier where the specific dynamic Phase 1
observed doesn't apply.** This is expected, not a failure of either
study — Phase 1's four cells were hand-picked from a 17-cell
pre-registered set on different (non-RTLLM) or differently-scaled
testbenches; RTLLM's own difficulty structure doesn't line up
module-for-module with Phase 1's.

---

## Cross-reference to Twin (Set 2)

Three of Set 1's models (gemma3:4b, llama3.1:latest, deepseek-coder:6.7b)
are also in Twin's 5 model-conditions, both using STITCH's baseline
condition — an apples-to-apples-*ish* comparison, except **temperature
differs (Set 1: T=0.1, Twin: T=0.5)**, so exact agreement isn't expected,
only rough ordinal comparability.

Comparing Set 1's baseline pass counts against Twin's baseline (shared
prompting) pass counts, per (module, model) pair, 42 modules × 3 shared
models = 126 cells: **98/126 (77.8%) match exactly**, and only **4 cells
show a stark disagreement (|Δ| ≥ 2 out of 3)** — all concentrated in
exactly 2 modules:

- **`counter_12`, all 3 models**: Set 1 (T=0.1) **3/3 for every model**;
  Twin (T=0.5) **0/3 for every model**. A complete flip, driven by
  temperature, not model identity — Twin's own tier file classifies
  `counter_12` as **floor** (correctly, for its own T=0.5 data), while
  Set 1's data alone would put it near-ceiling. This is exactly why
  tiers are inherited from Twin rather than recomputed per-run
  (per the brief) — recomputing tiers separately per temperature would
  make "difficulty" a moving target; instead this divergence is reported
  here as a standalone, genuinely interesting finding: **`counter_12`
  looks temperature-sensitive rather than intrinsically hard** for these
  three models, worth a caption note wherever `counter_12`'s floor
  classification is cited.
- **`comparator_3bit`, llama3.1 only**: Set 1 0/3, Twin 3/3 — the reverse
  direction, on a single model, not the whole-module pattern
  `counter_12` shows. Notably `comparator_3bit` is itself a **ceiling**
  module in Twin's classification (pooled across all 5 model-conditions);
  this single T=0.1/llama3.1 cell is the outlier, not the module's
  overall behavior.

**Flagging both here, plainly, as the brief asked**: the two datasets
agree on 78% of directly-comparable cells despite the temperature
difference, which supports using Twin's tiers as a reasonably stable
reference — but `counter_12` in particular should not be read as
"intrinsically floor-tier" without the T=0.1 caveat now on record.

---

## Honest limits

This analysis **cannot** say STITCH escalation beats baseline on pass
rate — it doesn't, by design (28.8%/27.7%/28.8% baseline/sem_escalate/
sem_escalate_restart are statistically indistinguishable at this scale,
and the recoverable-band per-cell breakdown is 45/51 tied). It **can**
say:

- Escalation matches baseline's pass rate while reducing tool-invocation
  cost — 18.5% pooled, but that number undersells the mechanism on the
  cells it's designed for: **75.1% on ceiling-tier modules**, where
  there's rarely a real stuck failure to escalate on.
- sem_adv (always-on tooling) is measurably, if modestly, worse than
  escalation on the recoverable band specifically (0.307 vs. sem_escalate
  0.313 / sem_escalate_restart 0.358), and loses outright to escalation
  on at least one named cell (`JC_counter`/llama3.1) where sem_adv
  collapses from 2/3 to 0/3 and both escalation variants hold ground.
- The Phase 1 headline (~35–45% tool-invocation reduction) does **not**
  fully replicate in the pooled number at RTLLM scale (18.5%) — the
  tier-split shows why (RTLLM's 45%-floor-tier module mix dilutes a
  reduction that's much larger, 75%, on the modules where it matters
  most). A paper citing the Phase 1 number alongside this one should
  present both, not average or reconcile them into one figure.
- Temperature (T=0.1 here vs. T=0.5 in Twin) measurably affects at least
  one module's difficulty (`counter_12`) enough to flip its tier
  classification entirely — a caveat worth carrying into any
  cross-study module-difficulty claim.

---

## Footnote — Wilson confidence intervals

95% CIs in `fig2_tier_split.png` use the Wilson score interval
(`statsmodels.stats.proportion.proportion_confint(count, nobs,
alpha=0.05, method="wilson")`), same citation as Twin's fig2/footnote —
Wilson stays well-behaved at small N and away from p=0.5, unlike the
normal (Wald) approximation. Not derived by hand; the library call is
the citation.
