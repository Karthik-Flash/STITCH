# Set 3 (Scale Ladder) — Setup Brief for Claude Code

Final HPC run of the extension. Extends the capability ladder into the
14B-32B range on the models the conference paper (Table 2) tested but the
extension has not yet run, to answer one research question, not just for
completeness: **does the harmful regime persist as model capability rises,
or does it vanish?** Capable models get stuck less often, so always-on
interpretation has fewer converging runs to derail; whether the four-point
recoverable-band drop from `sem_adv` survives at 14B-32B is a real finding
either way.

Do not launch anything. Deployment is user-side (scp + sbatch), same as
Set 1 and Set 2.

## Locked parameters

- **Models (3):** `qwen2.5-coder:14b`, `qwen2.5-coder:32b`, `gemma3:27b`.
  All three are already pulled on HPC under
  `/scratch/soumyaj/AutoChipHPC/ollama_models` (confirmed via manifest
  listing). No new pull needed if that path is reused; confirm in the
  runbook.
- **Modules (17):** the recoverable-band modules only, inherited verbatim
  from `phase2/twin_analysis/module_categories.json` (the entries with
  `difficulty_tier == "recoverable"`). Do NOT re-run ceilings or floors:
  Set 1 already showed all conditions coincide there, and re-paying for
  them wastes the larger models' much slower inference. Assert exactly 17
  after filtering.
- **Conditions (4):** `baseline`, `sem_adv`, `sem_escalate`,
  `sem_escalate_restart`. Same four as Set 1. The STITCH-conditions axis is
  the point of this run (harmful-regime persistence), so baseline-only is
  NOT acceptable here.
- **N = 3**, **T = 0.1** (matched to Set 1 for direct comparability; Set 1
  is the 3-small-model half of the same ladder).
- Total: 3 models x 4 conditions x 17 modules x N=3 = **612 runs**.

## Deliverables

### 1. `phase2/set3_runner.py`

Structurally identical to `phase2/set1_runner.py` (reuse it as the template
directly; this is the same experiment with a different model list and a
module filter). Differences only:

- **Module list**: load `phase2/twin_analysis/module_categories.json`,
  filter to `difficulty_tier == "recoverable"`, assert `len == 17`. Do NOT
  load from `task_a_screen.json` and re-derive tiers; the tier assignment
  is already fixed by the Twin analysis and must match it exactly.
- **Models**: `["qwen2.5-coder:14b", "qwen2.5-coder:32b", "gemma3:27b"]`.
- Everything else identical to `set1_runner.py`: same 4 conditions, same
  N=3, same T=0.1, same `detect_outcome(sim_log, "rtllm")` pass detection,
  same `_verify_ollama_models()` startup check (for the 3 new models), same
  `$OLLAMA_HOST`-aware client, same `master_log.json` checkpoint-resume,
  same per-cell output layout, same `[N/612]` progress line, same
  `--dry-run` flag that asserts exactly 612 and exits without launching.
- Output root: `/scratch/soumyaj/Set3_HPC/results/set3_run/`.

### 2. `phase2/set3_run.slurm`

Mirror `phase2/set1_run.slurm`. Differences:

- `#SBATCH --partition=gpu_a100_8`
- `#SBATCH --nodelist=gpunode4`
- `#SBATCH --gres=gpu:1`
- `#SBATCH --time=120:00:00` (5-day A100 cap; 612 runs on slow 32B models
  may need most of it, and a single long sbatch is cleaner than H200's
  24h churn for a run this size)
- `#SBATCH --job-name=set3_scale_ladder`
- `#SBATCH --output=/scratch/soumyaj/Set3_HPC/logs/set3_%j.log`
- `#SBATCH --error=/scratch/soumyaj/Set3_HPC/logs/set3_%j.err`
- Scratch root `/scratch/soumyaj/Set3_HPC/`.
- `OLLAMA_MODELS=/scratch/soumyaj/AutoChipHPC/ollama_models` (where the 3
  larger models already live — different from Set 1/2's
  `RTLCoderHPC/ollama_models`, because these three were pulled for the
  AutoChip project, not for this one). Confirm this path in the runbook and
  verify all 3 models resolve there before launch.
- Starts its own `ollama serve` bound to `127.0.0.1:11434`, `trap ... EXIT`
  to kill on exit, readiness loop, then bash-level model-presence check for
  the 3 models before invoking Python. Same defense-in-depth as Set 1.
- Header comment: total 612 runs, expected ~130-150h at larger-model pace,
  expected 1-2 sbatches, resume behavior.

### 3. `FULL_RUN_RUNBOOK` update

Add a Set 3 section to whatever runbook exists (or a standalone
`SET3_RUNBOOK.md`) covering: scratch dir setup, scp file list (set3_runner.py,
set3_run.slurm, plus stitch_runner_hpc.py, escalation_runner_hpc.py,
error_signature.py, escalation_state.py, pass_detection.py,
module_categories.json — the same dependency set Set 1 needed, since Set 3 is
Set 1 with different models), the verify greps, the HPC-side `--dry-run`
(must print 612), the `ollama list` check against the AutoChip models dir,
launch, monitor, resubmit, download.

## Verification before delivery

- `python phase2/set3_runner.py --dry-run` prints exactly **612** (run
  locally with `--rtllm-root` pointing at the local RTLLM clone, or note it
  must be run on HPC where the path resolves — same as Set 1).
- Module count asserts to 17 after the recoverable-band filter.
- `grep` for hardcoded pass strings in `set3_runner.py` returns nothing
  outside `detect_outcome` calls.
- `python -m pytest src/interpreter/tests/` still passes (this task adds
  files, touches no existing logic).

## What NOT to do

- Do not launch anything on HPC.
- Do not modify `src/interpreter/` or any existing runner.
- Do not re-run ceilings or floors; recoverable band only.
- Do not add Gemini/Claude API models here; those are a separate later
  laptop-side task, not part of this HPC run.
- Do not commit or push; stage only.

## Analysis (after the run completes — separate task, noted for planning)

Once Set 3 finishes, the analysis question is narrow and specific:
- Recompute the recoverable-band pass rate per condition for each of the 3
  larger models, in the same shape as Set 1's tier table.
- **The key comparison**: is `sem_adv`'s pass rate still below `baseline`
  on the recoverable band for these larger models, as it was for the 3
  small models (30.7% vs 35.3%)? If yes, the harmful regime is
  capability-independent (a strong, general claim). If it shrinks or
  vanishes at 32B, that is the more nuanced finding (harmful regime is a
  small-model phenomenon) and gets its own subsection.
- Extend the capability-ladder figure (currently 5 model-conditions from
  Twin) with these 3 larger models to show the full 4B-32B span.
- This confirms or refines the conference paper's compute-ceiling finding
  with the STITCH-conditions axis the conference paper lacked.
