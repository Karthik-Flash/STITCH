"""
phase2/set3_analysis/fig_capability_ladder_full.py -- deliverable 3:
extends Twin's 5-model-condition capability ladder
(phase2/twin_analysis_SET2/fig2.py) with Set 3's 3 larger models, so the
figure spans the FULL 4B-32B range in one place -- 8 bars total.

Pooled recoverable-band pass rate (Twin: its own baseline-only condition;
Set 3: the `baseline` STITCH condition, for direct comparability -- Set 3
ran 4 conditions, only `baseline` matches what Twin measured), Wilson 95%
CI, n-labels, ordered left-to-right by pass rate ascending, per the
brief.

HONEST CAVEAT, stated in the title/caption, not buried: Twin ran at
T=0.5, Set 3 at T=0.1. This is NOT a temperature-controlled comparison --
bars are colored by which run/temperature they come from, and the
figure's own claim is deliberately ORDINAL (where does each model fall
in the ladder), not a direct rate-magnitude comparison across the T
boundary.

`twin_analysis_SET2/_data.py` is loaded via importlib.util rather than a
plain `import _data` -- this script's own directory already has a module
literally named `_data.py` on sys.path (set3_analysis/_data.py, needed
below for the Set 3 numbers), and a second `import _data` would just
return the already-cached module instead of loading Twin's -- the same
collision set3_analysis/_data.py's own module docstring documents and
avoids for the Set 1 cross-reference; importlib sidesteps it here by
name, not by reimplementing Twin's whole pivot logic a second time.

Usage: python phase2/set3_analysis/fig_capability_ladder_full.py
Output: fig_capability_ladder_full.png (300 DPI), .pdf
"""
import importlib.util
import os
import sys

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from statsmodels.stats.proportion import proportion_confint

_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, _HERE)
import _data  # noqa: E402  -- set3_analysis's own _data.py

_TWIN_DIR = os.path.join(_HERE, "..", "twin_analysis_SET2")


def _load_twin_data():
    spec = importlib.util.spec_from_file_location(
        "twin_analysis_set2_data", os.path.join(_TWIN_DIR, "_data.py"))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


OUT_PNG = os.path.join(_HERE, "fig_capability_ladder_full.png")
OUT_PDF = os.path.join(_HERE, "fig_capability_ladder_full.pdf")


def build():
    twin_data = _load_twin_data()
    twin_entries = twin_data.load_master_log()
    twin_counts = twin_data.pivot_pass_counts(twin_entries)
    twin_categories = twin_data.load_categories()
    twin_recoverable = sorted(m for m, i in twin_categories.items() if i["difficulty_tier"] == "recoverable")

    rows = []
    for model, cond, label in twin_data.MODEL_CONDITIONS:
        n_pass = sum(twin_counts.get((m, model, cond), 0) for m in twin_recoverable)
        n_total = len(twin_recoverable) * twin_data.N_REPLICATES
        rows.append({"label": label, "run": "twin", "temperature": 0.5,
                     "n_pass": n_pass, "n_total": n_total})

    set3_entries = _data.load_master_log()
    for model in _data.MODELS:
        n_pass, n_total = _data.pooled_recoverable_rate(set3_entries, model, "baseline")
        rows.append({"label": _data.MODEL_DISPLAY[model], "run": "set3", "temperature": 0.1,
                     "n_pass": n_pass, "n_total": n_total})

    for r in rows:
        r["rate"] = r["n_pass"] / r["n_total"]
        lo, hi = proportion_confint(r["n_pass"], r["n_total"], alpha=0.05, method="wilson")
        r["ci_lo"], r["ci_hi"] = lo, hi

    rows.sort(key=lambda r: r["rate"])
    return rows


def write_fig(rows):
    labels = [r["label"] for r in rows]
    rates = [r["rate"] for r in rows]
    lowers = [r["rate"] - r["ci_lo"] for r in rows]
    uppers = [r["ci_hi"] - r["rate"] for r in rows]
    colors = ["#DD8452" if r["run"] == "twin" else "#4C72B0" for r in rows]

    x = np.arange(len(labels))
    fig, ax = plt.subplots(figsize=(12, 6.5))
    ax.bar(x, rates, yerr=[lowers, uppers], capsize=5, color=colors,
           edgecolor="black", linewidth=0.5)

    for i, r in enumerate(rows):
        ax.text(i, -0.28, f"T={r['temperature']}\nn={r['n_total']}\n({r['n_pass']}/{r['n_total']})",
                 ha="center", va="top", fontsize=7.5, transform=ax.get_xaxis_transform())

    from matplotlib.patches import Patch
    legend_handles = [
        Patch(facecolor="#DD8452", edgecolor="black", label="Twin (Set 2), T=0.5"),
        Patch(facecolor="#4C72B0", edgecolor="black", label="Set 3, T=0.1"),
    ]
    ax.legend(handles=legend_handles, loc="upper left")

    ax.set_xticks(x)
    ax.set_xticklabels(labels, rotation=25, ha="right")
    ax.set_ylabel("Pooled pass rate (recoverable band, Wilson 95% CI)")
    ax.set_ylim(0, 1.05)
    ax.set_title(
        "Full capability ladder, 4B-32B (8 model-conditions, 17 recoverable-band modules)\n"
        "Twin (T=0.5, baseline) + Set 3 (T=0.1, baseline) -- ORDINAL comparison only, "
        "temperature differs across the two colors"
    )
    ax.grid(axis="y", linestyle=":", alpha=0.4)
    fig.tight_layout()
    fig.subplots_adjust(bottom=0.4)
    fig.savefig(OUT_PNG, dpi=300)
    fig.savefig(OUT_PDF)


def main():
    rows = build()
    assert len(rows) == 8, f"expected 8 model-conditions (5 Twin + 3 Set 3), got {len(rows)}"

    write_fig(rows)

    print(f"Wrote {OUT_PNG}, {OUT_PDF}")
    for r in rows:
        print(f"{r['label']:<24} T={r['temperature']}  {r['n_pass']:>3}/{r['n_total']:<4} "
              f"{r['rate']*100:5.1f}%  95% CI [{r['ci_lo']*100:.1f}, {r['ci_hi']*100:.1f}]")


if __name__ == "__main__":
    main()
