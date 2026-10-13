# STITCH_EXT_v7.tex -> STITCH_EXT_v8.tex

v8 applies the planner's Phase 3 decisions after the final batch. It adds the pre-registered control arm, the
32B arm and the API ladder rows, and the sign-off oracle. v7 is untouched.

## Scope and invariants

- **Prefix.** Before `\section{Is STITCH Useful on Real Hardware? An MPSoC Case Study}`, only two things change:
  - the Phase 3 sentence of the abstract (item 1 of `ABSTRACT_INTRO_PATCH.md`, applied on the user's instruction on
    2026-09-30);
  - the header comment (item 3; not rendered).

  Everything else is byte-identical to v7: Sections 1-8, their tables, figures and labels. The script checks this
  (numbers section below).
- **Introduction.** Not edited. The optional roadmap sentence (item 2 of the patch) is not applied.
- **Section 10.** Only the Phase 3 paragraph and the Phase 3 item of "Directions" change (diff below). Everything
  else in Section 10 and the bibliography is byte-identical.
- **Labels.** Every Section 9 label that v7 defines is kept (`sec:mpsoc`, `sec:mpsoc-*`, `tab:mpsoc-prop`,
  `tab:mpsoc-cond`, `tab:mpsoc-compose`, `fig:mpsoc-cond`, `fig:mpsoc-call`), except `fig:mpsoc-compose`: that
  figure moved to `PHASE3_MPSOC_v2.tex` (see below). No earlier section referenced it. New labels:
  `tab:mpsoc-primary` and `tab:mpsoc-ladder`.
- **Compile.** Tectonic 0.15 compiles v8 with 0 undefined references and 0 undefined citations. v7 is 21 pages and
  v8 is 23. Section 9 spans 4.49 pages in v7 and 6.10 in v8 (+1.61, measured from the PDF; the longer abstract
  shifts it slightly).

## Abstract (applied)

The v7 sentence quoted:
- 990 runs, six models from 3B to 14B;
- 62% signed off, brought to 1%;
- +14.6 over raw text, CI [+3.5, +26.3];
- 23% fewer calls and tokens;
- escalation at 80%.

The v8 sentence quotes:
- 1,386 runs, seven models from 3B to 32B, scored by a specification-complete sign-off testbench;
- 63% signed off defective, including every sim-silent defect at every size tested, against 8% with the interpreter;
- the pre-registered control arm, with the interpreter +14.6 [+3.0, +26.3] and escalation +19.7 [+11.1, +29.3]
  over the alarm;
- +14.1 over raw text, CI [+3.5, +24.7];
- 23% fewer calls and tokens;
- escalation at 72% sign-off clean.

The rest of the abstract is unchanged.
- **Overfull boxes.** The two remaining overfull boxes also exist in v7: the abstract, and a Section 10 paragraph.
  v7's Section 9 overfull box is gone.
- **Style.** The new text has no em-dashes, no "breakthrough", "proves", "dramatic" or "significantly", and no
  non-ASCII byte.

## Section 9, change by change

- **Intro sentence.** "$990$ repair runs then give five results" becomes "$1{,}386$ repair runs, the last $396$
  pre-registered, then give eight results".
- **9.1-9.3** are unchanged.
- **9.4 Experiment.**
  - The first paragraph is unchanged apart from the end of the metric sentence, which moves to the "Two oracles"
    paragraph.
  - New paragraph "A pre-registered control arm":
    - `baseline_gate`, the logged `would_fire`, and the 32B arm;
    - the PREREG hash and the run counts;
    - the API rows, as descriptive only;
    - the Vulkan backend sentence.
  - New paragraph "Two oracles": the loop and sign-off testbenches, the equivalence audit, "post hoc for the 990,
    pre-registered for the new arms", and the definitions of sign-off clean and signed off defective. The as-run
    metric is kept as a sensitivity; the statistics sentence is kept.
- **9.5 Results.**
  - Table 9 is rebuilt: six rows (with `baseline_gate`), sign-off clean with Wilson CI, as-run in brackets, signed
    off defective, loop pass, calls and tokens.
  - Figure `fig_p3_clean_by_condition.png` is replaced by `fig_p3_v2_clean_by_condition.png`.
  - **(1)** is rewritten: "at every size", with the 32B and API 18/18. The latch-free sentence is kept; it is
    Yosys-only and depends on neither oracle.
  - **(2)** is new and is the headline: the ladder, Table `tab:mpsoc-primary` (four contrasts; strata for 1 and 2),
    R1, the sensitivity and as-run readings, the stratum note, the plateau, the loss of loop passes, would_fire
    (availability, not effect), and per model.
  - **(3)** is rewritten on sign-off clean: v2 is stated as the out-of-sample estimate, plus cost, first call and per
    model.
  - Figure `fig_p3_clean_by_call.png` is replaced by `fig_p3_v2_clean_by_call.png`.
  - **(4)** is rewritten: 72%, 47.5%, +14.4 (with +23.3 as run), and 7/1/8 of 15. The closing sentence is shortened
    to "(compare Section 8)".
  - **(5)** The composition table gains a `baseline_gate` column, and the text gains "the alarm alone reaches 11/18".
    The leaf-to-bound sentence is kept, marked "in the 990 runs".
  - **The composition figure is removed from Section 9** (deviation, see below).
  - **(6)** is new: "Up the ladder", with Table `tab:mpsoc-ladder` (32B and two API models).
  - **(7)** is the v7 upgrade paragraph, unchanged in substance. The opening sentence "The upgrade is first a coverage
    result" is dropped for length. The note "none of the four has a sign-off testbench that differs" is added. The
    ending now says "remains in-sample".
  - **(8)** is new: oracle integrity, the mem_wb_mux motivating case, the Address_select violation, the advice
    counts ("a count, not a causal claim"), the processor-level note, and the fix pointer to Section 10.
- **9.6** is rewritten at about the same length, closing with the six limitations of the brief and the composition
  item.

## Section 10 diff (the only changes)

```diff
@@ Phase 3 paragraph
 answer. On real hardware the decisive defects are often invisible to
-simulation, and a simulation-only loop signs them off ($62\%$ of its runs);
-the tool layer exposes them, interpretation repairs them more reliably, sooner
-and more cheaply than raw tool text ($+14.6$ points, about $23\%$ fewer calls
-and tokens), escalation reaches the highest clean rate, and repaired leaves
-restore synthesis of whole router meshes and of the processor top. In a
+simulation, and a simulation-only loop signs off defective RTL ($63\%$ of its
+runs, and every sim-silent run at every model size tested). What the model is
+then told decides the repair: a pre-registered control arm shows that the
+alarm that sign-off failed is worth no more than raw tool text, while
+interpretation adds $14.6$ points over the alarm and escalation $19.7$.
+Interpretation beats raw text by $14.1$ points with about $23\%$ fewer calls
+and tokens, escalation reaches the highest sign-off clean rate, and repaired
+leaves restore synthesis of whole router meshes and of the processor top. The
+benefit is largest on small models; at $32$B and on two API models any tool
+feedback suffices, but the guard is still needed. In a
 nutshell, STITCH is best understood as a deterministic sign-off guard and
@@ Directions
 immediate follow-ups from the case study are a held-out set of real defects to
-test the upgraded vocabulary out of sample, a control arm that separates
-escalation's generic sign-off message from the interpreter's contribution, and
+test the upgraded vocabulary out of sample, a directive that defaults to the
+value the specification defines rather than a constant, and
 integration-level feedback for defects that exist only when modules are
```

## Figures (new files; the old `fig_p3_*` are kept and are no longer used by v8)

| File | Content | Source |
|---|---|---|
| `fig_p3_v2_clean_by_condition.png` | sign-off clean by condition, sim-silent vs sim-visible, six models, six conditions | `phase3/evidence/phase3_final/figures/` |
| `fig_p3_v2_clean_by_call.png` | cumulative sign-off clean by LLM call | same |
| `fig_p3_v2_composition.png` | composition with the `baseline_gate` column (used in `PHASE3_MPSOC_v2.tex`) | same |
| `fig_p3_v2_by_model.png` | alarm, raw, v3, escalation by model (used in `PHASE3_MPSOC_v2.tex`) | same |

All four come from `phase3_figures.make_v2`, called by `python phase3/runner/analyze_phase3.py --final ...`. A sixth
categorical slot, `#008300`, is used for `baseline_gate`; the six-slot palette passes the palette validator.

## Deviations from the brief

1. **The composition figure is not in Section 9.** With it, Section 9 grew by 1.95 pages; the brief allows about
   1.5. Table 11 carries the same numbers, and the figure, with the gate column, is in `PHASE3_MPSOC_v2.tex`.
   Section 9 now grows by 1.59 pages.
2. **Contrast 3's per-stratum rows** are in `PHASE3_MPSOC_v2.tex` (Table 5), not in Section 9's Table 10. Section 9
   keeps all four contrasts pooled, and the strata for contrasts 1 and 2.
3. **PHASE3_MPSOC.** Following the user's instruction to label updated files v2, it is written as a new file,
   `PHASE3_MPSOC_v2.tex`. `PHASE3_MPSOC.tex` (version 1) is untouched. v2 compiles with 0 undefined references; its
   two overfull boxes are under 5 pt (long model names).

## Could not be sourced from a file

Nothing. Every Phase 3 number in v8 Sections 9-10 and in `PHASE3_MPSOC_v2.tex` is listed below with its line. The
numbers kept verbatim from v7 point at `phase3/evidence/phase3_run/PHASE3_RESULTS.md`; they are in 9.1-9.3,
Table 8, the pilot, "1.7 times", the leaf-to-bound 32/32 and 27/27, and the v3 coverage paragraph.

## Numbers and their sources (generated by paper/make_v8_changes.py)

Each source line below was located by the script and checked to contain the quoted values. Prefix (everything before the Section 9 heading): SHA-256 v7 `d16a6332d4354ef60178b985b9fc339e526030519ef78233369db6c2d0652af0`, v8 `6326c979e03cf90c9ffe66e55a6276403102301cc6b4a4023b09dc4ef1b44f4b`; outside the abstract and the header comment the two prefixes are byte-identical.

| Where | Number(s) as printed | Source (file:line) |
|---|---|---|
| S9 intro, 9.4, Table 9, S10: first 990 runs | 990 | `phase3/evidence/PREREG_FINAL.md`:11 |
| S9 intro, 9.4: control arm | 198 | `phase3/evidence/PREREG_FINAL.md`:12 |
| S9 intro, 9.4: 32B arm; 1,386 = 990 + 198 + 198 | 198; 1,386 | `phase3/evidence/PREREG_FINAL.md`:13 |
| S9 intro, 9.4: API runs (396 = 2 x 198) | 396; 198 each | `phase3/evidence/phase3_final/PAPER_NUMBERS.md`:68 |
| 9.4: pre-registration hash | 1b6eb915 | `phase3/evidence/FREEZE_FINAL.md`:11 |
| 9.4: backend check, identical first responses | 41% vs 41% | `phase3/evidence/phase3_final/backend_check_output.txt`:2 |
| MPSOC 5: backend check, identical prompts | 90/90 | `phase3/evidence/phase3_final/backend_check_output.txt`:1 |
| MPSOC 5: backend check, first-call func_pass | 42/90 vs 44/90 | `phase3/evidence/phase3_final/backend_check_output.txt`:3 |
| 9.4: nine other tasks equivalent; no tied-off output | (no number) | `phase3/evidence/FREEZE_FINAL.md`:98 |
| 9.4: cell bootstrap over 66 cells, 1.7 x Wilson (unchanged v7 sentence) | 66; 1.7 | `phase3/evidence/phase3_run/PHASE3_RESULTS.md`:19 |
| Table 9 baseline | 22% (17 to 28) [23%]; 63%; 85%; 1.34; 1,425 | `phase3/evidence/phase3_final/PAPER_NUMBERS.md`:9 |
| Table 9 raw_adv | 53% (46 to 59) [59%]; 12%; 65%; 3.27; 4,396 | `phase3/evidence/phase3_final/PAPER_NUMBERS.md`:10 |
| Table 9 v2 | 63% (56 to 69) [68%]; 8%; 71%; 2.83; 3,831 | `phase3/evidence/phase3_final/PAPER_NUMBERS.md`:11 |
| Table 9 v3 | 67% (60 to 73) [74%]; 8%; 74%; 2.51; 3,377 | `phase3/evidence/phase3_final/PAPER_NUMBERS.md`:12 |
| Table 9 esc | 72% (65 to 78) [80%]; 13%; 85%; 2.99; 3,798 | `phase3/evidence/phase3_final/PAPER_NUMBERS.md`:13 |
| Table 9 gate | 52% (45 to 59) [56%]; 15%; 67%; 3.39; 3,835 | `phase3/evidence/phase3_final/PAPER_NUMBERS.md`:14 |
| (1) baseline 125/198 signed off defective; all 108 sim-silent | 125/198 (63%); 108 | `phase3/evidence/phase3_final/PAPER_NUMBERS.md`:18 |
| (1) 18/18 sim-silent signed off, qwen2.5-coder:32b | 18/18 | `phase3/evidence/phase3_final/PAPER_NUMBERS.md`:58 |
| (1) 18/18 sim-silent signed off, claude-haiku-4.5 | 18/18 | `phase3/evidence/phase3_final/PAPER_NUMBERS.md`:69 |
| (1) 18/18 sim-silent signed off, gpt-4.1-mini | 18/18 | `phase3/evidence/phase3_final/PAPER_NUMBERS.md`:75 |
| (1) latch-free 24% -> 88% (Yosys only, oracle-independent); MPSOC also 65% gate | 24%; 88%; 35/144; 127/144; 94/144 | `phase3/evidence/phase3_final/PAPER_NUMBERS.md`:34 |
| (2) Table 10 contrast 1, all | +19.7 [+11.1, +29.3]; <0.001; 42/3; as run +23.7 | `phase3/evidence/phase3_final/PHASE3_FINAL.md`:102 |
| (2) Table 10 contrast 1, sim-silent | +23.1 [+11.1, +37.0]; 0.002; 27/2 | `phase3/evidence/phase3_final/PHASE3_FINAL.md`:103 |
| (2) Table 10 contrast 1, sim-visible | +15.6 [+4.4, +27.8]; 0.022; 15/1 | `phase3/evidence/phase3_final/PHASE3_FINAL.md`:104 |
| (2) Table 10 contrast 2, all | +14.6 [+3.0, +26.3]; 0.021; 43/14; as run +17.7 | `phase3/evidence/phase3_final/PHASE3_FINAL.md`:105 |
| (2) Table 10 contrast 2, sim-silent | +23.1 [+6.5, +39.8]; 0.014; 31/6 | `phase3/evidence/phase3_final/PHASE3_FINAL.md`:106 |
| (2) Table 10 contrast 2, sim-visible | +4.4 [-11.1, +20.0]; 0.688; 12/8 | `phase3/evidence/phase3_final/PHASE3_FINAL.md`:107 |
| (2) Table 10 contrast 3, all | -0.5 [-9.1, +8.1]; 1.000; 16/17 | `phase3/evidence/phase3_final/PHASE3_FINAL.md`:108 |
| MPSOC Table 5 contrast 3, sim-silent | -2.8 [-13.0, +7.4]; 0.738; 6/9 | `phase3/evidence/phase3_final/PHASE3_FINAL.md`:109 |
| MPSOC Table 5 contrast 3, sim-visible | +2.2 [-11.1, +15.6]; 0.882; 10/8 | `phase3/evidence/phase3_final/PHASE3_FINAL.md`:110 |
| (2) Table 10 contrast 4, sim-visible | -1.1 [-4.4, +2.2]; 1.000; 2/3 | `phase3/evidence/phase3_final/PHASE3_FINAL.md`:111 |
| (2) pre-registered reading R1 | R1 | `phase3/evidence/phase3_final/PHASE3_FINAL.md`:113 |
| (2) processor-level sensitivity, contrast 1 | +24.2 [+14.6, +34.3] | `phase3/evidence/phase3_final/PHASE3_FINAL.md`:121 |
| (2) processor-level sensitivity, contrast 2 | +19.7 [+7.6, +32.3] | `phase3/evidence/phase3_final/PHASE3_FINAL.md`:124 |
| MPSOC Table 6: sensitivity contrast 3 (both views) | -3.0 [-12.1, +6.1] | `phase3/evidence/phase3_final/PHASE3_FINAL.md`:127 |
| MPSOC Table 6: sensitivity contrast 4 (both views) | -2.2 [-7.8, +3.3] | `phase3/evidence/phase3_final/PHASE3_FINAL.md`:130 |
| (2) ladder: alarm 52% plateau from call 3 (50%) to call 6 (52%) | 50%; 52% | `phase3/evidence/phase3_final/PHASE3_FINAL.md`:312 |
| (2) escalation climbs 56% -> 72% | 56%; 72% | `phase3/evidence/phase3_final/PHASE3_FINAL.md`:311 |
| (2) sim-silent loop pass at end: alarm 80/108 | 80/108 | `phase3/evidence/phase3_final/PHASE3_FINAL.md`:85 |
| (2) sim-silent loop pass at end: escalation 97/108 | 97/108 | `phase3/evidence/phase3_final/PHASE3_FINAL.md`:84 |
| (2) would_fire: 95 failed, all 95 would fire, 38 on returned RTL; 103 clean | 95; 95; 38; 103 | `phase3/evidence/phase3_final/PHASE3_FINAL.md`:246 |
| (2) per model llama3.2:3b +39.4, Holm 0.006 | +39.4; 0.006; 19/33 vs 6/33 | `phase3/evidence/phase3_final/PHASE3_FINAL.md`:161 |
| (2) per model gemma3:4b +33.3, Holm 0.006 | +33.3; 0.006; 17/33 vs 6/33 | `phase3/evidence/phase3_final/PHASE3_FINAL.md`:162 |
| MPSOC: esc - gate deepseek-coder:6.7b | +12.1 | `phase3/evidence/phase3_final/PHASE3_FINAL.md`:163 |
| MPSOC: esc - gate qwen2.5-coder:7b | +18.2 | `phase3/evidence/phase3_final/PHASE3_FINAL.md`:164 |
| MPSOC: esc - gate llama3.1:8b | +9.1 | `phase3/evidence/phase3_final/PHASE3_FINAL.md`:165 |
| MPSOC: esc - gate qwen2.5-coder:14b | +6.1 | `phase3/evidence/phase3_final/PHASE3_FINAL.md`:166 |
| MPSOC: esc - gate noc_xbar4 = 0 (the only non-positive task) | +0.0 | `phase3/evidence/phase3_final/PHASE3_FINAL.md`:196 |
| (3) v3 - raw: 132 vs 104, +14.1 [+3.5, +24.7], p 0.014, 40/12 | 132/198; 104/198; +14.1; 0.014; 40/12 | `phase3/evidence/phase3_final/PHASE3_FINAL.md`:141 |
| (3) v2 - raw: +10.1 [+2.0, +18.7], p 0.030 | +10.1; 0.030 | `phase3/evidence/phase3_final/PHASE3_FINAL.md`:138 |
| (3) about 23% fewer calls and tokens (also S10) | -23.3%; -23.2% | `phase3/evidence/phase3_final/PAPER_NUMBERS.md`:23 |
| (3) tokens per sign-off clean pass | 5,066; 8,370 | `phase3/evidence/phase3_final/PAPER_NUMBERS.md`:25 |
| (3) clean after the first call 55 / 41 / 15%; MPSOC also 40% gate, 42% esc | 55%; 41%; 15%; 40%; 42% | `phase3/evidence/phase3_final/PAPER_NUMBERS.md`:27 |
| (3) 3B +24.2 | +24.2 (13/33 vs 5/33) | `phase3/evidence/phase3_final/PAPER_NUMBERS.md`:29 |
| (3) qwen2.5-coder:7b +27.3 | +27.3 (30/33 vs 21/33) | `phase3/evidence/phase3_final/PAPER_NUMBERS.md`:31 |
| (3) 14B at 30/33 either | 30/33 | `phase3/evidence/phase3_final/PAPER_NUMBERS.md`:33 |
| MPSOC: per-model v3/raw for gemma3:4b, deepseek, llama3.1 | 15/6; 25/24; 19/18 | `phase3/evidence/phase3_final/PAPER_NUMBERS.md`:86 |
| MPSOC Table 7: v3 - raw sim-silent / sim-visible | +20.4; +6.7 | `phase3/evidence/phase3_final/PHASE3_FINAL.md`:142 |
| MPSOC Table 7: v3 - raw sim-visible | +6.7 [-7.8, +21.1]; 0.474 | `phase3/evidence/phase3_final/PHASE3_FINAL.md`:143 |
| MPSOC Table 7: v3 - v2 | +4.0 [-4.0, +12.1]; 0.408 | `phase3/evidence/phase3_final/PHASE3_FINAL.md`:144 |
| MPSOC Table 7: esc - v3 | +5.1 [-2.0, +12.6]; 0.255 | `phase3/evidence/phase3_final/PHASE3_FINAL.md`:147 |
| MPSOC Table 7: esc - raw | +19.2 [+9.6, +28.8]; <0.001 | `phase3/evidence/phase3_final/PHASE3_FINAL.md`:150 |
| MPSOC Table 8: tokens per sign-off clean (all conditions) | 6,562; 8,370; 6,117; 5,066; 5,295; 7,372 | `phase3/evidence/phase3_final/PHASE3_FINAL.md`:69 |
| (4) tool rounds 47.5% fewer than v3 | 47.5% | `phase3/evidence/phase3_final/PAPER_NUMBERS.md`:35 |
| (4) esc - baseline sim-visible +14.4, 56/90 vs 43/90, p 0.048; as run +23.3 | +14.4 [+3.3, +27.8]; 0.048; +23.3 | `phase3/evidence/phase3_final/PHASE3_FINAL.md`:153 |
| (4) llama3.2:3b sim-visible 7 / 1 / 8 of 15 | 7/15; 1/15; 8/15 | `phase3/evidence/phase3_final/PAPER_NUMBERS.md`:39 |
| MPSOC: sim-visible deepseek 13/15, qwen7b 12/15 vs baseline 9/15 | 13/15; 12/15; 9/15 | `phase3/evidence/phase3_final/PAPER_NUMBERS.md`:87 |
| MPSOC: escalated vs not (109 -> 100; 89 -> 42) | 109; 100; 89; 42 | `phase3/evidence/phase3_final/PAPER_NUMBERS.md`:91 |
| (5) Table 11 2x2 mesh | 0 / 15 / 13 / 16 / 18 / 11 of 18 | `phase3/evidence/phase3_final/PAPER_NUMBERS.md`:94 |
| (5) Table 11 3x3 mesh | 0 / 15 / 13 / 16 / 18 / 11 of 18 | `phase3/evidence/phase3_final/PAPER_NUMBERS.md`:95 |
| (5) Table 11 MPSoC top | 0 / 13 / 12 / 16 / 15 / 11 of 18; gate at bound 1 | `phase3/evidence/phase3_final/PAPER_NUMBERS.md`:96 |
| (5) leaf-clean => bound, 990 runs (unchanged v7 sentence) | 32/32; 32/32; 27/27 | `phase3/evidence/phase3_run/PHASE3_RESULTS.md`:33 |
| MPSOC: 32B composition 3/3 at bound | 3/3 | `phase3/evidence/phase3_final/PAPER_NUMBERS.md`:99 |
| (6) Table 12 qwen2.5-coder:32b rows | 12(0/12) 28(16/12) 30(18/12) x4; tokens 663..1,850 | `phase3/evidence/phase3_final/PAPER_NUMBERS.md`:63 |
| (6) Table 12 qwen2.5-coder:32b tool rows | 30 (18/12); 1,492; 1,655; 1,660; 1,850 | `phase3/evidence/phase3_final/PAPER_NUMBERS.md`:62 |
| (6) Table 12 gpt-4.1-mini gate row | 28 (16/12); 1,529 | `phase3/evidence/phase3_final/PAPER_NUMBERS.md`:80 |
| (6) Table 12 gpt-4.1-mini v3 row | 30 (18/12); 1,257 | `phase3/evidence/phase3_final/PAPER_NUMBERS.md`:78 |
| (6) Table 12 claude-haiku-4.5 gate row | 30 (18/12); 1,099 | `phase3/evidence/phase3_final/PAPER_NUMBERS.md`:74 |
| (6) Table 12 claude-haiku-4.5 esc row | 30 (18/12); 1,101 | `phase3/evidence/phase3_final/PAPER_NUMBERS.md`:73 |
| (6) every 32B miss outside baseline is Address_select, plus 2 alarm runs on riscv_alu_flags | 3 each; 2 | `phase3/evidence/phase3_final/PAPER_NUMBERS.md`:64 |
| (6) every API miss outside baseline is Address_select, plus 2 alarm runs (gpt-4.1-mini) on riscv_alu_flags | 3 each; 2 | `phase3/evidence/phase3_final/PAPER_NUMBERS.md`:81 |
| MPSOC: 7-model pool esc - gate | +17.7 [+10.4, +25.6] | `phase3/evidence/phase3_final/PHASE3_FINAL.md`:351 |
| MPSOC: 7-model pool v3 - gate | +13.4 [+3.5, +23.8] | `phase3/evidence/phase3_final/PHASE3_FINAL.md`:354 |
| (7) focus tasks 42/72 -> 50/72 under sign-off | 42/72; 50/72 | `phase3/evidence/phase3_final/PAPER_NUMBERS.md`:41 |
| (7) +11.1, CI [-9.7, +31.9] (unchanged v7 numbers; tasks unaffected by the oracle) | +11.1; -9.7; +31.9 | `phase3/evidence/phase3_run/PHASE3_RESULTS.md`:27 |
| (7) 18/18 fired; 3/18 -> 15/18 interpreter-credited (unchanged v7 numbers) | 18/18; 3/18; 15/18 | `phase3/evidence/phase3_run/PHASE3_RESULTS.md`:27 |
| (8) mem_wb_mux: 16 loop-clean repairs violate the spec | 16 | `phase3/evidence/FREEZE_FINAL.md`:91 |
| (8) Address_select: 41 loop-clean repairs set J_addr = 0 | 41 | `phase3/evidence/FREEZE_FINAL.md`:92 |
| (8) gap runs with advice: v2 8 of 8 | 8; 8 | `phase3/evidence/phase3_final/PHASE3_FINAL.md`:258 |
| (8) gap runs with advice: v3 12 of 12 | 12; 12 | `phase3/evidence/phase3_final/PHASE3_FINAL.md`:260 |
| (8) gap runs with advice: esc 11 of 11 | 11; 11 | `phase3/evidence/phase3_final/PHASE3_FINAL.md`:262 |
| (8) gap runs without advice: baseline 3 | 3; 0 | `phase3/evidence/phase3_final/PHASE3_FINAL.md`:254 |
| (8) gap runs without advice: raw 7 | 7; 0 | `phase3/evidence/phase3_final/PHASE3_FINAL.md`:256 |
| (8) gap runs without advice: alarm 2 | 2; 0 | `phase3/evidence/phase3_final/PHASE3_FINAL.md`:264 |
| MPSOC Table 13: mem_wb_mux gap runs raw 6 (0), v2 3 (3), v3 2 (2), esc 5 (0), gate 6 (0) | 6/3/2/5/6 | `phase3/evidence/phase3_final/PHASE3_FINAL.md`:282 |
| MPSOC: mem_wb_mux advice reached all 11 sign-off clean v2 runs | 11/11 | `phase3/evidence/phase3_final/PHASE3_FINAL.md`:283 |
| MPSOC Table 12: audit ni_flit_pack / noc_xbar4 / registers | 36; 47; 69; 66 | `phase3/evidence/FREEZE_FINAL.md`:94 |
| MPSOC 6.1: sim-silent sign-off clean raw 64 / v2 83 / v3 86 / esc 86 / gate 61 (of 108) | 64; 83; 86; 86; 61 | `phase3/evidence/phase3_final/PHASE3_FINAL.md`:85 |
| MPSOC 6.1: sim-visible sign-off clean baseline 43 / raw 40 / v2 41 / v3 46 / esc 56 / gate 42 (of 90) | 43; 40; 41; 46; 56; 42 | `phase3/evidence/phase3_final/PHASE3_FINAL.md`:96 |
| MPSOC Table 9 (per task): Address_select | row | `phase3/evidence/phase3_final/PHASE3_FINAL.md`:400 |
| MPSOC Table 9 (per task): MuxPC | row | `phase3/evidence/phase3_final/PHASE3_FINAL.md`:401 |
| MPSOC Table 9 (per task): execute_mux | row | `phase3/evidence/phase3_final/PHASE3_FINAL.md`:402 |
| MPSOC Table 9 (per task): mem_wb_mux | row | `phase3/evidence/phase3_final/PHASE3_FINAL.md`:403 |
| MPSOC Table 9 (per task): mux3 | row | `phase3/evidence/phase3_final/PHASE3_FINAL.md`:404 |
| MPSOC Table 9 (per task): ni_flit_pack | row | `phase3/evidence/phase3_final/PHASE3_FINAL.md`:405 |
| MPSOC Table 9 (per task): noc_xbar4 | row | `phase3/evidence/phase3_final/PHASE3_FINAL.md`:406 |
| MPSOC Table 9 (per task): register_1bit | row | `phase3/evidence/phase3_final/PHASE3_FINAL.md`:407 |
| MPSOC Table 9 (per task): register_32bit | row | `phase3/evidence/phase3_final/PHASE3_FINAL.md`:408 |
| MPSOC Table 9 (per task): register_4bit | row | `phase3/evidence/phase3_final/PHASE3_FINAL.md`:409 |
| MPSOC Table 9 (per task): riscv_alu_flags | row | `phase3/evidence/phase3_final/PHASE3_FINAL.md`:410 |
| MPSOC Table 4 (would_fire): Address_select | row | `phase3/evidence/phase3_final/PHASE3_FINAL.md`:190 |
| MPSOC Table 4 (would_fire): MuxPC | row | `phase3/evidence/phase3_final/PHASE3_FINAL.md`:191 |
| MPSOC Table 4 (would_fire): execute_mux | row | `phase3/evidence/phase3_final/PHASE3_FINAL.md`:192 |
| MPSOC Table 4 (would_fire): mem_wb_mux | row | `phase3/evidence/phase3_final/PHASE3_FINAL.md`:193 |
| MPSOC Table 4 (would_fire): mux3 | row | `phase3/evidence/phase3_final/PHASE3_FINAL.md`:194 |
| MPSOC Table 4 (would_fire): ni_flit_pack | row | `phase3/evidence/phase3_final/PHASE3_FINAL.md`:195 |
| MPSOC Table 4 (would_fire): noc_xbar4 | row | `phase3/evidence/phase3_final/PHASE3_FINAL.md`:196 |
| MPSOC Table 4 (would_fire): register_1bit | row | `phase3/evidence/phase3_final/PHASE3_FINAL.md`:197 |
| MPSOC Table 4 (would_fire): register_32bit | row | `phase3/evidence/phase3_final/PHASE3_FINAL.md`:198 |
| MPSOC Table 4 (would_fire): register_4bit | row | `phase3/evidence/phase3_final/PHASE3_FINAL.md`:199 |
| MPSOC Table 4 (would_fire): riscv_alu_flags | row | `phase3/evidence/phase3_final/PHASE3_FINAL.md`:200 |
| MPSOC Table 10 (upgrade): fired counts v2/v3 (unchanged v7 table; oracle-independent) | 0/18; 18/18 | `phase3/evidence/phase3_run/PHASE3_RESULTS.md`:27 |
| MPSOC 7: keep-best, 23 of 198 (v3) and 11 (esc) lost a simulation pass (990 runs, loop testbench) | 23; 11 | `phase3/evidence/phase3_run/phase3_tables.md`:227 |
| MPSOC 7: keep-best, escalation 11 | 11 | `phase3/evidence/phase3_run/phase3_tables.md`:228 |
| Abstract: 8% signed off defective with the interpreter (v3; v2 also 8%) | 8% | `phase3/evidence/phase3_final/PAPER_NUMBERS.md`:12 |
| Abstract: control-arm CIs | +3.0 to +26.3; +11.1 to +29.3 | `phase3/evidence/phase3_final/PHASE3_FINAL.md`:102 |
| Abstract: interpretation vs raw | 14.1; +3.5 to +24.7 | `phase3/evidence/phase3_final/PHASE3_FINAL.md`:141 |
| 9.6, S10: 14.6 over the alarm, 19.7 for escalation; 14.1 over raw; 63%; 72% | 14.6; 19.7; 14.1; 63%; 72% | `phase3/evidence/phase3_final/PHASE3_FINAL.md`:105 |
