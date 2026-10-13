# Abstract and introduction patch for STITCH_EXT_v8.tex

**Status (2026-09-30).** Items 1 (abstract, full version) and 3 (header comment) have been applied to
`STITCH_EXT_v8.tex` on the user's instruction. Item 2 (roadmap sentence) has not been applied.

v8 keeps the abstract and Sections 1-8 byte-identical to v7, so these still quote the first write-up's Phase 3
numbers. Below is every place before Section 9 that quotes Phase 3, with the exact old text and a proposed
replacement. Each new number comes from `phase3/evidence/phase3_final/PHASE3_FINAL.md` or `PAPER_NUMBERS.md`, with
source lines in `V8_CHANGES.md`. A search of the v8 prefix for 990, 62, 1%, 14.6, 23%, 80%, MPSoC and Phase~3 finds
these places only: the abstract sentence (1), the roadmap sentence (2) and the header comment (3). Line 652
("The Phase~3 experiment of Section~\ref{sec:mpsoc} uses one shared budget for every condition") and line 946
("Section~\ref{sec:mpsoc} takes STITCH there.") quote no number and stay as they are.

## 1. Abstract (v8 lines 94-104): required

Old:

```latex
established where the interpreter acts, we asked whether STITCH is useful on
real hardware, and found that it catches the defects a simulation-only loop
signs off. On an independently developed RISC-V MPSoC with a mesh
network-on-chip ($990$ runs, six models from $3$B to $14$B), a
simulation-only repair loop signs off $62\%$ of its runs with synthesis defects
intact, and STITCH brings that to $1\%$; interpreting the lint and synthesis
output beats showing it raw by $14.6$ points (cell-level $95\%$ CI $+3.5$ to
$+26.3$) with about $23\%$ fewer model calls and tokens; escalation reaches the
highest clean pass rate ($80\%$); and the repaired leaf modules restore
top-level synthesis of $4$- and $9$-router meshes, which simulation-only
repair never achieves.
```

New:

```latex
established where the interpreter acts, we asked whether STITCH is useful on
real hardware, and found that it catches the defects a simulation-only loop
signs off. On an independently developed RISC-V MPSoC with a mesh
network-on-chip ($1{,}386$ runs, seven models from $3$B to $32$B, scored by a
specification-complete sign-off testbench), a simulation-only repair loop
signs off $63\%$ of its runs with defects intact, including every
simulation-silent defect at every model size tested, against $8\%$ with the
interpreter. A pre-registered control arm shows that the gain comes from what
the model is told, not from the alarm that sign-off failed: the alarm alone is
worth no more than raw tool text, while interpreted feedback adds $14.6$ points
over it and escalation $19.7$ (cell-level $95\%$ CIs $+3.0$ to $+26.3$ and
$+11.1$ to $+29.3$). Interpreting the lint and synthesis output beats showing
it raw by $14.1$ points (CI $+3.5$ to $+24.7$) with about $23\%$ fewer model
calls and tokens; escalation reaches the highest sign-off clean rate ($72\%$);
and the repaired leaf modules restore top-level synthesis of $4$- and
$9$-router meshes, which simulation-only repair never achieves.
```

| Number | Old | New | Source |
|---|---|---|---|
| runs | 990 | 1,386 (990 + 198 + 198) | PREREG_FINAL.md table |
| models | six, 3B to 14B | seven, 3B to 32B (six + qwen2.5-coder:32b) | PREREG_FINAL.md table |
| signed off defective, baseline | 62% (silent structural pass) | 63% (125/198) | PAPER_NUMBERS.md Table 9 |
| with STITCH | 1% (v3 silent structural pass) | 8% (v3 signed off defective, 15/198) | PAPER_NUMBERS.md Table 9 |
| alarm vs interpretation | not in v7 | +14.6 [+3.0, +26.3]; escalation +19.7 [+11.1, +29.3] | PHASE3_FINAL.md primary table |
| interpretation vs raw | +14.6 [+3.5, +26.3] | +14.1 [+3.5, +24.7] | PHASE3_FINAL.md restated table |
| fewer calls and tokens | about 23% | about 23% (unchanged; −23.3% calls, −23.2% tokens) | PAPER_NUMBERS.md |
| escalation clean rate | 80% | 72% (sign-off clean) | PAPER_NUMBERS.md Table 9 |

A shorter variant, if the abstract must not grow: keep the v7 sentence, replace "$990$ runs, six models from $3$B
to $14$B" with "$1{,}386$ runs, seven models from $3$B to $32$B", "$62\%$" with "$63\%$", "$1\%$" with "$8\%$",
"$14.6$ points (cell-level $95\%$ CI $+3.5$ to $+26.3$)" with "$14.1$ points (cell-level $95\%$ CI $+3.5$ to
$+24.7$)" and "($80\%$)" with "($72\%$)". Then add one clause: "; a pre-registered control arm shows the gain comes
from the interpreter's detail, not from the alarm that sign-off failed ($+19.7$ points for escalation over the alarm
alone)".

## 2. Roadmap (v8 lines 147-149): optional

Old:

```latex
Section~\ref{sec:mpsoc} then asks whether STITCH is useful on a real
multiprocessor design, and how the interpreter can be kept robust as it meets
new code and new tool versions.
```

New:

```latex
Section~\ref{sec:mpsoc} then asks whether STITCH is useful on a real
multiprocessor design, whether its gain comes from the interpreter's detail or
from the alarm that sign-off failed, and how the interpreter can be kept
robust as it meets new code and new tool versions.
```

## 3. Header comment (v8 lines 3 and 14-33): optional, not rendered

The header still says "REFERENCE DRAFT v7", describes Section 9 as "990 runs", and lists `fig_p3_*.png (3 used
here)` and `PHASE3_MPSOC.tex`. Suggested:
- line 3: `% Journal-extension draft (REFERENCE DRAFT v8)`;
- after line 21, add `% v8 rewrites Section 9 for the final Phase 3 batch (control arm, 32B, API rows, sign-off
  oracle; 1,386 cluster runs) and the Phase 3 items of Section 10; see V8_CHANGES.md.`;
- line 30: `fig_p3_v2_*.png (2 used here) <- phase3/evidence/phase3_final/figures/`;
- line 32: `PHASE3_MPSOC_v2.tex`.

This changes the prefix hash, so apply it together with the abstract patch.
