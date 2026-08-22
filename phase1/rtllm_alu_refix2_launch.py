"""
rtllm_alu_refix2_launch.py -- STEP 3 of the "does alu/calendar show
anything real once the harness is fully correct" budget-capped re-run
(2026-08-22, 8h laptop budget).

Thin driver, not a new harness: imports rtllm_pilot_runner.py unmodified
and calls its run_all() directly with a trimmed condition list and
restricted module set -- the same mechanism --modules/--results-dir
already use from the CLI, just adding a third axis (a custom conditions
list that isn't core4/core5) without touching rtllm_pilot_runner.py
itself. All measurement logic (run_one_condition, run_one_replicate,
pass detection, retry/incident logging, STUCK_THRESHOLD=2) is the
unmodified pilot runner, unmodified stitch_runner.py/escalation_runner.py
(both carrying the two 2026-08-21 harness fixes).

Scope, per go-ahead:
  Modules:    alu, calendar (both confirmed TESTABLE in STEP 1 -- golden
              reference passes its own testbench for both, post-fix).
  Conditions: baseline, sem_adv, sem_escalate only. raw_adv and
              sem_escalate_restart excluded to trim breadth (not rigor)
              and fit the budget -- these three answer the core question
              (does escalation beat baseline and always-on).
  N:          3 (unchanged -- N=1 is resampling noise, phase-0 lesson).
  Total:      2 modules x 5 models x 3 conditions x 3 replicates = 90 runs.

Usage: python phase1/rtllm_alu_refix2_launch.py
Output: phase1/results/rtllm_alu_refix2/master_log.json (gitignored, resumable)
"""
import os
import sys

_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, _HERE)
import rtllm_pilot_runner as p  # noqa: E402

RESULTS_ROOT = os.path.join(_HERE, "results", "rtllm_alu_refix2")
p.RESULTS_ROOT = RESULTS_ROOT
p.STAGED_ROOT = os.path.join(RESULTS_ROOT, "_staged")
p.MASTER_LOG = os.path.join(RESULTS_ROOT, "master_log.json")
p.INCIDENTS_LOG = os.path.join(RESULTS_ROOT, "incidents.log")

p.PILOT_DESIGNS = [t for t in p.PILOT_DESIGNS if t[0] in ("alu", "calendar")]

# BUDGET REVISION 2026-08-22, mid-run: gemma3:12b's observed steady-state
# pace (one full completed cell: 805s / 6 iterations = 134s/iter) is ~4.5x
# the three smaller models' confirmed pace (29.4s/iter over 180 completed
# iterations). At that pace, qwen2.5-coder:14b (comparable size, untested)
# would very likely push total wall-clock past the 8h hard cap. User
# decision: drop qwen2.5-coder:14b, keep the other 4 models + both modules.
# Nothing else about what's measured changes. The 28 cells already
# completed (incl. 1 gemma3:12b cell) are kept -- run_all()'s checkpoint
# just resumes forward with the trimmed model list; no qwen2.5-coder:14b
# cells had run yet, so nothing is discarded.
p.MODELS = [m for m in p.MODELS if m != "qwen2.5-coder:14b"]

CONDITIONS = ["baseline", "sem_adv", "sem_escalate"]

if __name__ == "__main__":
    print(f"Modules: {[t[0] for t in p.PILOT_DESIGNS]}")
    print(f"Models: {p.MODELS}")
    print(f"Conditions: {CONDITIONS}")
    print(f"Output: {p.MASTER_LOG}")
    p.run_all(CONDITIONS)
