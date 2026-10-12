#!/bin/bash
#SBATCH --job-name=p3_gate
#SBATCH --partition=gpu_h100_4
#SBATCH --nodelist=gpunode5
#SBATCH --gres=gpu:0
#SBATCH --cpus-per-task=4
#SBATCH --mem=8G
#SBATCH --time=00:30:00
#SBATCH --output=/scratch/soumyaj/Phase3_HPC/logs/p3_gate_%j.log
# GATE (CPU only, no GPU requested): tests on frozen logs + LIVE drift check on this cluster's toolchain
# + mock end-to-end smoke run + dry-run count. Nothing GPU-side is submitted unless this ends "ALL GATES PASSED".
set -euo pipefail
source "${PHASE3_BASE:-/scratch/soumyaj/Phase3_HPC}/phase3/hpc/common_env.sh"
cd $BASE
echo "== toolchain"; which yosys verilator iverilog vvp; yosys -V; verilator --version; (iverilog -V 2>&1 || true) | head -1
echo "== [G0] interpreter tests (frozen real logs)";  python3 phase3/tests/run_tests.py
echo "== [G1] tasks + live drift check";              python3 phase3/runner/validate_tasks.py
echo "== [G2] mock end-to-end smoke";                 rm -rf /tmp/p3_gate_$$
python3 phase3/runner/stitch_runner_p3.py --backend mock --mock-mode fix_on_2 --model gate-mock --reps 1 --out /tmp/p3_gate_$$ | tail -3
python3 phase3/runner/summarize_p3.py --results /tmp/p3_gate_$$ > /dev/null && echo "summarize OK"
echo "== [G5] baseline_gate feeds no tool detail, logs would_fire"
python3 - /tmp/p3_gate_$$ <<'PY'
import glob, json, sys
root = sys.argv[1] + "/gate-mock/baseline_gate"
leak = [p for p in glob.glob(root + "/*/rep1/iter*/prompt.txt")
        if any(k in open(p).read() for k in ("VERILATOR", "YOSYS", "SEMANTIC ANALYSIS"))]
ms = [json.load(open(f)) for f in glob.glob(root + "/*/rep1/metrics.json")]
bad = [m["task"] for m in ms if m["tool_feedback_iters"] or m["semantic_fired"] or "would_fire" not in m
       or m["escalated_at"] is not None or m["restarted"]]
assert len(ms) == 11 and not leak and not bad, (len(ms), leak, bad)
print(f"G5 PASS: {len(ms)} baseline_gate runs, no tool text in prompts, would_fire on {sum(m['would_fire'] for m in ms)}")
PY
echo "== [G4] composition bounds on this Yosys (2x2 mesh)"; python3 phase3/runner/check_compose_bounds.py
echo "== [G3] dry-run";  python3 phase3/runner/stitch_runner_p3.py --dry-run --models $(grep -v '^#' phase3/hpc/models_phase3.txt) | tail -1
echo "ALL GATES PASSED"
