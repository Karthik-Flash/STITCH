#!/bin/bash
# phase2/set1_run.slurm -- Set 1: STITCH conditions sweep, full RTLLM
# scale, on gpunode4 (A100, gpu_a100_8). Paper Graph Set 1: does
# sem_escalate beat MLCAD's always-on sem_adv on cost + pass rate.
# Runner: phase2/set1_runner.py (read that file's docstring first).
#
# SCOPE: 42 modules (44-compatible RTLLM pool minus
# EXCLUDE={edge_detect, square_wave} -- weak-oracle testbenches, see
# IMP_PHASE2_RUNNER_HARDENING_REPORT.md §4/§6) x 3 Ollama models
# (gemma3:4b, llama3.1:latest, deepseek-coder:6.7b) x 4 conditions
# (baseline, sem_adv, sem_escalate, sem_escalate_restart) x N=3 =
# 1,512 runs. Module list is loaded from task_a_screen.json AT RUNTIME
# by set1_runner.py (_load_module_pool()) -- never hardcoded here or
# there. Estimated ~198h wall-clock (see FULL_RUN_RUNBOOK.md's estimate
# table) -- does NOT fit in one job under this partition's 5-day cap;
# expect 2 sequential sbatches (1st fills the 120h cap, 2nd cleans the
# ~80h remainder). Re-submitting this SAME script picks up cleanly from
# master_log.json's already-done cells (same incremental-checkpoint
# pattern as every other runner in this project) -- do not create a
# separate "part 2" script.
#
# PREREQUISITE, run once, before this: sbatch pull_ollama_models.slurm
# (on Node 2 / RTLCoderHPC -- it already pulls exactly the 3 models this
# run also needs; Set 1 reuses that pull directly, via the SAME
# OLLAMA_MODELS directory, read-only from here. No separate pull script
# exists or is needed -- see FULL_RUN_RUNBOOK.md). This script FAILS
# LOUDLY, does not pull inline, if any of the 3 models aren't already
# present (step (c) below), and set1_runner.py's own
# _verify_ollama_models() checks again at the Python level as
# belt-and-suspenders, same pattern twin_run.slurm/twin_run_runner.py
# already established.
#
# TWO-NODE INDEPENDENCE (see FULL_RUN_RUNBOOK.md for the full checklist):
# this job binds its OWN ollama serve to 127.0.0.1:11434 -- safe despite
# twin_run.slurm doing the exact same thing, because gpunode4 and
# gpunode6 are different physical nodes, each with its own loopback.
# Zero port-collision risk. Scratch dirs, log filenames, and results
# trees are fully disjoint from Set 2's (Set1_HPC/ vs. RTLCoderHPC/).
# OLLAMA_MODELS is the one thing genuinely shared between the two jobs --
# safe because both only ever READ from it (never write/pull inline).
#
# Usage: sbatch set1_run.slurm
#SBATCH --job-name=set1_stitch_conditions
#SBATCH --partition=gpu_a100_8
#SBATCH --nodelist=gpunode4
#SBATCH --gres=gpu:1
#SBATCH --mem=48G
#SBATCH --cpus-per-task=8
#SBATCH --time=120:00:00
#SBATCH --output=/scratch/soumyaj/Set1_HPC/logs/set1_%j.log
#SBATCH --error=/scratch/soumyaj/Set1_HPC/logs/set1_%j.err

set -e

# ── (a) PATH + venv ──────────────────────────────────────────────────────
# venv is a symlink to RTLCoderHPC's venv (identical Python deps --
# openai, torch/transformers are NOT needed here, no RTLCoder in Set 1,
# but reusing one venv is simpler than maintaining two -- see
# FULL_RUN_RUNBOOK.md step 2). No HF_HOME needed -- Ollama-only run.
source /scratch/soumyaj/Set1_HPC/venv/bin/activate
export PATH=/scratch/soumyaj/AutoChipHPC/bin:/scratch/soumyaj/oss-cad-suite/bin:$PATH
export RTLLM_ROOT=/scratch/soumyaj/RTLCoderHPC/RTLLM
# Deliberately the SAME checkout Set 2 reads -- RTLLM is read-only I/O
# for both jobs, on different physical nodes; sharing one checkout avoids
# a second multi-hundred-MB clone. See FULL_RUN_RUNBOOK.md.
export STITCH_INTERPRETER_DIR=/scratch/soumyaj/Set1_HPC/src/interpreter
export TASK_A_SCREEN_JSON=/scratch/soumyaj/Set1_HPC/task_a_screen.json
echo "=== which ollama / iverilog ==="
which ollama
which iverilog

# ── (b) Ollama server: OWN server, started inside THIS job ─────────────
# Same pattern as twin_run.slurm -- safe on a DIFFERENT physical node
# (gpunode4 vs. gpunode6), see the two-node-independence note above.
# OLLAMA_MODELS points at Set 2's already-pulled models (read-only,
# shared, safe -- see prerequisite note above); this job never pulls.
export OLLAMA_MODELS=/scratch/soumyaj/RTLCoderHPC/ollama_models
export OLLAMA_HOST=127.0.0.1:11434
echo "=== starting ollama serve (OLLAMA_HOST=$OLLAMA_HOST, OLLAMA_MODELS=$OLLAMA_MODELS) ==="
ollama serve > /scratch/soumyaj/Set1_HPC/logs/ollama_set1_${SLURM_JOB_ID}.log 2>&1 &
OLLAMA_PID=$!
# `trap ... EXIT` guarantees the server gets killed on ANY exit path --
# success, an early `exit 1` above, or `set -e` aborting on the python
# call's failure below. Same reasoning as twin_run.slurm: a plain `kill`
# only at the bottom would NOT run if `set -e` aborts before reaching it.
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
    echo "FATAL: ollama server never became ready (30s). Check ollama_set1_${SLURM_JOB_ID}.log."
    exit 1  # trap above still fires and kills OLLAMA_PID
fi

# ── (c) confirm the 3 models are present -- FAIL LOUDLY if not, do not
# pull inline (a multi-GB download here would eat this job's own
# wall-clock budget silently). If this fires, the fix is: cancel this
# job, run pull_ollama_models.slurm (on Node 2) once, then resubmit this one.
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
    echo "  OLLAMA_MODELS=$OLLAMA_MODELS. Run"
    echo "  'sbatch /scratch/soumyaj/RTLCoderHPC/pull_ollama_models.slurm'"
    echo "  once (on Node 2 -- Set 1 does not have its own pull script,"
    echo "  see FULL_RUN_RUNBOOK.md), then resubmit this job."
    exit 1  # trap above still fires and kills OLLAMA_PID
fi
echo "All 3 Ollama models present."

# ── (d) dry-run sanity check, THEN the real run ─────────────────────────
# Cheap, fast, no Ollama/iverilog touched -- catches a scope regression
# (wrong module count) before burning any real wall-clock. Fails the
# whole job immediately (set -e) if the assertion in set1_runner.py's
# own --dry-run path doesn't hold.
cd /scratch/soumyaj/Set1_HPC
echo "=== dry-run sanity check ==="
python set1_runner.py --dry-run

echo "=== starting the real run ==="
python set1_runner.py
