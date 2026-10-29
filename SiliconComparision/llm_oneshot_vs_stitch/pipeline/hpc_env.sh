# Sourced by gen_job.slurm. Same environment logic as the frozen phase3/hpc/common_env.sh, with this study's base.
# python3 = oss-cad-suite/py3bin (3.11): compute-node /usr/bin/python3 is 3.6.
# Ollama binary and models are reused from Phase3_HPC by default, so qwen2.5-coder:32b keeps the digest it had in Phase 3.
export BASE=${GEN_BASE:-/scratch/$USER/STITCH_GEN}
export OSS_CAD=${OSS_CAD:-/scratch/$USER/oss-cad-suite}
export OSS_CAD_BIN=${OSS_CAD_BIN:-$OSS_CAD/bin}
export OLLAMA_DIR=${GEN_OLLAMA_DIR:-/scratch/soumyaj/Phase3_HPC}        # holds bin/ollama and lib/ollama
export OLLAMA_MODELS=/scratch/soumyaj/Phase3_HPC/ollama_models           # Phase 3 models: same digest
export PATH=$OSS_CAD/py3bin:$OSS_CAD_BIN:$OLLAMA_DIR/bin:$PATH           # python3, iverilog, vvp, yosys, verilator, ollama
export STITCH_INTERPRETER_DIR=$BASE/src/interpreter
export STUDY=$BASE/SiliconComparision/llm_oneshot_vs_stitch
# One port per job (11434 + job id mod 1000), so two jobs on one node never share an ollama server.
export OLLAMA_HOST=127.0.0.1:$((11434 + ${SLURM_JOB_ID:-0} % 1000))
export OLLAMA_KEEP_ALIVE=30m
export PYTHONUNBUFFERED=1
export PYTHONDONTWRITEBYTECODE=1
mkdir -p $BASE/logs
# Scratch purge: files untouched for 30 days are deleted. Reset the clock on everything the job depends on.
touch_deps() {
  find $OSS_CAD $OLLAMA_DIR/bin $OLLAMA_DIR/lib $OLLAMA_MODELS -exec touch -h {} + 2>/dev/null || true
}
start_ollama() {
  echo "ollama serve: OLLAMA_MODELS=$OLLAMA_MODELS OLLAMA_HOST=$OLLAMA_HOST ($(command -v ollama))"
  ollama serve > $BASE/logs/ollama_serve_${SLURM_JOB_ID:-local}.log 2>&1 &
  OLLAMA_PID=$!
  local t0=$SECONDS
  while (( SECONDS - t0 < 120 )); do
    python3 -c "import urllib.request;urllib.request.urlopen('http://$OLLAMA_HOST/api/tags',timeout=2)" 2>/dev/null && { echo "ollama up after $((SECONDS - t0))s"; return 0; }
    sleep 1
  done
  echo "ollama not up after 120 s"; return 1
}
stop_ollama() { [ -n "${OLLAMA_PID:-}" ] && kill $OLLAMA_PID 2>/dev/null || true; }
