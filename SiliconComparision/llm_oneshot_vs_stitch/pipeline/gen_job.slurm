#!/bin/bash
#SBATCH --job-name=stitch_gen
#SBATCH --gres=gpu:1
#SBATCH --cpus-per-task=4
#SBATCH --mem=48G
#SBATCH --time=24:00:00
#SBATCH --output=/scratch/%u/STITCH_GEN/logs/gen_%j.log
# LLM one-shot vs STITCH on the 2x2 mesh: drift gate -> preflight -> one-shot generation -> two feedback arms -> summary.
# Choose the node on the sbatch line: sbatch --partition=<PART> --nodelist=<NODE> pipeline/gen_job.slurm
# One job, qwen2.5-coder:32b, T=0.1, num_ctx 32768, budget 6, N=1, llama-server threads = --cpus-per-task.
# --time: remaining work at 8 tok/s (the slowest speed the first-call check accepts) x 1.5, from pipeline/speed.py
# (reports/SPEED.md). Resumable: resubmit the same script; finished one-shot modules and arm runs are skipped,
# infra errors (timeout, connection) and incomplete folders are retried.
# Exit codes: gate/preflight failure 1; first-call check failure (llama-server threads or speed < 8 tok/s) 3;
# finished with infra errors 2 (the log lists them; resubmit).
# Overrides: GEN_TASKS=encoder,mux (comma-separated subset for one-shot and both arms, empty = all 34; results go to
# the normal runs/ dirs, so a later full run skips them), GEN_MODEL, GEN_FULL_ROUTER=1 (whole-router bonus; off by
# default: its prompt alone is 32,290 of 32,768 tokens, reports/PREDEPLOY_BUDGET.md).
set -euo pipefail
source "${GEN_BASE:-/scratch/$USER/STITCH_GEN}/SiliconComparision/llm_oneshot_vs_stitch/pipeline/hpc_env.sh"
cd $STUDY
MODEL=${GEN_MODEL:-qwen2.5-coder:32b}
export GEN_TASKS=${GEN_TASKS:-}
MODS=${GEN_TASKS:+--modules ${GEN_TASKS//,/ }}
FULL=$([ "${GEN_FULL_ROUTER:-0}" = 1 ] && [ -z "$GEN_TASKS" ] && echo --full-router || true)
echo "== $(date) node $(hostname) job ${SLURM_JOB_ID:-none} cpus ${SLURM_CPUS_PER_TASK:-?} model $MODEL tasks ${GEN_TASKS:-all}"
trap stop_ollama EXIT

echo "== $(date) [1/5] drift gate"
python3 pipeline/gate.py || { echo "GATE FAILED: nothing generated"; exit 1; }

echo "== $(date) [2/5] preflight"
touch_deps
nvidia-smi -L
start_ollama
python3 pipeline/preflight.py --model "$MODEL" --host "http://$OLLAMA_HOST" || { echo "PREFLIGHT FAILED: nothing generated"; exit 1; }

echo "== $(date) [3/5] one-shot generation (${GEN_TASKS:-all 34 tasks}; 34 finished records when done)"
rc1=0; python3 pipeline/oneshot_gen.py --model "$MODEL" --host "http://$OLLAMA_HOST" --temperature 0.1 $MODS $FULL || rc1=$?
[ $rc1 = 3 ] && { echo "FIRST-CALL CHECK FAILED (threads or speed): stopping"; exit 3; }
[ $rc1 != 0 ] && [ $rc1 != 2 ] && { echo "ONE-SHOT FAILED (exit $rc1): stopping"; exit $rc1; }

echo "== $(date) [4/5] feedback arms (baseline = simloop, sem_esc_restart_v3 = stitch)"
rc2=0; python3 pipeline/run_arms.py --model "$MODEL" --host "http://$OLLAMA_HOST" --max-iters 6 --reps 1 $MODS || rc2=$?
[ $rc2 = 3 ] && { echo "FIRST-CALL CHECK FAILED (threads or speed): stopping"; exit 3; }
echo "GPU offload / thread lines in $OLLAMA_SERVE_LOG:"
grep -E "offloaded [0-9]+/[0-9]+ layers to GPU|n_threads = " "$OLLAMA_SERVE_LOG" | sort | uniq -c || true

echo "== $(date) [5/5] summary"
python3 pipeline/summarize.py --model "$MODEL" $MODS
if [ $rc1 != 0 ] || [ $rc2 != 0 ]; then
  echo "== $(date) JOB DONE WITH ERRORS (one-shot exit $rc1, arms exit $rc2; lists above): resubmit to retry"
  exit 2
fi
echo "== $(date) JOB DONE"
