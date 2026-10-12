# Set 4 and Set 4b report (API non-reasoning models, RTLLM)

Written 2026-09-29. Every number below comes from a script in `phase2/frontier/`
(`analysis_set4.py`, `analysis_set4b.py`, `oracle_audit.py`, `spend_summary.py`,
`parity_check.py`, `stats_set4.py`); raw outputs are in the gitignored
`phase2/results/set4_api/`. Money: INR = USD × 96 × 1.18 (18% GST).
Pre-registration: `SET4_PREREG.md` (original `ED262B53…9A4B`; after Amendment 1
`52DC7DEF…20F9`, 2026-09-28 18:25 UTC; after Amendment 2 and the Set 4b section
`8B376DF3…2C7C`, 2026-09-29 13:00 UTC; after Amendment 3 (Gemini completion) `62C1C0BE…216A`, 2026-10-12 13:21 UTC;
each written before the calls it governs). The latest results are in the last section.

**LEAK STATUS: clean.** No key value in any commit on any branch (`leak_audit.py`);
`scan_secrets.py` 0 matches after the Set 4b pilot and after the Set 4b full run.

**Spend (from the ledgers):**

| Provider | Set 4 | Set 4b | Total |
|---|---|---|---|
| OpenAI (`gpt-4.1-mini-2025-04-14`) | $0.2558 (INR 29.0) | $1.3042 (INR 147.7) | $1.5600 (INR 176.7) |
| Google (`gemini-2.5-flash`) | $0.4350 (INR 49.3) | $3.6156 (INR 409.6) | $4.0506 (INR 458.9) |
| Anthropic (`claude-haiku-4-5-20251001`) | $0.8993 (INR 101.9) | $3.1329 (INR 354.9) | $4.0322 (INR 456.8) |
| Moonshot (`kimi-k2.6`, smoke only) | $0.0004 (INR 0.0) | – | $0.0004 |
| **Total** | **$1.5905 (INR 180.2)** | **$8.0527 (INR 912.2)** | **$9.6432 (INR 1,092.4)** |

---

## Set 4: recoverable band (17 modules × 4 conditions × N=3, 204 runs per model)

612 runs, 0 errored, 0 truncated (max output 2,213 tokens vs max_tokens 8,192),
0 reasoning tokens. Toolchain: oss-cad-suite 20260917, matching the HPC exactly
(Yosys 0.69+71 150c32b03, Verilator 5.053 v5.052-103-g1aa87913c, Icarus 14.0
s20260301-451-gc9ed76463); parity on 140 saved Set 3 candidates 140/140 pass/fail,
51/51 interpreter.

**Statistics check.** `stats_set4.py` (copied from `phase3/runner/analyze_phase3.py`)
reproduces all 12 published Set 1/Set 3 numbers in `POSTHOC_CHECKS.md` exactly
(6 bootstrap CIs, 6 sign-flip p).

### Pass rate per condition (Wilson 95%)

| Model | baseline | sem_adv | sem_escalate | sem_escalate_restart |
|---|---|---|---|---|
| GPT-4.1 mini | 50/51 (98.0%) | 49/51 (96.1%) | 48/51 (94.1%) | 48/51 (94.1%) |
| Gemini 2.5 Flash | 51/51 (100%) | 51/51 (100%) | 51/51 (100%) | 51/51 (100%) |
| Claude Haiku 4.5 | 51/51 (100%) | 51/51 (100%) | 51/51 (100%) | 51/51 (100%) |
| Pooled | 152/153 (99.3%, 96.4–99.9) | 151/153 (98.7%, 95.4–99.6) | 150/153 (98.0%, 94.4–99.3) | 150/153 (98.0%, 94.4–99.3) |

**Two of three models are at 100% in every condition, so the condition comparison
rests entirely on GPT-4.1 mini** (17 cells). Condition − baseline, (model, module)
cells, Set 3's method:

| Scope | sem_adv | sem_escalate | sem_escalate_restart |
|---|---|---|---|
| Pooled (51 cells) | −0.7 [−2.0, +0.0], p=1.000 | −1.3 [−3.9, +0.0], p=1.000 | −1.3 [−3.9, +0.0], p=1.000 |
| GPT-4.1 mini (17 cells) | −2.0 [−5.9, +0.0], p=1.000 | −3.9 [−11.8, +0.0], p=1.000 | −3.9 [−11.8, +0.0], p=1.000 |

### Mechanism trace

| Model | sem_adv runs with semantic_fired | passes with it firing (fired before the passing iteration) | escalations (passed) |
|---|---|---|---|
| GPT-4.1 mini | 5 | 5 (0) | esc 3 (0), restart 3 (0) |
| Gemini 2.5 Flash | 6 | 6 (1) | esc 0, restart 1 (1) |
| Claude Haiku 4.5 | 9 | 9 (4) | esc 2 (2), restart 1 (1) |
| Pooled | 20 | 20 (5) | esc 5 (2), restart 5 (2) |

"Passes with it firing" counts a directive computed on the passing iteration itself,
which the model never sees; the stricter count (fired on an earlier iteration) is in
brackets. Escalation conditions: 1 run in total fired the interpreter (restart, Haiku).

### Tool invocations (Verilator + Yosys per run), sem_adv → sem_escalate

| | sem_adv | sem_escalate | Reduction |
|---|---|---|---|
| GPT-4.1 mini | 2.39 | 0.71 | 70.5% |
| Gemini 2.5 Flash | 2.22 | 0.00 | 100.0% |
| Claude Haiku 4.5 | 2.25 | 0.08 | 96.5% |
| Pooled Set 4 | 2.29 | 0.26 | **88.6%** |
| Set 1 (reference) | | | 16.6% recoverable, 75.1% ceiling |
| Set 3 (reference) | | | 27.6% recoverable |

### GPT-4.1 mini's 9 failures

All 9 are `sequence_detector`: baseline rep2; sem_adv rep2, rep3; sem_escalate
rep1–3; sem_escalate_restart rep1–3. Dominant failure: `logic_error` on every
iteration, the testbench reporting "Test completed with 2/3 failures"; the last
iteration of restart rep3 ended in a compile error (`Unable to bind wire/reg/memory
next_state`). The three escalation failures escalated and still failed.

### Cost (INR per run / per pass)

| Model | baseline | sem_adv | sem_escalate | sem_escalate_restart |
|---|---|---|---|---|
| GPT-4.1 mini | 0.112 / 0.114 | 0.127 / 0.132 | 0.158 / 0.168 | 0.158 / 0.168 |
| Gemini 2.5 Flash | 0.245 / 0.245 | 0.236 / 0.236 | 0.224 / 0.224 | 0.233 / 0.233 |
| Claude Haiku 4.5 | 0.506 / 0.506 | 0.473 / 0.473 | 0.478 / 0.478 | 0.495 / 0.495 |

Token overhead vs baseline: GPT-4.1 mini sem_adv +31%, escalation +104%/+108% (driven
by the 6 sequence_detector runs that used all 8 iterations); Gemini −2%/−17%/−8%;
Haiku −8%/−6%/−2%. Mean latency 3.2–3.9 s per call.

**OpenAI system fingerprints:** `fp_b43877da5b` on 256 full-run calls and
`fp_6050bec882` on 7, so OpenAI's serving backend changed during the run (same model
snapshot).

**Figures:** `analysis/fig5_capability_ladder_api.{png,pdf}` (Figure 5 with the three API
baseline bars in one colour, "4B to API models"); `analysis/fig_set4_inr_per_pass.{png,pdf}`.

---

## Set 4b: floor tier (19 modules × 4 conditions × N=3, 228 runs per model)

**Models and why.** Pilot (LIFObuffer, adder_16bit × 4 conditions × N=1 per model)
projected GPT-4.1 mini $0.88, Gemini $2.43, Haiku $2.12, total $5.42 (90% upper bound
$6.25) ≤ $12, so all three ran, in parallel, capped at 1.5× projection: $1.32, $3.64,
$3.18.

**All three hit their caps and stopped cleanly.** The pilot projection was too low (actual
reached 1.46–1.47× projection at the stop); both pilot modules passed quickly, so the pilot
did not sample the long 6–8-iteration failing runs that dominate floor cost. Caps were not
raised.

| Model | Runs completed | Errored | Truncated | Passes | Set 4b spend |
|---|---|---|---|---|---|
| GPT-4.1 mini | 180/228 | 0 | 0 | 103 | $1.3042 |
| Gemini 2.5 Flash | 220/228 | 0 | 0 | 134 | $3.6156 |
| Claude Haiku 4.5 | 105/228 | 0 | 0 | 82 | $3.1329 |

Runs go module by module, so the missing runs are the tail of the module order:
Haiku did not reach alu, barrel_shifter, counter_12, freq_divbyfrac, fsm, LIFObuffer,
parallel2serial, pulse_detect, serial2parallel or traffic_light (and float_multi is
partial); GPT-4.1 mini did not reach alu, pulse_detect, serial2parallel or
traffic_light. 3 transient first-attempt errors (2 × Anthropic 503, 1 Gemini connection
reset) all succeeded on retry; 0 reasoning tokens.

### Q1: which floor modules do API models pass at baseline? (baseline passes /3; tier = <20% floor, <80% recoverable, else ceiling)

| Module | GPT-4.1 mini | Gemini 2.5 Flash | Claude Haiku 4.5 |
|---|---|---|---|
| accu | 3/3 ceiling | 3/3 ceiling | 3/3 ceiling |
| adder_16bit | 3/3 ceiling | 3/3 ceiling | 3/3 ceiling |
| adder_32bit | 3/3 ceiling | 3/3 ceiling | 3/3 ceiling |
| adder_bcd | 3/3 ceiling | 3/3 ceiling | 3/3 ceiling |
| adder_pipe_64bit | 0/3 floor | 0/3 floor | 0/3 floor |
| alu | not run | 0/3 floor | not run |
| barrel_shifter | 1/3 recoverable | 3/3 ceiling | not run |
| counter_12 | 3/3 ceiling | 3/3 ceiling | not run |
| div_16bit | 0/3 floor | 0/3 floor | 2/3 recoverable |
| float_multi | 2/3 recoverable | 1/3 recoverable | 1/3 recoverable |
| freq_divbyfrac | 0/3 floor | 0/3 floor | not run |
| fsm | 3/3 ceiling | 3/3 ceiling | not run |
| LIFObuffer | 3/3 ceiling | 3/3 ceiling | not run |
| multi_pipe_4bit | 3/3 ceiling | 0/3 floor | 3/3 ceiling |
| multi_pipe_8bit | 0/3 floor | 1/3 recoverable | 3/3 ceiling |
| parallel2serial | 0/3 floor | 1/3 recoverable | not run |
| pulse_detect | not run | 3/3 ceiling | not run |
| serial2parallel | not run | 3/3 ceiling | not run |
| traffic_light | not run | 0/3 floor | not run |

15 of 19 floor modules leave the floor for at least one API model at baseline;
4 (accu, adder_16bit, adder_32bit, adder_bcd) are ceiling for all three. Still floor for
every model that ran them: adder_pipe_64bit, freq_divbyfrac, alu (Gemini only),
traffic_light (Gemini only). Note: counter_12 is floor in the Twin tiers (0/15) but passes
33/36 in Set 1 and 24/24 here; its Twin tier looks like an artefact of the Twin run, not a
property of the module.

### Q2: does the interpreter fire on floor failures, and do passes happen only with it?

| Condition | Runs | Fails | Fails with semantic_fired | Passes | Passes with a directive before the pass | ...in cells whose baseline was 0/3 |
|---|---|---|---|---|---|---|
| baseline | 129 | 48 | 0 | 81 | 0 | – |
| sem_adv | 127 | 52 | 28 | 75 | 10 | 3 |
| sem_escalate | 126 (67 escalated) | 47 | 26 | 79 | 0 | 0 |
| sem_escalate_restart | 123 (56 escalated) | 39 | 22 | 84 | 0 | 0 |

The interpreter does reach floor failures: it fired in about half of the failing
tool-condition runs. But in no escalation-condition run did a pass follow a directive.
The 3 sem_adv passes in baseline-0/3 cells, traced:
- **Gemini multi_pipe_4bit (sem_adv rep3).** The cell's sem_adv passes are 3/3 against
  baseline 0/3 (escalate 2/3, restart 3/3), but reps 1–2 passed on iteration 2 after raw
  Verilator/Yosys feedback with no directive. The gain there comes from tool output, not
  from interpreter directives.
- **Haiku adder_pipe_64bit (sem_adv rep2, rep3).** An `UNUSEDSIGNAL` directive on
  iterations 1–2 was followed by 2–3 more compile-error iterations before the pass, so the
  pass is not attributable to the directive.

No pass is attributable to the interpreter on this evidence.

### Q3: on cells still failing (baseline < 3/3), do conditions differ?

| Scope | sem_adv | sem_escalate | sem_escalate_restart |
|---|---|---|---|
| Pooled | −1.8 [−14.1, +14.0], 19 cells, p=1.000 | +1.9 [−13.0, +18.5], 18 cells, p=1.000 | +13.7 [−3.9, +31.4], 17 cells, p=0.245 |
| GPT-4.1 mini | −4.8 [−14.3, +0.0], 7, p=1.000 | −4.8 [−28.6, +19.0], 7, p=1.000 | −9.5 [−33.3, +9.5], 7, p=0.751 |
| Gemini 2.5 Flash | +0.0 [−22.2, +29.6], 9, p=1.000 | +16.7 [−4.2, +41.7], 8, p=0.374 | +29.2 [+8.3, +54.2], 8, p=0.126 |
| Claude Haiku 4.5 | +0.0 [−33.3, +66.7], 3, p=1.000 | −22.2 [−33.3, +0.0], 3, p=0.498 | +33.3 [+0.0, +66.7], 2, p=1.000 |

No contrast reaches significance (all sign-flip p ≥ 0.126). Gemini's restart CI excludes
zero, but with 8 cells and p=0.126 it is not a finding, and the escalation passes involved
0 directives delivered before the pass (Q2), so any gain would come from the restart prompt,
not from the interpreter. A few cells have unequal N where the cap stopped a module part
way.

### Q4: modules failed in every run, by every model, under every condition

**None among modules run by all three models.** Because of the caps, the strict test
could only be applied to the 9 modules all three models ran (8 complete, float_multi
partial for Haiku); each of those had at least one pass. Looking at the data that exist, two modules had zero passes in every run.
Neither is a strict Q4 module:

### Oracle audit (candidate, needs manual confirmation)

| Module | Runs (models) | Reference design under our harness + toolchain | Dominant failure | Spec/testbench mismatch? |
|---|---|---|---|---|
| freq_divbyfrac | 0/24 (GPT-4.1 mini, Gemini) | PASS | 164 of 168 failing iterations are simulation mismatches on `clk_div` ("Failed at N: … expected N"), typically 8–11 of 20 checks failing; 4 compile errors | Not clearly. The testbench releases `rst_n` on the same timestep as a `clk` posedge and then checks `clk_div` cycle-exactly from t=15 ns, so the exact phase after reset matters and the spec does not state it. But candidates fail by duty-cycle/shape, not by a pure one-edge shift. **Candidate: possible phase-alignment strictness; needs manual confirmation.** |
| alu | 0/4 (Gemini only) | PASS (with a `$readmemh reference.dat: Not enough words` warning also present for the reference) | 21 simulation "Error" verdicts, 3 compile errors | Too few runs (4, one model) to judge. **Candidate only by the data available; needs manual confirmation.** |

---

## Reading

Set 4 is a ceiling result. Gemini 2.5 Flash and Claude Haiku 4.5 pass all 204
recoverable-band runs in every condition, so they carry no information about the
conditions. The condition comparison rests on GPT-4.1 mini alone. There, sem_adv and both
escalation conditions are a few points below baseline (−2.0 and −3.9 cell points), none
significant (p = 1.000), and the whole gap is one module, sequence_detector. On the
recoverable band the API models make the interpreter nearly irrelevant: it fired in 20
sem_adv runs, a directive preceded a pass in 5, and escalation almost never triggered
(5 of 153 runs per escalation condition). The one strong number is cost discipline:
escalation cut tool invocations by 88.6% versus sem_adv (70.5–100% per model), above Set 3's
27.6%, because capable models rarely fail twice. That is a statement about how rarely
escalation triggers, not about repair quality.

Set 4b does not test what it was designed to test as cleanly as planned. All three
providers stopped at 1.5× a projection that underestimated floor cost, leaving Haiku with
105 of 228 runs. What it does show: most "floor" modules are not beyond these models. 15 of
19 leave the floor for at least one model and 4 are ceiling for all three. So the floor
tier is a property of the 4B–32B models, not of the modules. On the floor failures that
remain, the interpreter fires often, but no pass is attributable to a directive; the one
large cell-level gain (Gemini multi_pipe_4bit) came from raw tool feedback. The paper's
"floor is outside the interpreter's reach" is not contradicted, but this run cannot confirm
it either: coverage is incomplete, and the condition contrasts are null at 2–19 cells.
No module qualified as a strict oracle-failure candidate. freq_divbyfrac is worth a manual
look.

## Deviations from the pre-registration, with reasons

1. **Kimi dropped** (A8): stopped at smoke on `reasoning_tokens=1`, then dropped by
   decision, as a third ceiling model at T=0.6 would add nothing.
2. **Laptop toolchain** instead of HPC, matched exactly to the HPC oss-cad-suite
   (140/140, 51/51 parity); Set 3's own versions were never recorded.
3. **Per-call retries** (max 3) instead of Set 3's per-run re-runs, because re-runs cost
   money; there were 0 errored runs in either set.
4. **max_tokens 8,192** (A1); 0 truncations in Set 4 or Set 4b.
5. **`boot_ci` copied along with `signflip_p`.** A9 permitted `signflip_p` and its helpers.
   `boot_ci` sat in the same read window and replaced an earlier reimplementation that
   matched the published CIs only at one decimal. All 12 published numbers are reproduced
   exactly.
6. **Set 4b stopped at the caps**: incomplete coverage (180/220/105 of 228). The projection
   underestimated floor cost ~1.5×, and caps were not raised, per the brief.
7. **Q4 evaluated on available data**: the strict all-models test covers only the 9
   modules every model ran. The two zero-pass modules were audited, labelled as
   partial-coverage candidates.
8. **Tie-break for the Set 4b pilot modules** (Set 1 pass rate, then alphabetical) was
   added in the Set 4b pre-registration because 15 modules tie at 0/15 in Twin.
9. **Set 4b "passes with the interpreter"** uses the stricter "directive delivered before
   the pass" count alongside the raw semantic_fired count, because sem_adv also counts
   lint that fired on the passing iteration itself, which the model never saw.

---

## Set 4b update (2026-09-29): completion run (Part B of the final API batch)

**LEAK STATUS: clean.** Spend of the completion run: OpenAI $0.5786, Anthropic $2.2210 (tag
`floor_full` in `phase2/results/p3_api/ledgers/`). Set 4b total now $10.85 (INR 1,229). Running
total since Set 4, all batches: $13.03 (INR 1,477).

**Method.** Resumed from the existing master logs; no completed run re-run; same protocol and
toolchain. Whole modules in priority order (lowest pooled pass rate first). The projection per
remaining (model, module) was the max calls/run on that module among the other models × the model's
own USD/call × 1.3: OpenAI $0.53, Anthropic $7.94.

**Completion.**

| Model | Valid runs | Errored | Not run |
|---|---|---|---|
| GPT-4.1 mini | **228/228** | 0 | 0 |
| Gemini 2.5 Flash | 220/228 (unchanged, disclosed; no Gemini calls) | 0 | 8 (alu 8) |
| Claude Haiku 4.5 | 143/228 | **85** (HTTP 400: account credit exhausted) | 0 |

Haiku completed alu, freq_divbyfrac, parallel2serial and 2 of 3 float_multi runs before the Anthropic
account ran out of credit. Still missing for Haiku: traffic_light, barrel_shifter, pulse_detect,
LIFObuffer, fsm, serial2parallel, counter_12, and 1 float_multi run. So Haiku is complete on 12 of 19
modules. 0 truncations and 0 reasoning tokens in all calls.

### Q1 updated (baseline passes /3; tier at this model)

| Module | GPT-4.1 mini | Gemini 2.5 Flash | Claude Haiku 4.5 |
|---|---|---|---|
| accu | 3/3 ceiling | 3/3 ceiling | 3/3 ceiling |
| adder_16bit | 3/3 ceiling | 3/3 ceiling | 3/3 ceiling |
| adder_32bit | 3/3 ceiling | 3/3 ceiling | 3/3 ceiling |
| adder_bcd | 3/3 ceiling | 3/3 ceiling | 3/3 ceiling |
| adder_pipe_64bit | 0/3 floor | 0/3 floor | 0/3 floor |
| alu | 0/3 floor | 0/3 floor | 0/3 floor |
| barrel_shifter | 1/3 recoverable | 3/3 ceiling | not run |
| counter_12 | 3/3 ceiling | 3/3 ceiling | not run |
| div_16bit | 0/3 floor | 0/3 floor | 2/3 recoverable |
| float_multi | 2/3 recoverable | 1/3 recoverable | 1/3 recoverable |
| freq_divbyfrac | 0/3 floor | 0/3 floor | 0/3 floor |
| fsm | 3/3 ceiling | 3/3 ceiling | not run |
| LIFObuffer | 3/3 ceiling | 3/3 ceiling | not run |
| multi_pipe_4bit | 3/3 ceiling | 0/3 floor | 3/3 ceiling |
| multi_pipe_8bit | 0/3 floor | 1/3 recoverable | 3/3 ceiling |
| parallel2serial | 0/3 floor | 1/3 recoverable | 3/3 ceiling |
| pulse_detect | 0/3 floor | 3/3 ceiling | not run |
| serial2parallel | 3/3 ceiling | 3/3 ceiling | not run |
| traffic_light | 2/3 recoverable | 0/3 floor | not run |

16 of 19 floor modules leave the floor for at least one API model at baseline. Three stay floor for
every model that ran them: adder_pipe_64bit, alu and freq_divbyfrac.

### Q2 updated

| Condition | Runs | Fails | Fails with semantic_fired | Passes | Passes with a directive before the pass | ...in baseline-0/3 cells | Escalated |
|---|---|---|---|---|---|---|---|
| baseline | 150 | 61 | 0 | 89 | 0 | – | – |
| sem_adv | 148 | 67 | 37 | 81 | 11 | 3 (the same three as before, traced there) | – |
| sem_escalate | 147 | 60 | 32 | 87 | 1 | 0 | 81 |
| sem_escalate_restart | 146 | 56 | 32 | 90 | 0 | 0 | 73 |

The completion data leave the reading unchanged: the interpreter fires on about half of the failing
tool-condition runs, and no pass is attributable to a directive.

### Q3 updated (condition − baseline on cells with baseline < 3/3)

| Scope | sem_adv | sem_escalate | sem_escalate_restart |
|---|---|---|---|
| Pooled | −4.2 [−16.7, +9.7], 24 cells, p=0.694 | +1.4 [−10.1, +14.5], 23, p=1.000 | +5.8 [−8.7, +21.7], 23, p=0.602 |
| GPT-4.1 mini | −10.0 [−23.3, +0.0], 10, p=0.505 | −3.3 [−20.0, +13.3], 10, p=1.000 | −13.3 [−33.3, +3.3], 10, p=0.372 |
| Gemini 2.5 Flash | +0.0 [−22.2, +29.6], 9, p=1.000 | +16.7 [−4.2, +41.7], 8, p=0.374 | +29.2 [+8.3, +54.2], 8, p=0.126 |
| Claude Haiku 4.5 | +0.0 [−26.7, +33.3], 5, p=1.000 | −13.3 [−26.7, +0.0], 5, p=0.496 | +6.7 [−20.0, +40.0], 5, p=1.000 |

No contrast is significant (all p ≥ 0.126). The signs differ across models (GPT-4.1 mini negative,
Gemini positive), so there is no consistent condition effect on the floor.

### Q4 updated

Passes / valid runs per model, all conditions:

| Module | GPT-4.1 mini | Gemini 2.5 Flash | Claude Haiku 4.5 |
|---|---|---|---|
| alu | 0/12 | 0/4 | 0/12 |
| freq_divbyfrac | 0/12 | 0/12 | 0/12 |
| adder_pipe_64bit | 2/12 | 0/12 | 4/12 |
| div_16bit | 0/12 | 0/12 | 6/12 |

Zero passes over GPT + Haiku (both complete on these modules): **alu, freq_divbyfrac**. Zero over all
three (Gemini's alu only 4 runs, disclosed): **alu, freq_divbyfrac**.

### Oracle audit (both candidates, needs manual confirmation)

| Module | Runs | Reference under our harness + 0.69 toolchain | Dominant failure | Spec/testbench mismatch? |
|---|---|---|---|---|
| freq_divbyfrac | 0/36 (3 models) | PASS | 240 simulation mismatches, almost all first failing at check 3 ("clk_div=1, expected 0"), identically across all three models; 12 compile errors | **Possible.** Every model keeps clk_div high one half-step longer than the testbench expects. The testbench releases rst_n on the same timestep as a clk posedge and checks cycle-exactly from t=15 ns. The spec states "3 high, 4 low" but builds it from two OR-ed intermediate clocks without fixing their phase. A failure this consistent across three independent models points to an under-determined spec or a phase-strict testbench rather than model error alone. **Candidate, needs manual confirmation.** |
| alu | 0/28 (3 models) | PASS (a `$readmemh` "not enough words" warning is also present for the reference; only entries 0–16 are used) | 170 "===========Error===========" simulation verdicts; 22 compile errors (redeclared `r`, syntax) | **Unlikely a defect; a feedback-poor oracle.** The testbench reports one Error line for any mismatch over 17 opcodes, so the repair loop gets no per-operation signal. The spec fixes MIPS-style conventions a model can easily invert (shift amount from `a`; LUI from `a[15:0]`; `flag`='z' off SLT/SLTU). **Candidate, needs manual confirmation.** |

### Honest reading (updated)

Set 4b complete for GPT-4.1 mini, near-complete for Gemini, and 63% complete for Haiku.
- The floor tier is mostly a property of the 4B–32B models: 16 of 19 floor modules are solved at
  baseline by at least one API model.
- On what remains, the interpreter fires but no pass is attributable to it, and the condition contrasts
  are null with inconsistent signs. That is consistent with "the floor is outside the interpreter's
  reach", but it rests on a null at 5–24 cells, not a positive test.
- Two modules fail for every model: freq_divbyfrac is a plausible oracle-integrity finding; alu more
  likely a feedback-poor testbench plus a hard spec. Both need a human check.

### Deviations (completion run)

1. **Haiku incomplete** because the Anthropic account ran out of credit at a cumulative ledger spend of
   $6.69, not because of the $10 runner cap. The 85 errored runs cost $0.
2. **HTTP 400 credit exhaustion was not an automatic provider stop.** It is not covered by the
   auth-failure rule (401/403), so the runs errored one by one instead.
3. **Whole-module budget check used the projection;** Haiku's first module (alu) cost ~1.3× its
   projection. Moot in the end, since credit ran out first.

---

## Gemini completion run (2026-10-12): Set 4b alu and a Phase 3 ladder row

Gemini 2.5 Flash only, under `SET4_PREREG.md` Amendment 3 (appended 2026-10-12 13:21 UTC, before any call it
governs; SHA-256 after it `62C1C0BEFE0487C639161A724FFC56E89A806E45AB644501A0BBFB2ADBE3216A`). No OpenAI, Anthropic
or Moonshot call was made. Numbers come from `spend_summary.py`, `analysis_set4b.py`, `oracle_audit.py`,
`p3_api/p3_api_analysis.py`, `p3_api/p3_signoff_ladder.py` and `fig_gemini_completion.py`; stdout copies are in
`phase2/results/set4_api/analysis_4b_stdout_v3.txt`, `oracle_audit_stdout_v3.txt`,
`phase2/results/p3_api/p3_api_analysis_stdout_v2.txt`, `p3_ladder_signoff_stdout.txt` and
`spend_summary_gemini_completion.txt`.

**LEAK STATUS: clean.** `scan_secrets.py` found 0 matches after the smoke test and again at the end. `leak_audit.py`:
each exact key value is in 0 commits on any branch.

**Spend.** This run: $0.4961 (INR 56.2), all Gemini. That is smoke $0.0008, Part A (`floor_full`) $0.3179 and
Part B (`p3_full`) $0.1775, in `phase2/results/p3_api/ledgers/gemini_ledger.jsonl`. Caps: Part A $1.5 (used
$0.3187, smoke included); Part B $1.5 of its own spend (used $0.1775); combined $3.0 (used $0.4961). No cap was
reached. **Gemini total across all batches: $4.5467 (INR 515.0)**, under the INR 1,500 limit. The total since Set 4,
all providers, is $13.5306 (INR 1,532.7).

### Pre-flight and smoke test

- **Toolchain** (oss-cad-suite 20260917 via `STITCH_SET4_OSSCAD`): Yosys 0.69+71 (150c32b03), Verilator 5.053
  (v5.052-103-g1aa87913c), Icarus 14.0 (s20260301-451-gc9ed76463). This matches the HPC.
- **Offline checks:** `test_backends.py` passes, including the new stop rules. Mock parity now covers Gemini. The
  prompt-sequence hashes agree for 18 of 18 (condition, task) runs. The wire-level (system, user) sequences match
  the Ollama path in 96 of 96 requests, for OpenAI, Anthropic and Gemini.
- **Minimal call:** authentication OK, 0 reasoning tokens, finish `STOP`, and the ledger grew by one line.
  **modelVersion `gemini-2.5-flash`**, the same value as all 1,117 successful Gemini calls in the Set 4 and Set 4b
  ledgers. So the alias did not change. All 234 calls of this run returned the same value.
- **One full run** (`counter_12`, `sem_adv`, N=1, tag `smoke_gc`): passed on iteration 1, and
  `detect_outcome(sim_log, benchmark="rtllm")` returns `PASS` on its log. `semantic_fired` is logged (0). The run used
  776 tokens, identical to the Set 4 smoke run of 2026-09-28. Re-running the same command made 0 calls (the
  ledger stayed at 2 lines), so resume works.

### Part A: Set 4b completed for Gemini

Before the run the master log held 220 completed runs, 0 errored. The 8 missing runs were all alu: sem_adv rep2–3,
sem_escalate rep1–3 and sem_escalate_restart rep1–3. **Result: 228/228**, 0 errored, 49 calls, $0.3179, 0 reasoning
tokens, 0 truncations (largest completion 2,841 tokens). No retry pass was needed.

Gemini now passes alu in 3 of 12 runs: sem_adv rep2 (iteration 4), sem_escalate_restart rep1 (iteration 5) and
sem_escalate_restart rep2 (iteration 2). Baseline and sem_escalate stay at 0/3. No interpreter directive reached the
model before any of these passes:
- in sem_adv rep2 the interpreter never fired;
- in restart rep1 the run escalated at iteration 2, then had two compile-error iterations, and the interpreter ran
  only on the passing iteration 5;
- restart rep2 passed on iteration 2 without escalating.

| Coverage (of 228) | Valid | Errored | Not run |
|---|---|---|---|
| GPT-4.1 mini | 228 | 0 | 0 |
| Gemini 2.5 Flash | **228** | 0 | 0 |
| Claude Haiku 4.5 | 143 | 85 (HTTP 400, credit; **pending**, see `PENDING.md`) | 0 |

**Q1 (baseline passes /3) is unchanged** from the previous update, because Gemini's alu baseline was already
complete (0/3). 16 of 19 floor modules leave the floor for at least one API model. adder_pipe_64bit, alu and
freq_divbyfrac are floor at baseline for every model that ran them. New figure:
`phase2/results/set4_api/analysis_4b/fig_set4b_q1_baseline.{png,pdf}`.

#### Q2 updated

| Condition | Runs | Fails | Fails with semantic_fired | Passes | Passes with a directive before the pass | ...in baseline-0/3 cells | Escalated |
|---|---|---|---|---|---|---|---|
| baseline | 150 | 61 | 0 | 89 | 0 | – | – |
| sem_adv | 150 | 68 | 37 | 82 | 11 | 3 (the same three, traced above) | – |
| sem_escalate | 150 | 63 | 33 | 87 | 1 | 0 | 84 |
| sem_escalate_restart | 149 | 57 | 33 | 92 | 0 | 0 | 75 |

The reading is unchanged. The interpreter fires in about half of the failing tool-condition runs, and no pass in a
baseline-0/3 cell is attributable to a directive.

#### Q3 updated (condition − baseline on cells with baseline < 3/3)

| Scope | sem_adv | sem_escalate | sem_escalate_restart |
|---|---|---|---|
| Pooled | −2.8 [−15.3, +11.1], 24 cells, p=0.848 | +1.4 [−11.1, +13.9], 24, p=1.000 | +8.3 [−6.9, +23.6], 24, p=0.407 |
| GPT-4.1 mini | −10.0 [−23.3, +0.0], 10, p=0.505 | −3.3 [−20.0, +13.3], 10, p=1.000 | −13.3 [−33.3, +3.3], 10, p=0.372 |
| Gemini 2.5 Flash | +3.7 [−18.5, +33.3], 9, p=1.000 | +14.8 [−3.7, +37.0], 9, p=0.374 | +33.3 [+11.1, +55.6], 9, p=0.062 |
| Claude Haiku 4.5 | +0.0 [−26.7, +33.3], 5, p=1.000 | −13.3 [−26.7, +0.0], 5, p=0.496 | +6.7 [−20.0, +40.0], 5, p=1.000 |

No contrast is significant at 0.05: the smallest sign-flip p is 0.062, among 12 contrasts with no correction. The
largest is Gemini's sem_escalate_restart, now on 9 cells (alu's escalation cells are complete). Its bootstrap CI
excludes zero, but no sem_escalate_restart pass followed a directive (Q2). So any gain there comes from the restart
prompt and the raw tool feedback, not from the interpreter. Across models the signs still differ (GPT-4.1 mini
negative, Gemini positive).

#### Q4 updated (strict test on every module run by all three models)

The strict test now covers the 12 modules that every model ran: accu, adder_16bit, adder_32bit, adder_bcd,
adder_pipe_64bit, alu, div_16bit, float_multi, freq_divbyfrac, multi_pipe_4bit, multi_pipe_8bit and
parallel2serial. Haiku's float_multi has 11 of 12 runs.

| Module | GPT-4.1 mini | Gemini 2.5 Flash | Claude Haiku 4.5 |
|---|---|---|---|
| alu | 0/12 | **3/12** | 0/12 |
| freq_divbyfrac | 0/12 | 0/12 | 0/12 |
| adder_pipe_64bit | 2/12 | 0/12 | 4/12 |
| div_16bit | 0/12 | 0/12 | 6/12 |

**Strict Q4 (failed in every run, by every model, under every condition): freq_divbyfrac only.** alu drops out
because Gemini passes it 3 times. Zero passes over GPT-4.1 mini + Haiku is still alu and freq_divbyfrac.

#### Oracle audit (updated; candidates, need manual confirmation)

| Module | Runs | Reference under our harness + 0.69 toolchain | Dominant failure | Spec/testbench mismatch? |
|---|---|---|---|---|
| freq_divbyfrac | 0/36 (3 models) | PASS | 240 simulation mismatches, almost all first failing at check 3 ("clk_div=1, expected 0") in all three models; 12 compile errors (unchanged) | **Not supported as an oracle defect** (Q7 answer below): genuine model failures on a hard fractional-divider spec. Still the only strict Q4 module. **Needs manual confirmation.** |
| alu | 3/36 (Gemini 3/12; GPT-4.1 mini 0/12, Haiku 0/12) | PASS (the `$readmemh` "not enough words" warning is also present for the reference) | 206 "===========Error===========" verdicts over iterations; 32 compile-error iterations (12 redeclared `r`, 8 SystemVerilog declarations in an unnamed block) | **No longer a Q4 candidate.** A model passes the testbench as written, so the oracle can be passed. It is still a feedback-poor testbench (one Error line for any mismatch over 17 opcodes), and the passes came from simulation and tool feedback, not from directives. An oracle defect is not supported by this evidence. |

#### Q7 answer: freq_divbyfrac shifted-trace analysis (free, no paid calls)

Added 2026-10-12 under Amendment 5. Set 4c was closed before it reached this module, so this analysis of the 36
existing Set 4b runs answers Q7 instead.

**Method** (`set4c.py trace`; outputs in `phase2/results/set4_api/analysis_4c/freq_divbyfrac_trace.json` and
`freq_divbyfrac_trace_stdout.txt`):
- Run the **original** freq_divbyfrac testbench with one added line that prints `clk_div` at each of its 20
  checks, so every sample sees the same event ordering as the check itself.
- Do this for the final candidate of each Set 4b run and for the reference.
- Compare each trace with the expected sequence `11100001110000111000` (3 high and 4 low half-steps, repeating)
  at shifts of −2 to +2 checks, over the checks that overlap.

**Results:**
- **Reference:** passes; 20/20 at shift 0. It fails if shifted by one step (14/19 at ±1, 8/18 at ±2), so the
  expected sequence is not shift-tolerant.
- **Candidates:** 34 of the 36 final candidates compile (2 compile errors). **None of the 34 matches at shift 0 and
  none is a shifted copy of the expected sequence.**
- **Shape:** they have the wrong period and duty cycle. Typical traces are `H6 L7 H7` and `H7 L7 H6` (high 6–7 and
  low 7 half-steps, against the specified 3 and 4), a period of about 13–14 half-steps instead of 7.
  - In the 32 candidates that start high, the first high phase lasts 4 to 20 half-steps (H4 5, H5 3, H6 6, H7 7,
    H9 3, H11 3, H13 4, H20 1). It is never 3.
- **First failing check:** check 3 ("clk_div=1, expected 0") in 32 of 34; check 0 ("clk_div=0, expected 1") in 2.

**Verdict: genuine model failures on a hard fractional-divider spec; not supported as an oracle defect; needs
manual confirmation.** The expected sequence matches spec line 20 (3 high, 4 low half-steps), and the reference
passes it. The models fail by period and shape, not by a phase offset that a more lenient testbench would forgive.

**Correction** to the earlier wording in this report ("Every model keeps clk_div high one half-step longer than the
testbench expects"): that understates the gap. The first high phase lasts 4 to 20 half-steps, and the whole period
is about 2× the specified one.

The spec text and the testbench check lines (file:line) are in `FREQ_DIVBYFRAC_AUDIT.md` for human review.

**Reference counter check (added 2026-10-13, `set4c.py refcheck`).** Logged under its own testbench, the reference's
counter advances once per rising edge and wraps every 14 half steps, giving two `clk_div` periods (high 3, low 4) per
wrap, while spec line 17 says the counter "cycles through 7 half clock steps". In our reading the spec's description
of the counter does not match its own reference design, which plausibly explains the models' roughly doubled period: a
spec-wording defect, not a testbench defect. The same-timestep reset release is a minor robustness weakness that did
not cause the failures. Verdict unchanged.

### Part B: Phase 3 ladder row, Gemini 2.5 Flash

**Gates first** (`p3_gate_local.sh`, the same commands as `phase3/hpc/phase3_gate.slurm`, on a `/tmp` copy of
phase3/): G0 44 passed / 0 failed; G1 11/11 tasks OK (GATE 1 PASS); G2 mock smoke (66 runs) and summarize OK; G5
PASS (11 baseline_gate runs, no tool text in the prompts, would_fire on 11); G4 PASS; G3 198 runs per model. **ALL
GATES PASSED**, on the same toolchain as before.

**Run.** `p3_api_runner.py --api gemini`: the same Phase 3 runner (`stitch_runner_p3.py`, unmodified), prompts and
toolchain as the GPT-4.1 mini and Claude Haiku 4.5 rows. **198/198 runs**, 0 errored, 183 calls, $0.1775 (INR 20.1),
0 reasoning tokens, 0 truncations. Provenance is identical across all 594 API runs (3 models × 198): protocol
`feedback_first_v2`, interpreter v3 3.0.1, base interpreter sha256 `42f61a49…abff`, T=0.1, max_iters 6,
sem_include_raw 1, runner sha256 `119611fe…6a36`, and the same toolchain strings.

**Sign-off scoring** (`p3_api/p3_signoff_ladder.py`). It calls `load_many` and `apply_signoff` from
`phase3/runner/analyze_phase3.py`, imported read-only, which is the path `phase3_final/paper_numbers.py` used for
the two published API rows. The cache is a copy outside phase3/:
`phase2/results/p3_api/signoff_cache.json`.
- 19 new Gemini candidates (mem_wb_mux and Address_select) were simulated once against `tb_signoff.v`; the cache
  went from 318 to 337 entries.
- 0 candidates pass `tb_signoff.v` but fail `tb.v`.
- Checks: the script reproduces the published GPT-4.1 mini and Claude Haiku 4.5 rows of Table 12 exactly.
  Re-simulating the 27 cached GPT/Haiku candidates on this toolchain gives the cached verdict for 27 of 27.

#### Ladder rows in the format of Table 12 (`tab:mpsoc-ladder`)

Sign-off clean of 33 (sim-silent of 18 / sim-visible of 15), and tokens per run over all 33 runs. One model each,
N=3, descriptive, not pooled.

| Condition | gpt-4.1-mini clean | tokens | claude-haiku-4.5 clean | tokens | **gemini-2.5-flash clean** | **tokens** |
|---|---|---|---|---|---|---|
| baseline | 12 (0/12) | 440 | 12 (0/12) | 517 | 15 (0/15) | 516 |
| baseline_gate | 28 (16/12) | 1,529 | 30 (18/12) | 1,099 | 33 (18/15) | 1,160 |
| raw_adv | 30 (18/12) | 1,164 | 30 (18/12) | 1,334 | 30 (18/12) | 1,291 |
| sem_adv (v2) | 30 (18/12) | 1,255 | 30 (18/12) | 1,517 | 33 (18/15) | 1,478 |
| sem_adv (v3) | 30 (18/12) | 1,257 | 30 (18/12) | 1,524 | 32 (18/14) | 1,479 |
| sem_esc_restart (v3) | 30 (18/12) | 1,404 | 30 (18/12) | 1,101 | 33 (18/15) | 1,225 |

The GPT-4.1 mini and Claude Haiku 4.5 columns are the published ones, reproduced by the script. LaTeX for the
Gemini column, for a later edit:
`$15$ ($0$/$15$) & $516$`, `$33$ ($18$/$15$) & $1{,}160$`, `$30$ ($18$/$12$) & $1{,}291$`,
`$33$ ($18$/$15$) & $1{,}478$`, `$32$ ($18$/$14$) & $1{,}479$`, `$33$ ($18$/$15$) & $1{,}225$`.

Other Gemini numbers, all from the scripts:
- **As run (tb.v):** clean_pass is 33/33 in every tool condition and 15/33 at baseline (0/18 sim-silent, by
  protocol). All four primary contrasts are +0.0, with p=1.000.
- **Signed off defective:** baseline 18 (all 18 sim-silent runs), raw_adv 3, sem_adv_v3 1, and 0 in baseline_gate,
  sem_adv_v2 and sem_esc_restart_v3.
- **Every non-baseline miss is on Address_select:** raw_adv 3 of 3, sem_adv_v3 1 of 3.
- **baseline_gate runs not clean while would_fire = 1:** none.
- **LLM calls per run:** 1.00–1.06 in the tool conditions (0.45 at baseline). INR per clean pass (as run) is
  0.095–0.120.

New figure: `phase2/results/p3_api/analysis/fig_p3_api_ladder_signoff.{png,pdf}`.

**Reading.** Gemini 2.5 Flash is at ceiling on the sim-silent defects, like the other two API models. It reaches
18/18 under every tool condition and under the bare gate, and 0/18 at baseline, where simulation-only repair signs
off every sim-silent run as defective. So the gate alone carries the whole effect for this model, as it does for
Haiku. The interpreter adds nothing measurable over the gate (all contrasts 0), which fits Result (6): the
interpreter's pass-rate benefit is a small-model effect, and the guard is needed at every size.

Gemini differs from the other two on one task, Address_select, the specification gap of Result (8):
- Gemini's repairs meet the specification in most conditions: 15/15 sim-visible under baseline, baseline_gate, v2
  and escalation, 14/15 under v3.
- GPT-4.1 mini and Haiku get 12/15 in every condition.
- Gemini's misses on that task are raw_adv (3 of 3) and v3 (1 of 3).

At N=3 this is one task and one model, so it is descriptive only.

### Deviations (this run)

1. **Stricter stop rules** in `backends.py`, on error paths only: HTTP 400 or 402, a 429 that persists after the
   retries, and a truncated completion now stop the provider. None of them was triggered.
2. **Wrapper and analysis changes, no protocol change:**
   - `p3_api_runner.py` accepts `--api gemini`.
   - `backends.py` has a `STITCH_GEMINI_BASE` override, used only by the offline mock parity, which now covers Gemini.
   - `p3_api_analysis.py` includes Gemini and counts `MAX_TOKENS` as a truncation.
   - `analysis_set4b.py` reports per-model coverage.
   - `spend_summary.py` prints per-provider totals across all batches.
   - New scripts: `p3_api/p3_signoff_ladder.py` and `fig_gemini_completion.py`.
3. **The smoke run used a new tag, `smoke_gc`.** The old tag `smoke` already holds the 2026-09-28 counter_12 run,
   which resume would have skipped.
4. **The smoke spend counted against the Part A cap**, which makes it stricter. Part B's cap was set on the
   cumulative ledger as min(3.0, 0.3187 + 1.5) = $1.8187, so Part B could not spend more than $1.5 and the total
   could not exceed $3.0.
5. **The cap stops before the call that could cross it**, not after the current run, so a cap is never exceeded.
   No cap was reached.
6. **Sign-off cache copy.** Gemini candidates were scored into a copy of the Phase 3 cache, using the matched
   Icarus 14.0. Re-simulating the cached GPT/Haiku candidates gave the same verdicts (27/27), and the published rows
   are reproduced. `phase3/evidence/signoff_cache.json` was not touched.
7. **Figures.** The Set 4 figures (`analysis/fig5_capability_ladder_api`, `fig_set4_inr_per_pass`) depend on Set 4
   data only, which did not change, so they were not regenerated. The two new figures above are new files.
8. **No modelVersion change.** All 234 calls returned `gemini-2.5-flash`.

---

## Set 4c (2026-10-12): Gemini Pro reasoning run on the residual floor. CLOSED

**CLOSED, no results reported.**
- **Why:** the pre-registered stop rule fired on run 1, iteration 2. `gemini-2.5-pro` returned 10,237 thinking
  tokens against a 2,048 budget, and the answer was cut off (finish `MAX_TOKENS`).
- **Outcome:** 0 of 18 runs completed. The run was closed by decision, with no setting changed and no further
  paid calls (Amendment 5, 16:12 UTC; SHA-256 after it
  `CC23711DD2A30082299755A6BE169A20B8FF0D5DF4D2DE0DDA39E6142F64653B`).
- **Cost:** USD 0.1723 (INR 19.5): smoke $0.0321, run $0.1401.
- **Q5 and Q6:** unanswered.
- **Q7:** answered by the free shifted-trace analysis of the 36 Set 4b runs, under "Q7 answer" in the oracle
  audit of the Gemini completion section above.
- **Code:** the Set 4c code stays in place; `set4c_launch.sh` refuses to run without `--reopen`.

The record below is kept for traceability.

Under `SET4_PREREG.md` Amendment 4 (appended 14:38 UTC, before any call it governs; SHA-256 after it
`EDF26C7070366C565D7F93CA0D0AA45BC366843E2CCE0468AC9BA776DE1ABA02`). Set 4c uses a reasoning model, which
departs from Set 4's non-reasoning design; it is descriptive only and never pooled with Set 4 or 4b. Numbers come
from `set4c.py` (`project`, `analyze`, `trace`) and `spend_summary.py`. Outputs are in
`phase2/results/set4_api/analysis_4c/`, `ledgers_4c/` and `set4c_gemini.log`.

**LEAK STATUS: clean.** `scan_secrets.py` 0 matches after the smoke test and at the end; `leak_audit.py` clean.

**Spend.** Set 4c: $0.1723 (INR 19.5): smoke $0.0321, run $0.1401. Gemini across all batches: $4.7190
(INR 534.6). All providers since Set 4: $13.7029 (INR 1,552.3). The cap was $7.5 and was not reached.

### Model choice and settings

Pro models served on this key: `gemini-3.1-pro-preview` (the flagship), `gemini-pro-latest` (a moving alias) and
`gemini-2.5-pro`. Prices are from https://ai.google.dev/gemini-api/docs/pricing (page last updated 2026-10-09,
fetched 2026-10-12).

Worst case: 18 runs × 8 calls at the Set 4b per-call maxima for these modules (23,473 input and 4,023 answer
tokens over 732 calls), plus 2,048 thinking tokens per call.
- `gemini-3.1-pro-preview`: $17.25, over $7.5.
- So, by the brief's rule, the model is **`gemini-2.5-pro`**: $12.97 ($0.0901 per call, $0.7204 per run), also
  over $7.5, so the run went ahead with the cap as the stop.

Settings:
- `thinkingBudget` 2048 (the 2.5 Pro docs give a range of 128–32,768, call the budget a "soft limit", and say
  thinking cannot be turned off).
- No `includeThoughts`, so no thought text.
- `maxOutputTokens` 10,240 = 2,048 + 8,192, because the docs state that the output limit includes thought tokens.
- T=0.1, which the API accepted.

### Smoke test: passed

- **Minimal call:** model `gemini-2.5-pro`; T=0.1 accepted; 950 thinking tokens (> 0 and ≤ 2,048); finish `STOP`.
  The ledger records `reasoning_tokens` 950 inside `output_tokens` 982 and bills it at the output price
  ($0.010195 = (300 × 1.25 + 982 × 10) / 10⁶).
- **counter_12, baseline, N=1:** passed on iteration 1 with 1,840 thinking tokens; `detect_outcome(rtllm)` = PASS;
  the ledger grew by one line. Re-running made 0 calls, so resume works.
- `scan_secrets` 0.

### The run: stopped by a stop rule, 0 of 18 runs completed

Step (i), run 1 (adder_pipe_64bit, baseline, rep1):
- Iteration 1 used 1,706 thinking tokens and produced a design that failed to compile (`parameter DATA_WIDTH not
  found` in the testbench instantiation).
- On iteration 2 the model returned **10,237 thinking tokens and no answer**, with finish `MAX_TOKENS`. It used the
  whole 10,240-token output limit on thinking, about 5× the 2,048 budget.
- That breaks two stop rules: thinking over budget, and truncation. The runner stopped cleanly
  (`ReasoningDetected`, exit 3) before any further call.
- That run is not recorded, and no other run started. The projection after step (i) was therefore not reached.

Calls in the run: 2 (thinking 1,706 and 10,237; $0.0348 and $0.1054).

**Q5 and Q6: no data** (0 runs). **Q7: Set 4c has no data** (freq_divbyfrac was not reached). Q7 is answered
from the Set 4b runs in the oracle audit above ("Q7 answer: freq_divbyfrac shifted-trace analysis").

### Deviations and notes (Set 4c)

1. **The thinking budget was not respected.** Gemini 2.5 Pro used 10,237 thinking tokens against a 2,048 budget
   and hit the output limit. The docs call the budget a soft limit that "might vary slightly"; 5× is far beyond
   that. As pre-registered, this stops the run. No setting was changed.
2. **Model:** `gemini-2.5-pro` instead of the flagship `gemini-3.1-pro-preview`, by the brief's projection rule.
   For Gemini 3 the docs also deprecate `thinkingBudget` (in favour of `thinkingLevel`) and recommend T=1.0.
3. **Model choice was made before the amendment.** Step 1 (model choice, free) ran before Step 0, because the
   amendment had to record the chosen model. Both were free and both came before any paid call.
4. **Tooling:** `backends.py` takes a `thinking_budget` (None keeps Sets 4/4b exactly: budget 0, any reasoning
   stops). `set4_runner.py` adds `--thinking-budget` and `--run-worst-usd`, a between-run cap guard.
   `test_backends.py` covers both. New files: `set4c.py`, `set4c_launch.sh` and `FREQ_DIVBYFRAC_AUDIT.md`.
5. **Trace method:** the shifted-trace comparison instruments the original testbench, so each sample sees the same
   event ordering as the check itself. Check times coincide with clock edges.
