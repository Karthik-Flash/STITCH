"""
phase2/twin_analysis/fig2.py -- Figure 2 (paper): the capability-
conditional pattern the pilot flagged as untestable at N=1
(phase1/PHASE1_FINDINGS.md's capability-conditional hypothesis) --
testable now at full RTLLM scale with N=3.

Pooled across recoverable-band modules ONLY (ceiling/floor modules are
noise-free but signal-free -- pooling them in would dilute a real
capability-ladder signal with cells that never move regardless of
model). X-axis: the 5 model-conditions, same locked order as Table 1.
Y-axis: pooled pass rate over (recoverable-band modules) x N=3 cells for
that model-condition. Error bars: Wilson 95% CI (small-N appropriate --
`statsmodels.stats.proportion.proportion_confint(count, nobs,
method="wilson")`, cited here and in TWIN_RUN_ANALYSIS.md's footnote,
not derived by hand). An n= label sits under each bar (total draws
pooled into that bar).

Usage: python phase2/twin_analysis/fig2.py
Output: fig2_capability_ladder.png (300 DPI), fig2_capability_ladder.pdf
"""
import os
import sys

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from statsmodels.stats.proportion import proportion_confint

_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, _HERE)
import _data  # noqa: E402

OUT_PNG = os.path.join(_HERE, "fig2_capability_ladder.png")
OUT_PDF = os.path.join(_HERE, "fig2_capability_ladder.pdf")


def main():
    entries = _data.load_master_log()
    counts = _data.pivot_pass_counts(entries)
    categories = _data.load_categories()
    recoverable = sorted(m for m, info in categories.items() if info["difficulty_tier"] == "recoverable")

    labels, rates, lowers, uppers, ns, passes_list = [], [], [], [], [], []
    for model, cond, label in _data.MODEL_CONDITIONS:
        n_pass = sum(counts.get((m, model, cond), 0) for m in recoverable)
        n_total = len(recoverable) * _data.N_REPLICATES
        rate = n_pass / n_total
        lo, hi = proportion_confint(n_pass, n_total, alpha=0.05, method="wilson")

        labels.append(label)
        rates.append(rate)
        lowers.append(rate - lo)
        uppers.append(hi - rate)
        ns.append(n_total)
        passes_list.append(n_pass)

    x = np.arange(len(labels))
    fig, ax = plt.subplots(figsize=(9, 6))
    bars = ax.bar(x, rates, yerr=[lowers, uppers], capsize=5,
                   color="#4C72B0", edgecolor="black", linewidth=0.5)

    for i, (r, n_pass, n_total) in enumerate(zip(rates, passes_list, ns)):
        ax.text(i, -0.06, f"n={n_total}\n({n_pass}/{n_total})",
                ha="center", va="top", fontsize=8, transform=ax.get_xaxis_transform())

    ax.set_xticks(x)
    ax.set_xticklabels(labels, rotation=20, ha="right")
    ax.set_ylabel("Pooled pass rate (recoverable-band modules, Wilson 95% CI)")
    ax.set_ylim(0, 1.05)
    ax.set_title(
        f"Capability ladder -- {len(recoverable)} recoverable-band modules "
        f"x N={_data.N_REPLICATES}, T=0.5, baseline-only"
    )
    ax.grid(axis="y", linestyle=":", alpha=0.4)
    fig.tight_layout()
    fig.subplots_adjust(bottom=0.28)
    fig.savefig(OUT_PNG, dpi=300)
    fig.savefig(OUT_PDF)
    print(f"Wrote {OUT_PNG} and {OUT_PDF}")
    for label, r, n_pass, n_total, lo_d, hi_d in zip(labels, rates, passes_list, ns, lowers, uppers):
        print(f"  {label}: {n_pass}/{n_total} = {r:.3f}  "
              f"95% CI [{r - lo_d:.3f}, {r + hi_d:.3f}]")


if __name__ == "__main__":
    main()
