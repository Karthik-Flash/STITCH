#!/bin/bash
# phase2/pull_ollama_models_set3.slurm -- ONE-TIME setup job. Run this
# ONCE, before ever submitting set3_run.slurm. Mirrors
# phase2/pull_ollama_models.slurm's pattern exactly (which itself mirrors
# AutoChip's pull_models.sh, AutoChip_HPC_Reference.docx section 3.2):
# starts a throwaway ollama server just long enough to pull the 3 models
# this run needs, then kills it -- the real, long-running server for the
# actual Set 3 run is started separately, inside set3_run.slurm itself.
#
# WHY THIS SCRIPT EXISTS SEPARATELY FROM THE ORIGINAL PULL SCRIPT (2026
# scratch wipe): Set 3 originally planned to reuse qwen2.5-coder:14b/32b
# and gemma3:27b from AutoChipHPC/ollama_models (already pulled for that
# project, confirmed via manifest listing -- see
# phase2/SET3_ANALYSIS.md / set3_runner.py's earlier module
# docstring). The scratch tree holding that cache was fully wiped, so
# that reuse is no longer possible -- Set 3 now pulls and owns its own
# copy, under ITS OWN OLLAMA_MODELS directory, same self-contained
# pattern the original pull_ollama_models.slurm already established for
# Set 1/Set 2's 3 (different, smaller) models.
#
# Usage: sbatch pull_ollama_models_set3.slurm
#SBATCH --job-name=set3_ollama_pull
#SBATCH --partition=gpu_a100_8
#SBATCH --nodelist=<GPU_NODE>
#SBATCH --gres=gpu:1
#SBATCH --mem=32G
#SBATCH --cpus-per-task=4
#SBATCH --time=02:30:00
#SBATCH --output=/scratch/%u/Set3_HPC/logs/ollama_pull_%j.log
#SBATCH --error=/scratch/%u/Set3_HPC/logs/ollama_pull_%j.err

set -e

# `ollama` itself lives at /scratch/$USER/Set3_HPC/bin now (the
# AutoChipHPC/bin copy this used to reuse was wiped along with
# everything else under that tree) -- confirm it's actually there before
# running this (same re-deploy-first discipline every other script in
# this project follows for a post-wipe scratch tree).
export PATH=/scratch/$USER/Set3_HPC/bin:$PATH
export OLLAMA_MODELS=/scratch/$USER/Set3_HPC/ollama_models
export OLLAMA_HOST=127.0.0.1:11434
mkdir -p "$OLLAMA_MODELS"

echo "=== starting throwaway ollama server for the pull ==="
ollama serve > /scratch/$USER/Set3_HPC/logs/ollama_pull_setup_${SLURM_JOB_ID}.log 2>&1 &
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

echo "=== pulling the 3 models Set 3 needs ==="
ollama pull qwen2.5-coder:14b
ollama pull qwen2.5-coder:32b
ollama pull gemma3:27b

echo "=== verifying ==="
ollama list

echo "Done. Models live under $OLLAMA_MODELS -- set3_run.slurm points OLLAMA_MODELS at the same path."
