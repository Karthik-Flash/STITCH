"""
phase2/set3_analysis/harmful_regime_by_capability.py -- deliverable 2,
THE headline figure: does always-on interpretation's harm (sem_adv minus
baseline, on the recoverable band) shrink as model capability rises?
Spans all 6 models across Set 1 (4B-8B) + Set 3 (14B-32B), all on the
identical 17 recoverable-band modules, same 4 conditions, same T=0.1,
same benchmark -- the only axis that differs is the model.

Delta = (sem_adv pass rate) - (baseline pass rate), in percentage
points. Negative = harmful regime (always-on tooling hurts). CI on the
delta itself uses Newcombe's hybrid score method
(statsmodels.stats.proportion.confint_proportions_2indep(...,
method="newcomb", compare="diff")) -- the two-independent-proportions
generalization of the Wilson interval this project's single-proportion
figures already use, cited here and in SET3_ANALYSIS.md's footnote, not
derived by hand.

Ordering: x-axis ordered by each model's OWN baseline recoverable-band
rate, ascending, per the brief -- NOT by parameter count or model
family, since capability (as measured by this study) is what baseline
rate actually reflects.

HONEST NOTE, not smoothed over: the per-model deltas are NOT a clean
monotonic ramp toward zero. gemma3:27b's delta is *positive*
(sem_adv beats baseline there), qwen2.5-coder:32b -- the single
strongest model in the whole ladder -- still shows a real negative delta
comparable in magnitude to small-model llama3.1's. The GROUP-level trend
(mean of Set 1's 3 deltas vs. mean of Set 3's 3 deltas) is real and
matches the brief's headline table exactly; the PER-MODEL story is
noisier and reported as such, not forced into a smooth curve it doesn't
show. See SET3_ANALYSIS.md's per-model section.

Usage: python phase2/set3_analysis/harmful_regime_by_capability.py
Output: harmful_regime_by_capability.csv,
        fig_harmful_regime_ladder.png (300 DPI), .pdf
"""
import csv
import os
import sys

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from statsmodels.stats.proportion import confint_proportions_2indep

_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, _HERE)
import _data  # noqa: E402

OUT_CSV = os.path.join(_HERE, "harmful_regime_by_capability.csv")
OUT_PNG = os.path.join(_HERE, "fig_harmful_regime_ladder.png")
OUT_PDF = os.path.join(_HERE, "fig_harmful_regime_ladder.pdf")

# (label, run, model, temperature)
LADDER = [
    ("gemma3:4b", "set1", "gemma3:4b", 0.1),
    ("llama3.1:8b", "set1", "llama3.1:latest", 0.1),
    ("deepseek-coder:6.7b", "set1", "deepseek-coder:6.7b", 0.1),
    ("qwen2.5-coder:14b", "set3", "qwen2.5-coder:14b", 0.1),
    ("gemma3:27b", "set3", "gemma3:27b", 0.1),
    ("qwen2.5-coder:32b", "set3", "qwen2.5-coder:32b", 0.1),
]


def _rate(model, condition, run):
    if run == "set3":
        entries = _data.load_master_log()
        return _data.pooled_recoverable_rate(entries, model, condition)
    return _data.set1_pooled_recoverable_rate(model, condition)


def build():
    rows = []
    for label, run, model, t in LADDER:
        bp, bn = _rate(model, "baseline", run)
        sp, sn = _rate(model, "sem_adv", run)
        b_rate = bp / bn
        s_rate = sp / sn
        delta = (s_rate - b_rate) * 100
        lo, hi = confint_proportions_2indep(sp, sn, bp, bn, method="newcomb", compare="diff")
        rows.append({
            "model": label, "run": run, "temperature": t,
            "baseline_pass": bp, "baseline_n": bn, "baseline_rate": b_rate,
            "sem_adv_pass": sp, "sem_adv_n": sn, "sem_adv_rate": s_rate,
            "delta_pp": delta, "delta_ci_lo_pp": lo * 100, "delta_ci_hi_pp": hi * 100,
        })
    rows.sort(key=lambda r: r["baseline_rate"])
    return rows


def write_csv(rows):
    with open(OUT_CSV, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["model", "run", "temperature", "baseline_pass", "baseline_n", "baseline_rate",
                     "sem_adv_pass", "sem_adv_n", "sem_adv_rate", "delta_pp",
                     "delta_ci_lo_pp", "delta_ci_hi_pp"])
        for r in rows:
            w.writerow([r["model"], r["run"], r["temperature"], r["baseline_pass"], r["baseline_n"],
                         f"{r['baseline_rate']:.4f}", r["sem_adv_pass"], r["sem_adv_n"],
                         f"{r['sem_adv_rate']:.4f}", f"{r['delta_pp']:.2f}",
                         f"{r['delta_ci_lo_pp']:.2f}", f"{r['delta_ci_hi_pp']:.2f}"])


def write_fig(rows):
    labels = [r["model"] for r in rows]
    deltas = [r["delta_pp"] for r in rows]
    lowers = [r["delta_pp"] - r["delta_ci_lo_pp"] for r in rows]
    uppers = [r["delta_ci_hi_pp"] - r["delta_pp"] for r in rows]
    colors = ["#C44E52" if r["run"] == "set1" else "#4C72B0" for r in rows]

    x = np.arange(len(labels))
    fig, ax = plt.subplots(figsize=(11, 6.5))
    ax.axhline(0, color="black", linewidth=1, linestyle="-")
    ax.bar(x, deltas, yerr=[lowers, uppers], capsize=5, color=colors,
           edgecolor="black", linewidth=0.5)

    for i, r in enumerate(rows):
        ax.text(i, -0.30, f"baseline={r['baseline_rate']*100:.1f}%\nn={r['baseline_n']}",
                 ha="center", va="top", fontsize=7.5, transform=ax.get_xaxis_transform())

    ax.set_xticks(x)
    ax.set_xticklabels(labels, rotation=20, ha="right")
    ax.set_ylabel("sem_adv $-$ baseline pass rate (recoverable band, pp)")
    ax.set_title(
        "Always-on interpretation's harm vs. model capability\n"
        "17 recoverable-band modules, N=3, T=0.1, Set 1 (4B-8B, red) + Set 3 (14B-32B, blue)"
    )
    ax.grid(axis="y", linestyle=":", alpha=0.4)
    fig.tight_layout()
    fig.subplots_adjust(bottom=0.38)
    fig.savefig(OUT_PNG, dpi=300)
    fig.savefig(OUT_PDF)


def main():
    rows = build()
    assert len(rows) == 6

    write_csv(rows)
    write_fig(rows)

    print(f"Wrote {OUT_CSV}, {OUT_PNG}, {OUT_PDF}")
    print()
    for r in rows:
        print(f"{r['model']:<22} baseline={r['baseline_rate']*100:5.1f}%  "
              f"delta={r['delta_pp']:+6.2f}pp  95% CI [{r['delta_ci_lo_pp']:+.2f}, {r['delta_ci_hi_pp']:+.2f}]")

    set1_mean = sum(r["delta_pp"] for r in rows if r["run"] == "set1") / 3
    set3_mean = sum(r["delta_pp"] for r in rows if r["run"] == "set3") / 3
    print()
    print(f"Set 1 mean delta: {set1_mean:+.2f}pp (brief's stated pooled figure: -4.6pp)")
    print(f"Set 3 mean delta: {set3_mean:+.2f}pp (brief's stated pooled figure: -0.6pp)")


if __name__ == "__main__":
    main()
