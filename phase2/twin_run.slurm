#!/bin/bash
# phase2/twin_run.slurm -- the RTLCoder twin-comparison run (75 runs).
# Design: phase2/TWIN_RUN_PREREG.md. Deploy + verify steps:
# phase2/HPC_RTLCODER_COMMANDS.md section 10.
#
# PREREQUISITE, run once, before this: sbatch pull_ollama_models.slurm
# (this script FAILS LOUDLY, does not pull inline, if any of the 3
# Ollama models aren't already present -- see step (c) below and
# twin_run_runner.py's own _verify_ollama_models(), which checks again
# at the Python level as belt-and-suspenders).
#
# Usage: sbatch twin_run.slurm
#SBATCH --job-name=rtlcoder_twin
#SBATCH --partition=gpu_h100_4
#SBATCH --nodelist=gpunode6
#SBATCH --gres=gpu:1
#SBATCH --mem=48G
#SBATCH --cpus-per-task=8
#SBATCH --time=08:00:00
#SBATCH --output=/scratch/soumyaj/RTLCoderHPC/logs/twin_%j.log
#SBATCH --error=/scratch/soumyaj/RTLCoderHPC/logs/twin_%j.err

set -e

# ── (a) PATH + venv ──────────────────────────────────────────────────────
source /scratch/soumyaj/RTLCoderHPC/env.sh
source /scratch/soumyaj/RTLCoderHPC/venv/bin/activate
export PATH=/scratch/soumyaj/AutoChipHPC/bin:/scratch/soumyaj/oss-cad-suite/bin:$PATH
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
