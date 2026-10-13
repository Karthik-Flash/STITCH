# Repository index

What lives where, which file is the evidence for each part of the paper, and how to regenerate every table and
figure. Paths are relative to the repository root. Last updated 2026-10-13 (paper v10).

## Top level

| Path | What it is |
|---|---|
| `README.md` | entry point; links here |
| `REPO_INDEX.md` | this file |
| `handoff.md` | project state and conventions, for a new contributor or a new agent session |
| `src/interpreter/` | the STITCH interpreter: `stitch_interpreter.py` (production, "v2", never edited since Phase 2; SHA-256 of the LF-normalised file `42f61a49...2abff`), `stitch_interpreter_v3.py` + `_v3_parsers.py` (additive v3 layer), `pass_detection.py` (`detect_outcome(log, benchmark)` registry), `WARNING_TAXONOMY.md`, `tests/` |
| `src/runner/` | the original single-machine runner (Phase 0) |
| `phase0/` | single-run illustration hunt and the replicated illustrations |
| `phase1/` | escalation policies, the 255-run in-house benchmark, RTLLM pilot |
| `phase2/` | RTLLM study: Twin (Set 2), Set 1, Set 3 on the cluster; `phase2/frontier/` = Sets 4, 4b, 4c on API models |
| `phase3/` | the MPSoC case study: tasks, runner, analysis, cluster scripts, evidence |
| `MPSoC/` | the RISC-V MPSoC source (core, network interface, mesh router) as received |
| `benchmarks/` | in-house benchmark scaffolding |
| `analysis/` | early cross-run aggregation helpers |
| `paper/` | journal paper: `overleaf/` (v10, current, Overleaf-ready), v9 and v8 sources, generators, figures, change logs |
| `docs/` | runbooks, HPC commands, review notes; `docs/archive/` holds superseded documents |
| `plans/archive/` | superseded research plans |

## Per phase

**Phase 0** (`phase0/`). `README.md`; `illustrations/proven/` (decoder_3to8, mux4_oe: logs per iteration);
`illustrations/retired/`; `evidence/phase0_illustration_hunt_findings.md` and `combined_results.csv`;
`analysis/` (replay and checkpoint scripts); `results/` (tracked summaries).

**Phase 1** (`phase1/`). `escalation_state.py` (the `sem_escalate` / `sem_escalate_restart` state machine, pure and
unit-tested), `escalation_runner.py`, `error_signature.py`, `task3_runner.py` (255-run benchmark),
`rtllm_pilot_runner.py`, `rtllm_task_a_screen.py` (RTLLM compatibility screen); findings in `PHASE1_FINDINGS.md`,
`PHASE1_TASK3_ANALYSIS.md`; `RTLLM_PILOT_PREREG.md`; `tests/`.

**Phase 2** (`phase2/`). Cluster harness: `stitch_runner_hpc.py`, `escalation_runner_hpc.py`, `set1_runner.py`,
`set3_runner.py`, `twin_run_runner.py`, `rtlcoder_adapter.py`, `*.slurm`. Analyses: `twin_analysis_SET2/`
(tiers: `module_categories.json`), `set1_analysis/`, `set3_analysis/`; reports `TWIN_RUN_ANALYSIS.md`,
`SET1_ANALYSIS.md`, `SET3_ANALYSIS.md`; `TWIN_RUN_PREREG.md`.

**Phase 2, API models** (`phase2/frontier/`).
- Pre-registration `SET4_PREREG.md` (five dated, hashed amendments).
- Report `SET4_REPORT.md` (Sets 4, 4b, the Gemini completion, the Phase 3 API ladder rows, Set 4c, closed).
- `PENDING.md` (only Haiku's 85 Set 4b runs, optional) and `FREQ_DIVBYFRAC_AUDIT.md`.
- Code: `backends.py` (per-provider API adapters with caps, retries and stop rules), `api_secrets.py` (key loader),
  `set4_runner.py` (Set 3 engine with only the model call replaced), `analysis_set4.py`, `analysis_set4b.py`,
  `stats_set4.py`, `oracle_audit.py`, `parity_check.py`, `spend_summary.py`, `set4c.py`, `make_numbers_set4.py`.
- Secret hygiene: `scan_secrets.py` (working tree) and `leak_audit.py` (git history).
- `p3_api/`: the API rows of the Phase 3 study (`P3_API_PREREG.md`, `P3_API_REPORT.md`, `p3_api_runner.py`,
  `p3_signoff_ladder.py`, `p3_mock_parity.py`, `p3_gate_local.sh`).
- `evidence/`: unchanged snapshots of the analysis outputs the paper cites, since the result trees are gitignored.

**Phase 3** (`phase3/`).
- `README.md` and `HPC_PHASE3_COMMANDS.md`.
- `tasks/<task>/`: `spec.md`, `input.v`, `golden.v`, `tb.v` (loop testbench), `tb_signoff.v` (sign-off testbench),
  `meta.json`.
- `runner/`: `stitch_runner_p3.py`, `p3_eval.py`, `validate_tasks.py`, `compose.py`, `analyze_phase3.py`,
  `posthoc_checks.py`, `phase3_figures.py`.
- `hpc/`: Slurm and deploy scripts. `tests/`: G0 interpreter tests on frozen real logs. `designs/`: the sanitised
  designs used for composition.
- `evidence/`: `PREREG_FINAL.md`, `FREEZE_FINAL.md`, `phase3_final/` (`PHASE3_FINAL.md`, `PAPER_NUMBERS.md`,
  `PLANNER_BRIEF.md`, figures), `phase3_run/` (`PHASE3_RESULTS.md`, `POSTHOC_CHECKS.md`, `POSTHOC_SIGNOFF.md`),
  `preflight_final/`, `signoff_cache.json`.

**Paper** (`paper/`).
- **Current: `overleaf/` (v10).** `main.tex` (15 pages including references), `supplement.tex` (Supplementary
  Material S1 to S9), `figures/` (vector PDF, every figure both files use), `README.txt` (how to compile),
  `qa_contact_sheet.png` (page thumbnails from the last visual QA). Self-contained: no `\input` from outside the
  folder; the Set 4 macros and the S6 tables sit in marked `% BEGIN GENERATED` blocks inside the two files.
  `STITCH_overleaf.zip` is the same folder (without the contact sheet), ready to upload to Overleaf.
- Figure code: `figstyle.py` (the shared style: one colour per condition, final-size fonts, embedded fonts),
  `make_v10_figures.py` (every v10 figure except the floor heat map).
- Change logs: `V10_CHANGES.md` (v10: build, figures, tables, Haiku projection, QA rounds), `V9_CHANGES.md` and
  `V8_CHANGES.md` (every earlier change and number source).
- Previous versions, kept unchanged: `STITCH_EXT_v9.tex` with `STITCH_EXT_supplement.tex` and their generated
  inputs `numbers_set4.tex` and `tables_set4.tex` (now frozen); `STITCH_EXT_v8.tex` and `PHASE3_MPSOC_v2.tex`;
  `make_v9_figures.py` and `figures/`.
- Superseded drafts (v7, `PHASE3_MPSOC.tex` v1, the earlier compiled PDF) are in `docs/archive/paper/`.

## Canonical evidence for each part of the paper (v10; section numbers as in v9)

| Paper part | Canonical evidence file |
|---|---|
| 3 STITCH in brief (rule classes) | `src/interpreter/WARNING_TAXONOMY.md`, `phase3/docs/WARNING_TAXONOMY_PHASE3_ADDENDUM.md` |
| 4 Replicated cases, retirements | `phase0/evidence/phase0_illustration_hunt_findings.md`, `phase1/PHASE1_FINDINGS.md` |
| 5 Escalation (cost table; guarantee contrasts) | `phase1/PHASE1_TASK3_ANALYSIS.md`; `phase3/evidence/phase3_run/POSTHOC_CHECKS.md` (section "phase2") |
| 6 Harness hardening | `docs/IMP_PHASE2_RUNNER_HARDENING_REPORT.md` |
| 7 Study design, Twin | `phase2/TWIN_RUN_ANALYSIS.md`, `phase2/twin_analysis_SET2/module_categories.json` |
| 8.1 Set 1 | `phase2/SET1_ANALYSIS.md`, `phase2/set1_analysis/tier_pass_rates.csv`, `cost_by_tier.csv` |
| 8.2 Set 3 | `phase2/SET3_ANALYSIS.md`, `phase2/set3_analysis/*.csv` |
| 8.3 Sets 4 and 4b | `phase2/frontier/SET4_REPORT.md`; `phase2/frontier/evidence/set4_analysis_stdout.txt`, `set4b_analysis_stdout.txt` and the JSON beside them; the NUMBERS block of `paper/overleaf/main.tex`; Haiku projection: `phase2/frontier/evidence/set4b_haiku_projection.json` |
| 8.4 freq_divbyfrac | `phase2/frontier/FREQ_DIVBYFRAC_AUDIT.md`; `phase2/frontier/evidence/freq_divbyfrac_*` |
| 9 MPSoC case study | `phase3/evidence/phase3_final/PHASE3_FINAL.md` (reference for every CI), `PAPER_NUMBERS.md`; API rows: `phase2/frontier/evidence/p3_ladder_signoff_stdout.txt` |
| Supplement S1 to S9 | as above; per-number sources in `paper/V9_CHANGES.md`, additions in `paper/V10_CHANGES.md` |

## Regenerating tables and figures (repo root)

| Output | Command | Needs |
|---|---|---|
| Set 1 tables and figures | `python phase2/set1_analysis/cost_analysis.py`; `cost_by_tier.py`; `fig2_tier_split.py`; `table_condition_decision.py`; `table_full_grid.py` | `phase2/results/set1_run/` |
| Set 3 tables and figures | `python phase2/set3_analysis/fig_capability_ladder_full.py`; `harmful_regime_by_capability.py`; `per_model_tier.py`; `set3_cost_by_tier.py` | `phase2/results/set3_run/`, Twin results |
| Set 1 / Set 3 cell bootstrap | `python phase3/runner/posthoc_checks.py phase2` | Set 1 and Set 3 results |
| Set 4 analysis and figures | `python phase2/frontier/analysis_set4.py` | `phase2/results/set4_api/` |
| Set 4b analysis | `python phase2/frontier/analysis_set4b.py` | same |
| Set 4b oracle audit | WSL: `python3 phase2/frontier/oracle_audit.py alu freq_divbyfrac` (with `STITCH_SET4_OSSCAD`, `RTLLM_ROOT`) | oss-cad-suite 20260917, RTLLM checkout |
| freq_divbyfrac trace / reference check | WSL: `python3 phase2/frontier/set4c.py trace` / `refcheck` | same |
| Paper macros, S6 tables, Haiku projection, floor heat map | `python -B phase2/frontier/make_numbers_set4.py` (rewrites only the `% BEGIN/END GENERATED` blocks of `paper/overleaf/main.tex` and `supplement.tex`) | the two Set 4 analysis JSON files, the Set 4b master logs |
| Phase 3 analysis | `python phase3/runner/analyze_phase3.py --final --results phase3/results/phase3_run --more-results phase3/results/phase3_gate_ctrl phase3/results/phase3_32b` (fill the sign-off cache first with `--score-signoff`, under WSL) | `phase3/results/` |
| Phase 3 paper numbers | `python phase3/evidence/phase3_final/paper_numbers.py > phase3/evidence/phase3_final/PAPER_NUMBERS.md` | same |
| API ladder rows, sign-off | WSL: `bash phase2/frontier/p3_api/p3_env.sh phase2/frontier/p3_api/p3_signoff_ladder.py [--score] [--recheck]` | `phase2/results/p3_api/full/` |
| v10 figures | `python -B paper/make_v10_figures.py` (writes `paper/overleaf/figures/`) | Set 1 CSVs, Set 1/3/Twin results, Set 4 JSON, `PHASE3_FINAL.md`, `PAPER_NUMBERS.md`, `PHASE3_RESULTS.md`, `phase2/frontier/evidence/p3_ladder_signoff.json` |
| v9 figures (frozen) | `python -B paper/make_v9_figures.py` | as above |
| v9 number sources | `python -B paper/v9_number_sources.py > paper/v9_number_sources.md` | the evidence files |
| Compile the paper | `cd paper/overleaf && latexmk -pdf main.tex` and `latexmk -pdf supplement.tex`, or upload `paper/STITCH_overleaf.zip` to Overleaf | pdfLaTeX (TeX Live 2023+ or MiKTeX); no BibTeX step |

## What is gitignored, and where it lives

| Ignored | Where | Notes |
|---|---|---|
| Per-run result trees | `phase0/results/` (iteration-level files), `phase1/results/`, `phase2/results/` (Twin, Set 1, Set 3, `set4_api/`, `p3_api/`), `phase3/results/` | in the working tree on the maintainer's machine; available on request |
| API ledgers (request and response IDs, costs) | `phase2/results/set4_api/ledgers*/`, `phase2/results/p3_api/ledgers/` | inside `phase2/results/` |
| API keys | `%USERPROFILE%\.stitch\api_keys.env` | outside the repository; also `*.env` and `stitch-api-key.txt` are ignored |
| Private notes | `reSTITCH.md`, `reSTITCH_PHASE3_EXPLAINED.md`, `note.txt`, `phase3/docs/archive/HANDOFF_PHASE3_CLAUDE_CODE.md` | kept locally, ignored on purpose |
| Conference PDF | `paper/paper_112_final.pdf` | ignored by name |
| LaTeX build output | `paper/build/` and `*.aux`, `*.toc`, etc. | v9 compiles here; v10 builds in place in `paper/overleaf/`, whose PDFs are ignored |
| Caches and environments | `__pycache__/`, `.pytest_cache/`, `.venv/` | regenerable |

Before any commit: `python phase2/frontier/scan_secrets.py` (must report 0 matches) and
`python phase2/frontier/leak_audit.py` (must report "clean").

## Finishing Claude Haiku 4.5 on the floor tier, and removing the projections

Haiku is at 143/228 Set 4b runs; the paper projects its missing cells in two marked places (`paper/V10_CHANGES.md`
section 6). To replace the projections with measured values:
1. Run the 85 pending runs as described in `phase2/frontier/PENDING.md` section 1 (needs Anthropic credit and a
   pre-registration amendment).
2. `python phase2/frontier/analysis_set4b.py`, then `python -B phase2/frontier/make_numbers_set4.py`. The projected
   cells disappear, the counts become measured, the daggers and notes vanish, and the heat map is redrawn.
3. In `paper/overleaf/main.tex`, set `\finaltrue` (near the top). Any projection still left then stops the build with
   "Projected Haiku values remain". Rebuild both files and re-zip `paper/overleaf/` into `paper/STITCH_overleaf.zip`.

If Haiku is not completed, either keep the marked projections or delete the clause and the notes they feed
(`\SetFourBCeilingAllClause`, `\SetFourBProjNote`) and the hatched heat-map cells; `\finaltrue` will confirm that
none remains.
