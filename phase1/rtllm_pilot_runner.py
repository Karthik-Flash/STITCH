"""
rtllm_pilot_runner.py — RTLLM v2.1 pilot (TASKS C/D): the 5-module,
5-model, 4-or-5-condition, N=3 trial run. TRIAL/DEMO ONLY, not the full
50-module pass@5 study (deferred to HPC) -- see phase1/RTLLM_PILOT_PREREG.md.

Same pattern as task3_runner.py: baseline/raw_adv/sem_adv run through
stitch_runner.run_one_condition() unmodified (MAX_RETRIES=6, its own real
default); sem_escalate/sem_escalate_restart run through
escalation_runner.run_one_replicate() unmodified (Pass@8).
STUCK_THRESHOLD stays ON (real value 2), consistent with the Task 3
decision. Incremental checkpointing: every completed (module, model,
condition, replicate) is written to master_log.json immediately, so an
interrupted run resumes from completed keys rather than restarting --
see run_all()'s `done` set.

RTLLM ITSELF IS NEVER COPIED INTO THIS REPO. D:\\Projects\\RTLLM is read
live at run time (design_description.txt for the spec, testbench.v +
any companion data file for the harness); this script's only writes go
under the gitignored phase1/results/rtllm_pilot/ tree (staged, renamed
testbench copies + the run output).

Requires: WSL (Verilator/Yosys/Icarus) + Ollama serving all 5 Tier-1
models (gemma3:4b, llama3.1, deepseek-coder:6.7b, gemma3:12b,
qwen2.5-coder:14b) -- confirm with `ollama list` before launching.

Usage:
  python phase1/rtllm_pilot_runner.py --conditions core4   # 300 runs
  python phase1/rtllm_pilot_runner.py --conditions core5   # 375 runs, adds sem_escalate_restart
Output: phase1/results/rtllm_pilot/master_log.json (gitignored, resumable)
"""
import argparse
import json
import os
import re
import shutil
import sys
import traceback

_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(_HERE, "..", "src", "runner"))
import stitch_runner  # noqa: E402

sys.path.insert(0, _HERE)
import escalation_runner  # noqa: E402 -- module import (not `from`) so the
                           # pass-detection monkeypatch below can rebind its
                           # run_iverilog_sim name too, see _patch_pass_detection()
from escalation_runner import run_one_replicate  # noqa: E402
from escalation_state import EscalationConfig  # noqa: E402

# LAUNCH-BLOCKING FIX, found during pilot sanity-checking before any real
# run depended on it (same discipline as smoke_test.py catching the
# escalation_state logging bug in Task 1): stitch_runner.run_iverilog_sim()'s
# pass-detection heuristic checks for the literal substring "PASS"
# (case-sensitive) or "ALL TESTS PASSED" -- tuned for v20/v2's testbench
# convention. RTLLM's actual pass string is "Your Design Passed", which
# contains neither ("PASS" != "Pass" case-sensitively) -- so every genuine
# RTLLM pass would be misreported as a failure by the unmodified function.
# Not fixed by editing stitch_runner.py (shared with phase0's LOCKED
# regression checks); fixed the same way STUCK_THRESHOLD/TESTBENCH_DIR/
# RESULTS_DIR are already toggled here -- rebinding the module-global name
# stitch_runner.run_iverilog_sim (and escalation_runner.py's own separate
# binding of the same name, imported via `from stitch_runner import
# run_iverilog_sim` -- reassigning stitch_runner's copy does NOT change
# escalation_runner's, they are two different names after `from X import Y`)
# to a wrapper that defers to the real function for the actual compile/sim
# work and file-writing side effects, then only corrects the verdict.
_RTLLM_PASS_STRING = "Your Design Passed"
_original_run_iverilog_sim = stitch_runner.run_iverilog_sim


def _rtllm_aware_run_iverilog_sim(iter_dir, module_name):
    success, feedback = _original_run_iverilog_sim(iter_dir, module_name)
    if not success and _RTLLM_PASS_STRING in feedback:
        return True, feedback
    return success, feedback


def _patch_pass_detection():
    stitch_runner.run_iverilog_sim = _rtllm_aware_run_iverilog_sim
    escalation_runner.run_iverilog_sim = _rtllm_aware_run_iverilog_sim


_patch_pass_detection()

RTLLM_ROOT = r"D:\Projects\RTLLM"
REAL_STUCK_THRESHOLD = 2
N_REPLICATES = 3

RESULTS_ROOT = os.path.join(_HERE, "results", "rtllm_pilot")
STAGED_ROOT = os.path.join(RESULTS_ROOT, "_staged")
MASTER_LOG = os.path.join(RESULTS_ROOT, "master_log.json")

MODELS = ["gemma3:4b", "llama3.1:latest", "deepseek-coder:6.7b", "gemma3:12b", "qwen2.5-coder:14b"]
CORE4 = ["baseline", "raw_adv", "sem_adv", "sem_escalate"]
CORE5 = CORE4 + ["sem_escalate_restart"]

# (design, category, relative_path_under_RTLLM_ROOT) -- from RTLLM_PILOT_PREREG.md
PILOT_DESIGNS = [
    ("accu",           "Arithmetic",    "Arithmetic/Accumulator/accu"),
    ("counter_12",     "Control",       "Control/Counter/counter_12"),
    ("barrel_shifter", "Memory",        "Memory/Shifter/barrel_shifter"),
    ("alu",            "Miscellaneous", "Miscellaneous/RISC-V/alu"),
    ("calendar",        "Miscellaneous", "Miscellaneous/Others/calendar"),
]


def _stage_testbench(design):
    """Idempotent: copies <design>'s testbench.v to
    _staged/<design>/<design>_tb.v (stitch_runner's naming convention)
    plus any companion data file, so it can be handed to
    run_one_condition()/run_one_replicate() unmodified. Returns
    (testbench_dir, dependency_file_list)."""
    rel = next(p for d, c, p in PILOT_DESIGNS if d == design)
    src_dir = os.path.join(RTLLM_ROOT, rel)
    staged_dir = os.path.join(STAGED_ROOT, design)
    os.makedirs(staged_dir, exist_ok=True)

    tb_dst = os.path.join(staged_dir, f"{design}_tb.v")
    shutil.copy(os.path.join(src_dir, "testbench.v"), tb_dst)

    deps = []
    for f in os.listdir(src_dir):
        if f in ("testbench.v", "makefile", "design_description.txt") or f.startswith("verified_"):
            continue
        dep_dst = os.path.join(staged_dir, f)
        shutil.copy(os.path.join(src_dir, f), dep_dst)
        deps.append(dep_dst)

    return staged_dir, deps


def _get_spec(design):
    rel = next(p for d, c, p in PILOT_DESIGNS if d == design)
    with open(os.path.join(RTLLM_ROOT, rel, "design_description.txt"), encoding="utf-8") as f:
        return f.read()


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


def _run_classic(design, category, model, condition, spec, testbench_dir, deps, replicate):
    stitch_runner.STUCK_THRESHOLD = REAL_STUCK_THRESHOLD
    stitch_runner.TESTBENCH_DIR = testbench_dir
    safe_model = model.replace(":", "_").replace(".", "")
    stitch_runner.RESULTS_DIR = os.path.join(RESULTS_ROOT, "classic", condition, f"replicate_{replicate}")

    m = stitch_runner.run_one_condition(
        spec=spec, module_name=design, model=model, condition=condition, dependencies=deps,
    )
    err_seq = [it.get("err_type") for it in m["per_iter_detail"]]
    fires, fire_iters = _count_stuck_fires(err_seq)

    return {
        "module": design, "category": category, "model": model, "condition": condition,
        "run_replicate": replicate, "iteration_cap": 6,
        "pass": m["pass"], "iterations_to_pass": m["iterations_to_pass"],
        "total_iterations": m["total_iterations"], "total_tokens": m["total_tokens"],
        "semantic_fired": m["semantic_fired"],
        "stuck_threshold_fires": fires, "stuck_threshold_fire_iters": fire_iters,
        "escalation_iteration": None, "fired_escalate": None,
        "restart_iterations": None, "restart_threshold_reached_iterations": None,
        "restart_preempted_by_stuck_threshold": None,
        "per_iteration": m["per_iter_detail"],
    }


def _run_escalation(design, category, model, condition, spec, testbench_dir, deps, replicate):
    config = EscalationConfig(
        escalate_after=2, restart_after=3,
        allow_restart=(condition == "sem_escalate_restart"),
        signature_window=5, max_iterations=8,
    )
    results_dir = os.path.join(RESULTS_ROOT, "escalation", condition)

    run_log = run_one_replicate(
        spec=spec, module_name=design, model=model, condition=condition,
        run_replicate=replicate, config=config,
        testbench_dir=testbench_dir, results_dir=results_dir, dependencies=deps,
    )
    s = run_log["summary"]
    err_seq = [it["err_type"] for it in run_log["iterations"]]
    fires, fire_iters = _count_stuck_fires(err_seq)
    semantic_fired = sum(1 for it in run_log["iterations"] if it["interpreter_invoked"])

    return {
        "module": design, "category": category, "model": model, "condition": condition,
        "run_replicate": replicate, "iteration_cap": 8,
        "pass": s["pass"], "iterations_to_pass": s["iterations_to_pass"],
        "total_iterations": s["total_iterations"], "total_tokens": s["total_tokens"],
        "semantic_fired": semantic_fired,
        "stuck_threshold_fires": fires, "stuck_threshold_fire_iters": fire_iters,
        "escalation_iteration": s["escalation_iteration"], "fired_escalate": s["fired_escalate"],
        "restart_iterations": s.get("restart_iterations"),
        "restart_threshold_reached_iterations": s.get("restart_threshold_reached_iterations"),
        "restart_preempted_by_stuck_threshold": s.get("restart_preempted_by_stuck_threshold"),
        "per_iteration": run_log["iterations"],
    }


INCIDENTS_LOG = os.path.join(RESULTS_ROOT, "incidents.log")
RETRY_ATTEMPTS = 3  # total attempts per cell, unattended run -- see run-autonomy note below


def _log_incident(key, attempt, max_attempts, exc, final):
    """Append-only, human-readable. Every exception during the overnight
    run is logged here, whether it's a transient infra hiccup that a
    retry cleared or a cell that exhausted all retries. This function
    NEVER changes any harness behavior in response to what it logs --
    see the run-autonomy note on run_all() for why that boundary matters
    and is deliberately not crossed here."""
    os.makedirs(RESULTS_ROOT, exist_ok=True)
    module, model, condition, replicate = key
    ts = __import__("datetime").datetime.now().isoformat(timespec="seconds")
    status = "GIVING UP -- cell errored, logged to master_log.json, moving on" if final \
        else f"retrying (attempt {attempt+1}/{max_attempts})"
    with open(INCIDENTS_LOG, "a", encoding="utf-8") as f:
        f.write(f"[{ts}] {module} / {model} / {condition} / replicate {replicate}\n")
        f.write(f"  attempt {attempt}/{max_attempts} -- {status}\n")
        f.write(f"  exception: {type(exc).__name__}: {exc}\n")
        f.write("  traceback:\n")
        for line in traceback.format_exception(type(exc), exc, exc.__traceback__):
            f.write("    " + line)
        f.write("\n")


def run_all(conditions):
    """
    RUN-AUTONOMY BOUNDARY (read before touching this function):
    This loop retries a failing cell up to RETRY_ATTEMPTS times VERBATIM
    -- same function, same args, same config -- then logs and moves on.
    It does not, and must not, ever branch on WHAT the exception was to
    change harness behavior (e.g. patch a function, adjust a threshold,
    alter what's measured) in response to a failure discovered mid-run.
    That boundary is deliberate: an unattended "fix" applied overnight
    can silently change what the whole run measures and still look
    clean in the morning. Infra retries are safe because they change
    nothing about the measurement; anything that would require changing
    what's measured (the Task A pass-detection bug found before this
    launch is the precedent) gets logged with full repro detail and left
    for morning review, not auto-patched here.
    """
    entries = _load_master_log()
    done = {(e["module"], e["model"], e["condition"], e["run_replicate"]) for e in entries}

    total = len(PILOT_DESIGNS) * len(MODELS) * len(conditions) * N_REPLICATES
    done_count = len(done)

    for design, category, _rel in PILOT_DESIGNS:
        testbench_dir, deps = _stage_testbench(design)
        spec = _get_spec(design)
        for model in MODELS:
            for condition in conditions:
                for replicate in range(1, N_REPLICATES + 1):
                    key = (design, model, condition, replicate)
                    if key in done:
                        continue

                    done_count += 1
                    print(f"\n[{done_count}/{total}] {design} / {model} / {condition} / replicate {replicate}")

                    entry = None
                    last_exc = None
                    for attempt in range(1, RETRY_ATTEMPTS + 1):
                        try:
                            if condition in ("baseline", "raw_adv", "sem_adv"):
                                entry = _run_classic(design, category, model, condition, spec, testbench_dir, deps, replicate)
                            else:
                                entry = _run_escalation(design, category, model, condition, spec, testbench_dir, deps, replicate)
                            entry["error"] = None
                            entry["attempts"] = attempt
                            break
                        except Exception as e:
                            last_exc = e
                            print(f"  ERROR (attempt {attempt}/{RETRY_ATTEMPTS}): {e}")
                            _log_incident(key, attempt, RETRY_ATTEMPTS, e, final=(attempt == RETRY_ATTEMPTS))

                    if entry is None:
                        entry = {
                            "module": design, "category": category, "model": model, "condition": condition,
                            "run_replicate": replicate, "error": f"{type(last_exc).__name__}: {last_exc}",
                            "attempts": RETRY_ATTEMPTS,
                        }

                    entries.append(entry)
                    _save_master_log(entries)

    print(f"\nDone. {len(entries)} entries -> {MASTER_LOG}")
    n_errored = sum(1 for e in entries if e.get("error"))
    if n_errored:
        print(f"{n_errored} cell(s) errored after {RETRY_ATTEMPTS} attempts each -- see {INCIDENTS_LOG}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--conditions", choices=["core4", "core5"], default="core4",
                         help="core4 = baseline/raw_adv/sem_adv/sem_escalate (300 runs); "
                              "core5 = core4 + sem_escalate_restart (375 runs)")
    parser.add_argument("--modules", default=None,
                         help="Comma-separated subset of PILOT_DESIGNS names (default: all 5). "
                              "Additive CLI option, doesn't change what's measured per cell -- "
                              "added for the bug-fix validation re-run (alu, calendar only).")
    parser.add_argument("--results-dir", default=None,
                         help="Override the output directory (default: results/rtllm_pilot). "
                              "Use a fresh directory for a re-run so the incremental-checkpoint "
                              "'done' set doesn't wrongly skip cells whose old results predate "
                              "a harness fix -- that's what the bug-fix validation re-run does.")
    args = parser.parse_args()

    if args.modules:
        wanted = set(m.strip() for m in args.modules.split(","))
        unknown = wanted - {d for d, _, _ in PILOT_DESIGNS}
        if unknown:
            print(f"ERROR: unknown module(s) in --modules: {unknown}")
            sys.exit(1)
        PILOT_DESIGNS = [t for t in PILOT_DESIGNS if t[0] in wanted]
        print(f"Restricted to modules: {[t[0] for t in PILOT_DESIGNS]}")

    if args.results_dir:
        RESULTS_ROOT = args.results_dir
        STAGED_ROOT = os.path.join(RESULTS_ROOT, "_staged")
        MASTER_LOG = os.path.join(RESULTS_ROOT, "master_log.json")
        INCIDENTS_LOG = os.path.join(RESULTS_ROOT, "incidents.log")
        print(f"Output redirected to: {RESULTS_ROOT}")

    run_all(CORE4 if args.conditions == "core4" else CORE5)
