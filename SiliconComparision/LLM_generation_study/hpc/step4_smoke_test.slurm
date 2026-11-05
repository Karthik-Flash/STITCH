#!/bin/bash
#SBATCH --job-name=llmgen_smoke
#SBATCH --gres=gpu:1
#SBATCH --cpus-per-task=4
#SBATCH --mem=48G
#SBATCH --time=00:45:00
#SBATCH --output=/scratch/%u/STITCH_GEN/SiliconComparision/LLM_generation_study/hpc_logs/smoke_%j.log
# STEP 4 (GPU node, about 10 min): every condition the generation jobs need, on the node type they will run on.
#   1. GPU: at least 40 GiB (the 32B/31B model and its 32k context stay on the GPU)
#   2. golden checks on the cluster toolchain (scripts/check_golden.py, the STITCH runner's own checks); the report
#      is kept as hpc_logs/golden_checks_hpc_<JOBID>.md to compare with the laptop's reports/GOLDEN_CHECKS.md
#   3. both models answer one prompt (hpc/model_check.py): digest, quantisation, all layers on the GPU, tok/s
# Same resources as a generation job: 1 GPU, 4 CPUs, 48 GB (the site allows 4 CPUs per GPU).
# Submit with the line hpc/step3_pick_node.sh prints. Ends with "SMOKE: ALL PASSED" or "SMOKE: FAILED: <names>".
set -uo pipefail
source /scratch/$USER/STITCH_GEN/SiliconComparision/LLM_generation_study/hpc/hpc_env.sh
cd $STUDY
F=""
echo "== $(date '+%F %T') node $(hostname) partition ${SLURM_JOB_PARTITION:-?} job ${SLURM_JOB_ID:-none} cpus ${SLURM_CPUS_PER_TASK:-?}"
echo "== deployed commit $(cat DEPLOYED_COMMIT.txt)"

echo "== 1/3 GPU"
nvidia-smi --query-gpu=name,memory.total,driver_version --format=csv,noheader
mib=$(nvidia-smi --query-gpu=memory.total --format=csv,noheader,nounits | head -1)
[ "${mib:-0}" -ge 40960 ] && echo "[gpu] ok   $mib MiB" || { echo "[gpu] BAD  ${mib:-none} MiB, need 40960"; F="$F gpu"; }

echo "== 2/3 golden checks on the cluster toolchain"
echo "python3 $(python3 -V 2>&1 | cut -d' ' -f2); $(yosys -V | head -1); $(verilator --version | head -1); $(iverilog -V 2>&1 | head -1)"
python3 scripts/check_golden.py && echo "[golden] ok" || { echo "[golden] BAD"; F="$F golden"; }
cp reports/GOLDEN_CHECKS.md $LOGS/golden_checks_hpc_${SLURM_JOB_ID}.md

echo "== 3/3 both models"
touch_deps
start_ollama || { echo "SMOKE: FAILED: ollama"; exit 1; }
trap stop_ollama EXIT
python3 hpc/model_check.py --model $QWEN --host http://$OLLAMA_HOST --digest $QWEN_DIGEST || F="$F qwen"
python3 hpc/model_check.py --model $GEMMA --host http://$OLLAMA_HOST || F="$F gemma"
echo "GPU offload and thread lines from $OLLAMA_SERVE_LOG:"
grep -E "offloaded [0-9]+/[0-9]+ layers to GPU|n_threads = |model weights|kv cache|KvSize" $OLLAMA_SERVE_LOG | sort | uniq -c || true
part=$(grep -oE "offloaded [0-9]+/[0-9]+ layers" $OLLAMA_SERVE_LOG | grep -vE "offloaded ([0-9]+)/\1 layers" || true)
full=$(grep -cE "offloaded ([0-9]+)/\1 layers" $OLLAMA_SERVE_LOG || true)
if [ -n "$part" ]; then echo "[offload] BAD  $part"; F="$F offload"
elif [ "$full" -ge 2 ]; then echo "[offload] ok   both models fully on the GPU"
else echo "[offload] BAD  $full full-offload lines for 2 models: read $OLLAMA_SERVE_LOG"; F="$F offload"; fi

echo
[ -z "$F" ] && echo "SMOKE: ALL PASSED" || { echo "SMOKE: FAILED:$F"; exit 1; }
