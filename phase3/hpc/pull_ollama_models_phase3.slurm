#!/bin/bash
#SBATCH --job-name=p3_pull
#SBATCH --partition=gpu_h100_4
#SBATCH --nodelist=gpunode5
#SBATCH --gres=gpu:0
#SBATCH --cpus-per-task=4
#SBATCH --mem=16G
#SBATCH --time=03:00:00
#SBATCH --output=/scratch/soumyaj/Phase3_HPC/logs/ollama_pull_%j.log
# Pull the Phase 3 ladder (~30 GB) into Phase3_HPC/ollama_models. Exits non-zero if ANY model is missing,
# so `sbatch --dependency=afterok:<this>` never launches the run with a model absent.
# P3_PULL_MODELS="qwen2.5-coder:32b" pulls only that model: a re-pull of an already-used tag can move it to a newer
# digest, so models that already ran are never re-pulled. The presence check below still covers the whole ladder.
set -euo pipefail
source "${PHASE3_BASE:-/scratch/soumyaj/Phase3_HPC}/phase3/hpc/common_env.sh"
start_ollama; trap stop_ollama EXIT
df -h $BASE | tail -1
echo "== before"; ollama list
for m in ${P3_PULL_MODELS:-$(grep -v '^#' $BASE/phase3/hpc/models_phase3.txt)}; do echo "== pull $m"; for t in 1 2 3 4 5; do ollama pull "$m" && break; echo "retry $t"; sleep 60; done; done
echo "== after"; ollama list
df -h $BASE | tail -1
for m in $(grep -v '^#' $BASE/phase3/hpc/models_phase3.txt); do
  ollama list | awk '{print $1}' | grep -qx "$m" || { echo "MISSING $m"; exit 1; }
done
echo "ALL MODELS PRESENT"
