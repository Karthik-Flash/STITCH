# Paper v10: changes from v9

v10 is the Overleaf-ready build of the journal paper. It lives in `paper/overleaf/` (`main.tex`, `supplement.tex`,
`figures/`, `README.txt`) and is packed as `paper/STITCH_overleaf.zip`. v9 (`paper/archive/STITCH_EXT_v9.tex`, its
supplement and generated inputs) is kept unchanged.

The content is the same as v9: no new claim, and every number is unchanged and sourced. The one addition is the
clearly marked Haiku projection (section 5). Date: 2026-10-13.

## 1. Result

| Document | Pages | Clean-room build (`latexmk -pdf`, empty temp directory) |
|---|---|---|
| `main.tex` | **15** including references (limit 17) | 0 errors, 0 warnings, 0 undefined references or citations, 0 missing figures, 0 "Float too large", 0 overfull or underfull boxes |
| `supplement.tex` | 14 | the same: 0 of everything |

The zip was also extracted into a fresh directory and built again, with the same result. Every font is embedded
(`pdffonts`). Every `.tex` file and `README.txt` is ASCII only, with no em-dash.

## 2. Why v9 did not work on Overleaf, and the fixes

| Problem on Overleaf | Cause in v9 | Fix in v10 |
|---|---|---|
| Did not compile | `\input{numbers_set4}` and `\input{tables_set4}` pointed at files outside the uploaded set | The Set 4 macros sit inside `main.tex` (and `supplement.tex`) between `% BEGIN GENERATED NUMBERS` and `% END GENERATED NUMBERS`; the supplement's S6 tables sit between `% BEGIN GENERATED TABLES` and `% END GENERATED TABLES`. `make_numbers_set4.py` rewrites only those blocks. No `\input`, no absolute path. |
| Figures piled up at the end | `[t]` floats, default float fractions, no barriers | `[!htbp]` floats placed after the paragraph that first cites them; `placeins` with `[section]`; `\topfraction` 0.9, `\bottomfraction` 0.8, `\textfraction` 0.07, `\floatpagefraction` 0.8, `topnumber` 3, `bottomnumber` 2, `totalnumber` 4. No float lands more than one page after its first mention. |
| References missing | Follows from the failed compile | The inline `thebibliography` (24 entries, all cited) appears on pages 14 to 15. |
| TikZ arrows did not connect | Arrows drawn to diagonal anchors (`fb.north east`) and between nodes of different heights | Both diagrams redrawn: every arrow runs between node anchors with orthogonal routing (`-|`, `|-`), checked at 200 dpi. |
| Cluttered tables, poor look | Mixed `$...\%$` cells, `\fitbox` scaling, inconsistent sizes | See sections 3 and 4. |

## 3. Typography and layout

- `article`, 11 pt, 1 in margins (unchanged). Text font Times (`newtxtext`, `newtxmath`), typewriter Inconsolata
  (`zi4`), `microtype`.
- `caption` (small, bold labels), `subcaption` for side-by-side panels with (a), (b), (c) labels, `booktabs`,
  `siunitx` (signed, decimal-aligned contrast columns), `makecell` (two-line headers), `placeins`, `titlesec`
  (compact headings), `cleveref` loaded after `hyperref`.
- Figure captions below, table captions above; every caption states the takeaway in one or two sentences.
- Condition names always `\cond{...}`; numbers in math mode throughout, except inside bold run-in sentences.
- Colours shared by the figures and the diagrams, one per condition (section 4).

## 4. Figures

All figures come from one style module, `paper/figstyle.py`:
- **One colour per condition**, validated with the dataviz palette checker (all pairs, light mode: lightness band,
  chroma, colour-vision-deficiency separation and the normal-vision floor all pass):
  - `baseline`: grey `#8F8E89`;
  - `baseline_gate` (alarm only): light amber `#E3A835`;
  - `raw_adv`: vermillion `#D9622B`;
  - interpretation, a blue family: `sem_adv` (v2) `#6FA8E6`, v3 `#1D5AA6`;
  - escalation, a green family: `sem_escalate` `#63BF95`, `sem_esc_restart` `#006E4B` (the strongest).

  The light colours carry direct value labels, as the checker's contrast note requires.
- **Drawn at the final printed width:** 6.5 in for full width, 3.15 in for a half, 2.08 in for a third. They are
  included at natural size, so text stays at 7 to 8 pt.
- **Format:** vector PDF with TrueType fonts embedded.
- **Style:** light gridlines and Wilson or Newcombe error bars wherever the paper reports intervals.

Generators: `python -B paper/make_v10_figures.py` (all but the heat map) and
`python -B phase2/frontier/make_numbers_set4.py` (heat map).

### Main paper (in order)

| Fig. | Content | Panels | Source |
|---|---|---|---|
| 1 | Teaser: (a) signed off defective by condition; (b) latch-free clean synthesis on latch-bearing tasks; (c) top-level synthesis restored, 2x2 and 3x3 mesh and MPSoC | 3 x 2.08 in | `PHASE3_FINAL.md` (pooled, composition); `PAPER_NUMBERS.md` (latch line) |
| 2 | STITCH pipeline (TikZ) | full width | n/a |
| 3 | Escalation state machine (TikZ), beside Table 3 | half | n/a |
| 4 | Set 1: (a) pass rate by tier; (b) tool calls per run | 2 x half | `phase2/set1_analysis/tier_pass_rates.csv`, `cost_by_tier.csv` |
| 5 | Ladder: (a) baseline pass rate, every model; (b) always-on deficit, Newcombe CI | 2 x half | Set 3 builders, `set4_analysis.json` |
| 6 | Set 4b floor heat map, module x API model, baseline passes of 3; Haiku's projected cells hatched, italic, dagger, legend "proj." | full | `set4b_analysis.json` Q1, `evidence/set4b_haiku_projection.json` |
| 7 | (a) The latch defect at scale: latch cells vs router count (2,880; 6,480; 0 after repair; MPSoC 269 to 122); (b) top-level synthesis by condition and design | 2 x half | `PHASE3_RESULTS.md` T7; `PHASE3_FINAL.md` composition |
| 8 | Phase 3: (a) sign-off clean by condition and stratum; (b) cumulative sign-off clean by model call | 2 x half | `PHASE3_FINAL.md` |

The brief's F1 to F9 are all in the main paper:
- F5, the latch defect at scale, is Figure 7a. Figure 1c also annotates the aborting baseline.
- F9, composition, is Figure 7b. It replaces the composition table, which moved to the supplement.

### Supplement

| Fig. | Content |
|---|---|
| S1 | Twin: (a) fine-tuning twin at the shared prompt; (b) prompt format |
| S2 | Set 1 pooled: (a) tool calls per run; (b) pass rate |
| S3 | Phase 3 sign-off clean per model, four conditions |
| S4 | API ladder rows, sign-off clean of 33 by condition |

The old PNG figures (`twin_named_comparisons.png`, `set1_cost_passrate.png`, `fig_p3_v2_by_model.png`,
`fig_p3_v2_composition.png`, `fig_p3_api_ladder_signoff.png`) are regenerated in the shared style. The composition
figure is now Figure 7b of the main paper, so the supplement no longer repeats it.

## 5. Tables

**Main paper:**
1. Interpreter rule classes.
2. The replicated illustrations.
3. Cost per run (in-house benchmark), beside Figure 3.
4. The eleven tasks, with abbreviations explained in the caption.
5. Phase 3 by condition, with grouped columns: Sign-off, Loop, Cost.
6. Primary contrasts: aligned Delta, CI ("lo to hi"), p and discordant columns; stratum rows indented.
7. Ladder rows, with sim-silent and sim-visible as separate narrow columns plus tokens.

All tables use booktabs only, right-aligned or `siunitx`-aligned numbers, percentages as bare numbers under a
"%" header, `makecell` two-line headers and `\footnotesize`. None is scaled with `\resizebox`.

**Moved to the supplement:**
- Leaf defects composed into the designs (v9 Table 5) is now Table S17. The main text keeps its numbers in
  Section 9.1, and Figure 7a plots them.
- Top-level synthesis after splicing (v9 Table 9) is now Table S26 only. Figure 7b plots it.

**Supplement:** every table reformatted the same way; the S6 tables (`make_numbers_set4.py`) restyled.

## 6. Haiku projection (marked, removable)

Claude Haiku 4.5 is at 143/228 valid Set 4b runs. 7 modules were not run (barrel_shifter, counter_12, fsm,
LIFObuffer, pulse_detect, serial2parallel, traffic_light), plus one `sem_escalate_restart` run of float_multi.

**Method** (`make_numbers_set4.py`, `project()`). For each (module, condition) cell with fewer than 3 valid Haiku runs:
1. Start from the mean pass rate of GPT-4.1 mini and Gemini 2.5 Flash on that cell.
2. Shift it on the logit scale by Haiku's mean logit difference from those two models. That difference is taken
   over the cells all three measured in full: 47 cells on the 12 modules all three ran.
   - Logits are empirical, with one half added to each count, so 0/3 and 3/3 stay finite.
   - The offset is **+0.72 logits** (Haiku is the stronger model).
   - A mean rate of exactly 0 or 1 stays there.
3. Report a range from the lower to the higher of the two other models' rates. Because of the shift, the point
   projection can fall outside that range.

Inputs, method and outputs are in `phase2/frontier/evidence/set4b_haiku_projection.json`. The supplement states the
method (S6, Table S15).

**Projected cells** (29; passes of 3; the range in brackets):

| Module | baseline | sem_adv | sem_escalate | sem_esc_restart |
|---|---|---|---|---|
| barrel_shifter | 2.4 [1, 3] | 2.0 [0, 3] | 2.0 [0, 3] | 2.0 [0, 3] |
| counter_12 | 3.0 [3, 3] | 3.0 [3, 3] | 3.0 [3, 3] | 3.0 [3, 3] |
| float_multi | measured | measured | measured | 1.5 [0, 2] (one run missing; value for a full cell) |
| fsm | 3.0 [3, 3] | 3.0 [3, 3] | 3.0 [3, 3] | 2.4 [2, 2] |
| LIFObuffer | 3.0 [3, 3] | 2.4 [1, 3] | 2.7 [2, 3] | 3.0 [3, 3] |
| pulse_detect | 2.0 [0, 3] | 0.9 [0, 1] | 1.5 [0, 2] | 1.5 [0, 2] |
| serial2parallel | 3.0 [3, 3] | 2.7 [2, 3] | 3.0 [3, 3] | 3.0 [3, 3] |
| traffic_light | 1.5 [0, 2] | 0.0 [0, 0] | 2.4 [2, 2] | 1.5 [0, 2] |

**Where the paper uses projections.** Only where a trend needs a complete Haiku column:
- the floor heat map (Figure 6): the 7 baseline cells are hatched, italic, with a dagger;
- the Q1 count (Section 8.3): 4 of the 12 modules all three models ran are at ceiling for all three (observed), and
  **8**&dagger; of all 19 once Haiku's missing modules are projected.

Each place carries the note "Haiku: 12 of 19 modules measured; values marked † are projections, to be replaced".
Every observed conclusion uses measured runs only. Gemini is complete and reported as measured.

**Mechanics:**
- `\proj{...}` renders a value in italics with a dagger.
- `\newif\iffinal`, default `\finalfalse`. Under `\finaltrue`, `\proj{}` and the note raise
  `\errmessage{Projected Haiku values remain}`. Tested: the build stops with that message.
- When Haiku is completed, re-running `analysis_set4b.py` and then `make_numbers_set4.py` makes the projection list
  empty. Then:
  - the Q1 clause and the notes expand to nothing;
  - the counts use measured values;
  - the heat map is redrawn without hatching;
  - the supplement's projection subsection says no value is projected.

## 7. Content corrections (wording only)

- **freq_divbyfrac**: one consistent statement in Section 8.4, in direction (v) of the conclusion and in S7: not a
  testbench defect; the specification's own description of the counter does not match its reference design (our
  reading); the models fail on period and duty cycle. Removed:
  - "These are model failures on a hard specification; an oracle defect is not supported";
  - "The verdict stays: genuine model failures on a hard fractional-divider specification".
- **The latch result** opens Result (1) as its bold lead sentence. It is also named in the introduction's
  contribution list.
- **Figure 1** is announced in the introduction.
- **The "11" artefact** before Section 1: not present (checked on the rendered page 1).
- **Cross-references**: every `\cref`/`\ref` target exists (0 undefined), and each was checked against the float it
  names on the rendered pages.
- **Escalation algorithm**: the v9 algorithm box became prose in Section 5 plus Figure 3. The same facts are kept:
  N=2, M=3, a 5-line signature, budget 8.

## 8. Numbers newly quoted in the main text (all from existing evidence)

| Number | Where | Source |
|---|---|---|
| 85% (122/144), latch-free clean synthesis under v2 | Result (1), Figure 1b | `phase3/evidence/phase3_final/PAPER_NUMBERS.md`, line "(1) latch-bearing tasks" |
| raw text 15, 15 and 13 of 18; escalation 15/18 for the MPSoC top | Result (5) | `PHASE3_FINAL.md`, Composition (it was v9 Table 9) |
| 2,880; 6,480; 269; 0; 0; 122 latch cells | Section 9.1, Figure 7a | `PHASE3_RESULTS.md` T7 (it was v9 Table 5) |
| 8 to 15% signed off defective with tools | Figure 1 caption | `PHASE3_FINAL.md` pooled (it was v9 Table 6) |
| 8&dagger; of 19 at ceiling for all three; +0.72 logit offset; the 29 projected cells | Section 8.3, Figure 6, S6 | `phase2/frontier/evidence/set4b_haiku_projection.json` (projection) |

A token-level comparison of every number in the v10 bodies against v9 and its generated inputs finds only:
- TikZ and layout lengths;
- the projection values;
- `1,211`, which is v9's 1211 with a thousands separator.

## 9. Visual QA rounds (pages rendered at 110 dpi with `pdftoppm`, every page inspected)

1. **Round 1** (main 15 pages, first clean-room build):
   - Pipeline labels collided with an arrow ("Feedback prompt"); node text wrapped and hyphenated.
   - State-machine node text overflowed its boxes; the table beside it was bottom-aligned.
   - siunitx dropped the "+" signs in Table 6.
   - Ladder-table column groups ran together.
   - Bold lead numbers were set in non-bold math.
   - The deficit axis label was clipped.
   - Heat-map projected cells were hard to read under the hatch.
   - "1211" had no thousands separator.

   Fixed:
   - pipeline re-laid out at 8 pt with the sign-off box beside the loop;
   - wider state nodes, top-aligned minipages;
   - `retain-explicit-plus`;
   - 11 pt gaps between column groups;
   - text numbers in the bold lead;
   - a shorter axis label;
   - legible projected cells (solid label patch, light hatch, "proj." legend);
   - formatted macros.

   Added Figure 7 (F5 and F9) in the room left by the 15-page count.
2. **Round 2**:
   - The latch-scale legend overlapped a value label.
   - The composition panel showed no zero bars.
   - Supplement: one 52 pt overfull line (long model identifiers), a backtick ligature in the triple-backtick code-fence example, and
     "equiv_simple -seq 5" split across a line.

   Fixed: the legend moved above the axes; "0" labels added; `\allowbreak` in the identifiers;
   `\textasciigrave`; `\mbox`.
3. **Round 3**: one underfull line in the bibliography (a long URL). Fixed with `\newline`.

   **Final**: 0 warnings in both logs, all pages inspected, contact sheet `paper/overleaf/qa_contact_sheet.png`
   (main and supplement thumbnails).

## 10. Repository

- New: `paper/figstyle.py`, `paper/make_v10_figures.py`, `paper/overleaf/`, `paper/STITCH_overleaf.zip`,
  `phase2/frontier/evidence/set4b_haiku_projection.json`.
- Changed: `phase2/frontier/make_numbers_set4.py`.
  - Now: the projection, the in-file blocks, the heat map, and thousands separators.
  - No longer: `paper/numbers_set4.tex` and `paper/tables_set4.tex`. Those stay as v9's frozen inputs, now in
    `paper/archive/`.
- Placeholder replacement (its own commit), as approved at the checkpoint:
  - **Docs:** `<HPC_USER>@<HPC_HOST>`, `/scratch/<HPC_USER>`, `<GPU_NODE>`, `%USERPROFILE%`, `<REPO_ROOT>`,
    `<RTLLM_ROOT>`, `<DATA_ROOT>`.
  - **Slurm scripts:** `/scratch/$USER`, and `/scratch/%u` in `#SBATCH` lines, where Slurm does not expand
    variables.
  - **WSL launchers:** `REPO_ROOT` is derived from the script's location; `$WIN_HOME`, `$HOME` and `RTLLM_ROOT`
    have working defaults.
  - **Python defaults:** the RTLLM checkout is derived from the script location.
  - **Kept:** the MPSoC source attribution `p20230031/RISC-V`.
  - **Not touched:**
    - evidence files and logs;
    - pre-registrations;
    - the seven Phase 3 cluster scripts whose hashes are recorded in `phase3/evidence/FREEZE_FINAL.md`. Editing
      them would break the freeze record;
    - frozen test fixtures and test strings;
    - `phase1/demo_error_signature.py`, whose real log excerpts are demo input.

## 11. Edits after the checkpoint (2026-10-13)

1. **Design provenance, one wording.** The abstract ("an independently developed RISC-V MPSoC") and Section 9.1
   ("an in-group MPSoC") now both read "a RISC-V MPSoC developed within our group, independently of this study".
   The supplement used neither phrase.
   - The abstract grows from 249 to 256 words.
2. **Multiplicity of the primary contrasts.** Result (2) now states: "As pre-registered, the four primary contrasts
   are not corrected for multiplicity; contrast 1 (p<0.001) survives a Holm correction across the four, contrast 2
   (p=0.021) does not."
   - Holm across the four p-values (<0.001, 0.021, 1.000, 1.000) multiplies the second smallest by 3: 0.063, above
     0.05.
   - Threats to Validity (Statistical) adds the matching clause.
   - No number changes.
3. **Projections can be switched off.** `make_numbers_set4.py --no-projection` keeps the measured runs only. Haiku's
   missing cells read "not run" (a "–" in the heat map), and the Q1 clause and the projection table disappear.
   - Tested: both files compile under `\finaltrue` with 0 errors and 0 warnings.
   - Re-running without the flag restores the projected version byte for byte.
   - `phase2/frontier/PENDING.md` records the procedure.
4. **Rebuild.** Clean room, then the zip extracted and built again:
   - `main.tex` 15 pages, `supplement.tex` 14 pages;
   - 0 errors, 0 warnings, 0 undefined references, 0 overfull or underfull boxes;
   - the zip and `qa_contact_sheet.png` refreshed.
