# STITCH_EXT_v7.tex: what changed from v6

Built from your v6 paste (the paste was cut off inside the bibliography, and no v6 `.tex` exists on disk), plus the four
files you added for Phase 3 (`sec_mpsoc.tex`, `TEX_EDITS.md` and two PNGs). Those four were deleted on 2026-09-27 once
merged: `sec_mpsoc.tex` is inlined as Section 9, and the two PNGs are replaced by script-generated figures
(`figures/fig_p3_*.png`, from `phase3/runner/phase3_figures.py`). All figures now sit in `paper/figures/`. Not compiled (no LaTeX engine on this machine); checked
structurally instead: environments and braces balance, no undefined `\ref`/`\cite`, no em- or en-dash characters, ASCII
only, every table row has the right column count, and every number in Sections 1 to 8 occurs in `STITCH_EXT_FINAL.pdf`
except the ones listed under "numbers I added". **Please compile once in Overleaf.**

## A. Your TEX_EDITS.md, applied as written

E1 figure lines in the header; E2 abstract sentence (I added the CI "cell-level 95% CI +3.5 to +26.3" to it); E3 roadmap
sentence; E4 Phase 3 section directly before the Conclusion (inlined, not `\input`); E5 conclusion paragraph; E6 (a) and (b)
in Directions. **E7 (subtitle) not applied**, as you said it was optional.

## B. Wording fixes from `docs/EXT_FINAL_REVIEW.md` (no result changed)

| where | change |
|---|---|
| Abstract, Sec 4, Sec 8 intro, 8.2 finding 1, 8.4, 8.5 claims 2 to 4 and closing paragraph, Fig. 2 / Table 7 / harm-ladder captions, Conclusion | "measurably lowers pass rate" / "harmful regime replicates at scale" / "paper's headline" became "sits about four points below baseline, consistent in direction, within sampling noise at N=3". Added cell-level counts (worse in 7 of 51 cells, better in 3, equal in 41; cell-bootstrap CI -10.5 to +0.7) and the point that Set 1 has no raw_adv arm, so directives cannot be separated from raw tool text. Removed the "to our knowledge ... not previously demonstrated" sentence. Escalation's guarantee is unchanged and is stated not to depend on this. |
| 8.5 closing | "largest replicated evaluation ... we are aware of" became "rests on 2,124 replicated STITCH-condition runs (Sets 1 and 3)" |
| Table 1 text (2.1) | "six-iteration failure for both controls" now says gemma3:4b only; llama3.1 rows pass under the controls in two to four iterations |
| 2.2 and 8.2 finding 3 | floor-tier "sit outside the reachable class" became "consistent with", and marked as a prediction not yet tested |
| Sec 3 | "Three candidates ... all failed replication" now says two failed and `alu_with_enable` was retired as too easy |
| Abstract and Sec 5 | "three silent pass-detection defects" became "three silent harness defects (working directory, code-fence extraction, pass detection)" |
| Sec 6 and 8.1 (B1) | "6 transient timeouts, all floor-tier" now names the cells: 5 on RAM/llama3.1 (recoverable band, escalation arms), 1 on LIFObuffer/deepseek-coder (floor); explains the 150/151/170 denominators; adds that counting them as failures gives 47/153 and 54/153 and changes no conclusion |
| 8.1 (C) | new "Iteration budget" paragraph: baseline/sem_adv capped at 6, escalation arms at 8 (Twin 8); passes only in iterations 7 or 8: one each in Set 1 (47/150 to 46/150, 54/151 to 53/151), none in Set 3; equal-cap restart 53/151 (35.1%) vs baseline 54/153 (35.3%); Phase 3 shares one budget. Sec 4 points to it. |
| 8.2 (D) | "matches baseline exactly (54/151 vs 54/153)" became "matches baseline (54/151, 35.8%, vs 54/153, 35.3%)" |
| 8.4 (B2) | flip sentence now arithmetically exact: +4 replicates (90 vs 86) from six cells gaining seven in total against three cells losing one each |
| 8.4 (B3) | "plus the extra iteration budget" became "after escalation, within the first six iterations" |
| 8.4 | restart clause added: 1 of its 88 passing runs had the interpreter fire, and 7 of sem_adv's 85 |
| 7.2, 7.3, 7.4, Fig. 1 caption, abstract, conclusion (D) | Twin: all three totals given (deepseek shared 32/51, RTLCoder native 29/51, shared 21/51) and each sentence says which it uses; 0/13/4 is shared vs shared, native vs deepseek is 5/6/6 (a wash); 9/9 and 3/3 scoped to the recoverable band (three signal-processing modules, one Memory module); Control 2/6 vs 0/6; caption lists the four losing modules and says width_8to16 is a tie under the rule; prompt effect now also gives native 29/51 vs shared 21/51 and claims no direction; abstract and conclusion both say signal-processing (memory noted in the body) |
| Bibliography (E) | the five `[?]` citations are now defined (see D below); Verilator, Yosys, Icarus, Wilson and the HPC entry are now cited once in the text |

## C. Numbers I added (all recomputed in the earlier review or in `phase3_analysis.json`)

62.7 / 56.9 / 41.2 % and 32 / 29 / 21 of 51; 5-6-6 (native vs deepseek); 9/15 and 6/12; 2/6 vs 0/6; 7 / 3 / 41 cells and
-10.5 to +0.7; 47/153, 54/153, 53/151, 35.1 %, 35.8 %; 2,124 runs; 14.6 points CI +3.5 to +26.3 (abstract).

## D. Please check

1. **Bibliography.** Entries [1] to [8] and the last five are copied from the reference list of `STITCH_EXT_FINAL.pdf`.
   The four missing keys behind the `[?]` (`deepseekcoder`, `gemma3`, `llama3`, `qwen25coder`) are **written by me from
   memory**: DeepSeek-Coder arXiv:2401.14196, Gemma 3 arXiv:2503.19786, Llama 3 arXiv:2407.21783, Qwen2.5-Coder
   arXiv:2409.12186. Verify them. Also verify the author list and venue of [2] RTLCoder and [4] AutoChip, which I copied
   as they were. RTLFixer, VerilogEval, Self-Refine, HDLBits and RAG are in the list but cited nowhere (as in v6);
   cite or delete them.
2. **Pilot claim** in 9.4 ("an 8B model fixed every defect on its first call under every condition"): the pilot output is
   not in the repo, so I could not re-verify it (commit `fde3652`, "pilot showed ceiling", is consistent with it).
3. Any of the B-table wording you do not want: each row is independent, so revert freely. The one with substance is the
   first row (the always-on deficit); it follows the data (Fisher p = 0.47 on pooled runs, cell-bootstrap CI -10.5 to +0.7).
4. "Only comment about v3": I kept the v2 columns in your Phase 3 tables and figures (v2 = the production interpreter
   comparison), and the prose treats v3 as the upgrade. Dropping v2 would mean regenerating the two PNGs.

## E. Section 9 rewrite (2026-09-27)

Order is now: substrate, propagation, the v3 upgrade (why it exists), experiment, five results, summary. Results:
(1) STITCH catches what simulation signs off (adds 1/198 silent structural passes for v3 and latch-free 24% -> 88%);
(2) interpretation beats raw text, sooner and cheaper (adds v2 vs raw +9.1, CI +1.0..+17.7; 62% clean after one
call; per-model gains; new figure `fig_p3_clean_by_call.png`); (3) escalation: highest clean rate, fewest tool rounds,
+23.3 over baseline on sim-visible tasks, protects llama3.2:3b; (4) composition; (5) the upgrade's coverage result.
Section 8 ends with a two-sentence bridge into Section 9; the subtitle adds "and a Real-MPSoC Case Study"; the
abstract and conclusion carry the escalation result. Every number is from `phase3/evidence/phase3_run/PHASE3_RESULTS.md`.
`PHASE3_MPSOC.tex` is the long form with all Phase 3 tables (tasks, pooled, contrasts, cost, per task, upgrade,
composition with golden-bound counts) and four figures.

## F. Framing edits (2026-09-27, user-approved)

1. Abstract: the Phase 3 sentence now says STITCH "catches the defects a simulation-only loop signs off" before the numbers.
2. End of Section 8: added that the interpreter spoke in only about a third of always-on runs on RTLLM's recoverable band
   (52 of 153, Set 1), and that STITCH's benefit scales with the structural share of a failure, which is why RTLLM pass
   rates stay flat.
3. Conclusion: "good-to-have, low-cost sign-off assistant" became "a deterministic sign-off guard and translator ... a
   low-cost addition worth having in any repair loop" (keeps both framings).
