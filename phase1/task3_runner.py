"""
task3_runner.py — TASK 3: the targeted escalation benchmark.

17 cells (10 harmful + 3 enabling + 4 regression-gate) x 5 conditions
(baseline, raw_adv, sem_adv, sem_escalate, sem_escalate_restart) x N=3 = 255 runs.

baseline/raw_adv/sem_adv run through stitch_runner.run_one_condition() --
completely unmodified, MAX_RETRIES=6 (its own real default, same cap the
LOCKED decoder_3to8/mux4_oe reference results were captured at -- see
phase0/illustrations/proven/decoder_3to8/metrics_*.json, all total_iterations=6).

sem_escalate/sem_escalate_restart run through
escalation_runner.run_one_replicate() -- also unmodified -- at Pass@8
(EscalationConfig.max_iterations default), per the original Task 1 spec.

THE CAP MISMATCH IS DELIBERATE AND FLAGGED, NOT HIDDEN: the escalation
conditions get 8 iterations, the other three get 6 (matching LOCKED and
every prior sem_adv number in this project's history). This is not
symmetric and the report must say so every place it matters -- a
sem_escalate pass at iteration 7 or 8 had runway sem_adv/baseline never
had, and the regression gate comparison against LOCKED (captured at cap=6)
is only a clean comparison for the cap<=6 conditions.

STUCK_THRESHOLD is ON (real value, 2) for every condition -- the decided
precedence from the Task 2.5 diagnostic. Fire counts are recomputed
post-hoc from each run's own err_type sequence (same deterministic
technique used for the diagnostic and the historical fire-rate analysis)
and logged for every condition, not just the escalation ones -- this is
the "instrumented axis" the user asked for.

Usage: python phase1/task3_runner.py
Output:
  phase1/results/task3/master_log.json   -- one named-field object per run,
    with the full per-iteration trace embedded. THIS is "the JSON path"
    to hand over before any summary table.
  phase1/results/task3/<condition-specific subtrees>/... -- the underlying
    per-run metrics.json / run_log.json files stitch_runner.py and
    escalation_runner.py already write, kept as the raw per-run record.

Requires: WSL (Verilator/Yosys/Icarus) + Ollama serving all 4 models used
across the 17 cells (deepseek-coder:6.7b, llama3.1, gemma3:4b -- qwen2.5-
coder:14b and gemma3:12b have no cell in this run set, see
PHASE1_TASK3_ANALYSIS.md for why). Produced: phase1/results/task3/master_log.json,
analyzed in full in phase1/PHASE1_TASK3_ANALYSIS.md -- read that before
this file's raw output.
"""
import json
import os
import sys

_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(_HERE, "..", "src", "runner"))
import stitch_runner  # noqa: E402

sys.path.insert(0, _HERE)
from v20_specs import V20_SPECS, V20_DEPENDENCIES  # noqa: E402
from escalation_runner import run_one_replicate  # noqa: E402
from escalation_state import EscalationConfig  # noqa: E402

REGRESSION_TESTBENCH_DIR = os.path.join(_HERE, "..", "phase0", "illustrations", "proven")
V20_TESTBENCH_DIR = os.path.join(_HERE, "..", "benchmarks", "v20_diagnostic")
RESULTS_ROOT = os.path.join(_HERE, "results", "task3")
MASTER_LOG = os.path.join(RESULTS_ROOT, "master_log.json")

REAL_STUCK_THRESHOLD = 2
N_REPLICATES = 3
CONDITIONS = ["baseline", "raw_adv", "sem_adv", "sem_escalate", "sem_escalate_restart"]

# (module, model, category, spec_source, testbench_dir, dependency_files)
CELLS = [
    # --- regression gate: 4 cells ---
    ("decoder_3to8", "gemma3:4b",       "regression", "benchmark", REGRESSION_TESTBENCH_DIR, []),
    ("decoder_3to8", "llama3.1:latest", "regression", "benchmark", REGRESSION_TESTBENCH_DIR, []),
    ("mux4_oe",      "gemma3:4b",       "regression", "benchmark", REGRESSION_TESTBENCH_DIR, []),
    ("mux4_oe",      "llama3.1:latest", "regression", "benchmark", REGRESSION_TESTBENCH_DIR, []),
    # --- harmful: 10 cells ---
    ("counter_4bit",       "deepseek-coder:6.7b", "harmful", "v20", V20_TESTBENCH_DIR, []),
    ("full_adder",         "deepseek-coder:6.7b", "harmful", "v20", V20_TESTBENCH_DIR, []),
    ("full_adder",         "llama3.1:latest",     "harmful", "v20", V20_TESTBENCH_DIR, []),
    ("gray_counter_4bit",  "llama3.1:latest",     "harmful", "v20", V20_TESTBENCH_DIR, []),
    ("pipeline_mult_4x4",  "deepseek-coder:6.7b", "harmful", "v20", V20_TESTBENCH_DIR, []),
    ("pwm_generator",      "deepseek-coder:6.7b", "harmful", "v20", V20_TESTBENCH_DIR, []),
    ("ripple_carry_adder", "deepseek-coder:6.7b", "harmful", "v20", V20_TESTBENCH_DIR,
        [os.path.join(_HERE, "fixtures", "full_adder_dependency.v")]),
    ("simple_cpu_alu",     "llama3.1:latest",     "harmful", "v20", V20_TESTBENCH_DIR, []),
    ("sync_fifo_8",        "deepseek-coder:6.7b", "harmful", "v20", V20_TESTBENCH_DIR, []),
    ("sync_fifo_8",        "llama3.1:latest",     "harmful", "v20", V20_TESTBENCH_DIR, []),
    # --- enabling: 3 cells ---
    ("alu_8bit",        "deepseek-coder:6.7b", "enabling", "v20", V20_TESTBENCH_DIR, []),
    ("alu_8bit",        "gemma3:4b",           "enabling", "v20", V20_TESTBENCH_DIR, []),
    ("spi_master_8bit", "gemma3:4b",           "enabling", "v20", V20_TESTBENCH_DIR, []),
]

FLAGGED_CELLS = {
    ("alu_8bit", "gemma3:4b"),
    ("pwm_generator", "deepseek-coder:6.7b"),
    ("ripple_carry_adder", "deepseek-coder:6.7b"),
}


def _get_spec(module, spec_source):
    if spec_source == "benchmark":
        return stitch_runner.BENCHMARK[module]["spec"]
    return V20_SPECS[module]


def _count_stuck_fires(err_type_seq, threshold=REAL_STUCK_THRESHOLD):
    consecutive, last_err, fires, fire_iters = 0, None, 0, []
    for i, et in enumerate(err_type_seq, start=1):
        if et in (None, "PASS"):
            continue
        if et == last_err:
            consecutive += 1
        else:
            consecutive, last_err = 1, et
        if consecutive >= threshold:
            fires += 1
            fire_iters.append(i)
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


def _run_classic(module, model, condition, category, spec, testbench_dir, deps, replicate):
    stitch_runner.STUCK_THRESHOLD = REAL_STUCK_THRESHOLD
    stitch_runner.TESTBENCH_DIR = testbench_dir
    stitch_runner.RESULTS_DIR = os.path.join(RESULTS_ROOT, "classic", condition, f"replicate_{replicate}")

    m = stitch_runner.run_one_condition(
        spec=spec, module_name=module, model=model, condition=condition, dependencies=deps,
        # Every task3_runner.py cell runs against V20_TESTBENCH_DIR or
        # REGRESSION_TESTBENCH_DIR (phase0-proven) -- the "phase1"
        # convention. See pass_detection.py.
        benchmark="phase1",
    )
    err_seq = [it.get("err_type") for it in m["per_iter_detail"]]
    fires, fire_iters = _count_stuck_fires(err_seq)

    return {
        "module": module, "model": model, "condition": condition, "category": category,
        "run_replicate": replicate, "iteration_cap": 6,
        "pass": m["pass"], "iterations_to_pass": m["iterations_to_pass"],
        "total_iterations": m["total_iterations"],
        "total_tokens": m["total_tokens"],
        "total_prompt_tokens": m["total_prompt_tokens"],
        "total_completion_tokens": m["total_completion_tokens"],
        "semantic_fired": m["semantic_fired"],
        "verilator_catches": m["verilator_catches"],
        "latch_warnings": m["latch_warnings"], "loop_warnings": m["loop_warnings"],
        "stuck_threshold_fires": fires, "stuck_threshold_fire_iters": fire_iters,
        # escalation-specific fields: not applicable to classic conditions
        "escalation_iteration": None, "fired_escalate": None,
        "restart_threshold_reached_iterations": None, "restart_iterations": None,
        "restart_preempted_by_stuck_threshold": None,
        "per_iteration": m["per_iter_detail"],
        "flagged_diagnostic_cell": (module, model) in FLAGGED_CELLS,
    }


def _run_escalation(module, model, condition, category, spec, testbench_dir, deps, replicate):
    config = EscalationConfig(
        escalate_after=2, restart_after=3,
        allow_restart=(condition == "sem_escalate_restart"),
        signature_window=5, max_iterations=8,
    )
    results_dir = os.path.join(RESULTS_ROOT, "escalation", condition)

    run_log = run_one_replicate(
        spec=spec, module_name=module, model=model, condition=condition,
        run_replicate=replicate, config=config,
        testbench_dir=testbench_dir, results_dir=results_dir, dependencies=deps,
        benchmark="phase1",
    )
    s = run_log["summary"]
    err_seq = [it["err_type"] for it in run_log["iterations"]]
    fires, fire_iters = _count_stuck_fires(err_seq)

    semantic_fired = sum(1 for it in run_log["iterations"] if it["interpreter_invoked"])

    return {
        "module": module, "model": model, "condition": condition, "category": category,
        "run_replicate": replicate, "iteration_cap": 8,
        "pass": s["pass"], "iterations_to_pass": s["iterations_to_pass"],
        "total_iterations": s["total_iterations"],
        "total_tokens": s["total_tokens"],
        "total_prompt_tokens": None, "total_completion_tokens": None,
        "semantic_fired": semantic_fired,
        "verilator_catches": None, "latch_warnings": None, "loop_warnings": None,
        "stuck_threshold_fires": fires, "stuck_threshold_fire_iters": fire_iters,
        "escalation_iteration": s["escalation_iteration"], "fired_escalate": s["fired_escalate"],
        "restart_threshold_reached_iterations": s.get("restart_threshold_reached_iterations"),
        "restart_iterations": s.get("restart_iterations"),
        "restart_preempted_by_stuck_threshold": s.get("restart_preempted_by_stuck_threshold"),
        "per_iteration": run_log["iterations"],
        "flagged_diagnostic_cell": (module, model) in FLAGGED_CELLS,
    }


def run_all():
    entries = _load_master_log()
    done = {(e["module"], e["model"], e["condition"], e["run_replicate"]) for e in entries}

    total = len(CELLS) * len(CONDITIONS) * N_REPLICATES
    done_count = len(done)

    for module, model, category, spec_source, testbench_dir, deps in CELLS:
        spec = _get_spec(module, spec_source)
        for condition in CONDITIONS:
            for replicate in range(1, N_REPLICATES + 1):
                key = (module, model, condition, replicate)
                if key in done:
                    continue

                done_count += 1
                print(f"\n[{done_count}/{total}] {module} / {model} / {condition} / replicate {replicate} (cat={category})")

                try:
                    if condition in ("baseline", "raw_adv", "sem_adv"):
                        entry = _run_classic(module, model, condition, category, spec, testbench_dir, deps, replicate)
                    else:
                        entry = _run_escalation(module, model, condition, category, spec, testbench_dir, deps, replicate)
                    entry["error"] = None
                except Exception as e:
                    print(f"  ERROR: {e}")
                    entry = {
                        "module": module, "model": model, "condition": condition, "category": category,
                        "run_replicate": replicate, "error": str(e),
                    }

                entries.append(entry)
                _save_master_log(entries)

    print(f"\nDone. {len(entries)} entries -> {MASTER_LOG}")


if __name__ == "__main__":
    run_all()
