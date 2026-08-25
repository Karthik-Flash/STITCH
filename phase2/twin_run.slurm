#!/bin/bash
# phase2/twin_run.slurm -- Set 2: the RTLCoder twin-comparison run, full
# RTLLM scale (revised 2026-08-25, was the 75-run pilot).
# Design: phase2/TWIN_RUN_PREREG.md. Deploy + verify steps:
# phase2/HPC_RTLCODER_COMMANDS.md section 10.
#
# SCOPE (revised 2026-08-25): 42 modules (44-compatible RTLLM pool minus
# EXCLUDE={edge_detect, square_wave} -- weak-oracle testbenches, see
# IMP_PHASE2_RUNNER_HARDENING_REPORT.md §4/§6) x 5 model-conditions
# (RTLCoder native+shared, 3 Ollama models shared-only) x N=3 = 630 runs.
# Module list is loaded from task_a_screen.json AT RUNTIME by
# twin_run_runner.py (_load_module_pool()) -- NOT hardcoded here or
# there; the pilot's 5-module subset is retired. Estimated ~82h
# wall-clock (see FULL_RUN_RUNBOOK.md's estimate table) -- does NOT fit
# in one job under this partition's 3-day cap, expect 2 sequential
# sbatches (this script re-submitted after the first hits --time; the
# runner resumes from master_log.json's already-done cells, same
# incremental-checkpoint pattern as every other runner in this project).
#
# PREREQUISITE, run once, before this: sbatch pull_ollama_models.slurm
# (this script FAILS LOUDLY, does not pull inline, if any of the 3
# Ollama models aren't already present -- see step (c) below and
# twin_run_runner.py's own _verify_ollama_models(), which checks again
# at the Python level as belt-and-suspenders). pull_ollama_models.slurm
# already pulls exactly the 3 models Set 1 (gpunode4) also needs --
# Set 1 reuses this same pull, no second pull script exists or is needed.
#
# Usage: sbatch twin_run.slurm
#SBATCH --job-name=rtlcoder_twin
#SBATCH --partition=gpu_h100_4
#SBATCH --nodelist=gpunode6
#SBATCH --gres=gpu:1
#SBATCH --mem=48G
#SBATCH --cpus-per-task=8
#SBATCH --time=72:00:00
#SBATCH --output=/scratch/soumyaj/RTLCoderHPC/logs/twin_%j.log
#SBATCH --error=/scratch/soumyaj/RTLCoderHPC/logs/twin_%j.err

set -e

# ── (a) PATH + venv ──────────────────────────────────────────────────────
source /scratch/soumyaj/RTLCoderHPC/env.sh
source /scratch/soumyaj/RTLCoderHPC/venv/bin/activate
export PATH=/scratch/soumyaj/AutoChipHPC/bin:/scratch/soumyaj/oss-cad-suite/bin:$PATH
# Deployment-path robustness (2026-08-25): stitch_runner_hpc.py is
# deployed FLAT in this directory (no repo tree around it) -- state
# where src/interpreter/ (stitch_interpreter.py, pass_detection.py) and
# task_a_screen.json actually landed explicitly, rather than relying on
# a "../src/interpreter" relative guess from a flat deploy. See
# FULL_RUN_RUNBOOK.md's deployment section for exactly what goes where.
export STITCH_INTERPRETER_DIR=/scratch/soumyaj/RTLCoderHPC/src/interpreter
export TASK_A_SCREEN_JSON=/scratch/soumyaj/RTLCoderHPC/task_a_screen.json
echo "=== which ollama / iverilog ==="
which ollama
which iverilog

# ── (b) Ollama server: OWN server, started inside THIS job ─────────────
# Unlike the laptop, HPC's ollama binary is not on PATH by default and
# nothing is already listening -- this job starts and owns its own
# server for its own lifetime, same pattern as AutoChip's run_*.slurm
# (AutoChip_HPC_Reference.docx section 4.3's per-job port note; this job
# only ever runs ONE ollama server at a time, so there's no multi-job
# port-collision risk to design around -- the default port is fine, set
# explicitly rather than left implicit).
export OLLAMA_MODELS=/scratch/soumyaj/RTLCoderHPC/ollama_models
export OLLAMA_HOST=127.0.0.1:11434
echo "=== starting ollama serve (OLLAMA_HOST=$OLLAMA_HOST, OLLAMA_MODELS=$OLLAMA_MODELS) ==="
ollama serve > /scratch/soumyaj/RTLCoderHPC/logs/ollama_twin_${SLURM_JOB_ID}.log 2>&1 &
OLLAMA_PID=$!
# `trap ... EXIT` guarantees the server gets killed on ANY exit path --
# success, an early `exit 1` above, or `set -e` aborting on the python
# call's failure below. A plain `kill` placed only at the bottom of the
# script would NOT run if `set -e` aborts before reaching it.
trap 'kill $OLLAMA_PID 2>/dev/null || true' EXIT

echo "=== waiting for ollama to be ready ==="
READY=0
for i in $(seq 1 15); do
    if ollama list > /dev/null 2>&1; then
        READY=1
        break
    fi
    sleep 2
done
if [ "$READY" -ne 1 ]; then
    echo "FATAL: ollama server never became ready (30s). Check ollama_twin_${SLURM_JOB_ID}.log."
    exit 1  # trap above still fires and kills OLLAMA_PID
fi

# ── (c) confirm the 3 models are present -- FAIL LOUDLY if not, do not
# pull inline (a multi-GB download here would eat this job's own
# wall-clock budget silently). If this fires, the fix is: cancel this
# job, run pull_ollama_models.slurm once, then resubmit this one.
echo "=== confirming required Ollama models are present ==="
ollama list
MISSING=0
for m in deepseek-coder:6.7b gemma3:4b llama3.1:latest; do
    if ! ollama list | grep -q "^${m}"; then
        echo "MISSING: $m"
        MISSING=1
    fi
done
if [ "$MISSING" -ne 0 ]; then
    echo "FATAL: one or more required Ollama models are missing from"
    echo "  OLLAMA_MODELS=$OLLAMA_MODELS. Run 'sbatch pull_ollama_models.slurm'"
    echo "  once, then resubmit this job. Not pulling inline -- see comment above."
    exit 1  # trap above still fires and kills OLLAMA_PID
fi
echo "All 3 Ollama models present."

# ── (d) run the twin comparison ─────────────────────────────────────────
# twin_run_runner.py reads $OLLAMA_HOST itself (see that file's module
# docstring / OLLAMA_HOST constant) -- it and this script's server are
# structurally bound to the same host:port, not just hoped to match.
# No manual exit-code juggling needed below: if this fails, `set -e`
# aborts the script with that same exit code, and the trap above still
# fires on the way out either way.
cd /scratch/soumyaj/RTLCoderHPC
python twin_run_runner.py
