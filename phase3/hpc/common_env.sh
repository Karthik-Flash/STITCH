# Sourced by every Phase 3 slurm script. Edit ONLY here if a path changes.
# python3 = oss-cad-suite/py3bin (3.11.6): compute-node /usr/bin/python3 is 3.6 and miniconda3 was broken by the scratch purge.
export BASE=${PHASE3_BASE:-/scratch/soumyaj/Phase3_HPC}
export OSS_CAD_BIN=${OSS_CAD_BIN:-/scratch/soumyaj/oss-cad-suite/bin}
export PATH=/scratch/soumyaj/oss-cad-suite/py3bin:$OSS_CAD_BIN:$BASE/bin:$PATH      # iverilog, vvp, yosys, verilator + ollama
export STITCH_INTERPRETER_DIR=$BASE/src/interpreter
export OLLAMA_MODELS=$BASE/ollama_models
export OLLAMA_HOST=127.0.0.1:11434
export OLLAMA_KEEP_ALIVE=30m
export PYTHONUNBUFFERED=1
[ -f $BASE/venv/bin/activate ] && source $BASE/venv/bin/activate   # optional: runner needs stdlib only
start_ollama() {
  ollama serve > $BASE/logs/ollama_serve_${SLURM_JOB_ID:-local}.log 2>&1 &
  OLLAMA_PID=$!
  for i in $(seq 1 90); do
    python3 -c "import urllib.request;urllib.request.urlopen('http://$OLLAMA_HOST/api/tags',timeout=2)" 2>/dev/null && { echo "ollama up after ${i}s"; return 0; }
    sleep 1
  done
  echo "ollama failed to start"; return 1
}
stop_ollama() { [ -n "${OLLAMA_PID:-}" ] && kill $OLLAMA_PID 2>/dev/null || true; }
