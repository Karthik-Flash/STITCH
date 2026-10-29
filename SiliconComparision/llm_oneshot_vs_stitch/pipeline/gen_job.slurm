#!/bin/bash
#SBATCH --job-name=stitch_gen
#SBATCH --partition=gpu_h200_8
#SBATCH --nodelist=<GPU_NODE>
#SBATCH --gres=gpu:1
#SBATCH --cpus-per-task=8
#SBATCH --mem=48G
#SBATCH --time=08:00:00
#SBATCH --output=/scratch/%u/STITCH_GEN/logs/gen_%j.log
# LLM one-shot vs STITCH on the 2x2 mesh: drift gate -> one-shot generation -> two feedback arms -> summary.
# One job, qwen2.5-coder:32b, T=0.1, budget 6, N=1. Resumable: resubmit the same script; finished one-shot modules
# (runs/oneshot/<m>/record.json) and finished arm runs (metrics.json) are skipped. The gate re-runs each time.
# Overrides: GEN_MODEL, GEN_MODULES="encoder mux" (subset), GEN_FULL_ROUTER=0 (skip the whole-router bonus prompt).
set -euo pipefail
source "${GEN_BASE:-/scratch/$USER/STITCH_GEN}/SiliconComparision/llm_oneshot_vs_stitch/pipeline/hpc_env.sh"
cd $STUDY
MODEL=${GEN_MODEL:-qwen2.5-coder:32b}
MODS=${GEN_MODULES:+--modules $GEN_MODULES}
FULL=$([ "${GEN_FULL_ROUTER:-1}" = 1 ] && [ -z "${GEN_MODULES:-}" ] && echo --full-router || true)
echo "== $(date) node $(hostname) model $MODEL"
touch_deps
nvidia-smi --query-gpu=name,memory.total --format=csv || true
which python3 yosys verilator iverilog ollama

echo "== $(date) [1/4] drift gate"
python3 pipeline/gate.py

echo "== $(date) [2/4] one-shot generation"
start_ollama; trap stop_ollama EXIT
ollama list | awk '{print $1}' | grep -qx "$MODEL" || { echo "MISSING model $MODEL in $OLLAMA_MODELS"; exit 1; }
python3 pipeline/oneshot_gen.py --model "$MODEL" --host "http://$OLLAMA_HOST" --temperature 0.1 $MODS $FULL

echo "== $(date) [3/4] feedback arms (baseline = simloop, sem_esc_restart_v3 = stitch)"
python3 pipeline/run_arms.py --model "$MODEL" --host "http://$OLLAMA_HOST" --max-iters 6 --reps 1 $MODS

echo "== $(date) [4/4] summary"
python3 pipeline/summarize.py --model "$MODEL" $MODS
echo "== $(date) JOB DONE"
