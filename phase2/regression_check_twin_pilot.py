"""
phase2/regression_check_twin_pilot.py -- Bug #3 fix, regression oracle
(deliverable #5 of the runner-hardening task, 2026-08-24).

Replays every real, on-disk sim_log.txt from the 64-run twin pilot
(phase2/results/twin_run_pilot/, gitignored but present on disk) through
the new detect_outcome("rtllm") and re-derives per-cell pass/fail the
SAME way the harness does at run time (first iteration whose simulation
output reaches "PASS" -- see stitch_runner_hpc.run_iverilog_sim()), then
diffs the result against phase2/results/twin_run_pilot/corrected_pass.json
-- the ground truth TWIN_RUN_ANALYSIS.md (Appendix A) built by manually re-scanning
every log for the literal "Design Passed" substring before this fix
existed. If detect_outcome() is correct, this script's output must match
corrected_pass.json exactly, cell for cell.

This is NOT a re-run of the harness (no LLM calls, no simulator
invocations) -- it reads the sim_log.txt files the original twin-pilot job
already produced and re-judges them, so it's fast, deterministic, and
proves the NEW detection logic against the SAME real data the OLD logic
got wrong, without needing WSL/Ollama/RTLLM available.

Usage: python phase2/regression_check_twin_pilot.py
Exit code: 0 if every cell matches corrected_pass.json AND the grid
stated in the runner-hardening brief; 1 otherwise (with a diff table
printed).
"""
import json
import os
import re
import sys

_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(_HERE, "..", "src", "interpreter"))
from pass_detection import detect_outcome  # noqa: E402

RESULTS_ROOT = os.path.join(_HERE, "results", "twin_run_pilot")
CORRECTED_JSON = os.path.join(RESULTS_ROOT, "corrected_pass.json")
MASTER_LOG = os.path.join(RESULTS_ROOT, "master_log.json")

CONDITION = "baseline"  # twin run's CONDITION is fixed at "baseline" -- see twin_run_runner.py


def _safe_model(model):
    """Mirrors stitch_runner(_hpc).run_one_condition()'s own
    safe_model = model.replace(":", "_").replace(".", "") -- must match
    exactly, since that's literally the directory name on disk."""
    return model.replace(":", "_").replace(".", "")


def _cell_dir(module, model, prompt_condition, run_replicate):
    return os.path.join(
        RESULTS_ROOT, prompt_condition, f"replicate_{run_replicate}",
        _safe_model(model), CONDITION, module,
    )


_ITER_DIR_RE = re.compile(r"^iter_(\d+)$")


def _real_pass_from_disk(cell_dir):
    """Scans every iter_N/sim_log.txt present under cell_dir, in
    iteration order, and returns (real_pass, real_pass_iter) -- the
    iteration of the FIRST simulation whose output detect_outcome()s to
    "PASS". This is exactly the twin-pilot analysis (TWIN_RUN_ANALYSIS.md, Appendix A)'s stated methodology
    ("what this analysis uses instead: the iteration of the first real
    pass"), just automated through the new shared detector instead of a
    manual "Design Passed" grep.

    Only the "--- SIMULATION ---" section of sim_log.txt is fed to
    detect_outcome() -- matching exactly what run_iverilog_sim() itself
    passes it (compile-stage text is never part of that argument)."""
    if not os.path.isdir(cell_dir):
        return False, None, 0

    iters = []
    for name in os.listdir(cell_dir):
        m = _ITER_DIR_RE.match(name)
        if m:
            iters.append(int(m.group(1)))
    iters.sort()

    for i in iters:
        log_path = os.path.join(cell_dir, f"iter_{i}", "sim_log.txt")
        if not os.path.exists(log_path):
            continue
        with open(log_path, encoding="utf-8", errors="replace") as f:
            content = f.read()
        marker = "--- SIMULATION ---"
        if marker not in content:
            continue  # compile error iteration -- never reached simulation
        sim_section = content.split(marker, 1)[1]
        if detect_outcome(sim_section, "rtllm") == "PASS":
            return True, i, len(iters)

    return False, None, len(iters)


# Brief's stated grid (handoff task prompt, Task 5) -- {(module, model,
# prompt_condition): expected_pass_count_out_of_3_or_None_if_no_data}.
# Not all model-conditions are listed per module in the brief; only the
# ones it explicitly calls out are checked here.
EXPECTED_GRID = {
    ("accu", "rtlcoder-deepseek-v1.1", "native"):    0,
    ("accu", "rtlcoder-deepseek-v1.1", "shared"):    0,
    ("accu", "deepseek-coder:6.7b", "shared"):       0,
    ("accu", "gemma3:4b", "shared"):                 0,
    ("accu", "llama3.1:latest", "shared"):           0,
    ("counter_12", "rtlcoder-deepseek-v1.1", "native"): 3,
    ("counter_12", "rtlcoder-deepseek-v1.1", "shared"): 3,
    ("counter_12", "deepseek-coder:6.7b", "shared"):    3,
    ("counter_12", "gemma3:4b", "shared"):              3,
    ("counter_12", "llama3.1:latest", "shared"):        3,
    ("barrel_shifter", "deepseek-coder:6.7b", "shared"): 1,
    ("alu", "rtlcoder-deepseek-v1.1", "native"):     0,
    ("alu", "rtlcoder-deepseek-v1.1", "shared"):     0,
    ("alu", "deepseek-coder:6.7b", "shared"):        0,
    ("alu", "gemma3:4b", "shared"):                  0,
    ("alu", "llama3.1:latest", "shared"):             0,
    ("calendar", "rtlcoder-deepseek-v1.1", "native"): 3,
}
# barrel_shifter is 0/3 for every OTHER model-condition present in the
# pilot -- filled in below once we know which model-conditions actually
# have data, rather than hand-enumerating them here.
_BARREL_EXCEPTION = ("barrel_shifter", "deepseek-coder:6.7b", "shared")


def main():
    if not os.path.exists(CORRECTED_JSON):
        print(f"FATAL: {CORRECTED_JSON} not found -- this script needs the "
              f"twin pilot's real (gitignored) results tree on disk.")
        sys.exit(1)

    with open(CORRECTED_JSON, encoding="utf-8") as f:
        corrected = json.load(f)

    mismatches = []
    rows = []
    for entry in corrected:
        module = entry["module"]
        model = entry["model"]
        prompt_condition = entry["prompt_condition"]
        replicate = entry["run_replicate"]

        cell_dir = _cell_dir(module, model, prompt_condition, replicate)
        real_pass, real_pass_iter, n_iters = _real_pass_from_disk(cell_dir)

        expected_pass = entry["real_pass"]
        expected_iter = entry["real_pass_iter"]

        ok = (real_pass == expected_pass) and (real_pass_iter == expected_iter)
        rows.append((module, model, prompt_condition, replicate,
                     expected_pass, expected_iter, real_pass, real_pass_iter, ok))
        if not ok:
            mismatches.append(rows[-1])

    W = 100
    print("=" * W)
    print("  Twin-pilot regression check -- detect_outcome() vs corrected_pass.json")
    print("=" * W)
    print(f"  {'module':<16}{'model':<24}{'cond':<8}{'rep':<4}"
          f"{'expect':<8}{'expect_i':<9}{'got':<8}{'got_i':<7}{'status'}")
    for (module, model, cond, rep, exp_p, exp_i, got_p, got_i, ok) in rows:
        status = "OK" if ok else "MISMATCH"
        print(f"  {module:<16}{model:<24}{cond:<8}{rep:<4}"
              f"{str(exp_p):<8}{str(exp_i):<9}{str(got_p):<8}{str(got_i):<7}{status}")

    print(f"\n  {len(rows) - len(mismatches)}/{len(rows)} cells match corrected_pass.json exactly.")

    # Aggregate into the module/model-condition grid and check against the
    # brief's stated numbers.
    from collections import defaultdict
    agg = defaultdict(lambda: [0, 0])  # key -> [n_pass, n_total]
    for (module, model, cond, rep, exp_p, exp_i, got_p, got_i, ok) in rows:
        key = (module, model, cond)
        agg[key][1] += 1
        if got_p:
            agg[key][0] += 1

    grid_mismatches = []
    print(f"\n{'=' * W}")
    print("  Aggregated pass/N per (module, model, prompt_condition) vs. brief's stated grid")
    print("=" * W)
    for key in sorted(agg):
        n_pass, n_total = agg[key]
        expected = EXPECTED_GRID.get(key)
        if key == _BARREL_EXCEPTION:
            expected = 1
        elif key[0] == "barrel_shifter":
            expected = 0
        note = ""
        if expected is not None and expected != n_pass:
            grid_mismatches.append((key, expected, n_pass))
            note = f"  <-- EXPECTED {expected}, GOT {n_pass}"
        print(f"  {key[0]:<16}{key[1]:<24}{key[2]:<8} {n_pass}/{n_total}{note}")

    print()
    if mismatches or grid_mismatches:
        print(f"REGRESSION CHECK FAILED: {len(mismatches)} cell mismatch(es) vs. "
              f"corrected_pass.json, {len(grid_mismatches)} grid mismatch(es) vs. the brief.")
        sys.exit(1)

    print("REGRESSION CHECK PASSED: detect_outcome() reproduces corrected_pass.json "
          "exactly, and the aggregated grid matches the runner-hardening brief.")
    sys.exit(0)


if __name__ == "__main__":
    main()
