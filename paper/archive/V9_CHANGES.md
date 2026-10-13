# STITCH_EXT_v8.tex -> STITCH_EXT_v9.tex (and the new supplement)

Written 2026-10-13. v8 is kept unchanged. New files:

| File | What it is |
|---|---|
| `STITCH_EXT_v9.tex` | the journal paper, v9 |
| `STITCH_EXT_supplement.tex` | Supplementary Material S1 to S9 (folds in `PHASE3_MPSOC_v2.tex`, updated) |
| `numbers_set4.tex` | generated Set 4 / 4b macros (`python -B phase2/frontier/make_numbers_set4.py`) |
| `tables_set4.tex` | generated Set 4 / 4b tables for S6 (same command) |
| `make_v9_figures.py` | generates `figures/fig_v9_set1_tiers`, `fig_v9_ladder_deficit`, `fig_v9_p3` (`.pdf` and `.png`) |
| `v9_number_sources.py`, `v9_number_sources.md` | locates the source line of every new or changed number (table below) |
| `figures/fig_p3_api_ladder_signoff.png` | copy of `phase2/results/p3_api/analysis/fig_p3_api_ladder_signoff.png` (S8) |

## Compile check

Engine: MiKTeX `pdflatex` (the engine Overleaf uses). Tectonic is not installed on this machine, so the Tectonic
compile was not repeated. The sources use only standard packages (geometry, booktabs, tabularx, graphicx, xcolor,
enumitem, amsmath, tikz, hyperref); there are no Tectonic-only constructs.

| Document | Pages (incl. references) | Errors | Undefined refs | Undefined cites | Overfull boxes |
|---|---|---|---|---|---|
| `STITCH_EXT_v9.tex` | **16** (limit 17) | 0 | 0 | 0 | 0 |
| `STITCH_EXT_supplement.tex` | 16 | 0 | 0 | 0 | 0 |

Abstract: 249 words (limit 250). Every bibliography entry is cited (24 of 24). No em-dash, no "breakthrough",
"proves" or "dramatic", and no non-ASCII byte in either source.

## A. Title (easy to revert)

- v8: `reSTITCHing: Refining STITCH` / `From Single-Run Illustrations to N=3 Evidence, Cost-Controlled Semantic Escalation, and a Real-MPSoC Case Study`
- v9: `reSTITCHing: Replicated, Cost-Controlled, and Sign-off-Aware Repair of LLM-Generated RTL`

To revert, restore the `\title{...}` of v8 (lines 54 to 56) in v9.

## Structure: v8 -> v9 (main text) and what moved to the supplement

| v9 section | Built from (v8) | Moved to the supplement |
|---|---|---|
| Abstract | rewritten (B) | -- |
| 1 Introduction | v8 Section 1, rewritten; contributions list; "Relation to the conference version" (C) | -- |
| 2 Related Work | new (D) | -- |
| 3 STITCH in Brief | new: pipeline figure (TikZ), rule-class table, algorithm box (E) | S1: verification status per class, v3 details, condition and escalation timing details |
| 4 Replicated Cases, and What Replication Retired | v8 Sections 2 and 3, condensed; proven table kept | S2: reachability table, token-cost note, retirement details, in-house benchmark collapse |
| 5 Cost-Controlled Escalation | v8 Section 4; guarantee corrected (F); cost table kept | -- |
| 6 Harness Hardening | v8 Section 5, condensed to one paragraph | S3: the three defects in full |
| 7 RTLLM Study Design and the Fine-Tuning Twin | v8 Sections 6 and 7, condensed | S4: pool, pilot, twin design and verdict in full, twin figure |
| 8 STITCH at RTLLM Scale | v8 Section 8 plus Set 4 / 4b (G) and freq_divbyfrac (I) | S5: Set 1/3 tables (tier pass, tier cost, Set 3 pooled and per model), Set 1 cost figure, timeouts, iteration budget, replicate trace, cell-bootstrap table; S6: API study design, deviations and all Set 4 / 4b tables; S7: freq_divbyfrac in full |
| 9 An MPSoC Case Study | v8 Section 9, condensed; task table added; ladder table gains Gemini (J) | S8: the full Phase 3 write-up (from `PHASE3_MPSOC_v2.tex`): substrate, v3 layer, experiment details, backend check, metrics, pooled table with silent structural pass, primary contrasts with all strata, sensitivity table, would-fire table, per-model figure, re-stated contrasts, cost table, per-task table, upgrade table, escalation details, composition table with bounds and figure, audit table, advice table, ladder table and API ladder figure, seven-model pool, next steps |
| 10 Threats to Validity | new (K) | -- |
| 11 Conclusion and Directions | v8 Section 10, rewritten (H, F) | -- |
| Availability, Acknowledgments | new (L) | S9: statistics and reproducibility |

Figures in the main text: 4 (pipeline; Set 1 two panels; ladder and deficit side by side; Phase 3 two panels).
Tables in the main text: 9.

## Required content changes

- **A. Title**: see above.
- **B. Abstract**: rewritten at 249 words. It covers what is new relative to MLCAD '26, the RTLLM evidence, the
  escalation cost trend (16.6, 27.6, 88.6%), the guard (63% signed off defective, every sim-silent defect at every
  model size), the pre-registered control-arm result, interpretation against raw text, composition, and the latch
  result (24% to 88%, Yosys only). Two intervals: Set 1 restart (0.0, CI -4.6 to +4.6) and escalation over the alarm
  (+19.7, CI +11.1 to +29.3).
- **C. Conference paper**: cited as `stitch26` (MLCAD '26, DOI 10.1145/3831599.3840333; authors and title from
  `paper_112_final.pdf`, page 1). Section 1 has a "Relation to the conference version" paragraph that lists the new
  content.
- **D. Related work**: new Section 2; six new references, each verified (log below); existing entries verified and
  corrected; uncited entries removed.
- **E. Recap**: Figure 1 (TikZ pipeline), Table 1 (v2 classes and v3 additions, one line each), and an algorithm box
  for `sem_escalate` / `sem_escalate_restart`.
- **F. Escalation guarantee**: corrected everywhere (details below).
- **G. Set 4**: Section 8.3, all numbers from `numbers_set4.tex` macros; disclosures (Haiku 143/228, Kimi dropped,
  OpenAI fingerprint change, T=0.1, no reasoning, matched toolchain with parity 140/140 and 51/51, RTLLM public and
  possible contamination). Set 4c appears only in the supplement (S6, one paragraph). Figure 3 (a) adds the API bars
  in a distinct colour ("API, non-reasoning, T=0.1"), side by side with the always-on deficit (b), which also adds
  the three API models.
- **H. "A prediction we have not yet tested"** (v8 2.2 and 8.2) and the Directions items on floor modules and frontier
  models: replaced. The floor result is now Section 8.3 ("the floor is mostly a property of the 4B to 32B models") and
  claim 6 of 8.5. Directions now names reasoning models as untested.
- **I. freq_divbyfrac**: verified mechanically before writing (details below), Section 8.4 and S7.
- **J. Phase 3**:
  - Table 9 (ladder) gains the Gemini 2.5 Flash column and the notation `sim-silent + sim-visible` (e.g. `18+12`).
  - Result (2) keeps the 38 and drops the "all 95" clause.
  - Result (5) says "loop-clean".
  - A compact task table is in the paper (Table 5).
  - The latch result is in Result (1), in bold, and in the abstract.
- **K. Threats to validity**: new Section 10, covering replicate correlation, single temperature, quantisation and
  backends, toolchain versions, in-sample v3, the post hoc oracle, RTLLM contamination, API drift and synthesis-only
  composition.
- **L. Availability and Acknowledgments**:
  - The repository URL and the three pre-registration hashes; result trees on request.
  - The Xilinx-AMD acknowledgment, carried over verbatim from `paper_112_final.pdf`.
  - The HPC facility, moved from a bibliography entry into the acknowledgments, because it could not be verified as a
    reference.
- **M. The "11" before Section 1**:
  - **Cause:** the abstract filled page 1 exactly (confirmed by compiling v7), so the page-1 footer "1" sat directly
    above the section number "1" at the top of page 2. The text layer reads "1\n1 Why This Extension...".
  - **Fix:** with the 249-word abstract, Section 1 now starts on page 1 (checked in the PDF text layer).

## F. The escalation guarantee, every location

| Location | v8 | v9 |
|---|---|---|
| Abstract | "conditional escalation matches baseline with a structural worst-case guarantee" | "conditional escalation with a restart matches baseline on small models (0.0 points, CI -4.6 to +4.6)" |
| Section 5 (old 4) | "on any problem baseline solves, escalation behaves identically to baseline. Its worst case is therefore bounded below by baseline" | "on runs that converge before the trigger it is the baseline policy. Beyond the trigger it diverges... A worst case equal to baseline can therefore be claimed only for the runs that converge before the trigger." Plus the measured contrasts: restart 0.0 [-4.6, +4.6], p=1.000; plain escalation -4.7 [-10.7, 0.0], p=0.148; sem_adv -4.6 [-10.5, +0.7] |
| 8.1 finding (2) (old 8.2 point 2) | "the worst-case-equals-baseline guarantee of Section 4 observed at scale" | "sem_escalate_restart matches baseline (54/151 against 54/153; 0.0, CI -4.6 to +4.6), and plain sem_escalate does not (47/150; -4.7, CI -10.7 to 0.0)" |
| 8.5 claim 3 (old 8.5 claim 3) | "The worst-case-equals-baseline guarantee holds across the whole ladder, and it is structural rather than statistical" | "Escalation is the baseline policy on every run that converges before its trigger; beyond the trigger only its restart variant matches baseline on small models..., while plain escalation trails like always-on interpretation" |
| Conclusion | "escalation protects weak models from that deficit and costs strong models nothing" | "escalation is the baseline policy until a run is stuck, matches baseline on small models when it can restart" |

Source of the three Set 1 contrasts: `phase3/evidence/phase3_run/POSTHOC_CHECKS.md` lines 56 to 58 (cell bootstrap).

## I. freq_divbyfrac: the mechanical check

`python3 phase2/frontier/set4c.py refcheck` (WSL, oss-cad-suite 20260917) runs the RTLLM reference under its own
testbench with one added `$strobe` per clock edge.

Result (`phase2/frontier/evidence/freq_divbyfrac_refcheck_stdout.txt`, last line):
- the counter advances once per rising edge;
- its period is 14 half steps;
- `clk_div` has a period of 7 half steps (H3 L4);
- there are 2 output periods per counter wrap;
- the reference passes.

Spec line 17 says "7 half clock steps". The check **confirms** the hypothesis, so v9 adds the sentence "the
specification's description of the counter does not match its own reference design, which plausibly explains the
models' roughly doubled period: a spec-wording defect, not a testbench defect", marked "in our reading". It also adds
the same-timestep reset/clock race as a minor robustness weakness that did not cause the failures. Full analysis: S7.

## Numbers: every new or changed number and its source

Generated by `python -B paper/v9_number_sources.py` (the full table, with the matched source line, is in
`v9_number_sources.md`). Phase 3 numbers use `PHASE3_FINAL.md` as the reference where files differ in the last digit.

| Claim (v9 location) | v9 value | Source file:line |
|---|---|---|
| Set 1 restart - baseline (abstract, 5, 8.1, 8.5) | 0.0 [-4.6, +4.6], p=1.000 | `phase3/evidence/phase3_run/POSTHOC_CHECKS.md:58` |
| Set 1 sem_escalate - baseline (5, 8.1, 8.5) | -4.7 [-10.7, 0.0], p=0.148 | `POSTHOC_CHECKS.md:57` |
| Set 1 sem_adv - baseline (5, 8.1) | -4.6 [-10.5, +0.7], p=0.199 | `POSTHOC_CHECKS.md:56` |
| Set 3 contrasts (8.2) | -0.7 [-7.8, +6.5]; +2.6 [-1.3, +7.2], p=0.404; +2.0 [-2.6, +7.2], p=0.596 | `POSTHOC_CHECKS.md:61-63` |
| Set 4 pooled pass rates (8.3) | 99.3 / 98.7 / 98.0 / 98.0% | `phase2/frontier/evidence/set4_analysis_stdout.txt:11-14`; macros `numbers_set4.tex` |
| Set 4 tool-call cut (abstract, 8.3, 8.5, 11) | 88.6% (2.29 to 0.26) | `set4_analysis_stdout.txt:18` |
| Set 4 GPT-4.1 mini contrasts (8.3) | -2.0, -3.9, -3.9; every p = 1.000 | `set4_analysis_stdout.txt:25-27` |
| Set 4 INR per passing module (8.3) | 0.11 to 0.51 | `numbers_set4.tex:26-27` (min/max of `cost.*.inr_per_pass`, `evidence/set4_analysis.json`) |
| Set 4 parity (8.3, S6) | 140/140, 51/51 | `numbers_set4.tex` (`evidence/parity_check_osscad.json` summary) |
| OpenAI fingerprints (8.3, S6) | 256 and 7 calls | `set4_analysis_stdout.txt:75` |
| Set 4b coverage (8.3, S6) | 228 / 228 / 143 (85 errored) | `evidence/set4b_analysis_stdout.txt:11-13` |
| Floor modules leaving the floor (8.3) | 16 of 19; 4 at ceiling for all | `numbers_set4.tex` (Q1 of `evidence/set4b_analysis.json`) |
| Interpreter fires on floor failures (8.3) | 55% (103/188) | `numbers_set4.tex` (Q2 of `set4b_analysis.json`) |
| Passes after a directive in 0/3 cells (8.3) | 3 | `set4b_analysis_stdout.txt` (Q2 sem_adv line) |
| Smallest Q3 p (8.3) | 0.062 of 12 contrasts | `set4b_analysis_stdout.txt` (Q3, gemini restart) |
| Q4 strict (8.3) | freq_divbyfrac, 36 runs | `set4b_analysis_stdout.txt:96` |
| API runs (1) | 1,211 = 612 + 599 | `numbers_set4.tex:41` |
| freq_divbyfrac reference (8.4, S7) | 14 half steps, 2 periods per wrap, H3 L4 | `evidence/freq_divbyfrac_refcheck_stdout.txt:27` |
| freq_divbyfrac shift test (8.4, S7) | reference 20/20 at 0, 14/19 at +-1; 0 of 34 a shift | `evidence/freq_divbyfrac_trace_stdout.txt:2` and lines 3-8 |
| freq_divbyfrac first mismatch (8.4, S7) | check 3 in 32 of 34 (11 + 10 + 11) | `freq_divbyfrac_trace_stdout.txt:4, 6, 8` |
| freq_divbyfrac first high phase (S7) | H4 5, H5 3, H6 6, H7 7, H9 3, H11 3, H13 4, H20 1 | `evidence/freq_divbyfrac_trace.json` (`final_candidates` shape keys) |
| Latch-free clean synthesis (abstract, Result 1) | 35/144 (24%) to 127/144 (88%); raw 104; alarm 94 | `phase3/evidence/phase3_final/PAPER_NUMBERS.md:34` |
| Alarm runs whose returned RTL v3 names (Result 2) | 38 of 95 | `PAPER_NUMBERS.md:53` |
| Escalation minus alarm (abstract, Result 2) | +19.7 [+11.1, +29.3] | `phase3/evidence/phase3_final/PHASE3_FINAL.md:102` |
| v3 minus raw (abstract, Result 3) | +14.1 [+3.5, +24.7] | `PHASE3_FINAL.md:141` |
| Calls and tokens, v3 vs raw (abstract, Result 3) | -23.3% calls, -23.2% tokens | `PAPER_NUMBERS.md:23` |
| Gemini ladder column (Table 9, S8) | 0+15 / 516; 18+15 / 1,160; 18+12 / 1,291; 18+15 / 1,478; 18+14 / 1,479; 18+15 / 1,225 | `evidence/p3_ladder_signoff_stdout.txt:8-13` |
| Published GPT/Haiku ladder rows reproduced (S8) | yes | `p3_ladder_signoff_stdout.txt:4` |
| Gemini Address_select misses (Result 6, S8) | raw_adv 3, v3 1 | `p3_ladder_signoff_stdout.txt:34` |
| Pre-registration hashes (Availability) | 1b6eb915...cc63; CC23711D...653B; 680F24F5...C130 | `phase3/evidence/FREEZE_FINAL.md:11`; `phase2/frontier/SET4_REPORT.md:634`; `phase2/frontier/p3_api/P3_API_REPORT.md:12` |

All other numbers are carried over unchanged from v8, and their sources are in `V8_CHANGES.md` (Phase 3) and
`V7_CHANGES.md` (Sections 1 to 8). The Set 4 / 4b macros and tables are regenerated by script. If Haiku's 85 pending
runs are completed later, re-run `analysis_set4b.py`, then `make_numbers_set4.py`; no text edit is needed.

## Figures

| v9 figure | File | Source data | Command |
|---|---|---|---|
| 1 pipeline | TikZ in the .tex | -- | -- |
| 2 Set 1 tiers and tool calls | `figures/fig_v9_set1_tiers.pdf` | `phase2/set1_analysis/tier_pass_rates.csv`, `cost_by_tier.csv` | `python -B paper/make_v9_figures.py` |
| 3 ladder and deficit (with API) | `figures/fig_v9_ladder_deficit.pdf` | Twin, Set 1, Set 3 master logs via `phase2/set3_analysis` builders; `set4_analysis.json` | same |
| 4 Phase 3 by condition and by call | `figures/fig_v9_p3.pdf` | `phase3/evidence/phase3_final/PHASE3_FINAL.md` stratum and cumulative tables | same |

The colours come from the validated categorical palette (dataviz reference instance).

**Correction:** v8's caption for the deficit figure said "Wilson 95% CIs". The plotted intervals were Newcombe
intervals for a difference of proportions (`statsmodels.confint_proportions_2indep(method="newcomb")`). v9 says so
and cites Newcombe (1998).

## Bibliography verification log (fetched 2026-10-13)

Each entry was checked against Crossref (DOI registry metadata, `api.crossref.org`), the arXiv API (abstract
metadata), or the official site. Changes are in bold.

| Key | Verified against | Result |
|---|---|---|
| stitch26 (new) | `paper_112_final.pdf` page 1 (title, authors, venue, DOI printed) | DOI 10.1145/3831599.3840333 returned 404 at doi.org (not yet registered) and 403 at dl.acm.org (bot block); cited from the published PDF |
| autochip | arXiv:2311.04887 | **v8 said "Proc. DAC, 2024"; no venue found on arXiv or Crossref, so now cited as arXiv:2311.04887** |
| rtlfixer | Crossref 10.1145/3649329.3657353 | DAC 2024 confirmed; **title singular "Large Language Model"; DOI added** |
| verilogeval | Crossref 10.1109/ICCAD57390.2023.10323812; arXiv comment "ICCAD 2023 Invited Paper" | **venue ICCAD 2023 and DOI added** (v8: arXiv only) |
| lu2024rtllm | Crossref 10.1109/ASP-DAC58780.2024.10473904; arXiv:2308.05345 | confirmed; **DOI added** |
| rtlcoder | Crossref 10.1109/LAD62341.2024.10691788; arXiv:2312.08617 | **author list corrected**: v8 had "S. Liu, Y. Lu, W. Fang, M. Li, Z. Xie" (that is OpenLLM-RTL's list); correct: S. Liu, W. Fang, Y. Lu, Q. Zhang, H. Zhang, Z. Xie; **venue: IEEE LLM Aided Design Workshop (LAD) 2024** |
| rtlcoder_hf | huggingface.co/ishorn5/RTLCoder-Deepseek-v1.1 | page exists and links arXiv:2312.08617; **author attribution "HKUST Zhiyao Lab" removed** (not stated on the page) |
| selfrefine | Crossref 10.52202/075280-2019 (NeurIPS 36); arXiv:2303.17651 | confirmed |
| qiu2024 (new) | arXiv:2404.07235 (comment: accepted at LAD 2024; DOI 10.1109/LAD62341.2024.10691721) | added |
| verilogcoder (new) | Crossref 10.1609/aaai.v39i1.32007; arXiv:2408.08927 | added (AAAI 2025) |
| mage (new) | Crossref 10.1109/DAC63849.2025.11133191; arXiv:2412.07822 | added (DAC 2025) |
| aivril (new) | arXiv:2409.11411 | added as arXiv (no venue found) |
| meic (new) | Crossref 10.1145/3676536.3676801; arXiv:2405.06840 | added (ICCAD 2024) |
| uvllm (new) | arXiv:2411.16238 | added as arXiv (Crossref query failed; no venue claimed) |
| deepseekcoder | arXiv:2401.14196 | confirmed |
| gemma3 | arXiv:2503.19786 | confirmed |
| llama3 | arXiv:2407.21783 | confirmed (first author Grattafiori in the current version) |
| qwen25coder | arXiv:2409.12186 | confirmed |
| iverilog | steveicarus.github.io/iverilog (HTTP 200, title "Icarus Verilog documentation") | confirmed; **year removed** |
| verilator | veripool.org/verilator (title "Veripool") | confirmed; **year and subtitle removed** |
| yosys | yosyshq.net/yosys (title "Yosys Open SYnthesis Suite :: About") | **v8's "Proc. IWLS, 2012" could not be verified; now cited as the project site** |
| ollama | ollama.com (HTTP 200) | confirmed |
| wilson1927 | Crossref 10.1080/01621459.1927.10502953 | confirmed (vol. 22, no. 158, pp. 209-212); **DOI added** |
| newcombe1998 (new) | Crossref 10.1002/(sici)1097-0258(19980430)17:8<873::aid-sim779>3.0.co;2-i | added (Statistics in Medicine 17(8):873-890); needed for the deficit-figure intervals |
| hdlbits, rag | -- | **removed** (not cited in v8 or v9) |
| bitshpc | no authoritative page to fetch | **removed from the bibliography**; the facility is credited in the Acknowledgments |

Unverified, not added: none. Every reference I meant to add was verified.

## Other notes

- **Evidence snapshots.** The result trees are gitignored, so the analysis outputs the paper relies on were copied,
  unchanged, into `phase2/frontier/evidence/`. Before copying, `p3_signoff_ladder.py` was changed to print paths
  relative to the repository and re-run; its numbers are unchanged.
- **Repository URL.** `https://github.com/Karthik-Flash/STITCH` is the configured `origin`. It returned 404 to an
  anonymous request on 2026-10-13, so it is probably private. The availability statement needs it to be public, or it
  needs changing.
- **Set 4c** is not mentioned in the main text. S6 has one paragraph.
