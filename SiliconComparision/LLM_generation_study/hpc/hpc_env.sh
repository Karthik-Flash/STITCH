# Sourced by every script in hpc/. One place for the cluster paths, tools, models and the Ollama server.
# Layout on the cluster (/scratch/soumyaj/STITCH_GEN is shared with the closed llm_oneshot_vs_stitch study):
#   $BASE/SiliconComparision/LLM_generation_study   this study, as shipped by hpc/deploy_to_hpc.ps1
#   $STUDY/hpc_logs                                  every job log of this study
#   $BASE/ollama_models                              this study's model store: qwen hard-linked from Phase 3 (same
#                                                    bytes, same digest, no copy) + Gemma pulled by step 2
#   $BASE/ollama                                     a newer Ollama, only if step 2 had to install one
# python3 = oss-cad-suite/py3bin (3.11): the compute-node /usr/bin/python3 is 3.6.
export BASE=${GEN_BASE:-/scratch/$USER/STITCH_GEN}
export STUDY=$BASE/SiliconComparision/LLM_generation_study
export LOGS=$STUDY/hpc_logs
export OSS_CAD=${OSS_CAD:-/scratch/$USER/oss-cad-suite}
export PHASE3_STORE=/scratch/soumyaj/Phase3_HPC/ollama_models          # read only: never pull or serve from it
export OLLAMA_MODELS=$BASE/ollama_models
# Ollama binary: the study's own copy if step 2 installed one, else Phase 3's (0.34.1 in the closed study).
if [ -x $BASE/ollama/bin/ollama ]; then export OLLAMA_DIR=$BASE/ollama; else export OLLAMA_DIR=/scratch/soumyaj/Phase3_HPC; fi
export PATH=$OSS_CAD/py3bin:$OSS_CAD/bin:$OLLAMA_DIR/bin:$PATH        # python3, iverilog, vvp, yosys, verilator, ollama
export STITCH_INTERPRETER_DIR=$BASE/src/interpreter

# The two models. qwen's digest is the one all 198 Phase 3 runs recorded; Gemma's is recorded by step 2 and frozen in
# phase 1. Gemma: the instruction-tuned 31B at Q4_K_M, the same quantisation as qwen2.5-coder:32b.
export QWEN=qwen2.5-coder:32b
export QWEN_DIGEST=b92d6a0bd47ee79114298de0177bf920c05a706d12633950b3936778492bef41
export GEMMA=gemma4:31b-it-q4_K_M
export MANIFESTS=registry.ollama.ai/library                            # under $OLLAMA_MODELS/manifests

# One port per job (11434 + job id mod 1000), so two jobs on one node never share a server. Outside a job (login node)
# a random port, so a server left over by someone else is never reused.
if [ -n "${SLURM_JOB_ID:-}" ]; then PORT=$((11434 + SLURM_JOB_ID % 1000)); else PORT=$((20000 + RANDOM % 10000)); fi
export OLLAMA_HOST=127.0.0.1:$PORT
export OLLAMA_SERVE_LOG=$LOGS/ollama_serve_${SLURM_JOB_ID:-login_$$}.log
# CPU threads = the job's CPUs (without this llama-server starts one thread per node core and runs at ~5 tok/s).
export LLAMA_ARG_THREADS=${SLURM_CPUS_PER_TASK:-4}
export LLAMA_ARG_THREADS_BATCH=${SLURM_CPUS_PER_TASK:-4}
export OLLAMA_KEEP_ALIVE=30m
export PYTHONUNBUFFERED=1
export PYTHONDONTWRITEBYTECODE=1
mkdir -p $LOGS

ollama_version() { ollama -v 2>&1 | grep -o '[0-9]\+\.[0-9]\+\.[0-9]\+' | tail -1; }
manifest_digest() { sha256sum "$OLLAMA_MODELS/manifests/$MANIFESTS/${1%%:*}/${1#*:}" 2>/dev/null | cut -d' ' -f1; }
# Scratch purge: files untouched for 30 days are deleted. Reset the clock on everything the jobs depend on.
touch_deps() { find $OSS_CAD $OLLAMA_DIR/bin $OLLAMA_DIR/lib $OLLAMA_MODELS -exec touch -h {} + 2>/dev/null || true; }
start_ollama() {
  echo "ollama serve: $(command -v ollama) $(ollama_version), OLLAMA_MODELS=$OLLAMA_MODELS, OLLAMA_HOST=$OLLAMA_HOST"
  ollama serve > $OLLAMA_SERVE_LOG 2>&1 &
  OLLAMA_PID=$!
  local t0=$SECONDS
  while (( SECONDS - t0 < 120 )); do
    python3 -c "import urllib.request;urllib.request.urlopen('http://$OLLAMA_HOST/api/tags',timeout=2)" 2>/dev/null && { echo "ollama up after $((SECONDS - t0)) s"; return 0; }
    sleep 1
  done
  echo "ollama not up after 120 s (log: $OLLAMA_SERVE_LOG)"; return 1
}
stop_ollama() { [ -n "${OLLAMA_PID:-}" ] && kill $OLLAMA_PID 2>/dev/null || true; }
