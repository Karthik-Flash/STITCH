#!/bin/bash
#SBATCH --job-name=llmgen_gen
#SBATCH --gres=gpu:1
#SBATCH --cpus-per-task=4
#SBATCH --mem=48G
#SBATCH --time=24:00:00
#SBATCH --output=/scratch/%u/STITCH_GEN/SiliconComparision/LLM_generation_study/hpc_logs/gen_%x_%j.log
# Generation job for ONE model: freeze check -> mock end-to-end test -> Ollama -> preflight -> generate.py
# (one-shot, simloop, stitch; 7 modules x 5 reps). Pick the model with GEN=qwen or GEN=gemma:
#   sbatch -J llmgen_qwen  --export=ALL,GEN=qwen  hpc/gen_job.slurm
#   sbatch -J llmgen_gemma --export=ALL,GEN=gemma hpc/gen_job.slurm
# Each model writes only to results/<model>/, and each job has its own Ollama port, so the two jobs may run at the
# same time. Never run two jobs of the SAME model at once.
# Resumable: resubmit the same line; finished work is skipped.
# Exit codes: 1 freeze, mock test or preflight failed (nothing generated); 2 unfinished work (resubmit);
# 3 first-call check failed (llama-server threads, or slower than 8 tok/s).
set -uo pipefail
source /scratch/$USER/STITCH_GEN/SiliconComparision/LLM_generation_study/hpc/hpc_env.sh
cd $STUDY
case "${GEN:-}" in
  qwen)  MODEL=$QWEN ;;
  gemma) MODEL=$GEMMA ;;
  *) echo "set GEN=qwen or GEN=gemma (sbatch --export=ALL,GEN=qwen ...)"; exit 1 ;;
esac
echo "== $(date '+%F %T') node $(hostname) partition ${SLURM_JOB_PARTITION:-?} job ${SLURM_JOB_ID:-none} cpus ${SLURM_CPUS_PER_TASK:-?} model $MODEL"
echo "== deployed commit $(cat DEPLOYED_COMMIT.txt)"

echo "== $(date '+%F %T') [1/4] freeze check"
python3 pipeline/freeze.py --check || { echo "FREEZE CHECK FAILED: nothing generated"; exit 1; }
echo "== $(date '+%F %T') [2/4] mock end-to-end test (no model)"
python3 pipeline/mock_e2e.py 2>&1 | sed 's/^/[selftest] /'
[ "${PIPESTATUS[0]}" = 0 ] || { echo "MOCK TEST FAILED: nothing generated"; exit 1; }

touch_deps
nvidia-smi -L
start_ollama || exit 1
trap stop_ollama EXIT
echo "== $(date '+%F %T') [3/4] preflight"
python3 pipeline/preflight.py --model $MODEL --host http://$OLLAMA_HOST || { echo "PREFLIGHT FAILED: nothing generated"; exit 1; }

echo "== $(date '+%F %T') [4/4] generation"
rc=0; python3 pipeline/generate.py --model $MODEL --host http://$OLLAMA_HOST || rc=$?
echo "GPU offload and thread lines in $OLLAMA_SERVE_LOG:"
grep -E "offloaded [0-9]+/[0-9]+ layers to GPU|n_threads = " $OLLAMA_SERVE_LOG | sort | uniq -c || true
case $rc in
  0) echo "== $(date '+%F %T') JOB DONE" ;;
  2) echo "== $(date '+%F %T') JOB DONE WITH UNFINISHED WORK: resubmit the same line" ;;
  3) echo "== $(date '+%F %T') FIRST-CALL CHECK FAILED: do not resubmit, send the log tail" ;;
  *) echo "== $(date '+%F %T') JOB FAILED (exit $rc)" ;;
esac
exit $rc
