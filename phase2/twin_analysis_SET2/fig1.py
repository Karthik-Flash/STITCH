"""
phase2/twin_analysis/fig1.py -- Figure 1 (paper): the two named
comparisons at full RTLLM scale, matching the pilot's Figure 5 shape
(STITCH_EXT.pdf p.9) but at 42-module scale, watermark REMOVED (this is
confirmatory data, not a pilot).

Panel (a) -- Fine-tuning twin: RTLCoder shared vs. deepseek-coder shared.
Panel (b) -- Prompt-format effect: RTLCoder native vs. RTLCoder shared.

Both panels: recoverable-band modules ONLY (per the brief -- ceiling/
floor modules show tied 3/3 or tied 0/3 on both bars in a pair and would
just add noise-free-but-signal-free rows to a comparison figure).
Grouped bars, one pair per module, y-axis = pass count out of N=3.

Usage: python phase2/twin_analysis/fig1.py
Output: fig1_named_comparisons.png (300 DPI), fig1_named_comparisons.pdf
"""
import os
import sys

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, _HERE)
import _data  # noqa: E402

OUT_PNG = os.path.join(_HERE, "fig1_named_comparisons.png")
OUT_PDF = os.path.join(_HERE, "fig1_named_comparisons.pdf")


def _recoverable_modules(categories):
    mods = [m for m, info in categories.items() if info["difficulty_tier"] == "recoverable"]
    mods.sort(key=lambda m: (categories[m]["functional_class"], m))
    return mods


def _bar_panel(ax, modules, counts, cond_a, cond_b, label_a, label_b, title):
    x = np.arange(len(modules))
    width = 0.38
    vals_a = [counts.get((m,) + cond_a, 0) for m in modules]
    vals_b = [counts.get((m,) + cond_b, 0) for m in modules]

    ax.bar(x - width / 2, vals_a, width, label=label_a, color="#4C72B0")
    ax.bar(x + width / 2, vals_b, width, label=label_b, color="#DD8452")

    ax.set_xticks(x)
    ax.set_xticklabels(modules, rotation=60, ha="right", fontsize=8)
    ax.set_ylabel("Passes (of N=3)")
    ax.set_yticks([0, 1, 2, 3])
    ax.set_ylim(0, 3.4)
    ax.set_title(title, fontsize=11)
    ax.legend(fontsize=9, loc="upper right")
    ax.grid(axis="y", linestyle=":", alpha=0.4)


def main():
    entries = _data.load_master_log()
    counts = _data.pivot_pass_counts(entries)
    categories = _data.load_categories()
    modules = _recoverable_modules(categories)
    n = len(modules)

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(16, 6))

    _bar_panel(
        ax1, modules, counts,
        ("rtlcoder-deepseek-v1.1", "shared"), ("deepseek-coder:6.7b", "shared"),
        "RTLCoder shared", "deepseek-coder shared",
        "(a) Fine-tuning twin comparison",
    )
    _bar_panel(
        ax2, modules, counts,
        ("rtlcoder-deepseek-v1.1", "native"), ("rtlcoder-deepseek-v1.1", "shared"),
        "RTLCoder native", "RTLCoder shared",
        "(b) Prompt-format effect",
    )

    fig.suptitle(
        "Twin run -- recoverable-band modules only (n=%d modules, N=3 replicates/cell, "
        "T=0.5, baseline-only; ceiling/floor modules excluded -- tied on both bars by "
        "construction)" % n,
        fontsize=10,
    )
    fig.tight_layout(rect=[0, 0, 1, 0.94])
    fig.savefig(OUT_PNG, dpi=300)
    fig.savefig(OUT_PDF)
    print(f"Wrote {OUT_PNG} and {OUT_PDF} ({n} recoverable-band modules)")


if __name__ == "__main__":
    main()
