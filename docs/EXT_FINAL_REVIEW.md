# Review of STITCH_EXT_FINAL.pdf against the raw data

Written 2026-09-24 for the authors, as notes to keep while editing. **The paper was not edited.** Only `STITCH_EXT_FINAL.pdf`
was reviewed (16 pages, read as extracted text, so the figures themselves were not inspected). Every number below was
recomputed from the raw master logs (`phase2/results/{set1_run,set3_run,twin_run}/master_log.json` and
`phase2/twin_analysis_SET2/module_categories.json`) by `docs/ext_final_verify.py`, without reusing the analysis scripts, and
then compared with the analysis outputs and documents. Re-run the script after editing to re-check.

## Bottom line

The paper's numbers reproduce, its escalation design argument stands, and its treatment of Set 3 (retiring the pooled
escalation "win" after a replicate-level trace) is exactly the standard the project set itself. What needs attention is
mostly wording and one asymmetry of standards:

1. **The Set 1 harm headline is stated more strongly than the data (and than `SET1_ANALYSIS.md`) supports.** Details in A.
2. **Three small factual slips**, each verifiable and easy to fix (B1 to B3).
3. **One undisclosed setup detail** that turns out to cost nothing: escalation runs had an 8-iteration cap, baseline and
   sem_adv had 6 (C).
4. **Bibliography:** five unresolved `[?]` citations, one duplicate entry and many uncited entries (E).

None of this weakens the positive result: escalation matches baseline everywhere, it costs less, and its worst case is
bounded by baseline by construction. The fixes are about making each sentence as strong as its evidence, not less.

## What checks out (recomputed, matches the paper)

- Table 4 (Set 1 by tier), all 12 cells and the pooled row: 109/378, 103/378, 104/375, 108/375 (28.8%, 27.2%, 27.7%, 28.8%).
- Tier counts 6 / 17 / 19, and every module's tier matches the stated thresholds (max Twin pass rate at least 0.8 is
  ceiling, 0.2 to under 0.8 recoverable, under 0.2 floor).
- Run counts 630 + 1,512 + 612 = 2,754, and the error counts 0 / 6 / 2.
- Table 5 and the Set 3 cost figure: 75.1%, 16.6%, 10.1%, pooled 18.5%; Set 3 27.6% (5.31 to 3.85). Table 3 matches
  `reSTITCH.md`.
- Tables 6 and 7 (Set 3), including n=49 for qwen2.5-coder:32b restart, and the per-model deltas (+7.8, -5.9, group mean
  -0.65).
- The Set 3 trace: 88 never escalated (all 88 passed), 65 escalated (2 passed), the interpreter fired in 32 runs and none of
  those passed.
- Twin: RTLCoder shared against deepseek-coder shared is 0 wins / 13 ties / 4 losses; native against shared is 3 / 12 / 2;
  RTLCoder native is 9/9 on the recoverable signal-processing modules.
- Section 5: 58 of 659 (8.8%) is documented in `phase1/PHASE1_FINDINGS.md`; 20 of 64 (31%) is arithmetically consistent with
  the 31% recorded in `docs/FULL_RUN_RUNBOOK.md`.

## A. The Set 1 harm claim is stronger than the evidence

Where it appears: abstract ("measurably lowers pass rate"), Section 8.2 finding (1) ("The harmful regime replicates at scale",
"the paper's headline"), Section 8.5 claim 2 ("real, replicated across 17 modules and three small models"), the conclusion,
and the novelty sentence ("To our knowledge this effect has not previously been demonstrated at ... replicated scale").

What the data show, recoverable band, Set 1 (17 modules x 3 models x N=3):

| quantity                                                 | value                                                                                             |
| -------------------------------------------------------- | ------------------------------------------------------------------------------------------------- |
| baseline vs sem_adv                                      | 54/153 (35.3%) vs 47/153 (30.7%), difference -4.6 points                                          |
| Wilson 95% CIs                                           | baseline 28.2 to 43.1, sem_adv 24.0 to 38.4 (heavily overlapping, as in the paper's own Figure 2) |
| Fisher exact, pooled runs                                | p = 0.47                                                                                          |
| cell level (51 module x model cells)                     | sem_adv worse in 7 cells (-10 replicates in total), better in 3 (+3), equal in 41                 |
| sign test on non-tied cells / Wilcoxon on 51 cell deltas | p = 0.34 / p = 0.13                                                                               |
| cell-bootstrap 95% CI of the pooled difference           | -10.5 to +0.7 points                                                                              |
| per model (51 runs each)                                 | deepseek-coder 33 to 33 (0.0), gemma3:4b 4 to 0 (-7.8), llama3.1 17 to 14 (-5.9)                  |

So the direction is consistent and the point estimate is negative, but it is not distinguishable from zero at this sample
size, and one of the three small models shows no effect at all. The paper applies a stricter standard to the same kind of
result elsewhere: Set 3's pooled +2.6 points for escalation is reported as noise because "every confidence interval crosses
zero", and no fired mechanism sits under it. `phase2/SET1_ANALYSIS.md` is more measured than the paper on the Set 1 dip: on
the recoverable band it calls it "a real-looking sem_adv dip and a real-looking sem_escalate_restart recovery, neither large
enough to call decisive at this N" (lines 179 to 181), and for the pooled 42-module figure "small enough to be within noise on
its own" (line 147). It also says "measurably, if modestly, worse" (line 335), so the word is not new, but "headline" and
"replicates at scale" go beyond "modest, not decisive".

Two further points a reviewer can raise:

- **Mechanism is not shown for the harm.** The project rule is to gate mechanism claims on `semantic_fired`. In Set 1 the
  interpreter fired in 52 of the 153 sem_adv runs on the band, and in the 7 cells where sem_adv did worse it fired in only
  5 of 21 runs. In the others sem_adv was baseline plus raw Verilator/Yosys text on every iteration. Set 1 has no raw_adv
  condition, so harm from the directives cannot be separated from harm from raw tool text (the conference paper's own
  protective regime says raw verbosity can hurt capable models). "Firing a repair interpreter on every iteration" is
  therefore not yet isolated as the cause.
- **"Replicated across three small models"** (8.5 claim 2) is not what the per-model rows show: two models drop, one is flat.

What is safe to say, and it does not depend on the harm being significant: escalation matches baseline on the recoverable
band (53 to 54 of 151 against 54 of 153), starts every run as baseline so its worst case is baseline by construction, and
always-on interpretation shows a consistent-direction but non-significant deficit on small models (-4.6 points, cell-level
95% CI -10.5 to +0.7) and essentially none (-0.65) on the large models as a group. Suggested handling: soften "measurably lowers" and
"replicates at scale" to "lowers, though within sampling noise at N=3", add the cell-level counts (7 worse, 3 better), state
that Set 1 cannot separate directive text from raw tool text, and drop or soften the novelty sentence. The escalation
argument in Section 4 needs none of the harm's significance.

## B. Small factual slips

**B1. "6 transient timeouts ... all floor-tier" (Section 8.1; the same line is in `reSTITCH.md` line 575).**
Five of the six are `RAM` / llama3.1 (`sem_escalate` reps 1 to 3, `sem_escalate_restart` reps 1 and 3), and `RAM` is a
recoverable-band module. Only `LIFObuffer` / deepseek-coder / restart rep 2 is floor-tier. The paper's own Table 4
denominators say so (150 and 151 out of 153 on the recoverable band, 170 out of 171 on the floor). `SET1_ANALYSIS.md`
states the cells correctly. Also, "transient" is doubtful for five errors in one module-model pair, all in the escalation
conditions; `RAM` / llama3.1 `sem_escalate` has zero valid replicates. Effect on the results is small: `RAM` / llama3.1 is
0/3 under baseline and 0/3 under sem_adv, so counting the missing runs as failures moves the recoverable-band rates to
47/153 (30.7%) for sem_escalate and 54/153 (35.3%) for restart, and no conclusion changes.

**B2. The Set 3 flip sentence (Section 8.4).** "four cells out of 153 flipping by one replicate each, three cells flipping the
other way" cannot produce the net +4. From the raw data, sem_escalate against baseline over the 51 cells: six cells gain
(one by 2, five by 1; +7 in total) and three cells lose 1 each (-3), net +4 = 90 - 86. `SET3_ANALYSIS.md` lists the same six
gains and three losses. Suggested: "six cells gaining seven replicates in total against three cells losing one each".

**B3. "plus the extra iteration budget" (Section 8.4).** The two escalated runs that passed both passed within six iterations
(all 90 sem_escalate passes in Set 3 are at iteration 6 or earlier), so the extra two iterations were not what rescued them.
`SET3_ANALYSIS.md` (line 199) has the same phrase and attributes those passes to the raw tool text after escalation.

## C. Iteration caps are not stated in the paper

`baseline` and `sem_adv` were capped at 6 iterations; `sem_escalate` and `sem_escalate_restart` at 8 (`iteration_cap` in every
master-log row, Sets 1 and 3; Twin was 8). The paper never says so, and the guarantee "escalation matches baseline" is
stated for an unequal budget. Measured cost of that: passes that came only in iterations 7 or 8:

| set, recoverable band | sem_escalate                            | sem_escalate_restart           |
| --------------------- | --------------------------------------- | ------------------------------ |
| Set 1                 | 1 pass (47/150 becomes 46/150 at cap 6) | 1 pass (54/151 becomes 53/151) |
| Set 3                 | 0                                       | 0                              |

At an equal cap of 6 the picture is unchanged (restart 53/151 = 35.1% against baseline 54/153 = 35.3%), so this is a
disclosure gap that can be turned into a strength: state the caps and give the equal-budget figures. Phase 3's runner already
uses one shared budget for all conditions, which removes this from the new experiment.

## D. Consistency and clarity

- **"matches baseline exactly (54/151 versus baseline's 54/153)" (8.2).** The counts match, the rates are 35.8% and 35.3%.
- **Twin, Section 7.2, the "wash".** Three comparators are mixed. On the 17 recoverable modules (51 runs each): deepseek-coder
  shared 32/51 (62.7%), RTLCoder native 29/51 (56.9%), RTLCoder shared 21/51 (41.2%). The 0 / 13 / 4 verdict is shared against
  shared, where the base model is ahead by 11 passes; `TWIN_RUN_ANALYSIS.md` reads this as "if anything a mild disadvantage ...
  'leans against'". The class exception uses the native prompt, and native against deepseek is 29 vs 32 (5 wins, 6 ties,
  6 losses), which is a wash. Suggested: give all three totals and say which one each sentence uses.
- **Scope of "every signal-processing module (9/9) and every Memory module (3/3)".** These hold on the recoverable band only:
  3 signal-processing modules (`freq_div`, `freq_divbyeven`, `signal_generator`) and 1 Memory module (`LFSR`, 3 runs).
  Across all 42 modules RTLCoder native is 9/15 on signal-processing and 6/12 on Memory. "Holds the Control class" is
  native 2/6 against deepseek 0/6 (2 modules).
- **Abstract vs body.** The abstract credits a clear edge on signal-processing only; Sections 7.2 and 7.4 and the conclusion
  say signal-processing and memory.
- **Figure 1 caption** lists five modules that "go against RTLCoder" (`adder_8bit`, `fixed_point_adder`,
  `fixed_point_substractor`, `RAM`, `width_8to16`), while the text counts four losses. `width_8to16` is 1/3 against 2/3, which the
  tie rule counts as a tie.
- **Section 3 "Three larger-module candidates" describes two.** The third is `alu_with_enable` ("too easy after the redesign",
  `phase0/illustrations/retired/retired_candidates.md` section 1c); one clause would close the gap.
- **Sections 2.2 and 8.2 say the floor modules' defects "sit outside the interpreter's reachable class".** That is a prediction, not a
  result here: the conclusion proposes to inspect the floor corpus for exactly this. "Consistent with" would be accurate.
- **Section 2.1 (Table 1).** "against a six-iteration failure for both controls" holds for the gemma3:4b rows only; both llama3.1
  rows pass under the controls.
- **Abstract, "three silent pass-detection defects".** Defects A (simulator working directory) and B (code-fence extraction) are
  harness defects, not pass detection; only C is.
- **Set 3 restart.** The "no fired mechanism" trace is given for sem_escalate (0 of 90 passes with the interpreter fired). For
  sem_escalate_restart one of its 88 passing runs had the interpreter fire (and 7 of sem_adv's 85), so a clause for restart
  would keep the statement exactly true.

## E. Bibliography

- Unresolved `[?]`: five, on the deepseek-coder base weights (Section 7.1), gemma3:4b and llama3.1 (7.1), and
  qwen2.5-coder and gemma3:27b (8.1). Looks like undefined BibTeX keys.
- `[4]` and `[9]` are the same AutoChip entry; the body cites only `[9]`.
- Cited in the body: `[1]`, `[2, 3]`, `[8]`, `[9]`. Never cited: `[4]` to `[7]` (Verilator, Yosys, Icarus are named in the text without a
  citation) and `[10]` to `[16]` (RTLFixer, VerilogEval, Self-Refine, HDLBits, RAG, the BITS HPC entry, and Wilson, whose intervals
  are used throughout).

## Not checked

Figures 1 to 5 as images (only their captions and the tables they summarise), Table 1 and Table 2 beyond a spot-check of the
decoder_3to8 record, Table 3 against raw Phase 1 logs (it matches `reSTITCH.md`), and the related-work and reference details
of `[1]` to `[16]`.
