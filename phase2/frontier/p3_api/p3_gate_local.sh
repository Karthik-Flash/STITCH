#!/bin/bash
# Phase 3 gate checks G0-G5 (same commands as phase3/hpc/phase3_gate.slurm) on the matched 0.69 suite,
# run on a throwaway COPY of phase3/ + src/interpreter/ in /tmp, so nothing under the real phase3/ is written
# (validate_tasks.py writes phase3/evidence/). Run in WSL: bash p3_gate_local.sh
set -euo pipefail
export STITCH_SET4_OSSCAD=${STITCH_SET4_OSSCAD:-/home/flash/set4_osscad/20260917/oss-cad-suite}
export PATH="$STITCH_SET4_OSSCAD/bin:$PATH" PYTHONDONTWRITEBYTECODE=1
REPO=/mnt/d/Projects/STITCH
BASE=/tmp/p3gate_repo; rm -rf $BASE; mkdir -p $BASE/src
tar -C $REPO -cf - --exclude='phase3/results' --exclude='__pycache__' phase3 | tar -C $BASE -xf -
cp -r $REPO/src/interpreter $BASE/src/
cd $BASE
echo "== toolchain"; which yosys verilator iverilog vvp; yosys -V; verilator --version; (iverilog -V 2>&1 || true) | head -1
echo "== [G0] interpreter tests (frozen real logs)";  python3 phase3/tests/run_tests.py
echo "== [G1] tasks + live drift check";              python3 phase3/runner/validate_tasks.py
echo "== [G2] mock end-to-end smoke";                 rm -rf /tmp/p3_gate_mock
python3 phase3/runner/stitch_runner_p3.py --backend mock --mock-mode fix_on_2 --model gate-mock --reps 1 \
    --system-prompt-file phase3/runner/system_prompt.txt --out /tmp/p3_gate_mock | tail -3
python3 phase3/runner/summarize_p3.py --results /tmp/p3_gate_mock > /dev/null && echo "summarize OK"
echo "== [G5] baseline_gate feeds no tool detail, logs would_fire"
python3 - /tmp/p3_gate_mock <<'PY'
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
