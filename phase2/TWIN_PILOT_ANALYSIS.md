# Phase 2 twin pilot — analysis (64/75 runs)

**Design**: `phase2/TWIN_RUN_PREREG.md`. **Raw data**: `phase2/results/twin_run_pilot/`
(gitignored — `master_log.json` plus a `corrected_pass.json` built during
this analysis, see below). **Graphs**: `phase2/graphs/` (staged for the
paper, not gitignored — see the commit proposal at the end).

This is a **pilot**, stopped by wall-clock timeout, not a completed
run. Every number below is labeled for what it actually establishes.

---

## Preamble — a real bug found during this analysis, corrected here, and needed before the full run

**Before Task 1: the `pass` field in `master_log.json` is wrong, for a known and fixable reason.**

`stitch_runner_hpc.py`'s `run_iverilog_sim()` — a faithful, byte-for-byte
port of the classic `stitch_runner.py` in this respect — checks for the
case-sensitive substring `"PASS"` or `"ALL TESTS PASSED"` in simulation
output. Every RTLLM testbench in this pilot instead prints
`"Your Design Passed"` (capital P, lowercase `assed`) — which contains
**neither** string. `phase1/rtllm_pilot_runner.py` already has a patch
for exactly this (`_rtlcoder_aware_run_iverilog_sim`, checking for the
literal RTLLM pass string), but that patch was never carried into
`twin_run_runner.py`. Confirmed directly: `counter_12`'s very first
completed cell has `sim_log.txt` reading `===========Your Design
Passed===========`, recorded as `"pass": false`.

**Consequence, checked exhaustively, not sampled**: every one of the 64
completed cells' `iter_N/sim_log.txt` files was re-scanned for the
literal string `"Design Passed"` (robust to `barrel_shifter`'s testbench
having an extra space around it). **20 of 64 entries (31%) actually
passed** and were recorded as failures. All 20 are listed in Task 2.

**This also corrupted run trajectories, not just final labels.** A cell
that actually passed on iteration 1 was told `"SIMULATION FAILED:\n
===========Your Design Passed==========="` and asked to fix code that
already worked — burning the rest of its 8-iteration cap on a solved
problem, under a false-failure signal. So `total_iterations`/
`iterations_to_pass` for every flipped cell (always recorded as the
full cap, 8) is **not** a real "how long did this take" number. What
this analysis uses instead: the iteration of the **first** real pass
(directly readable from the sim logs, since the true outcome doesn't
change even though the harness kept going past it).

**This is a correctness bug, not a tuning or interpreter/adapter
question** — it sits in the same shared pass-detection code path Task 3
and the RTLLM pilot already needed two other fixes for (bug #1, bug #2,
`phase1/PILOT_INSIGHTS.md`). It must be fixed in `twin_run_runner.py`
(the same `_rtlcoder_aware_run_iverilog_sim`-style wrap
`rtllm_pilot_runner.py` already uses) **before the full HPC run** — not
done in this pass, since this task was analysis only. Every table below
uses the **corrected** pass value (`real_pass` in
`phase2/results/twin_run_pilot/corrected_pass.json`), not the raw
`master_log.json` field — reported plainly as a correction, not silently
substituted.

---

## Task 1 — what completed, what's missing, what's partial

**64 of the pre-registered 75 runs completed, 0 errors**, stopped by the
`--time=08:00:00` wall-clock limit.

**The missing 11 are not random — every one is `calendar`**, the last
module in run order (`accu → counter_12 → barrel_shifter → alu →
calendar`), confirmed by diffing the full 75-cell pre-registered set
against `master_log.json`:

| module | model | prompt_condition | replicate |
|---|---|---|---|
| calendar | rtlcoder-deepseek-v1.1 | shared | 2 |
| calendar | rtlcoder-deepseek-v1.1 | shared | 3 |
| calendar | deepseek-coder:6.7b | shared | 1 |
| calendar | deepseek-coder:6.7b | shared | 2 |
| calendar | deepseek-coder:6.7b | shared | 3 |
| calendar | gemma3:4b | shared | 1 |
| calendar | gemma3:4b | shared | 2 |
| calendar | gemma3:4b | shared | 3 |
| calendar | llama3.1:latest | shared | 1 |
| calendar | llama3.1:latest | shared | 2 |
| calendar | llama3.1:latest | shared | 3 |

**One of these (`calendar / rtlcoder-deepseek-v1.1 / shared / replicate
2`) is genuinely partial, not simply "never started"**: its directory
has `iter_1` through `iter_5` on disk (of an 8-iteration cap), no
`metrics.json` (the run never reached a `pass`/`fail` verdict before the
job was killed). As a bonus data point, not counted toward any N=3 cell
below (the run itself never completed): its `iter_1/sim_log.txt` also
shows `"Your Design Passed"` — consistent with every other RTLCoder ×
calendar cell, but **not folded into any table**, since this replicate's
run never finished.

**Everything else (60 of 64 entries, all of `accu`/`counter_12`/
`barrel_shifter`/`alu`, plus `calendar`'s `rtlcoder/native` (3/3) and
`rtlcoder/shared` replicate 1) is a clean, complete stop** — no other
partial cells found.

---

## Task 2 — baseline-first per-cell decomposition (corrected pass data)

N=3 for every row unless marked. "iters" = iteration of first real pass
if passed, else the full cap (8, genuine — every non-passing cell here
ran the complete cap).

| module | model-condition | pass (corrected) | iters | complete? |
|---|---|---|---|---|
| accu | RTLCoder / native | 0/3 | [8, 8, 8] | yes |
| accu | RTLCoder / shared | 0/3 | [8, 8, 8] | yes |
| accu | deepseek-coder:6.7b / shared | 0/3 | [8, 8, 8] | yes |
| accu | gemma3:4b / shared | 0/3 | [8, 8, 8] | yes |
| accu | llama3.1:latest / shared | 0/3 | [8, 8, 8] | yes |
| counter_12 | RTLCoder / native | **3/3** | [1, 1, 1] | yes |
| counter_12 | RTLCoder / shared | **3/3** | [1, 1, 1] | yes |
| counter_12 | deepseek-coder:6.7b / shared | **3/3** | [1, 1, 1] | yes |
| counter_12 | gemma3:4b / shared | **3/3** | [1, 1, 1] | yes |
| counter_12 | llama3.1:latest / shared | **3/3** | [2, 1, 1] | yes |
| barrel_shifter | RTLCoder / native | 0/3 | [8, 8, 8] | yes |
| barrel_shifter | RTLCoder / shared | 0/3 | [8, 8, 8] | yes |
| barrel_shifter | deepseek-coder:6.7b / shared | **1/3** | [8, 8, 5] | yes |
| barrel_shifter | gemma3:4b / shared | 0/3 | [8, 8, 8] | yes |
| barrel_shifter | llama3.1:latest / shared | 0/3 | [8, 8, 8] | yes |
| alu | RTLCoder / native | 0/3 | [8, 8, 8] | yes |
| alu | RTLCoder / shared | 0/3 | [8, 8, 8] | yes |
| alu | deepseek-coder:6.7b / shared | 0/3 | [8, 8, 8] | yes |
| alu | gemma3:4b / shared | 0/3 | [8, 8, 8] | yes |
| alu | llama3.1:latest / shared | 0/3 | [8, 8, 8] | yes |
| calendar | RTLCoder / native | **3/3** | [1, 1, 1] | yes |
| calendar | RTLCoder / shared | **1/1** | [1] | **NO — n=1, see Task 1** |
| calendar | deepseek-coder:6.7b / shared | — | — | **NO DATA** |
| calendar | gemma3:4b / shared | — | — | **NO DATA** |
| calendar | llama3.1:latest / shared | — | — | **NO DATA** |

### Module classification (pooled corrected pass rate, all available model-conditions)

| module | pooled | classification |
|---|---|---|
| accu | 0/15 (0%) | **FLOOR** |
| counter_12 | 15/15 (100%) | **CEILING** |
| barrel_shifter | 1/15 (7%) | **FLOOR** (near-floor, one exception) |
| alu | 0/15 (0%) | **FLOOR** |
| calendar | 4/4 (100%) | **CEILING — but only 1 of 5 model-conditions tested (RTLCoder only); not a full classification, incomplete coverage** |

**Same lesson as the laptop pilot's failure decomposition**: 4 of 5
modules show zero discriminating power (uniform ceiling or uniform
floor across every model-condition) — only `barrel_shifter`'s single
`deepseek-coder` flip and `calendar`'s (incomplete) contrast carry any
signal at all. This pilot's module mix landed almost entirely outside
the recoverable band where any comparison could show something either
way.

---

## Task 3 — the two named comparisons

### (a) Fine-tuning twin: RTLCoder/shared vs deepseek-coder:6.7b/shared

| module | RTLCoder/shared | deepseek-coder/shared | gap |
|---|---|---|---|
| accu | 0/3 | 0/3 | +0 |
| counter_12 | 3/3 | 3/3 | +0 |
| barrel_shifter | 0/3 | 1/3 | **−1** |
| alu | 0/3 | 0/3 | +0 |
| calendar | — | — | **insufficient data — do not interpret** (RTLCoder n=1, deepseek-coder n=0) |

**Read plainly**: across the 4 modules with complete data, RTLCoder
**does not beat** its fine-tuning twin. Three modules tie exactly (both
0/3 or both 3/3 — module ceiling/floor structure, not a model
difference). The one module with any separation (`barrel_shifter`) goes
**against** RTLCoder, by a single replicate. **A 1-replicate gap at N=3
is not distinguishable from resampling noise** — the same lesson Task 3
already established for this project (`PHASE1_TASK3_ANALYSIS.md` §1):
N=3 is the minimum to even ask the question, not enough to call a
single-replicate difference a real effect. **No fine-tuning advantage is
shown here, in either direction**, on the 4 modules this pilot actually
tested cleanly.

### (b) Prompt-format effect: RTLCoder native vs RTLCoder shared

| module | native | shared | gap |
|---|---|---|---|
| accu | 0/3 | 0/3 | +0 |
| counter_12 | 3/3 | 3/3 | +0 |
| barrel_shifter | 0/3 | 0/3 | +0 |
| alu | 0/3 | 0/3 | +0 |
| calendar | 3/3 | 1/1 | **insufficient data — do not interpret** (shared n=1) |

**Read plainly**: zero separation on every module with complete data.
Native and shared are indistinguishable in this pilot — both track the
module's own ceiling/floor exactly. `calendar` shows 3/3 vs 1/1, which
*looks* consistent with "no effect" too, but with shared at n=1 it
cannot be reported as a real data point either way.

**Neither comparison shows a real effect on the data this pilot actually
completed.** That is itself a legitimate pilot finding — not a failure
of the pilot — but it is a null result on 4 (comparison a) or 4
(comparison b) modules, not a confirmed absence of any effect; see the
verdict below.

---

## Task 4 — graphs

Generated into `phase2/results/twin_run_pilot/graphs/` (gitignored, the
raw run-output copy) and staged for the paper from `phase2/graphs/`
(not gitignored — see the commit proposal at the end). Every figure
watermarked `"PILOT -- 64/75 runs, 5 modules, N=3 at T=0.5, NOT
confirmatory"` directly on the image, not just in this doc:

- **`pilot_graph1_pass_grid.png`** — module × model-condition grid,
  corrected pass rate, color-coded; missing cells shown as a distinct
  **gray "NO DATA"**, never as zero or omitted.
- **`pilot_graph2_comparisons.png`** — the two named comparisons (a) and
  (b) side by side, insufficient-data cells (`calendar`) visibly
  dimmed and labeled, not silently dropped or zero-filled.
- **`pilot_graph3_no_capability_pattern.png`** — checked for a
  capability-conditional pattern (the Phase 1 hypothesis) and found
  **none observable**: this design has no STITCH-interpreter axis at
  all (`condition` fixed at `"baseline"` throughout — see
  `TWIN_RUN_PREREG.md`), so the hypothesis isn't testable here in its
  original form. Pooled across the 4 fully-covered modules (calendar
  deliberately excluded from this one figure — see its caption: pooling
  it in would have visually favored RTLCoder purely because it's the
  only model-condition with any calendar data, an artifact of the
  timeout, not a real signal), every model-condition lands at 3/12 or
  4/12 — flat, no pattern to report.

---

## Task 5 — honest verdict

**This pilot is a correctness check on the harness and a first read of
5 modules under real wall-clock constraints, not a confirmatory result
on the twin comparison.**

**What it showed**: a real, previously-unknown pass-detection bug —
20 of 64 completed runs (31%) were silently misclassified as failures
because the shared harness's pass-string check doesn't match RTLLM's
actual `"Your Design Passed"` output. This is the pilot's most concrete,
load-bearing finding, and it must be fixed before the full run — the
same fix (`phase1/rtllm_pilot_runner.py`'s pattern) already exists,
it simply wasn't carried into `twin_run_runner.py`. Beyond that: 4 of 5
modules (`accu`, `counter_12`, `alu` as clean floor/ceiling,
`barrel_shifter` as near-floor) showed no discriminating power at all
between any model-condition — the pilot's module mix mostly missed the
recoverable band where a real difference could show up either way,
echoing the same structural lesson the phase1 laptop pilot already
documented.

**What it did not show**: on the 4 modules with complete, corrected
data, **RTLCoder-Deepseek-v1.1 did not outperform its un-fine-tuned
twin, deepseek-coder:6.7b** — three modules tied exactly, and the one
module with any separation went against RTLCoder by a single replicate,
which is not distinguishable from noise at N=3. The prompt-format
comparison (RTLCoder native vs. shared) showed zero separation
anywhere it could be checked. **Stated plainly, since it needs to be
said plainly: this pilot does not show RTLCoder beating deepseek-coder,
and does not show a meaningful prompt-format effect either** — not
because of a flaw in the comparison, but because both readable
comparisons landed on modules with too little room to differentiate,
plus 11 cells (all of `calendar`, the module where the only real
passes for the non-ceiling models could have shown up) never ran.

**What remains open for the full HPC run**: whether `calendar` — the one
module in this pilot where RTLCoder is 4/4 and every other model is
untested — shows a real gap or is just another ceiling once the 3
Ollama models actually get to run it; whether a broader, correctly
pass-detected module set surfaces any real mid-band signal at all for
either named comparison; and the pass-detection fix itself needs
verifying (golden-reference before/after, same discipline as bug #1/#2)
before those 11-plus-partial cells are worth re-running.

**This is a MODEL comparison, not a STITCH validation, and stays that
way regardless of outcome.** Nothing in this pilot's design runs
STITCH's interpreter — `condition` is fixed at `baseline` for every
cell — so nothing here is evidence for or against STITCH working,
whichever direction the fine-tuning twin comparison eventually lands.
No interpreter or adapter changes are recommended based on this pilot's
numbers; the one concrete, necessary change identified is the harness
pass-detection fix, which is a correctness bug independent of model or
interpreter performance.
