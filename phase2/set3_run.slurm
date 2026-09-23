#!/bin/bash
# phase2/set3_run.slurm -- Set 3: the scale ladder. Same STITCH-conditions
# sweep as Set 1 (baseline/sem_adv/sem_escalate/sem_escalate_restart), on
# 3 larger Ollama models (qwen2.5-coder:14b, qwen2.5-coder:32b,
# gemma3:27b) the conference paper's Table 2 tested but the extension
# hasn't run yet, restricted to the recoverable-band module pool only.
# Research question: does the harmful regime (sem_adv below baseline on
# the recoverable band, phase2/SET1_ANALYSIS.md's tier-split result)
# persist as model capability rises from 4B to 32B, or does it vanish?
# Runner: phase2/set3_runner.py (read that file's docstring first).
#
# SCOPE: 17 recoverable-band modules (difficulty_tier == "recoverable" in
# phase2/twin_analysis_SET2/module_categories.json, loaded verbatim --
# NOT re-derived here or in the runner) x 3 Ollama models x 4 conditions
# (baseline, sem_adv, sem_escalate, sem_escalate_restart) x N=3 =
# 612 runs. Module list is resolved from module_categories.json +
# task_a_screen.json AT RUNTIME by set3_runner.py (_load_module_pool())
# -- never hardcoded here or there. Expected ~130-150h wall-clock at
# these larger models' slower inference pace (14B-32B vs. Set 1's 4-7B) --
# expect 1-2 sbatches against this partition's 120h cap. Re-submitting
# this SAME script picks up cleanly from master_log.json's already-done
# cells (same incremental-checkpoint pattern as every other runner in
# this project) -- do not create a separate "part 2" script.
#
# PREREQUISITE (2026 scratch wipe): the AutoChip scratch tree that used
# to hold these 3 models was fully wiped, so Set 3 no longer reuses it --
# it now pulls and owns its own copy under
# OLLAMA_MODELS=/scratch/soumyaj/Set3_HPC/ollama_models, via
# phase2/pull_ollama_models_set3.slurm (mirrors the existing
# phase2/pull_ollama_models.slurm pattern -- run it ONCE before this
# script, same as that script is required once before twin_run.slurm/
# set1_run.slurm). This script still FAILS LOUDLY, does not pull inline,
# if any of the 3 models aren't already present (step (c) below), and
# set3_runner.py's own _verify_ollama_models() checks again at the
# Python level as belt-and-suspenders, same pattern Set 1/Set 2 already
# established. The `ollama` binary itself is also no longer at
# AutoChipHPC/bin (wiped) -- it now lives at
# /scratch/soumyaj/Set3_HPC/bin, and iverilog/verilator/yosys come from
# /scratch/soumyaj/oss-cad-suite/bin (being re-extracted there after the
# wipe -- confirm it landed before launching, same as any prior PATH
# assumption in this project).
#
# NODE REUSE, NOT CONCURRENT: this targets gpunode4, the SAME node Set 1
# used -- unlike Set 1/Set 2, which ran concurrently on separate physical
# nodes, Set 3 is a later, single, sequential job (Set 1 has already
# completed by the time this runs). No two-node-independence concern
# here. Scratch dir (Set3_HPC/), log filenames (set3_%j.*), and results
# tree (results/set3_run/) are still fully disjoint from Set 1's/Set 2's,
# as a matter of hygiene, not because of any concurrency risk.
#
# Usage: sbatch set3_run.slurm
#SBATCH --job-name=set3_scale_ladder
#SBATCH --partition=gpu_a100_8
#SBATCH --nodelist=gpunode4
#SBATCH --gres=gpu:1
#SBATCH --mem=48G
#SBATCH --cpus-per-task=8
#SBATCH --time=120:00:00
#SBATCH --output=/scratch/soumyaj/Set3_HPC/logs/set3_%j.log
#SBATCH --error=/scratch/soumyaj/Set3_HPC/logs/set3_%j.err

set -e

# ── (a) PATH + venv ──────────────────────────────────────────────────────
# venv is a FRESH build here (2026 scratch wipe -- the RTLCoderHPC venv
# this used to symlink to is gone too; see docs/FULL_RUN_RUNBOOK.md's setup
# section for the `python -m venv` + `pip install openai` steps). No
# HF_HOME needed -- Ollama-only run, no torch/transformers.
source /scratch/soumyaj/Set3_HPC/venv/bin/activate
export PATH=/scratch/soumyaj/Set3_HPC/bin:/scratch/soumyaj/oss-cad-suite/bin:$PATH
export RTLLM_ROOT=/scratch/soumyaj/RTLCoderHPC/RTLLM
# Deliberately the SAME checkout Set 1/Set 2 read -- RTLLM is read-only
# I/O for every job; sharing one checkout avoids yet another
# multi-hundred-MB clone. See docs/FULL_RUN_RUNBOOK.md / docs/FULL_RUN_RUNBOOK.md.
export STITCH_INTERPRETER_DIR=/scratch/soumyaj/Set3_HPC/src/interpreter
export TASK_A_SCREEN_JSON=/scratch/soumyaj/Set3_HPC/task_a_screen.json
export MODULE_CATEGORIES_JSON=/scratch/soumyaj/Set3_HPC/module_categories.json
echo "=== which ollama / iverilog ==="
which ollama
which iverilog

# ── (b) Ollama server: OWN server, started inside THIS job ─────────────
# Same pattern as set1_run.slurm/twin_run.slurm. OLLAMA_MODELS points at
# Set 3's OWN pulled models now (post-wipe -- see
# phase2/pull_ollama_models_set3.slurm, run once before this script),
# not AutoChipHPC's (that tree was wiped and is no longer reused).
# Binding to 127.0.0.1:11434 is safe: by the time Set 3 runs, Set 1/Set 2
# have already completed (this is a later, sequential job, not
# concurrent with either), so there is no port-collision risk to reason
# about here the way set1_run.slurm/twin_run.slurm had to for each other.
export OLLAMA_MODELS=/scratch/soumyaj/Set3_HPC/ollama_models
export OLLAMA_HOST=127.0.0.1:11434
echo "=== starting ollama serve (OLLAMA_HOST=$OLLAMA_HOST, OLLAMA_MODELS=$OLLAMA_MODELS) ==="
ollama serve > /scratch/soumyaj/Set3_HPC/logs/ollama_set3_${SLURM_JOB_ID}.log 2>&1 &
OLLAMA_PID=$!
# `trap ... EXIT` guarantees the server gets killed on ANY exit path --
# success, an early `exit 1` above, or `set -e` aborting on the python
# call's failure below. Same reasoning as set1_run.slurm/twin_run.slurm.
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
    echo "FATAL: ollama server never became ready (30s). Check ollama_set3_${SLURM_JOB_ID}.log."
    exit 1  # trap above still fires and kills OLLAMA_PID
fi

# ── (c) confirm the 3 models are present -- FAIL LOUDLY if not, do not
# pull inline (a multi-GB download here would eat this job's own
# wall-clock budget silently). If this fires, the fix is: cancel this
# job, run `sbatch pull_ollama_models_set3.slurm` once, then resubmit
# this one.
echo "=== confirming required Ollama models are present ==="
ollama list
MISSING=0
for m in qwen2.5-coder:14b qwen2.5-coder:32b gemma3:27b; do
    if ! ollama list | grep -q "^${m}"; then
        echo "MISSING: $m"
        MISSING=1
    fi
done
if [ "$MISSING" -ne 0 ]; then
    echo "FATAL: one or more required Ollama models are missing from"
    echo "  OLLAMA_MODELS=$OLLAMA_MODELS. Run"
    echo "  'sbatch /scratch/soumyaj/Set3_HPC/pull_ollama_models_set3.slurm'"
    echo "  once, then resubmit this job."
    exit 1  # trap above still fires and kills OLLAMA_PID
fi
echo "All 3 Ollama models present."

# ── (d) dry-run sanity check, THEN the real run ─────────────────────────
# Cheap, fast, no Ollama/iverilog touched -- catches a scope regression
# (wrong module count, wrong recoverable-band filter) before burning any
# real wall-clock. Fails the whole job immediately (set -e) if the
# assertion in set3_runner.py's own --dry-run path doesn't hold.
cd /scratch/soumyaj/Set3_HPC
echo "=== dry-run sanity check ==="
python set3_runner.py --dry-run

echo "=== starting the real run ==="
python set3_runner.py
