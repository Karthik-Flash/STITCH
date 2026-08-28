"""
phase2/twin_analysis/_data.py -- shared data-loading/pivoting for the
Twin run (Set 2) analysis scripts. Every deliverable in this directory
(table1, fig1, fig2, table2, prompt-format check) reads the exact same
630-row master_log.json and needs the exact same pivot -- centralized
here once rather than duplicated per script, unlike this project's usual
per-runner-duplication convention (that convention is for independently
deployable HPC runners; these are tightly-coupled analysis scripts
consumed together in one sitting, a different situation).

Non-negotiable (see the analysis brief): pass/fail comes ONLY from
master_log.json's own `pass` field -- detect_outcome() already did that
work correctly (regression-verified 64/64, see
IMP_PHASE2_RUNNER_HARDENING_REPORT.md §5). Nothing here re-derives
anything from sim logs.
"""
import json
import os
import sys
from collections import defaultdict

_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, _HERE)
from categorize import FUNCTIONAL_CLASS_ORDER  # noqa: E402
MASTER_LOG = os.path.join(_HERE, "..", "results", "twin_run", "master_log.json")
CATEGORIES_JSON = os.path.join(_HERE, "module_categories.json")

# Column order for every table/figure in this directory -- locked, per
# the brief's Table 1 spec. (model, prompt_condition, display_label).
MODEL_CONDITIONS = [
    ("rtlcoder-deepseek-v1.1", "native", "RTLCoder native"),
    ("rtlcoder-deepseek-v1.1", "shared", "RTLCoder shared"),
    ("deepseek-coder:6.7b", "shared", "deepseek-coder shared"),
    ("gemma3:4b", "shared", "gemma3:4b shared"),
    ("llama3.1:latest", "shared", "llama3.1 shared"),
]
N_REPLICATES = 3
EXPECTED_TOTAL_RUNS = 630
EXPECTED_MODULE_COUNT = 42


def load_master_log(path=MASTER_LOG):
    with open(path, encoding="utf-8") as f:
        entries = json.load(f)
    assert len(entries) == EXPECTED_TOTAL_RUNS, (
        f"expected exactly {EXPECTED_TOTAL_RUNS} entries in master_log.json, "
        f"got {len(entries)} -- data may be incomplete or from the wrong run."
    )
    assert all(not e.get("error") for e in entries), (
        "master_log.json has entries with a non-null 'error' field -- "
        "this brief assumes 0 errors (630/630 clean); investigate before "
        "trusting any downstream table/figure."
    )
    return entries


def load_categories(path=CATEGORIES_JSON):
    if not os.path.exists(path):
        raise FileNotFoundError(
            f"{path} not found -- run phase2/twin_analysis/categorize.py first."
        )
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def pivot_pass_counts(entries):
    """Returns {(module, model, prompt_condition): passes_out_of_3}.
    passes_out_of_3 is a raw int count of `pass: true` entries for that
    cell -- always exactly N_REPLICATES=3 draws per cell in this run
    (verified below)."""
    counts = defaultdict(int)
    totals = defaultdict(int)
    for e in entries:
        key = (e["module"], e["model"], e["prompt_condition"])
        totals[key] += 1
        if e["pass"]:
            counts[key] += 1
    bad = {k: v for k, v in totals.items() if v != N_REPLICATES}
    assert not bad, f"cell(s) without exactly N={N_REPLICATES} replicates: {bad}"
    return counts


def module_list(entries):
    """All 42 module names, sorted."""
    mods = sorted(set(e["module"] for e in entries))
    assert len(mods) == EXPECTED_MODULE_COUNT, (
        f"expected exactly {EXPECTED_MODULE_COUNT} modules, got {len(mods)}"
    )
    assert "edge_detect" not in mods and "square_wave" not in mods
    return mods


def sorted_modules_by_group(categories):
    """Returns modules sorted by (functional_class, difficulty_tier,
    module name) -- the grouping order Table 1 and every other
    module-ordered deliverable in this directory uses, so they all
    agree on row order."""
    tier_order = {"ceiling": 0, "recoverable": 1, "floor": 2}
    class_order = {c: i for i, c in enumerate(FUNCTIONAL_CLASS_ORDER)}

    def key(m):
        info = categories[m]
        return (class_order[info["functional_class"]], tier_order[info["difficulty_tier"]], m)

    return sorted(categories.keys(), key=key)
