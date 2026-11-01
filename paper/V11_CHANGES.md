# Paper v11: how the narrative was drafted, and what changed from v10

v11 is `paper/main.tex`, the single working copy of the journal paper from now on: **14 pages including references,
no supplement**. Its figures are `paper/figures/` (vector PDF). Build: `paper/README.md`. Date: 2026-10-30.

Every number in v11 is a number v10 already reported, from the same evidence files; no new result was added and no
result changed. What changed is the order, the words, the names, and what the paper explains itself instead of
leaving to a supplement. The one new quoted item is the motivating example (Section 2 below), taken from frozen real
tool logs already in the repository.

## 1. Where things went

| Item | v10 | v11 |
|---|---|---|
| Paper source | `paper/overleaf/main.tex` | `paper/main.tex` |
| Figures | `paper/overleaf/figures/` | `paper/figures/` (paper only) and `docs/figures/*.png` (paper + former supplement, for `docs/reSTITCH.md`) |
| Supplement | `paper/overleaf/supplement.tex` (S1 to S9, 14 pages) | none; its content is Part 15 of `docs/reSTITCH.md` |
| Figure script | `paper/make_v10_figures.py` | `paper/make_figures.py` (renamed; writes both folders) |
| Overleaf zip | `paper/STITCH_overleaf.zip` | `paper/STITCH_v11_overleaf.zip` (`main.tex`, `figures/`, `README.md`) |
| Change log | `paper/V10_CHANGES.md` | this file |
| Earlier drafts | `paper/archive/` (tracked) | `paper/archive/` (**gitignored, local only**); v10's build, zip, supplement and change log moved to `paper/archive/v10/`. v10 is in git history at commit `e77bf73` (`paper/overleaf/`) |

`phase2/frontier/make_numbers_set4.py` writes its macro blocks into the v10 files, now at
`paper/archive/v10/overleaf/`. v11 quotes its values as plain numbers, so it no longer depends on that script; run it
only to read the values (it prints every macro) or to rebuild v10.

## 2. How the narrative was drafted

The brief: the paper must stand alone for a reader who has never seen the conference paper or the supplement, read
smoothly, carry fewer numbers in the opening, and use plain technical vocabulary. The drafting followed one storyline:

1. **Start from the problem, not from STITCH.** v10 opened with "a language model that writes Verilog can be put in a
   loop". v11 opens with what simulation cannot see: a design that simulates is not a design that can be signed off.
   The motivating example is real, not constructed: `MuxPC`, the next-PC multiplexer of the hand-written RISC-V core,
   omits a select value that "does not occur in operation", passes its testbench, and synthesises to 32 latches
   (Figure 1: the RTL, what Icarus, Verilator and Yosys report, and the STITCH directive, all quoted from
   `phase3/tests/fixtures/real/mpsoc_MuxPC/` and the v3 interpreter's output on it). The next paragraph says why a
   silently shipped latch matters (glitches on its enable, paths through a level-sensitive element that can fail
   timing although simulation passes, test insertion) and lists the other sign-off failures the paper meets: two
   drivers on one net, an unmappable reset, width truncation. This motivation is deliberately different from the
   conference paper's (a weak model's enable multiplexer). It cites one new reference, Cummings, "full_case
   parallel_case, the Evil Twins of Verilog Synthesis" (SNUG 1999), for incomplete `case` statements as a known
   source of latches and simulation-synthesis mismatch. No result of the separate silicon (PPA) study in
   `SiliconComparision/` is used anywhere.
2. **Then the gap.** Repair loops such as AutoChip stop exactly when these defects become invisible. STITCH adds the
   checks a sign-off flow runs first and an interpreter that costs no model call. Its evidence was single runs.
3. **Then the questions,** and why the MPSoC answers the last one: it was written by hand for an earlier project
   within the group, independently of this study (the source is not named in the paper); its defects are natural, in
   leaf modules instantiated many times; and it lets us ask whether leaf repair restores whole-design synthesis.
4. **Claims, not bullet points.** The contribution bullets became five numbered claims, each a finding with its
   evidence and its section: C1 simulation-only repair signs off defective hardware at every model size; C2 the
   diagnosis, not the alarm, drives repair; C3 module-level repairs compose; C4 escalation preserves accuracy (with
   one restart) and saves tool calls; C5 on a testbench-scored benchmark the effect is small and model-dependent, and
   only replication shows it. Ordered by importance, not by section.
5. **Method once, early.** A new Section 4 gathers what every study shares: the study map (Table 4), one paragraph on
   N=3 and the statistics, and the harness hardening.
6. **Results in the order replication, RTLLM, MPSoC,** with the MPSoC told as a case study: what the design is, how
   hand-written code hides sign-off defects (three recurring patterns, each with its real module), the defect at scale,
   then the experiment and eight results.

## 3. What changed, item by item (against the brief)

**0. Motivation.** New opening (Section 2 above). The introduction now gives concrete sign-off failures.

**1. Abstract.** About 40% shorter. Kept: the 24% to 88% latch result and "nearly two-thirds" for simulation-only
sign-off. Removed: every confidence interval, the 16.6/27.6/88.6% series, run counts, the 14.1 and 19.7 point
contrasts and the 23% figure. The statistics are explained once, in Section 4.2, in one paragraph: why N=3, what a
Wilson interval and a cell-level bootstrap are, when a difference is called significant, and the `semantic_fired`
rule. Elsewhere intervals appear only where a claim rests on them.

**2 and 7. The MPSoC.** Section 7.1 rewritten as a story: the architecture (RV32 cores, network interfaces,
virtual-channel wormhole mesh), that it was hand-written in an FPGA flow (Vivado) for an earlier project, what was
changed for the open tools (compile-level only), how hand-written code hides sign-off defects (incomplete `case`/`if`,
an `always @(clr, ce)` register, a reset that depends on a synchronous clear), and the defect at scale (2,880 and 6,480
latch cells, the same two Yosys messages). The tasks table gained a "role in the design" column and plain origin and
testbench columns. "Conditions", "Models and pre-registration" and "Two oracles" became two readable paragraphs plus
two bold definitions (sign-off clean, signed off defective); the per-model Ollama list moved into Table 4.

**3. Contributions** became claims (Section 2, step 4).

**4. RTLLM study naming.** "Set 1, Set 2 (Twin), Set 3, Sets 4 and 4b" are gone from the paper. The studies are named
by what they ask: tiering and fine-tuning, small open models, larger open models, commercial models (recoverable and
floor tiers). The bullet list became Table 4, a study map: models as rows (grouped open and commercial), studies as
columns, with tasks, conditions (colour swatches), temperature and runs per study. "The fine-tuning twin" became
"Does Verilog Fine-Tuning Help? A Same-Base Comparison". Model names are written as their makers write them (Gemma 3
4B, Qwen2.5-Coder 32B, ...) instead of Ollama tags (`gemma3:4b`).

**Condition names.** The repository's code names (`baseline`, `baseline_gate`, `raw_adv`, `sem_adv`, `sem_escalate`,
`sem_escalate_restart`) became Baseline, Alarm, Raw, Interpret (v2/v3), Escalate and Escalate-R, set in small capitals
and defined in Table 2 with the colour each has in the figures. The figures were regenerated with the same names
(`paper/figstyle.py`, `LABEL` and `MODEL`). The mapping is in the header of `main.tex` and at the top of
`docs/reSTITCH.md`.

**5. Floor heat map removed** (v10 Figure 6), because Claude Haiku 4.5's floor runs are incomplete (143 of 228) and
the heat map needed projected values for its missing modules. The floor paragraph uses measured runs only and states
the coverage once. No `\proj` macro, dagger or projection remains in v11. The capability ladder (v10 Figure 5, now
Figure 6), with GPT-4.1 mini, Gemini 2.5 Flash and Claude Haiku 4.5, and the MPSoC ladder table (v10 Table 7, now
Table 8) are kept as they were. The note on a fourth commercial model dropped at its smoke test was removed; the pre-registration still records it. The heat map stays in `docs/reSTITCH.md`
(Part 9) for the record; to bring it back, complete Haiku's runs (`phase2/frontier/PENDING.md`).

**6. freq_divbyfrac.** No longer its own subsection (v10 8.4). It is a run-in paragraph inside Section 6.4 (the floor
tier), which first says what it is (one of the 19 floor modules, a divide-by-3.5 clock divider, and the only floor
module every commercial model fails in every run) and then why it fails (the specification's description of the
counter does not match its reference design). The full trace is in `docs/reSTITCH.md`, Part 15, G.

**8. Results, threats, conclusion.** Content unchanged; vocabulary simplified (simulation-silent instead of
sim-silent, condition names), each result's run-in title states the finding, a few repeated numbers were dropped
(they are in `docs/reSTITCH.md`), and the threats became one compact paragraph with run-in labels.

**9. Supplement removed.** Every former supplement table and figure is in `docs/reSTITCH.md` Part 15 (tables as
Markdown, figures as PNG in `docs/figures/`). The paper no longer cites "Supplementary Material" anywhere; where v10
deferred a detail to it, v11 either states the detail in one sentence or drops a number the argument does not need.

**10. Availability.** The pre-registration hashes and the `REPO_INDEX.md` pointer were removed; it now gives the
repository and says per-run logs are available on request. The hashes remain in `phase3/evidence/PREREG_FINAL.md`,
`phase2/frontier/SET4_PREREG.md` and `phase2/frontier/p3_api/P3_API_PREREG.md`.

**Look.** ACM journal manner on the article class (kept so the page count stays controllable and Overleaf compiles in
one click): sans-serif headings with sections in capitals, ACM purple and dark-blue link colours, small-caps condition
names with colour swatches matching the figures, a code listing for Figure 1, Times text. Captions were shortened to
the takeaway.

## 4. Figures in v11

| Fig. | Content | File(s) | Change from v10 |
|---|---|---|---|
| 1 | Motivating example: `MuxPC` RTL, tool reports, STITCH directive | LaTeX listings | new |
| 2 | MPSoC teaser (signed off defective; latch-bearing tasks; top-level synthesis) | `fig_teaser_a/b/c.pdf` | condition names |
| 3 | The STITCH loop | TikZ | labels |
| 4 | Escalation policies, beside Table 3 | TikZ | labels |
| 5 | Small open models: pass rate by tier; tool calls | `fig_set1_tiers.pdf`, `fig_set1_calls.pdf` | condition names |
| 6 | Capability ladder; always-on deficit | `fig_ladder.pdf`, `fig_deficit.pdf` | model names, legend, 0.3 in shorter |
| 7 | Latch defect at scale; top-level synthesis by condition | `fig_latch_scale.pdf`, `fig_compose.pdf` | condition names |
| 8 | MPSoC: sign-off clean by task type; by model call | `fig_p3_stratum.pdf`, `fig_p3_bycall.pdf` | condition names, 0.15 in shorter |
| - | v10 Figure 6, floor heat map | `docs/figures/fig_floor_heatmap_v10.png` only | removed from the paper |

Tables: 1 interpreter rules; 2 feedback conditions (new); 3 in-house cost; 4 study map (new); 5 MPSoC tasks; 6 MPSoC
by condition; 7 pre-registered contrasts; 8 larger and commercial models in the MPSoC study. v10's Table 2 (the two
replicated illustrations) is now two sentences in Section 5.

## 5. Build check

`latexmk -pdf main.tex` in `paper/`: 14 pages, 0 errors, 0 warnings, 0 overfull or underfull boxes, 0 undefined
references. Every page was inspected visually after the last edit.

## 6. For co-authors making tweaks

- Edit `paper/main.tex` only. Keep the condition macros (`\Base`, `\Alarm`, `\Raw`, `\Interp`, `\Itwo`, `\Ithree`,
  `\Esc`, `\EscR`) so the names stay consistent.
- A number you change must match its evidence file (`REPO_INDEX.md`, "Canonical evidence for each part of the paper").
- To change a plot, edit `paper/make_figures.py` (or the shared style in `paper/figstyle.py`) and run
  `python -B paper/make_figures.py`; then re-zip `paper/STITCH_v11_overleaf.zip` if you use Overleaf.
- The page budget is 13 to 14 pages; the build is at 14 and the last page is now full, so any addition needs an
  equal cut.

## 7. Corrections after the first read (2026-11-01)

- **Tier definition (a factual fix).** v10 and the first v11 said each module is tiered by its *highest* Baseline pass
  rate in the tiering study. The code (`phase2/twin_analysis_SET2/categorize.py`) has always used the *pooled* count
  over the module's 15 tiering runs (five configurations x three): ceiling 12 to 15, recoverable 3 to 11, floor 0 to
  2. A maximum of per-configuration rates could never give "12 of 15". Section 6.1 now says so; no tier, module or
  number changes. Fixed in the same way in `docs/reSTITCH.md`, `docs/PHASES_EXPLAINED.md` and the Q&A.
- **C2** states the two rates (Alarm 52%, Escalate-R 72%) instead of "about 20 points".
- **C5** names its "two first readings" (a harmful effect at scale; an escalation win on larger models).
- **Table 4 caption** says what a dot means; **Table 5 caption** says the dot marks the stricter sign-off testbench.
- **Threats:** "one temperature per study"; a new run-in, *Scope*: no timing analysis or test insertion was run.
- **Cummings (1999)** checked: the SNUG Boston 1999 paper exists with this title, author, venue and year.
- **Condition names** are kept as they are, by the authors' decision.
- **Section 6.4:** the sentence on Claude Haiku 4.5's incomplete floor runs (143 of 228, account credit) was removed
  by the authors; Threats still states that Haiku is incomplete on the floor tier.
- `docs/reSTITCH_REVISITED_QA.md` now follows v11 (order, names, figure and table numbers), with a guide to every
  table and new questions on Figure 1, the claims, Tables 4 and 5, and a review-panel part.
