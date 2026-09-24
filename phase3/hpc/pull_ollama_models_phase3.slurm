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
set -euo pipefail
source "${PHASE3_BASE:-/scratch/soumyaj/Phase3_HPC}/phase3/hpc/common_env.sh"
start_ollama; trap stop_ollama EXIT
for m in $(grep -v '^#' $BASE/phase3/hpc/models_phase3.txt); do echo "== pull $m"; ollama pull "$m"; done
ollama list
for m in $(grep -v '^#' $BASE/phase3/hpc/models_phase3.txt); do
  ollama list | awk '{print $1}' | grep -qx "$m" || { echo "MISSING $m"; exit 1; }
done
echo "ALL MODELS PRESENT"
