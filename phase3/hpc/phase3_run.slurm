#!/bin/bash
#SBATCH --job-name=p3_run
#SBATCH --partition=gpu_h100_4
#SBATCH --nodelist=gpunode5
#SBATCH --gres=gpu:1
#SBATCH --cpus-per-task=8
#SBATCH --mem=64G
#SBATCH --time=72:00:00
#SBATCH --output=/scratch/soumyaj/Phase3_HPC/logs/p3_run_%j.log
# Phase 3 main run: 6 models x 11 tasks x 5 conditions x N=3 = 990 runs, T=0.1, max 6 iterations (all conditions).
# One ollama serve, models run sequentially (order = models_phase3.txt). Resubmit the same script to resume:
# every run with a metrics.json is skipped.
set -euo pipefail
source "${PHASE3_BASE:-/scratch/soumyaj/Phase3_HPC}/phase3/hpc/common_env.sh"
cd $BASE
nvidia-smi --query-gpu=name,memory.total --format=csv || true
start_ollama; trap stop_ollama EXIT
SP=""; [ -f $BASE/phase3/runner/system_prompt.txt ] && SP="--system-prompt-file $BASE/phase3/runner/system_prompt.txt"
[ -z "$SP" ] && echo "WARNING: phase3/runner/system_prompt.txt absent -> runner DEFAULT_SYSTEM_PROMPT used (not production)"
# Overrides for the pilot (HPC_PHASE3_COMMANDS.md Part E):  P3_MODELS="llama3.1:latest"
#   P3_EXTRA_ARGS="--tasks mux3 register_4bit register_1bit ni_flit_pack --reps 1"  P3_OUT=$BASE/results/phase3_pilot
MODELS=${P3_MODELS:-$(grep -v '^#' phase3/hpc/models_phase3.txt | tr '\n' ' ')}
OUT=${P3_OUT:-$BASE/results/phase3_run}
for m in $MODELS; do
  echo "===== $(date) model $m"
  python3 phase3/runner/stitch_runner_p3.py --model "$m" --host "http://$OLLAMA_HOST" --reps 3 \
      --temperature 0.1 --max-iters 6 --out $OUT $SP ${P3_EXTRA_ARGS:-} || echo "model $m exited non-zero (continuing)"
done
echo "===== $(date) all models finished"
