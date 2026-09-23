# Twin run (Set 2) — full-scale analysis

**This document replaces the earlier twin pilot analysis (merged below as Appendix A) as the paper's
Section 7 material.** The pilot (64/75 runs, 5 modules) was a
correctness check on the harness, not a confirmatory result — its own
verdict said so explicitly. This is the confirmatory run: 630/630
completed, 0 errors, 42 modules, full RTLLM v2.1 scale.

All artifacts referenced below live in `phase2/twin_analysis_SET2/` and are
regenerated from `phase2/results/twin_run/master_log.json` by the
scripts of the same name (`categorize.py`, `table1.py`, `fig1.py`,
`fig2.py`, `table2.py`, `prompt_format.py`) — pure functions of that one
file, nothing re-derived from sim logs, nothing hand-edited. Re-run
`categorize.py` first if `master_log.json` ever changes; the rest read
its output.

---

## Run summary

630 runs completed, **0 errors**, across the **42 RTLLM-compatible
modules** this study covers (`edge_detect` and `square_wave` excluded —
both were found, before this run, to pass with every output stuck at a
constant wrong value, a defect in each design's own testbench check
logic, not a `detect_outcome()` issue; see
`docs/IMP_PHASE2_RUNNER_HARDENING_REPORT.md` §6). Five model-conditions ×
N=3 replicates per module: RTLCoder-Deepseek-v1.1 (native and shared
prompting), deepseek-coder:6.7b, gemma3:4b, and llama3.1:latest (the
latter three, shared-prompting only — see `TWIN_RUN_PREREG.md` for why
native/shared collapse to one condition for non-RTLCoder models).
Sampling is **T=0.5, top_p=0.9 across every model-condition** (matched
deliberately, to remove temperature as a confound in what is fundamentally
a model comparison — see `TWIN_RUN_PREREG.md`'s temperature section),
`baseline` STITCH condition only (iverilog-only feedback loop; no
Verilator/Yosys/interpreter anywhere in this run — this is **not** a
STITCH-interpreter result in any cell). All pass/fail decisions come
directly from `master_log.json`'s `pass` field, itself a product of the
hardened `detect_outcome()` (regression-verified 64/64 against the
pilot's own corrected ground truth — `docs/IMP_PHASE2_RUNNER_HARDENING_REPORT.md`
§5); nothing in this analysis re-derives anything from a `sim_log.txt`.
Total passes across the full 42×5 grid: **193/630** (cross-checked
against `table1.py`'s own independent sum).

---

## Difficulty-tier breakdown

Tiers are computed from each module's **pooled** pass rate across all 5
model-conditions × N=3 = 15 total attempts (`categorize.py`) —
`>= 80% (>=12/15)` ceiling, `20%-80% (3/15-11/15)` recoverable band,
`<20% (<3/15)` floor.

| Tier | N modules | Share |
|---|---|---|
| Ceiling | 6 | 14% |
| Recoverable band | 17 | 40% |
| Floor | 19 | 45% |

**Worked examples** (one per tier, from `module_categories.json`):

- **Ceiling** — `sub_64bit` (Arithmetic): 3/3 on RTLCoder native, RTLCoder
  shared, and deepseek-coder shared; drops to 1/3 and 2/3 only on the two
  weakest models (gemma3:4b, llama3.1). A module every capable model
  solves reliably — no discriminating power between the two axes this
  study cares about (fine-tuning, prompt format), by construction.
- **Recoverable band** — `calendar` (Miscellaneous → protocol): mixed
  across model-conditions (see Table 1 / `table1_full_grid.csv` for the
  exact per-cell counts) — this is exactly the band where a real
  fine-tuning or prompt-format effect could show up in either direction,
  and where Table 2 and Figure 2 below draw their signal from.
- **Floor** — `accu` (Arithmetic): 0/15 — every model-condition, every
  replicate, failed. Not a borderline case; see "Honest failures" below.

---

## Fine-tuning twin comparison

Table 2 (`table2_twin_decision.tex` / `.csv`) decomposes the fine-tuning
question — RTLCoder-Deepseek-v1.1/shared vs. its un-fine-tuned twin
deepseek-coder:6.7b/shared, same prompt, same temperature, same
everything else — per recoverable-band module (n=17, the only band
where a difference is even visible; ceiling/floor modules tie by
construction and were excluded, per the brief).

**Verdict: RTLCoder-Deepseek-v1.1 wins 0, ties 13, loses 4 of 17
recoverable-band modules.** No overclaiming either direction: this is
not a decisive result, but it is not a null one either — RTLCoder never
wins outright on a single module, and pooling the same 17 modules ×
N=3=51 draws per model-condition (Figure 2) puts RTLCoder/shared at
21/51 (41.2%, 95% CI [28.8%, 54.8%]) against deepseek-coder/shared at
32/51 (62.7%, 95% CI [49.0%, 74.7%]) — non-overlapping point estimates,
overlapping CIs. **Read plainly: this run shows no fine-tuning advantage
for RTLCoder-Deepseek-v1.1, and if anything a mild disadvantage against
its base model** — the honest signal is "leans against," not "proven
against," given CI overlap.

## Mechanism: why the fine-tuning comparison actually loses

The pooled numbers (41.2% vs. 62.7%) say RTLCoder-Deepseek-v1.1 loses to
its un-fine-tuned base — they don't say *why*. Traced directly against
the generated `.v` files under `phase2/results/twin_run/` for all 4
modules where the fine-tuning twin comparison calls "Base wins"
(`RAM`, `adder_8bit`, `fixed_point_adder`, `fixed_point_substractor` —
RTLCoder 0/3 on every one, deepseek-coder 3/3 on every one, per
`table2_twin_decision.csv`): **all four fail at compilation, on every
single iteration, across all 8 retries — RTLCoder never changes strategy
even after 8 rounds of direct `iverilog` error feedback.** Three
distinct, concrete root causes, not one:

- **`adder_8bit`**: RTLCoder writes a properly hierarchical design — 8
  instantiations of a `full_adder` submodule — but never emits the
  `full_adder` definition itself (the harness extracts and compiles a
  single file). `Unknown module type: full_adder` on iteration 1, still
  true byte-for-byte on iteration 8.
- **`RAM`**: RTLCoder writes `for (int i = 0; ...)` — an inline-typed
  SystemVerilog-2005+ loop variable — which `iverilog`'s default
  Verilog-2001 mode rejects (`Incomprehensible for loop`). Identical at
  iteration 8.
- **`fixed_point_adder`**: RTLCoder writes a parameterized module
  (`[N-1:0] a`), but the parameter binding against RTLLM's testbench
  never resolves (`Unable to bind parameter 'N'`, `Dimensions must be
  constant`).
- **`fixed_point_substractor`**: RTLLM's own `design_description.txt`
  states `Module name: fixed_point_subtractor` (correct spelling, and
  what the testbench instantiates) — RTLCoder ignores the live prompt
  and writes `fixed_point_substractor`, matching RTLLM's own **folder
  name** (`RTLLM/Arithmetic/Other/fixed_point_substractor/`) instead.
  This is memorization from the fine-tuning corpus overriding the actual
  instruction in front of the model, and it reproduces identically under
  **both** `native` and `shared` prompts (verified against
  `phase2/results/twin_run/native/.../fixed_point_substractor/iter_1/`)
  — not a prompt-format artifact.

**None of this is "RTLCoder writes worse logic."** It writes more
textbook-idiomatic RTL — real submodule hierarchy, real parameterization
— than deepseek-coder does, and that sophistication is exactly what
breaks against this harness's single-file, non-parameterized, plain-
Verilog compilation pipeline. The bigger tell is that 8 iterations of
identical, unrecovered failure means the fine-tuning didn't teach the
model to *repair* from compiler feedback, only to generate — a narrower
and more specific finding than "fine-tuning didn't help."

**Where RTLCoder is actually strongest.** Broken out by functional class
(recoverable band, `RTLCoder native` vs. `RTLCoder shared` vs.
`deepseek-coder shared`, passes out of n):

| Class | RTLCoder native | RTLCoder shared | deepseek-coder shared |
|---|---|---|---|
| **signal_processing** (freq_div, freq_divbyeven, signal_generator) | **9/9 (100%)** | 5/9 | 6/9 |
| **Memory** (LFSR) | **3/3 (100%)** | 2/3 | 1/3 |
| **Control** (JC_counter, sequence_detector) | 2/6 | 1/6 | **0/6** |
| Arithmetic (6 modules) | 8/18 | 4/18 | **12/18** |
| arithmetic_misc (RAM, instr_reg, width_8to16) | 4/9 | 4/9 | **7/9** |
| protocol (calendar, synchronizer) | 3/6 | 5/6 | **6/6** |

Signal-processing under RTLCoder's **native** prompt is a clean sweep —
`freq_div` alone is the sharpest single case: native 3/3, while both
RTLCoder/shared **and** deepseek-coder go 0/3 (a logic/timing bug both
control conditions hit; RTLCoder's own prompt convention avoids it
entirely). Control is the other notable case: deepseek-coder collapses
to 0/6 there while RTLCoder gets partial credit. Arithmetic — anything
needing submodule hierarchy, generic-width parameters, or exact
testbench-name matching — is RTLCoder's clear weak spot, for the reasons
traced above.

## Prompt-format effect

Full detail: `prompt_format_verdict.md`. RTLCoder native vs. RTLCoder
shared, recoverable-band modules (n=17), same delta/threshold method as
Table 2: **native wins 3, shared wins 2, tied 12.** Pooled across the
same 51 draws per condition (Figure 2): native 29/51 (56.9%, 95% CI
[43.3%, 69.5%]) vs. shared 21/51 (41.2%, 95% CI [28.8%, 54.8%]) — a
larger pooled gap than the per-module win count alone suggests, because
several of the 12 "tied" modules still lean native without crossing the
±2 threshold. **Read plainly: prompt format is not fully neutral — native
prompting shows a modest, real-looking edge — but the per-module win
count (3 vs. 2) keeps this from being a strong claim either.**

## Capability ladder

Figure 2 (`fig2_capability_ladder.png`/`.pdf`) pools all 17
recoverable-band modules × N=3 per model-condition (n=51 draws each) and
plots pass rate with Wilson 95% CIs. The five model-conditions spread
clearly: deepseek-coder shared (62.7%) and RTLCoder native (56.9%) lead,
RTLCoder shared (41.2%) and llama3.1 shared (35.3%) sit in the middle,
and **gemma3:4b shared collapses to 7.8%** (95% CI [3.1%, 18.5%]) —
visibly, non-overlapping-CI separate from every other model-condition.
This is a real capability-conditional pattern, and it is exactly what
the pilot could not see (the pilot's own Figure 3 found "no pattern,"
but with only 4 modules and no recoverable-band coverage worth pooling —
a scale limitation, not evidence the pattern doesn't exist; see
"Cross-references" below).

## Honest failures

**19 of 42 modules (45%) are in the floor tier** — no model-condition
recovers them reliably. Of those, **15 are a true universal wipeout,
0/15 across every model-condition and every replicate**: `LIFObuffer`,
`accu`, `adder_32bit`, `adder_bcd`, `adder_pipe_64bit`, `alu`,
`barrel_shifter`, `counter_12`, `div_16bit`, `float_multi`,
`freq_divbyfrac`, `multi_pipe_4bit`, `multi_pipe_8bit`, `pulse_detect`,
`serial2parallel`. The remaining 4 floor-tier modules (`adder_16bit`,
`fsm`, `parallel2serial`, `traffic_light`) have 1-2 passes out of 15,
not literally zero, but still below the 20% recoverable-band threshold.
**This is the paper's clean argument for "outside the recoverable
band"**: nearly half the RTLLM-compatible pool is currently unsolvable
by any of these five model-conditions at T=0.5 under a baseline
iverilog-only feedback loop, regardless of fine-tuning or prompt format
— the study's comparisons are honestly scoped to the 40% of modules
(the recoverable band) where a difference could be observed at all, and
say nothing, positive or negative, about the other 60%.

---

## Cross-references — revisiting the pilot's three findings at full N

The pilot's Task 5 verdict (Appendix A) stated three findings on 4-5
modules of pilot data. Revisited here with 42 modules / 630 runs:

1. **Pilot**: "No fine-tuning advantage is shown here, in either
   direction" (3 of 4 complete modules tied exactly, one module a
   single-replicate gap against RTLCoder — explicitly flagged as
   noise-level, not a real effect).
   **Full run**: still no advantage — but now with real statistical
   power (17 recoverable modules vs. the pilot's 4), the direction
   sharpens from "can't tell" to **"leans against RTLCoder, not
   decisively"** (0 wins / 13 ties / 4 losses, pooled 41.2% vs. 62.7%
   with overlapping CIs). The pilot's null finding **holds up** in
   direction, and gains a mild negative lean the pilot didn't have the
   power to detect.

2. **Pilot**: "Neither comparison shows a real effect" on prompt format
   — zero separation on every module with complete pilot data.
   **Full run**: **this pilot finding does NOT fully hold at scale.**
   Native shows a modest, real-looking pooled edge (56.9% vs. 41.2%),
   even though the per-module win count (3 native / 2 shared / 12 tied)
   stays too close to call decisively. The pilot's "no effect" read was
   a product of having only 4 modules with complete data, not evidence
   the effect doesn't exist — worth flagging explicitly as a case where
   pilot-scale data understated a real (if modest) signal.

3. **Pilot**: "No capability-conditional pattern observable" — flat
   3/12-4/12 across every model-condition on the 4 fully-covered
   modules, and the pilot's own write-up attributed this explicitly to
   scale (too few modules, too little recoverable-band coverage), not to
   the pattern's absence.
   **Full run**: **the pattern is now clearly visible.** Figure 2 shows
   a ~55-point spread between the strongest (deepseek-coder shared,
   62.7%) and weakest (gemma3:4b shared, 7.8%) model-conditions on the
   identical recoverable-band population, with non-overlapping CIs at
   the low end. This directly confirms the pilot's own caveat: the
   "no pattern" finding was a scale artifact, and the capability ladder
   this project's Phase 1 findings first flagged as a hypothesis
   (`PHASE1_FINDINGS.md`'s capability-conditional note) is real and
   visible once there's enough recoverable-band data to pool.

**Net revision**: 2 of the pilot's 3 findings change in a material way
once real statistical power is available (#2 and #3); only #1 holds up
essentially as stated, sharpened rather than reversed. This is exactly
why the pilot's own verdict called itself non-confirmatory — it was
right to.

---

## Footnote — Wilson confidence intervals

95% CIs in Figure 2 use the Wilson score interval
(`statsmodels.stats.proportion.proportion_confint(count, nobs,
alpha=0.05, method="wilson")`), not the normal (Wald) approximation —
Wilson stays well-behaved at small N and away from p=0.5, which the
Wald interval does not (it can produce bounds outside [0,1] and
under-covers near the extremes, both live risks here given `gemma3:4b
shared`'s 4/51). Not derived by hand; the library call is the citation.

---

## Appendix A — the pilot that preceded this run (merged from the former `TWIN_PILOT_ANALYSIS.md`)

The standalone pilot document was merged here so there is one Twin
analysis, not two. Everything the pilot produced is either superseded by
the numbers above or preserved below. The pilot's raw data lives in
`phase2/results/twin_run_pilot/` (gitignored: `master_log.json` plus the
manually built `corrected_pass.json`); its three watermarked figures
("PILOT — 64/75 runs, 5 modules, N=3 at T=0.5, NOT confirmatory") are
still in `phase2/graphs/`.

**What the pilot was.** A first real HPC attempt at the twin comparison
(5 modules: `accu`, `counter_12`, `barrel_shifter`, `alu`, `calendar`),
stopped by the `--time=08:00:00` wall-clock limit at **64 of 75**
pre-registered runs, 0 errors. The 11 missing runs were all `calendar`
(the last module in run order), one of them partially executed
(`calendar / rtlcoder / shared / replicate 2`, iterations 1-5 on disk, no
verdict). No cell from an incomplete N=3 was folded into any table.

**The bug it exposed (the pilot's real output).** Its raw `pass` field
was wrong. `stitch_runner_hpc.py` checked for the case-sensitive
substrings `"PASS"` / `"ALL TESTS PASSED"`; every RTLLM testbench prints
`"Your Design Passed"`, which contains neither. Re-scanning all 64
completed cells' `sim_log.txt` files for the literal `"Design Passed"`
showed **20 of 64 (31%) had actually passed and were recorded as
failures**, including every `counter_12` cell. It also corrupted
trajectories: a cell that passed on iteration 1 was then told
`SIMULATION FAILED` and burned the rest of its 8-iteration cap "fixing"
correct code, so its recorded iteration count (always the cap) was
meaningless. The pilot's corrected ground truth (`real_pass`, first real
pass read from the sim logs) is what
`phase2/regression_check_twin_pilot.py` later replays to verify the
structural fix: 64/64 cells reproduced exactly (see
`docs/IMP_PHASE2_RUNNER_HARDENING_REPORT.md` §5). The fix was structural
(the `detect_outcome()` registry with a required `benchmark` argument),
not a one-file patch. See `reSTITCH.md` Part 5, Defect C.

**Corrected pilot results (5 modules, N=3, T=0.5).**

| module | model-condition set | corrected pass | classification |
|---|---|---|---|
| `accu` | all 5 | 0/15 | floor |
| `counter_12` | all 5 | 15/15 | ceiling |
| `barrel_shifter` | all 5 | 1/15 (`deepseek-coder:6.7b` only, iteration 5) | near-floor |
| `alu` | all 5 | 0/15 | floor |
| `calendar` | RTLCoder only (4/4) | — | incomplete coverage, not classifiable |

Two named comparisons, on the 4 modules with complete data:

- **Fine-tuning twin (RTLCoder/shared vs deepseek-coder:6.7b/shared):**
  three modules tie exactly (module ceiling/floor structure, not a model
  difference); `barrel_shifter` separates 0/3 vs 1/3 *against* RTLCoder,
  a single replicate, indistinguishable from noise at N=3.
- **Prompt format (RTLCoder native vs shared):** zero separation on every
  module with complete data.

The pilot's verdict, kept because the full run confirmed it: *no
fine-tuning advantage shown in either direction, no prompt-format effect
readable*, because 4 of 5 modules sat at a uniform ceiling or floor and
the recoverable band, where a difference could show, was almost entirely
missed. It also noted (and this remains true of the full run) that the
design has no STITCH-interpreter axis, since `condition` is fixed at
`baseline`, so it is a model comparison, never a STITCH validation. The
"Cross-references" section above records how each pilot finding fared at
full scale.
