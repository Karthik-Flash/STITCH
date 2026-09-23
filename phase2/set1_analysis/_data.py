"""
phase2/set1_analysis/_data.py -- shared data-loading/pivoting/cost-
extraction for the Set 1 (STITCH conditions on RTLLM) analysis scripts.

Non-negotiable (see the analysis brief): pass/fail comes ONLY from
master_log.json's own `pass` field -- detect_outcome() already did that
work correctly (regression-verified 64/64, see
docs/IMP_PHASE2_RUNNER_HARDENING_REPORT.md). Nothing here re-derives anything
from a sim_log.txt.

Difficulty tiers and functional classes are INHERITED VERBATIM from
Twin's (Set 2) module_categories.json -- not recomputed here. Twin's
pooled rate is over 5 model-conditions x N=3 = 15 draws/module; Set 1's
own pool would only be 3 models x 4 conditions x N=3 = 36 draws/module
using a materially different (STITCH-condition, not model) axis -- reusing
Twin's tiers keeps "difficulty" defined once, by the stronger/orthogonal
signal, rather than two competing tier definitions across the two RTLLM
analyses. Both runs share the identical 42-module pool (verified below).

Set 1 has exactly 6 known transient (`APITimeoutError`) cells dropped
from master_log.json's 1512 rows -- KNOWN_ERROR_CELLS is the exact
(module, model, condition, run_replicate) list, cross-checked at load
time so any *additional*, unexpected failure can't hide behind this known
set (load_master_log asserts an exact set match, not just a count match).
"""
import json
import os
import sys
import warnings
from collections import defaultdict

_HERE = os.path.dirname(os.path.abspath(__file__))
_TWIN_DIR = os.path.join(_HERE, "..", "twin_analysis_SET2")
sys.path.insert(0, _TWIN_DIR)
from categorize import FUNCTIONAL_CLASS_ORDER  # noqa: E402

MASTER_LOG = os.path.join(_HERE, "..", "results", "set1_run", "master_log.json")
CATEGORIES_JSON = os.path.join(_TWIN_DIR, "module_categories.json")
RESULTS_ROOT = os.path.join(_HERE, "..", "results", "set1_run")

# Condition display order -- locked, matches Phase 1 Table 4's column
# order (baseline, sem_adv, sem_escalate, sem_escalate_restart). No
# raw_adv in Set 1 -- not part of this run's condition set.
CONDITIONS = ["baseline", "sem_adv", "sem_escalate", "sem_escalate_restart"]

# Model order/labels -- locked, matches the brief's Table-full-grid spec
# (3 model blocks: gemma3:4b, llama3.1, deepseek-coder).
MODELS = ["gemma3:4b", "llama3.1:latest", "deepseek-coder:6.7b"]
MODEL_DISPLAY = {
    "gemma3:4b": "gemma3:4b",
    "llama3.1:latest": "llama3.1",
    "deepseek-coder:6.7b": "deepseek-coder",
}

N_REPLICATES = 3
EXPECTED_TOTAL_RUNS = 1512
EXPECTED_MODULE_COUNT = 42
EXPECTED_ERROR_COUNT = 6

# The exact 6 known transient-timeout cells (module, model, condition,
# run_replicate) -- from direct inspection of master_log.json's `error`
# field. load_master_log() asserts the real error set equals this exactly.
KNOWN_ERROR_CELLS = {
    ("LIFObuffer", "deepseek-coder:6.7b", "sem_escalate_restart", 2),
    ("RAM", "llama3.1:latest", "sem_escalate", 1),
    ("RAM", "llama3.1:latest", "sem_escalate", 2),
    ("RAM", "llama3.1:latest", "sem_escalate", 3),
    ("RAM", "llama3.1:latest", "sem_escalate_restart", 1),
    ("RAM", "llama3.1:latest", "sem_escalate_restart", 3),
}
# Cells (module, model, condition) touched by at least one of the errors
# above -- these are the only cells allowed to have fewer than N=3 valid
# replicates anywhere downstream.
KNOWN_ERROR_AFFECTED_CELLS = {(m, mo, c) for m, mo, c, _r in KNOWN_ERROR_CELLS}


def _safe_model(model):
    """Mirrors set1_runner.py's own sanitization exactly (see its
    _relocate()/cell path helpers) -- ':' and '.' both stripped."""
    return model.replace(":", "_").replace(".", "")


def cell_dir(module, model, condition, replicate):
    return os.path.join(RESULTS_ROOT, module, _safe_model(model), condition, f"rep{replicate}")


def load_master_log(path=MASTER_LOG):
    with open(path, encoding="utf-8") as f:
        entries = json.load(f)
    assert len(entries) == EXPECTED_TOTAL_RUNS, (
        f"expected exactly {EXPECTED_TOTAL_RUNS} entries in master_log.json, "
        f"got {len(entries)} -- data may be incomplete or from the wrong run."
    )
    errored = {
        (e["module"], e["model"], e["condition"], e["run_replicate"])
        for e in entries if e.get("error")
    }
    assert errored == KNOWN_ERROR_CELLS, (
        "master_log.json's actual error set does not match the known "
        f"6-cell transient-timeout set this analysis was built against. "
        f"Extra: {errored - KNOWN_ERROR_CELLS}  Missing: {KNOWN_ERROR_CELLS - errored}. "
        "Investigate before trusting any downstream table/figure -- this "
        "analysis must not silently absorb a NEW kind of failure into the "
        "known-6 bucket."
    )
    return entries


def valid_entries(entries):
    """Entries with no error -- the 1506 rows every pass-rate/cost number
    in this directory is built from. The 6 known-errored rows are never
    silently treated as fails or passes; they are excluded entirely and
    reported separately (see SET1_ANALYSIS.md's run summary)."""
    return [e for e in entries if not e.get("error")]


def load_categories(path=CATEGORIES_JSON):
    if not os.path.exists(path):
        raise FileNotFoundError(
            f"{path} not found -- Twin's categorize.py must have been run "
            "first (phase2/twin_analysis_SET2/categorize.py). Set 1 reuses "
            "those tiers verbatim, per the brief; it does not recompute them."
        )
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def module_list(entries):
    """All 42 module names, sorted. Uses ALL entries (not just valid
    ones) -- a module is never dropped by the 6 known errors, only
    individual replicates within it are."""
    mods = sorted(set(e["module"] for e in entries))
    assert len(mods) == EXPECTED_MODULE_COUNT, (
        f"expected exactly {EXPECTED_MODULE_COUNT} modules, got {len(mods)}"
    )
    assert "edge_detect" not in mods and "square_wave" not in mods
    return mods


def sorted_modules_by_group(categories):
    """Modules sorted by (functional_class, difficulty_tier, module) --
    same grouping convention Twin's table1.py uses, reimplemented here
    (not cross-imported) to avoid a same-named `_data` module collision
    between the two analysis directories."""
    tier_order = {"ceiling": 0, "recoverable": 1, "floor": 2}
    class_order = {c: i for i, c in enumerate(FUNCTIONAL_CLASS_ORDER)}

    def key(m):
        info = categories[m]
        return (class_order[info["functional_class"]], tier_order[info["difficulty_tier"]], m)

    return sorted(categories.keys(), key=key)


def pivot_pass_counts(entries):
    """Returns {(module, model, condition): (n_pass, n_valid)} for all
    42 x 3 x 4 = 504 cells. n_valid is normally exactly N_REPLICATES=3;
    it is < 3 (down to 0) ONLY for the 6 cells touched by a known
    transient error -- asserted explicitly below, so an unexpected
    missing replicate anywhere else fails loudly rather than silently
    under-counting a cell."""
    mods = module_list(entries)
    passes = defaultdict(int)
    totals = defaultdict(int)
    for e in valid_entries(entries):
        key = (e["module"], e["model"], e["condition"])
        totals[key] += 1
        if e["pass"]:
            passes[key] += 1

    result = {}
    bad = {}
    for m in mods:
        for model in MODELS:
            for cond in CONDITIONS:
                key = (m, model, cond)
                n_valid = totals.get(key, 0)
                if key not in KNOWN_ERROR_AFFECTED_CELLS and n_valid != N_REPLICATES:
                    bad[key] = n_valid
                result[key] = (passes.get(key, 0), n_valid)
    assert not bad, f"cell(s) with unexpected replicate count (not in the known-error set): {bad}"
    return result


# ---------------------------------------------------------------------
# Per-run cost extraction (tool invocations, tokens, iterations).
# ---------------------------------------------------------------------
#
# baseline / sem_adv write phase2/stitch_runner_hpc.py's own metrics.json
# (no per-iteration tool_invocations field -- verilator/yosys invocation
# has to be reconstructed from documented, verified-exact gating logic):
#   - use_tools = condition in ("raw_adv", "sem_adv")  [stitch_runner_hpc.py:508]
#   - verilator is invoked on EVERY iteration when use_tools (line 590) --
#     unconditionally, before pass/fail is known -- so
#     verilator_calls == total_iterations when use_tools, else 0.
#   - yosys is invoked when use_tools AND "COMPILATION ERROR" not in
#     iverilog_fb (line 625) -- i.e. skipped only on a compile failure.
#     metrics["compile_errors"] increments exactly when
#     "COMPILATION" in iverilog_fb (line 675), and the only two code
#     paths that ever put "COMPILATION" into iverilog_fb both write
#     "COMPILATION ERROR:..." (lines 306, 315 -- verified by direct
#     inspection, no other construction site exists) -- so
#     "COMPILATION" in iverilog_fb <=> "COMPILATION ERROR" in iverilog_fb
#     for this codebase, and yosys_calls == total_iterations -
#     compile_errors exactly, when use_tools; 0 for baseline.
#
# sem_escalate / sem_escalate_restart write phase2/escalation_runner_hpc.py's
# run_log.json, which records real per-iteration tool_invocations
# {"iverilog":1,"vvp":0/1,"verilator":0/1,"yosys":0/1,"count":n} directly
# -- no reconstruction needed; summed straight from the file.
def _warn(module, model, condition, replicate, path, exc):
    print(
        f"[set1_analysis] WARNING: cost data missing/malformed for "
        f"{module}/{model}/{condition}/rep{replicate} ({path}): {exc}. "
        "Cell dropped from cost analysis and counted separately from the "
        "6 known transient-timeout errors.",
        file=sys.stderr,
    )


def load_run_cost(module, model, condition, replicate):
    """Returns {tokens, verilator_calls, yosys_calls, iterations} for one
    real completed run, or None (with a stderr warning) if its metrics
    file is missing/malformed. Callers must treat None as "drop this
    run", never as zero-cost."""
    d = cell_dir(module, model, condition, replicate)
    if condition in ("sem_escalate", "sem_escalate_restart"):
        path = os.path.join(d, "run_log.json")
        try:
            with open(path, encoding="utf-8") as f:
                run_log = json.load(f)
            iters = run_log["iterations"]
            verilator = sum(it["tool_invocations"]["verilator"] for it in iters)
            yosys = sum(it["tool_invocations"]["yosys"] for it in iters)
            tokens = run_log["summary"]["total_tokens"]
            n_iter = run_log["summary"]["total_iterations"]
        except (FileNotFoundError, json.JSONDecodeError, KeyError, IndexError) as ex:
            _warn(module, model, condition, replicate, path, ex)
            return None
    else:
        path = os.path.join(d, "metrics.json")
        try:
            with open(path, encoding="utf-8") as f:
                m = json.load(f)
            n_iter = m["total_iterations"]
            tokens = m["total_tokens"]
            if condition == "baseline":
                verilator = 0
                yosys = 0
            elif condition == "sem_adv":
                verilator = n_iter
                yosys = n_iter - m["compile_errors"]
            else:
                raise ValueError(f"unrecognized condition {condition!r}")
        except (FileNotFoundError, json.JSONDecodeError, KeyError) as ex:
            _warn(module, model, condition, replicate, path, ex)
            return None
    return {
        "tokens": tokens,
        "verilator_calls": verilator,
        "yosys_calls": yosys,
        "tool_calls": verilator + yosys,
        "iterations": n_iter,
    }


def iter_valid_runs(entries):
    """Yields (module, model, condition, replicate) for every valid
    (non-errored) run in master_log.json -- the exact 1506-run universe
    every cost number is drawn from."""
    for e in valid_entries(entries):
        yield e["module"], e["model"], e["condition"], e["run_replicate"]
