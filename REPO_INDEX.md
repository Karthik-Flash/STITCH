# Repository index

What lives where, which file is the evidence for each part of the paper, and how to rebuild everything. Paths are
relative to the repository root. Last updated 2026-10-14 (final state: paper v10, consolidated docs).

## Start here

| If you want to... | Read |
|---|---|
| understand the project quickly | `docs/reSTITCH_REVISITED_QA.md` (glossary, "the paper in 10 sentences", 93 questions in paper order) |
| know the whole story, decisions and corrections | `docs/reSTITCH.md` |
| understand one phase | `docs/PHASES_EXPLAINED.md` |
| run anything on the GPU cluster | `docs/HPC_GUIDE.md` |
| pick up the work | `handoff.md`, then `phase2/frontier/PENDING.md` |
| build the paper | `paper/overleaf/README.txt` |

## Top level

| Path | What it is |
|---|---|
| `README.md` | entry point; links here |
| `REPO_INDEX.md` | this file |
| `handoff.md` | the final state and the standing conventions, for a new contributor or agent session |
| `src/interpreter/` | the STITCH interpreter; see below |
| `src/runner/` | the original single-machine runner (Phase 0) |
| `phase0/` | the illustration hunt and the two replicated illustrations |
| `phase1/` | escalation policies, the 255-run in-house benchmark, the RTLLM pilot |
| `phase2/` | the RTLLM study on the cluster (Twin, Set 1, Set 3); `phase2/frontier/` is the API study (Sets 4, 4b, 4c) |
| `phase3/` | the MPSoC case study: tasks, runner, analysis, cluster scripts, evidence |
| `MPSoC/` | the RISC-V MPSoC source as received (from `p20230031/RISC-V`) |
| `benchmarks/`, `analysis/` | in-house benchmark scaffolding; early aggregation helpers |
| `paper/` | the journal paper: `overleaf/` (v10, current) and `archive/` (every earlier draft) |
| `docs/` | the four current documents; `docs/archive/` holds the documents they replaced |
| `plans/archive/` | superseded research plans |

`src/interpreter/` in detail:
- `stitch_interpreter.py`: the production interpreter, "v2". It has not been edited since Phase 2; the SHA-256 of the
  LF-normalised file is `42f61a49...2abff`.
- `stitch_interpreter_v3.py` and `_v3_parsers.py`: the additive v3 layer.
- `pass_detection.py`: the `detect_outcome(log, benchmark)` registry.
- `WARNING_TAXONOMY.md` and `tests/`.

## Per phase

**Phase 0** (`phase0/`).
- `README.md`.
- `illustrations/proven/`: `decoder_3to8` and `mux4_oe`, frozen.
- `illustrations/retired/`.
- `evidence/`: `phase0_illustration_hunt_findings.md` and `combined_results.csv`.
- `analysis/`: the replay and checkpoint scripts. They read `STITCH_DATA_ROOT`, the Phase 0 data folder outside the
  repository.

**Phase 1** (`phase1/`).
- `README.md`.
- `escalation_state.py`: the escalation state machine, unit-tested.
- `error_signature.py`, `escalation_runner.py`.
- `task3_runner.py`: the 255-run benchmark.
- `rtllm_pilot_runner.py`, `rtllm_task_a_screen.py`.
- Findings: `PHASE1_FINDINGS.md`, `PHASE1_TASK3_ANALYSIS.md`. Pre-registration: `RTLLM_PILOT_PREREG.md`.

**Phase 2** (`phase2/`).
- `README.md`.
- **Cluster harness:** `stitch_runner_hpc.py`, `escalation_runner_hpc.py`, `set1_runner.py`, `set3_runner.py`,
  `twin_run_runner.py`, `rtlcoder_adapter.py`, `*.slurm`.
- **Analyses:** `twin_analysis_SET2/` (the tiers are in `module_categories.json`), `set1_analysis/` (including
  `ceiling_tool_call_distribution.txt`), `set3_analysis/`.
- **Reports:** `TWIN_RUN_ANALYSIS.md`, `SET1_ANALYSIS.md`, `SET3_ANALYSIS.md`. Pre-registration:
  `TWIN_RUN_PREREG.md`.

**Phase 2, the API study** (`phase2/frontier/`).
- **Documents:**
  - `SET4_PREREG.md`: the pre-registration, with five dated, hashed amendments;
  - `SET4_REPORT.md`: the report;
  - `PENDING.md`: open items and the wrap-up status;
  - `FREQ_DIVBYFRAC_AUDIT.md`.
- **Code:**
  - `backends.py`: per-provider adapters, with caps and stop rules;
  - `api_secrets.py`: the key loader;
  - `set4_runner.py`: the Set 3 engine, with only the model call replaced;
  - `analysis_set4.py`, `analysis_set4b.py`, `stats_set4.py`, `oracle_audit.py`, `parity_check.py`,
    `spend_summary.py`, `set4c.py`, `make_numbers_set4.py`.
- **Secret hygiene:** `scan_secrets.py` (the working tree) and `leak_audit.py` (git history).
- **`p3_api/`:** the Phase 3 API ladder rows (`P3_API_PREREG.md`, `P3_API_REPORT.md`, the runner, the sign-off scorer,
  the parity check, and `p3_gate_local.sh`, which runs gates G0 to G5 in WSL).
- **`evidence/`:** snapshots of every analysis output the paper cites (the result trees themselves are gitignored),
  including `set4b_haiku_projection.json` and `spend_summary.txt`.

**Phase 3** (`phase3/`).
- `README.md`, and `docs/` (`PHASE3_EXPLAINED.md`, the warning-taxonomy addendum, the journal errata notes).
- `tasks/<task>/`: `spec.md`, `input.v`, `golden.v`, `tb.v` (the loop testbench), `tb_signoff.v` (the sign-off
  testbench), `meta.json`.
- `runner/`: `stitch_runner_p3.py`, `p3_eval.py`, `validate_tasks.py`, `compose.py`, `analyze_phase3.py`,
  `posthoc_checks.py`, `phase3_figures.py`.
- `hpc/`: the Slurm and deploy scripts. They are hash-frozen in `evidence/FREEZE_FINAL.md`, so they keep their
  original cluster paths.
- `tests/`: G0, the interpreter tests on frozen real logs.
- `designs/`: the sanitised designs and `SANITISATION.md`.
- `evidence/`:
  - `PREREG_FINAL.md` and `FREEZE_FINAL.md`;
  - `phase3_final/`: `PHASE3_FINAL.md`, the reference for every interval, with `PAPER_NUMBERS.md` and
    `PLANNER_BRIEF.md`;
  - `phase3_run/`: `PHASE3_RESULTS.md`, `POSTHOC_CHECKS.md`, `POSTHOC_SIGNOFF.md`.

**Paper** (`paper/`).
- **`overleaf/`, v10, the only current build:**
  - `main.tex`: 15 pages including references;
  - `supplement.tex`: Supplementary Material S1 to S9, 14 pages;
  - `figures/`: vector PDF;
  - `README.txt`: how to compile;
  - `qa_contact_sheet.png`: page thumbnails from the final visual QA.

  The folder is self-contained. The Set 4 macros and the S6 tables sit in marked `% BEGIN GENERATED` blocks.
- **`STITCH_overleaf.zip`:** the same folder (without the contact sheet), ready to upload to Overleaf.
- **Figure code:** `figstyle.py` (the shared style, one colour per condition) and `make_v10_figures.py`.
- **`V10_CHANGES.md`:** the v10 change log: build, figures, tables, Haiku projection, QA rounds, and later edits.
- **`archive/`:** v7, v8 and v9 with their change logs, generated inputs, scripts and figures, and the earlier compiled
  PDF. Kept for provenance and not maintained; see `paper/archive/README.md`.

**Docs** (`docs/`).
- **Current:**
  - `PHASES_EXPLAINED.md`;
  - `HPC_GUIDE.md`;
  - `reSTITCH.md`;
  - `reSTITCH_REVISITED_QA.md`.
- **`archive/`:** the documents they replaced, unchanged. That includes `IMP_PHASE2_RUNNER_HARDENING_REPORT.md`, still
  the evidence for Section 6, and the three earlier HPC documents.

## Canonical evidence for each part of the paper (v10)

| Paper part | Canonical evidence file |
|---|---|
| 3 STITCH in brief (rule classes) | `src/interpreter/WARNING_TAXONOMY.md`, `phase3/docs/WARNING_TAXONOMY_PHASE3_ADDENDUM.md` |
| 4 Replicated cases, retirements | `phase0/evidence/phase0_illustration_hunt_findings.md`, `phase1/PHASE1_FINDINGS.md` |
| 5 Escalation (cost table; guarantee contrasts) | `phase1/PHASE1_TASK3_ANALYSIS.md`; `phase3/evidence/phase3_run/POSTHOC_CHECKS.md` (section "phase2") |
| 6 Harness hardening | `docs/archive/IMP_PHASE2_RUNNER_HARDENING_REPORT.md` |
| 7 Study design, Twin | `phase2/TWIN_RUN_ANALYSIS.md`, `phase2/twin_analysis_SET2/module_categories.json` |
| 8.1 Set 1 | `phase2/SET1_ANALYSIS.md`, `phase2/set1_analysis/tier_pass_rates.csv`, `cost_by_tier.csv`, `ceiling_tool_call_distribution.txt` |
| 8.2 Set 3 | `phase2/SET3_ANALYSIS.md`, `phase2/set3_analysis/*.csv` |
| 8.3 Sets 4 and 4b | `phase2/frontier/SET4_REPORT.md`; `phase2/frontier/evidence/` (analysis stdout and JSON, `set4b_haiku_projection.json`); the NUMBERS block of `paper/overleaf/main.tex` |
| 8.4 freq_divbyfrac | `phase2/frontier/FREQ_DIVBYFRAC_AUDIT.md`; `phase2/frontier/evidence/freq_divbyfrac_*` |
| 9 MPSoC case study | `phase3/evidence/phase3_final/PHASE3_FINAL.md`, `PAPER_NUMBERS.md`; API rows: `phase2/frontier/evidence/p3_ladder_signoff_stdout.txt` |
| Supplement S1 to S9 | as above; number sources in `paper/V10_CHANGES.md` and `paper/archive/V9_CHANGES.md` |

## How to rebuild everything (from the repository root)

| Output | Command | Needs |
|---|---|---|
| the paper and supplement | `cd paper/overleaf && latexmk -pdf main.tex && latexmk -pdf supplement.tex` (or upload `paper/STITCH_overleaf.zip` to Overleaf) | pdfLaTeX (TeX Live 2023+ or MiKTeX); no BibTeX step |
| the Overleaf zip | zip `main.tex`, `supplement.tex`, `README.txt` and `figures/` from `paper/overleaf/` | |
| v10 figures | `python -B paper/make_v10_figures.py` (writes `paper/overleaf/figures/`) | Set 1 CSVs, Set 1, Set 3 and Twin results, Set 4 JSON, `PHASE3_FINAL.md`, `PAPER_NUMBERS.md`, `PHASE3_RESULTS.md`, `phase2/frontier/evidence/p3_ladder_signoff.json` |
| Set 4 macros, S6 tables, Haiku projection, floor heat map | `python -B phase2/frontier/make_numbers_set4.py [--no-projection]` (rewrites only the `% BEGIN/END GENERATED` blocks of the two `.tex` files) | the Set 4 and 4b analysis JSON, the Set 4b master logs |
| Set 1 tables and figures | `python phase2/set1_analysis/cost_analysis.py`; `cost_by_tier.py`; `fig2_tier_split.py`; `table_condition_decision.py`; `table_full_grid.py` | `phase2/results/set1_run/` |
| Set 3 tables and figures | `python phase2/set3_analysis/fig_capability_ladder_full.py`; `harmful_regime_by_capability.py`; `per_model_tier.py`; `set3_cost_by_tier.py` | `phase2/results/set3_run/`, Twin results |
| Set 1 and Set 3 cell bootstrap | `python phase3/runner/posthoc_checks.py phase2` | Set 1 and Set 3 results |
| Set 4 and 4b analysis | `python phase2/frontier/analysis_set4.py`; `python phase2/frontier/analysis_set4b.py` | `phase2/results/set4_api/` |
| Set 4b oracle audit; freq_divbyfrac trace | WSL: `python3 phase2/frontier/oracle_audit.py alu freq_divbyfrac`; `python3 phase2/frontier/set4c.py trace` / `refcheck` | oss-cad-suite 20260917, an RTLLM checkout |
| Phase 3 analysis | `python phase3/runner/analyze_phase3.py --final --results phase3/results/phase3_run --more-results phase3/results/phase3_gate_ctrl phase3/results/phase3_32b` (fill the sign-off cache first with `--score-signoff`, under WSL) | `phase3/results/` |
| Phase 3 paper numbers | `python phase3/evidence/phase3_final/paper_numbers.py > phase3/evidence/phase3_final/PAPER_NUMBERS.md` | same |
| API ladder rows, sign-off | WSL: `bash phase2/frontier/p3_api/p3_env.sh phase2/frontier/p3_api/p3_signoff_ladder.py [--score] [--recheck]` | `phase2/results/p3_api/full/` |
| tests | `python -m pytest src/interpreter/tests phase1/tests`; `python -B phase2/frontier/test_backends.py`; WSL: `bash phase2/frontier/p3_api/p3_gate_local.sh` (gates G0 to G5) | oss-cad-suite for the gates |

## Archive and private policy

- **Superseded material is archived, never deleted.**
  - Paper drafts go to `paper/archive/`.
  - Documents go to `docs/archive/`.
  - Both moves use `git mv`, so their history is kept.
- **Never moved or edited:** anything a script, test, freeze record or hash refers to. That covers evidence,
  pre-registrations, task files, designs, fixtures and `phase3/hpc/`.
  - Code comments may still name an archived document by bare file name. The document is in `docs/archive/`.
- **Private notes stay local.** The private notes (the original reSTITCH notes, the private Phase 3 explainer,
  `note.txt`) live in `private/`, which is gitignored. They are never committed. `docs/reSTITCH.md` is the public
  compilation built from them.
- **Placeholders replace personal paths and cluster identifiers** in documents and scripts: `<HPC_USER>`,
  `<HPC_HOST>`, `<GPU_NODE>`, `<REPO_ROOT>`, `<RTLLM_ROOT>`, `<DATA_ROOT>`, `$USER`, `$HOME`, `$WIN_HOME`.
  - Evidence, pre-registrations and hash-frozen scripts keep their original text.

## What is gitignored, and where it lives

| Ignored | Where | Notes |
|---|---|---|
| Per-run result trees | `phase0/results/` (iteration-level files), `phase1/results/`, `phase2/results/`, `phase3/results/` | on the maintainer's machine; available on request |
| API ledgers (request and response IDs, costs) | `phase2/results/set4_api/ledgers*/`, `phase2/results/p3_api/ledgers/` | inside `phase2/results/` |
| API keys | `%USERPROFILE%\.stitch\api_keys.env` | outside the repository; `*.env` and `stitch-api-key.txt` are ignored too |
| Private notes | `private/` | local only |
| Conference PDF | `paper/paper_112_final.pdf` | ignored by name |
| LaTeX build output | `paper/build/`, `paper/overleaf/*.pdf`, `*.aux`, `*.toc` and similar | regenerable |
| Caches and environments | `__pycache__/`, `.pytest_cache/`, `.venv/` | regenerable |

Line endings: `.gitattributes` keeps LF for `*.sh`, `*.slurm` and `phase3/**`, so WSL bash and `sbatch` accept the
scripts.

**Before any commit,** both checks must pass:
- `python phase2/frontier/scan_secrets.py`, which must report 0 matches;
- `python phase2/frontier/leak_audit.py`, which must report "clean".

## Finishing Claude Haiku 4.5 on the floor tier, and removing the projections

Haiku is at 143/228 Set 4b runs. The paper projects its missing cells in two marked places only
(`paper/V10_CHANGES.md`, section 6).

**To replace the projections with measured values:**
1. Run the 85 pending runs as described in `phase2/frontier/PENDING.md`, section 1. This needs Anthropic credit and a
   pre-registration amendment.
2. Run `python phase2/frontier/analysis_set4b.py`, then `python -B phase2/frontier/make_numbers_set4.py`.
3. Set `\finaltrue` near the top of `paper/overleaf/main.tex` and `supplement.tex`. Any projection still left stops
   the build with "Projected Haiku values remain".
4. Rebuild, and re-zip.

**If Haiku cannot be completed:**
1. Run `python -B phase2/frontier/make_numbers_set4.py --no-projection`. Haiku's missing cells then read "not run".
2. Set `\finaltrue` and confirm that both files compile.
