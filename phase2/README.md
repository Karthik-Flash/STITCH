# Phase 2: STITCH at RTLLM scale, and the API study

Phase 2 runs STITCH on the external RTLLM v2.1 benchmark (42 modules) with replication.

**The runs, on the GPU cluster:**
- Set 2, the fine-tuning twin (`twin_run_runner.py`), 630 runs;
- Set 1, small models (`set1_runner.py`), 1,512 runs;
- Set 3, large models (`set3_runner.py`), 612 runs.

All three share the cluster ports of the runner (`stitch_runner_hpc.py`, `escalation_runner_hpc.py`) and the Slurm
scripts (`*.slurm`).

**Analyses and reports:**

| Set | Analysis | Report |
|---|---|---|
| Twin | `twin_analysis_SET2/`, whose tiers are in `module_categories.json` | `TWIN_RUN_ANALYSIS.md` |
| Set 1 | `set1_analysis/` | `SET1_ANALYSIS.md` |
| Set 3 | `set3_analysis/` | `SET3_ANALYSIS.md` |

The Twin pre-registration is `TWIN_RUN_PREREG.md`.

**`frontier/` is the API study** (Sets 4, 4b and 4c), with commercial non-reasoning models:
- pre-registration `SET4_PREREG.md`, report `SET4_REPORT.md`;
- evidence snapshots in `frontier/evidence/`;
- the Phase 3 API ladder rows in `frontier/p3_api/`;
- `frontier/PENDING.md`, the only open item.

**In the paper**, Sections 6 to 8 of `../paper/overleaf/main.tex`.

**See also:**
- `../docs/PHASES_EXPLAINED.md`, section "Phase 2";
- `../docs/HPC_GUIDE.md`, the cluster commands;
- `../REPO_INDEX.md`, the regeneration commands.

Result trees (`results/`) are gitignored and kept locally.
