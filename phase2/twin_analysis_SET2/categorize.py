"""
phase2/twin_analysis/categorize.py -- difficulty-tier + functional-class
categorization for the Twin run (Set 2), full RTLLM scale (630 runs,
42 modules, 0 errors, T=0.5, baseline-only -- see
phase2/results/twin_run/master_log.json).

DIFFICULTY TIERS -- computed from the POOLED pass rate across all 5
model-conditions x N=3 = 15 total attempts per module. The analysis
brief's phrasing ("max pass rate across all model-conditions... i.e.
>= 12/15") is this pooled rate, not a literal max-of-5-separate-cells
operation: a single model-condition's own rate can only ever be 0/3,
1/3, 2/3, or 3/3, and the MAX of five such rates -- even expressed as an
equivalent /15 fraction -- can only land on 0, 5, 10, or 15 out of 15,
never 12. "12/15" only makes arithmetic sense as a POOLED count across
all 15 attempts, so that's what's implemented here (verified against
master_log.json's actual shape -- every module has exactly 15 entries,
5 model-conditions x N=3 -- before writing this).

  Ceiling:            pooled rate >= 80% (>= 12/15)
  Recoverable band:   20% <= pooled rate < 80% (3/15 to 11/15)
  Floor:              pooled rate < 20% (< 3/15)

FUNCTIONAL CLASSES -- RTLLM's own top-level taxonomy (Arithmetic,
Control, Memory, Miscellaneous), taken as-is for 3 of the 4 categories,
per the brief ("take these as-is, don't invent"). Miscellaneous is the
2nd-largest category in this run (16 of 42 modules -- Arithmetic is
larger at 17, but Miscellaneous is by far the most functionally
heterogeneous: it mixes memory-adjacent primitives (RAM, ROM),
datapath/control pieces (alu, pe, instr_reg, width_8to16),
signal-generation/detection logic (freq_div*, signal_generator,
pulse_detect), and serial/protocol logic (parallel2serial,
serial2parallel, synchronizer, calendar, traffic_light) under one
label -- splitting it is worth doing regardless of exact rank, since the
paper's analysis benefits from not lumping a RAM model in with a
frequency divider. Split by direct inspection into 3 sub-classes; the
mapping below (MISC_SUBCLASS) covers all 16 Miscellaneous modules
present in this run's data with no leftover -- verified by
_functional_class() raising loudly on any unmapped Miscellaneous module
rather than silently defaulting:

  signal_processing: freq_div, freq_divbyeven, freq_divbyfrac,
                      signal_generator, pulse_detect
  protocol:           parallel2serial, serial2parallel, synchronizer,
                      calendar, traffic_light
  arithmetic_misc:    alu, pe, RAM, ROM, instr_reg, width_8to16

(edge_detect would also fall under signal_processing by this scheme,
but it's excluded from this run entirely -- see
IMP_PHASE2_RUNNER_HARDENING_REPORT.md §4/§6 -- so it never reaches this
classification; not listed in MISC_SUBCLASS on purpose.)

Usage: python phase2/twin_analysis/categorize.py
Output: phase2/twin_analysis/module_categories.json
  {module: {difficulty_tier, functional_class, max_pass_rate,
            pooled_passes, pooled_total}}
"""
import json
import os
from collections import defaultdict

_HERE = os.path.dirname(os.path.abspath(__file__))
MASTER_LOG = os.path.join(_HERE, "..", "results", "twin_run", "master_log.json")
OUT_JSON = os.path.join(_HERE, "module_categories.json")

MISC_SUBCLASS = {
    "freq_div": "signal_processing", "freq_divbyeven": "signal_processing",
    "freq_divbyfrac": "signal_processing", "signal_generator": "signal_processing",
    "pulse_detect": "signal_processing",
    "parallel2serial": "protocol", "serial2parallel": "protocol",
    "synchronizer": "protocol", "calendar": "protocol", "traffic_light": "protocol",
    "alu": "arithmetic_misc", "pe": "arithmetic_misc", "RAM": "arithmetic_misc",
    "ROM": "arithmetic_misc", "instr_reg": "arithmetic_misc", "width_8to16": "arithmetic_misc",
}

CEILING_THRESHOLD = 0.80
FLOOR_THRESHOLD = 0.20

# Functional-class display order for tables/figures (paper-facing).
FUNCTIONAL_CLASS_ORDER = [
    "Arithmetic", "Control", "Memory",
    "arithmetic_misc", "protocol", "signal_processing",
]


def _functional_class(module, category):
    if category == "Miscellaneous":
        if module not in MISC_SUBCLASS:
            raise ValueError(
                f"module {module!r} is in Miscellaneous but not mapped to a "
                f"sub-class in MISC_SUBCLASS -- add it explicitly, don't "
                f"silently default. This is a hard stop: a new/renamed "
                f"Miscellaneous module must be classified by a human, not "
                f"guessed by this script."
            )
        return MISC_SUBCLASS[module]
    return category


def categorize(master_log_path=MASTER_LOG):
    """Returns {module: {difficulty_tier, functional_class, max_pass_rate,
    pooled_passes, pooled_total}}. Pure function of master_log.json --
    reads it, never writes it (analysis-only, per the brief)."""
    with open(master_log_path, encoding="utf-8") as f:
        entries = json.load(f)

    by_module = defaultdict(list)
    module_category = {}
    for e in entries:
        by_module[e["module"]].append(e)
        module_category[e["module"]] = e["category"]

    result = {}
    for module, rows in by_module.items():
        n_total = len(rows)
        n_pass = sum(1 for r in rows if r["pass"])
        rate = n_pass / n_total if n_total else 0.0

        if rate >= CEILING_THRESHOLD:
            tier = "ceiling"
        elif rate < FLOOR_THRESHOLD:
            tier = "floor"
        else:
            tier = "recoverable"

        result[module] = {
            "difficulty_tier": tier,
            "functional_class": _functional_class(module, module_category[module]),
            "max_pass_rate": round(rate, 4),
            "pooled_passes": n_pass,
            "pooled_total": n_total,
        }

    return result


def main():
    result = categorize()

    # Verification invariants (see brief's Verification section) --
    # checked here, at generation time, not left implicit.
    assert len(result) == 42, f"expected exactly 42 modules, got {len(result)}"
    assert "edge_detect" not in result and "square_wave" not in result, (
        "edge_detect/square_wave must be absent -- excluded from this run"
    )
    for m, info in result.items():
        assert info["difficulty_tier"] in ("ceiling", "recoverable", "floor")
        assert info["functional_class"] in FUNCTIONAL_CLASS_ORDER, (
            f"{m}: unexpected functional_class {info['functional_class']!r}"
        )

    os.makedirs(_HERE, exist_ok=True)
    with open(OUT_JSON, "w", encoding="utf-8") as f:
        json.dump(result, f, indent=2, sort_keys=True)

    tiers = defaultdict(list)
    classes = defaultdict(list)
    for m, info in result.items():
        tiers[info["difficulty_tier"]].append(m)
        classes[info["functional_class"]].append(m)

    print(f"{len(result)} modules categorized -> {OUT_JSON}")
    print("\nDifficulty tiers:")
    for tier in ("ceiling", "recoverable", "floor"):
        mods = sorted(tiers[tier])
        print(f"  {tier} ({len(mods)}): {mods}")
    print("\nFunctional classes:")
    for cls in FUNCTIONAL_CLASS_ORDER:
        mods = sorted(classes[cls])
        print(f"  {cls} ({len(mods)}): {mods}")


if __name__ == "__main__":
    main()
