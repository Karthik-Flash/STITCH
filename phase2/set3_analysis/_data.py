"""
phase2/set3_analysis/_data.py -- shared data-loading/pivoting/cost-
extraction for the Set 3 (scale ladder) analysis scripts.

Non-negotiable: pass/fail comes ONLY from master_log.json's own `pass`
field -- detect_outcome() already did that work correctly. Nothing here
re-derives anything from a sim_log.txt.

Recoverable-band tier membership is INHERITED VERBATIM from Twin's
(Set 2) module_categories.json -- the same 17-module set Set 3 was
scoped to at runtime (set3_runner.py's own _load_recoverable_names()),
never recomputed here either.

Set 3 has exactly 2 known transient (`APITimeoutError`) cells dropped
from master_log.json's 612 rows -- KNOWN_ERROR_CELLS is the exact list,
cross-checked at load time so any *additional*, unexpected failure can't
hide behind this known set.

This module also loads Set 1's master_log.json (via
phase2/set1_analysis/_data.py, sys.path-inserted) for the
harmful-regime-by-capability figure, which spans all 6 models across
both runs -- Set 3 alone only has 3 of the 6 points that figure needs.
"""
import json
import os
import sys
from collections import defaultdict

_HERE = os.path.dirname(os.path.abspath(__file__))
_TWIN_DIR = os.path.join(_HERE, "..", "twin_analysis_SET2")
sys.path.insert(0, _TWIN_DIR)
from categorize import FUNCTIONAL_CLASS_ORDER  # noqa: E402

MASTER_LOG = os.path.join(_HERE, "..", "results", "set3_run", "master_log.json")
CATEGORIES_JSON = os.path.join(_TWIN_DIR, "module_categories.json")
RESULTS_ROOT = os.path.join(_HERE, "..", "results", "set3_run")

CONDITIONS = ["baseline", "sem_adv", "sem_escalate", "sem_escalate_restart"]
MODELS = ["qwen2.5-coder:14b", "gemma3:27b", "qwen2.5-coder:32b"]
MODEL_DISPLAY = {
    "qwen2.5-coder:14b": "qwen2.5-coder:14b",
    "gemma3:27b": "gemma3:27b",
    "qwen2.5-coder:32b": "qwen2.5-coder:32b",
}

N_REPLICATES = 3
EXPECTED_TOTAL_RUNS = 612
EXPECTED_MODULE_COUNT = 17

# The exact 2 known transient-timeout cells, from direct inspection of
# master_log.json's `error` field.
KNOWN_ERROR_CELLS = {
    ("comparator_4bit", "qwen2.5-coder:32b", "sem_escalate_restart", 1),
    ("multi_booth_8bit", "qwen2.5-coder:32b", "sem_escalate_restart", 2),
}
KNOWN_ERROR_AFFECTED_CELLS = {(m, mo, c) for m, mo, c, _r in KNOWN_ERROR_CELLS}


def _safe_model(model):
    return model.replace(":", "_").replace(".", "")


def cell_dir(module, model, condition, replicate):
    return os.path.join(RESULTS_ROOT, module, _safe_model(model), condition, f"rep{replicate}")


def load_master_log(path=MASTER_LOG):
    with open(path, encoding="utf-8") as f:
        entries = json.load(f)
    assert len(entries) == EXPECTED_TOTAL_RUNS, (
        f"expected exactly {EXPECTED_TOTAL_RUNS} entries in master_log.json, "
        f"got {len(entries)}."
    )
    errored = {
        (e["module"], e["model"], e["condition"], e["run_replicate"])
        for e in entries if e.get("error")
    }
    assert errored == KNOWN_ERROR_CELLS, (
        "master_log.json's actual error set does not match the known "
        f"2-cell transient-timeout set this analysis was built against. "
        f"Extra: {errored - KNOWN_ERROR_CELLS}  Missing: {KNOWN_ERROR_CELLS - errored}."
    )
    return entries


def valid_entries(entries):
    return [e for e in entries if not e.get("error")]


def load_categories(path=CATEGORIES_JSON):
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def module_list(entries):
    mods = sorted(set(e["module"] for e in entries))
    assert len(mods) == EXPECTED_MODULE_COUNT, (
        f"expected exactly {EXPECTED_MODULE_COUNT} modules, got {len(mods)}"
    )
    categories = load_categories()
    recoverable = {m for m, info in categories.items() if info["difficulty_tier"] == "recoverable"}
    assert set(mods) == recoverable, (
        f"Set 3's module set does not exactly equal Twin's recoverable-band "
        f"set -- extra: {set(mods) - recoverable}, missing: {recoverable - set(mods)}. "
        f"A ceiling/floor module leaked in, or a recoverable one is missing."
    )
    return mods


def pivot_pass_counts(entries):
    """{(module, model, condition): (n_pass, n_valid)} for all
    17 x 3 x 4 = 204 cells. n_valid is exactly N_REPLICATES=3 except the
    2 cells touched by a known transient error."""
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


def pooled_recoverable_rate(entries, model, condition):
    """(n_pass, n_valid) pooled over all 17 recoverable-band modules for
    one (model, condition)."""
    counts = pivot_pass_counts(entries)
    mods = module_list(entries)
    n_pass = sum(counts[(m, model, condition)][0] for m in mods)
    n_valid = sum(counts[(m, model, condition)][1] for m in mods)
    return n_pass, n_valid


# ---------------------------------------------------------------------
# Per-run cost extraction -- IDENTICAL formulas to
# phase2/set1_analysis/_data.py's load_run_cost() (same runner code,
# same condition-gating logic; see that file's long comment for the full
# derivation/verification of the baseline/sem_adv reconstruction
# formula). Reimplemented here (not cross-imported) for the same
# same-module-name-collision reason set1_analysis/_data.py's own
# sorted_modules_by_group() gives for not cross-importing Twin's.
def load_run_cost(module, model, condition, replicate):
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
            print(f"[set3_analysis] WARNING: cost data missing/malformed for "
                  f"{module}/{model}/{condition}/rep{replicate} ({path}): {ex}",
                  file=sys.stderr)
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
            print(f"[set3_analysis] WARNING: cost data missing/malformed for "
                  f"{module}/{model}/{condition}/rep{replicate} ({path}): {ex}",
                  file=sys.stderr)
            return None
    return {
        "tokens": tokens, "verilator_calls": verilator, "yosys_calls": yosys,
        "tool_calls": verilator + yosys, "iterations": n_iter,
    }


def iter_valid_runs(entries):
    for e in valid_entries(entries):
        yield e["module"], e["model"], e["condition"], e["run_replicate"]


# ---------------------------------------------------------------------
# Set 1 access, for the 6-model harmful-regime-by-capability figure.
#
# NOT done via `import _data` against set1_analysis/ on sys.path: this
# file IS ALSO named _data.py, and Python caches modules in sys.modules
# by their import name -- by the time this file's own body executes, the
# name "_data" already resolves (to THIS file, still initializing), so a
# plain `import _data` here would silently return this module itself,
# never load set1_analysis/_data.py at all. Same name-collision
# set1_analysis/_data.py's own sorted_modules_by_group() comment already
# flags for why it reimplements rather than cross-imports Twin's _data.py
# -- same fix here: read Set 1's master_log.json directly and reimplement
# the small pivot/filter needed, rather than import the colliding module.
SET1_MASTER_LOG = os.path.join(_HERE, "..", "results", "set1_run", "master_log.json")
SET1_EXPECTED_TOTAL_RUNS = 1512


def set1_pooled_recoverable_rate(model, condition):
    """(n_pass, n_valid) pooled over Set 1's 17 recoverable-band modules
    (Twin's tier file, same as this file's own CATEGORIES_JSON) for one
    (model, condition) -- Set 1's own module pool is 42 modules; this
    filters to the recoverable-band 17 exactly as
    set1_analysis/fig2_tier_split.py does."""
    with open(SET1_MASTER_LOG, encoding="utf-8") as f:
        entries = json.load(f)
    assert len(entries) == SET1_EXPECTED_TOTAL_RUNS, (
        f"expected exactly {SET1_EXPECTED_TOTAL_RUNS} entries in Set 1's "
        f"master_log.json, got {len(entries)}."
    )
    categories = load_categories()
    recoverable = {m for m, info in categories.items() if info["difficulty_tier"] == "recoverable"}

    n_pass, n_valid = 0, 0
    for e in entries:
        if e.get("error"):
            continue
        if e["model"] != model or e["condition"] != condition:
            continue
        if e["module"] not in recoverable:
            continue
        n_valid += 1
        if e["pass"]:
            n_pass += 1
    return n_pass, n_valid
