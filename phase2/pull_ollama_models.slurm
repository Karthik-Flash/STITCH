#!/bin/bash
# phase2/pull_ollama_models.slurm -- ONE-TIME setup job. Run this ONCE,
# before ever submitting twin_run.slurm. Mirrors AutoChip's
# pull_models.sh pattern (AutoChip_HPC_Reference.docx section 3.2):
# starts a throwaway ollama server just long enough to pull the 3 models
# this run needs, then kills it -- the real, long-running server for the
# actual twin run is started separately, inside twin_run.slurm itself.
#
# Per AutoChip_HPC_Reference.docx's own pull list (qwen2.5-coder:32b,
# gemma3:27b, qwen2.5-coder:14b), NONE of the 3 models this run needs
# (deepseek-coder:6.7b, gemma3:4b, llama3.1:latest) were already pulled
# for that project -- different names, different sizes. This job pulls
# all 3 fresh into THIS project's own OLLAMA_MODELS directory, kept
# separate from AutoChipHPC/'s so this stays self-contained. Re-run
# `ollama list` yourself first if you want to double-check nothing's
# changed since this comment was written.
#
# DUAL-USE (2026-08-25): Set 1 (phase2/set1_runner.py /
# phase2/set1_run.slurm, gpunode4) needs the EXACT SAME 3 models --
# deepseek-coder:6.7b, gemma3:4b, llama3.1:latest, nothing more. Set 1's
# OLLAMA_MODELS points directly at this job's output directory
# (read-only, safe -- see FULL_RUN_RUNBOOK.md's two-node-independence
# section) rather than pulling a second copy. Run this script ONCE,
# before launching either twin_run.slurm OR set1_run.slurm -- there is
# no separate pull script for Set 1.
#
# Usage: sbatch pull_ollama_models.slurm
#SBATCH --job-name=rtlcoder_ollama_pull
#SBATCH --partition=gpu_h100_4
#SBATCH --nodelist=gpunode6
#SBATCH --gres=gpu:1
#SBATCH --mem=32G
#SBATCH --cpus-per-task=4
#SBATCH --time=01:30:00
#SBATCH --output=/scratch/soumyaj/RTLCoderHPC/logs/ollama_pull_%j.log
#SBATCH --error=/scratch/soumyaj/RTLCoderHPC/logs/ollama_pull_%j.err

set -e

export PATH=/scratch/soumyaj/AutoChipHPC/bin:$PATH
export OLLAMA_MODELS=/scratch/soumyaj/RTLCoderHPC/ollama_models
export OLLAMA_HOST=127.0.0.1:11434
mkdir -p "$OLLAMA_MODELS"

echo "=== starting throwaway ollama server for the pull ==="
ollama serve > /scratch/soumyaj/RTLCoderHPC/logs/ollama_pull_setup_${SLURM_JOB_ID}.log 2>&1 &
OLLAMA_PID=$!
# trap, not a manual kill at the bottom -- guarantees cleanup even if a
# pull fails partway and `set -e` aborts the script early.
trap 'kill $OLLAMA_PID 2>/dev/null || true' EXIT

echo "=== waiting for it to be ready ==="
READY=0
for i in $(seq 1 15); do
    if ollama list > /dev/null 2>&1; then
        READY=1
        break
    fi
    sleep 2
done
if [ "$READY" -ne 1 ]; then
    echo "FATAL: ollama server never became ready (30s). Check ollama_pull_setup_${SLURM_JOB_ID}.log."
    exit 1
fi

echo "=== pulling the 3 models this run needs ==="
ollama pull deepseek-coder:6.7b
ollama pull gemma3:4b
ollama pull llama3.1:latest

echo "=== verifying ==="
ollama list

echo "Done. Models live under $OLLAMA_MODELS -- twin_run.slurm points OLLAMA_MODELS at the same path."
