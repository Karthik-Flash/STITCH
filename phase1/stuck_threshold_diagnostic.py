"""
stuck_threshold_diagnostic.py — TASK 2.5: is the pre-existing STUCK_THRESHOLD
rewrite mechanism (coarse err_type, threshold=2, already active in every
condition) masking sem_adv's real effect?

Design: run stitch_runner.run_one_condition() -- completely UNMODIFIED,
not reimplemented -- for condition="sem_adv" on the 13 harmful+enabling
cells (the operational run set already resolved from
phase0/evidence/combined_results.csv), twice: once with STUCK_THRESHOLD at
its real value (2, "ON"), once with it effectively disabled ("OFF"). N=3
replicates each. STUCK_THRESHOLD is toggled by monkeypatching
stitch_runner.STUCK_THRESHOLD before each call -- Python functions read
module globals at call time, so this changes real behavior without editing
stitch_runner.py on disk. Everything else (MAX_RETRIES=6, the feedback
builders, the interpreter, the tool invocations) is exactly what sem_adv
has always done.

"OFF" = STUCK_THRESHOLD set to a value no run can reach within
MAX_RETRIES=6 (10**9) -- the `if consecutive >= STUCK_THRESHOLD` branch
simply never taints any iteration's feedback, every iteration falls
through to the normal sem_adv feedback builder.

Specs for the 10 distinct v20 modules involved come from v20_specs.py
(extracted verbatim from real recorded run feedback.txt files -- see that
file's docstring for exact provenance and the ripple_carry_adder
dependency note).

Requires: WSL (Verilator/Yosys/Icarus) + Ollama serving all 3 models used
by these 13 cells (deepseek-coder:6.7b, llama3.1, gemma3:4b).
Produced: the Task 2.5 finding — STUCK_THRESHOLD is a real, mixed-
direction confound, not a non-issue. 3/13 cells flip pass/fail between
on and off; aggregate pass rate moves 76.9% (off) -> 84.6% (on), driven
mostly by one cell (alu_8bit/gemma3:4b) while another moves the opposite
direction (ripple_carry_adder/deepseek). Full per-cell traces in
phase1/results/stuck_threshold_diag/master_log.json (gitignored; re-run
this script to regenerate).

Usage: python phase1/stuck_threshold_diagnostic.py
Output: phase1/results/stuck_threshold_diag/master_log.json (appended to
incrementally, so a partial run is never lost) plus stitch_runner's own
per-run metrics.json trees under phase1/results/stuck_threshold_diag/<on|off>/replicate_<r>/...
"""
import json
import os
import sys

_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(_HERE, "..", "src", "runner"))
import stitch_runner  # noqa: E402 -- run_one_condition etc. reused unmodified

sys.path.insert(0, _HERE)
from v20_specs import V20_SPECS, V20_DEPENDENCIES  # noqa: E402

REAL_STUCK_THRESHOLD = 2                # stitch_runner.py's actual value
DISABLED_STUCK_THRESHOLD = 10 ** 9      # unreachable within MAX_RETRIES=6

TESTBENCH_DIR = os.path.join(_HERE, "..", "benchmarks", "v20_diagnostic")
RESULTS_ROOT = os.path.join(_HERE, "results", "stuck_threshold_diag")
MASTER_LOG = os.path.join(RESULTS_ROOT, "master_log.json")

N_REPLICATES = 3

# 13 cells: the operationally-resolved harmful + enabling set, NOT the
# regression gate, NOT the full v20 suite. (module, model, category)
CELLS = [
    # harmful (baseline PASS, sem_adv FAIL)
    ("counter_4bit",       "deepseek-coder:6.7b", "harmful"),
    ("full_adder",         "deepseek-coder:6.7b", "harmful"),
    ("full_adder",         "llama3.1:latest",     "harmful"),
    ("gray_counter_4bit",  "llama3.1:latest",     "harmful"),
    ("pipeline_mult_4x4",  "deepseek-coder:6.7b", "harmful"),
    ("pwm_generator",      "deepseek-coder:6.7b", "harmful"),
    ("ripple_carry_adder", "deepseek-coder:6.7b", "harmful"),
    ("simple_cpu_alu",     "llama3.1:latest",     "harmful"),
    ("sync_fifo_8",        "deepseek-coder:6.7b", "harmful"),
    ("sync_fifo_8",        "llama3.1:latest",     "harmful"),
    # enabling (baseline FAIL, sem_adv PASS)
    ("alu_8bit",           "deepseek-coder:6.7b", "enabling"),
    ("alu_8bit",           "gemma3:4b",           "enabling"),
    ("spi_master_8bit",    "gemma3:4b",           "enabling"),
]


def _count_stuck_fires(per_iter_detail, threshold):
    """Recompute, post-hoc, exactly how many times STUCK_THRESHOLD's own
    trigger condition (consecutive same err_type >= threshold, reset after
    firing) was met across this run's err_type sequence. This is not an
    approximation -- it is the same deterministic condition
    run_one_condition() itself evaluates, computed from the err_type
    sequence it already recorded."""
    consecutive, last_err, fires, fire_iters = 0, None, 0, []
    for it in per_iter_detail:
        et = it.get("err_type")
        if et in (None, "PASS"):
            continue
        if et == last_err:
            consecutive += 1
        else:
            consecutive, last_err = 1, et
        if consecutive >= threshold:
            fires += 1
            fire_iters.append(it["iter"])
            consecutive = 0
    return fires, fire_iters


def _load_master_log():
    if os.path.exists(MASTER_LOG):
        with open(MASTER_LOG, encoding="utf-8") as f:
            return json.load(f)
    return []


def _save_master_log(entries):
    os.makedirs(RESULTS_ROOT, exist_ok=True)
    with open(MASTER_LOG, "w", encoding="utf-8") as f:
        json.dump(entries, f, indent=2)


def run_all():
    entries = _load_master_log()
    done = {(e["module"], e["model"], e["toggle"], e["replicate"]) for e in entries}

    total = len(CELLS) * 2 * N_REPLICATES
    done_count = len(done)

    for toggle, threshold in [("on", REAL_STUCK_THRESHOLD), ("off", DISABLED_STUCK_THRESHOLD)]:
        for module, model, category in CELLS:
            for replicate in range(1, N_REPLICATES + 1):
                key = (module, model, toggle, replicate)
                if key in done:
                    continue

                stitch_runner.STUCK_THRESHOLD = threshold
                stitch_runner.TESTBENCH_DIR = TESTBENCH_DIR
                stitch_runner.RESULTS_DIR = os.path.join(RESULTS_ROOT, toggle, f"replicate_{replicate}")

                dep_files = [os.path.join(_HERE, d) for d in V20_DEPENDENCIES.get(module, [])]

                done_count += 1
                print(f"\n[{done_count}/{total}] {module} / {model} / STUCK_THRESHOLD={toggle} / replicate {replicate}")

                try:
                    metrics = stitch_runner.run_one_condition(
                        spec=V20_SPECS[module], module_name=module, model=model,
                        condition="sem_adv", dependencies=dep_files,
                    )
                except Exception as e:
                    print(f"  ERROR: {e}")
                    metrics = None

                fires, fire_iters = (0, [])
                if metrics is not None:
                    fires, fire_iters = _count_stuck_fires(metrics["per_iter_detail"], threshold)

                entry = {
                    "module": module, "model": model, "category": category,
                    "toggle": toggle, "replicate": replicate,
                    "pass": metrics["pass"] if metrics else None,
                    "iterations_to_pass": metrics["iterations_to_pass"] if metrics else None,
                    "total_iterations": metrics["total_iterations"] if metrics else None,
                    "semantic_fired": metrics["semantic_fired"] if metrics else None,
                    "stuck_threshold_fires": fires,
                    "stuck_threshold_fire_iters": fire_iters,
                    "per_iter_err_types": [it.get("err_type") for it in metrics["per_iter_detail"]] if metrics else None,
                    "error": None if metrics else "run_one_condition raised -- see console log above",
                }
                entries.append(entry)
                _save_master_log(entries)

    print(f"\nDone. {len(entries)} entries -> {MASTER_LOG}")


if __name__ == "__main__":
    run_all()
