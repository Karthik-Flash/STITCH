#!/bin/bash
#SBATCH --job-name=stitch_gen
#SBATCH --gres=gpu:1
#SBATCH --cpus-per-task=4
#SBATCH --mem=48G
#SBATCH --time=24:00:00
#SBATCH --output=/scratch/%u/STITCH_GEN/logs/gen_%j.log
# LLM one-shot vs STITCH: drift gate -> preflight -> one-shot generation -> two feedback arms -> summary, per study.
# Choose the node on the sbatch line: sbatch --partition=<PART> --nodelist=<NODE> pipeline/gen_job.slurm
# STUDIES (space-separated, default 2x2): 2x2, mesh3x3, ni. Each study generates the modules that have a task folder
# (2x2: all 34; mesh3x3 and ni: only their NEW modules, reports/REUSE.md). Every study is gated before the model
# server starts; then the studies run one after the other in the same job.
# One job, qwen2.5-coder:32b, T=0.1, num_ctx 32768, budget 6, N=1, llama-server threads = --cpus-per-task.
# --time: 2x2 from pipeline/speed.py (reports/SPEED.md); mesh3x3 + ni: --time=2:00:00 on the sbatch line, from pipeline/walltime.py
# (mesh3x3/reports/WALLTIME.md). Resumable: resubmit the same script; finished one-shot modules and arm runs are
# skipped, infra errors (timeout, connection) and incomplete folders are retried.
# Exit codes: gate/preflight failure 1; first-call check failure (llama-server threads or speed < 8 tok/s) 3;
# finished with infra errors 2 (the log lists them; resubmit).
# Overrides: GEN_TASKS=encoder,mux (comma-separated subset for one-shot and both arms in every study of STUDIES,
# empty = all; results go to the normal runs/ dirs, so a later full run skips them), GEN_MODEL, GEN_FULL_ROUTER=1
# (2x2 whole-router bonus; off by default: its prompt alone is 32,290 of 32,768 tokens, reports/PREDEPLOY_BUDGET.md).
set -euo pipefail
source "${GEN_BASE:-/scratch/$USER/STITCH_GEN}/SiliconComparision/llm_oneshot_vs_stitch/pipeline/hpc_env.sh"
cd $STUDY
MODEL=${GEN_MODEL:-qwen2.5-coder:32b}
STUDIES=${STUDIES:-2x2}
export GEN_TASKS=${GEN_TASKS:-}
MODS=${GEN_TASKS:+--modules ${GEN_TASKS//,/ }}
echo "== $(date) node $(hostname) job ${SLURM_JOB_ID:-none} cpus ${SLURM_CPUS_PER_TASK:-?} model $MODEL studies $STUDIES tasks ${GEN_TASKS:-all}"
trap stop_ollama EXIT

for s in $STUDIES; do
  export STITCH_STUDY=$s
  echo "== $(date) [$s 1/5] drift gate"
  python3 pipeline/gate.py || { echo "GATE FAILED ($s): nothing generated"; exit 1; }
done

touch_deps
nvidia-smi -L
start_ollama
bad=""
for s in $STUDIES; do
  export STITCH_STUDY=$s
  FULL=$([ "$s" = 2x2 ] && [ "${GEN_FULL_ROUTER:-0}" = 1 ] && [ -z "$GEN_TASKS" ] && echo --full-router || true)
  echo "== $(date) [$s 2/5] preflight"
  python3 pipeline/preflight.py --model "$MODEL" --host "http://$OLLAMA_HOST" || { echo "PREFLIGHT FAILED ($s): nothing generated"; exit 1; }

  echo "== $(date) [$s 3/5] one-shot generation (${GEN_TASKS:-every task of $s})"
  rc1=0; python3 pipeline/oneshot_gen.py --model "$MODEL" --host "http://$OLLAMA_HOST" --temperature 0.1 $MODS $FULL || rc1=$?
  [ $rc1 = 3 ] && { echo "FIRST-CALL CHECK FAILED (threads or speed): stopping"; exit 3; }
  [ $rc1 != 0 ] && [ $rc1 != 2 ] && { echo "ONE-SHOT FAILED ($s, exit $rc1): stopping"; exit $rc1; }

  echo "== $(date) [$s 4/5] feedback arms (baseline = simloop, sem_esc_restart_v3 = stitch)"
  rc2=0; python3 pipeline/run_arms.py --model "$MODEL" --host "http://$OLLAMA_HOST" --max-iters 6 --reps 1 $MODS || rc2=$?
  [ $rc2 = 3 ] && { echo "FIRST-CALL CHECK FAILED (threads or speed): stopping"; exit 3; }
  echo "GPU offload / thread lines in $OLLAMA_SERVE_LOG:"
  grep -E "offloaded [0-9]+/[0-9]+ layers to GPU|n_threads = " "$OLLAMA_SERVE_LOG" | sort | uniq -c || true

  echo "== $(date) [$s 5/5] summary"
  python3 pipeline/summarize.py --model "$MODEL" $MODS
  if [ $rc1 != 0 ] || [ $rc2 != 0 ]; then
    echo "== $(date) STUDY $s DONE WITH ERRORS (one-shot exit $rc1, arms exit $rc2; lists above)"
    bad="$bad $s"
  else
    echo "== $(date) STUDY $s DONE"
  fi
done
if [ -n "$bad" ]; then
  echo "== $(date) JOB DONE WITH ERRORS in:$bad: resubmit to retry"
  exit 2
fi
echo "== $(date) JOB DONE"
