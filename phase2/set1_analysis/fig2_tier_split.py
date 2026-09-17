"""
phase2/set1_analysis/fig2_tier_split.py -- deliverable 2: pooled pass
rate per condition, split into three panels (one per Twin-inherited
difficulty tier: ceiling/recoverable/floor). Wilson 95% CIs
(statsmodels.stats.proportion.proportion_confint, method="wilson" --
same citation as Twin's fig2.py / TWIN_RUN_ANALYSIS.md's footnote).

What we might expect from Phase 1 patterns (ceilings: sem_adv slightly
below baseline / harmful regime, esc-restart close to baseline /
protective; recoverable band: the interesting one, esc/restart lift over
baseline if the mechanism generalizes; floors: everything near zero) is
NOT assumed here -- the panel data is read straight off master_log.json
and reported as-is; SET1_ANALYSIS.md's tier-split section says plainly
whether or not the expectation held.

Usage: python phase2/set1_analysis/fig2_tier_split.py
Output: fig2_tier_split.png (300 DPI), fig2_tier_split.pdf, tier_pass_rates.csv
"""
import csv
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

OUT_PNG = os.path.join(_HERE, "fig2_tier_split.png")
OUT_PDF = os.path.join(_HERE, "fig2_tier_split.pdf")
OUT_CSV = os.path.join(_HERE, "tier_pass_rates.csv")
TIERS = ["ceiling", "recoverable", "floor"]
CONDITION_LABEL = {
    "baseline": "baseline", "sem_adv": "sem_adv",
    "sem_escalate": "sem_escalate", "sem_escalate_restart": "sem_esc_restart",
}


def build(entries, categories):
    counts = _data.pivot_pass_counts(entries)
    modules_by_tier = {t: [m for m, info in categories.items() if info["difficulty_tier"] == t] for t in TIERS}

    rows = []
    for tier in TIERS:
        mods = modules_by_tier[tier]
        for cond in _data.CONDITIONS:
            n_pass = sum(counts[(m, model, cond)][0] for m in mods for model in _data.MODELS)
            n_valid = sum(counts[(m, model, cond)][1] for m in mods for model in _data.MODELS)
            rate = n_pass / n_valid if n_valid else float("nan")
            if n_valid:
                lo, hi = proportion_confint(n_pass, n_valid, alpha=0.05, method="wilson")
            else:
                lo, hi = float("nan"), float("nan")
            rows.append({
                "tier": tier, "condition": cond, "n_modules": len(mods),
                "n_pass": n_pass, "n_valid": n_valid, "rate": rate,
                "ci_lo": lo, "ci_hi": hi,
            })
    return rows


def write_csv(rows):
    with open(OUT_CSV, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["tier", "condition", "n_modules", "n_pass", "n_valid",
                     "pass_rate", "wilson_ci_lo", "wilson_ci_hi"])
        for r in rows:
            w.writerow([r["tier"], r["condition"], r["n_modules"], r["n_pass"],
                         r["n_valid"], f"{r['rate']:.4f}", f"{r['ci_lo']:.4f}", f"{r['ci_hi']:.4f}"])


def write_fig(rows):
    fig, axes = plt.subplots(1, 3, figsize=(15, 5.5), sharey=True)
    by_tier = {t: [r for r in rows if r["tier"] == t] for t in TIERS}

    for ax, tier in zip(axes, TIERS):
        trows = by_tier[tier]
        labels = [CONDITION_LABEL[r["condition"]] for r in trows]
        rates = [r["rate"] for r in trows]
        lowers = [r["rate"] - r["ci_lo"] for r in trows]
        uppers = [r["ci_hi"] - r["rate"] for r in trows]
        x = np.arange(len(labels))
        ax.bar(x, rates, yerr=[lowers, uppers], capsize=5,
               color="#55A868", edgecolor="black", linewidth=0.5)
        ax.set_xticks(x)
        ax.set_xticklabels(labels, rotation=25, ha="right", fontsize=9)
        n_modules = trows[0]["n_modules"]
        ax.set_title(f"{tier} ({n_modules} modules)")
        ax.grid(axis="y", linestyle=":", alpha=0.4)
        for i, r in enumerate(trows):
            ax.text(i, -0.22, f"{r['n_pass']}/{r['n_valid']}", ha="center", va="top",
                     fontsize=7.5, transform=ax.get_xaxis_transform())

    axes[0].set_ylabel("Pooled pass rate (Wilson 95% CI)")
    axes[0].set_ylim(0, 1.05)
    fig.suptitle(
        "Set 1: pass rate by STITCH condition, split by difficulty tier "
        "(tiers inherited from Twin's module_categories.json)"
    )
    fig.tight_layout()
    fig.subplots_adjust(bottom=0.32, top=0.88)
    fig.savefig(OUT_PNG, dpi=300)
    fig.savefig(OUT_PDF)


def main():
    entries = _data.load_master_log()
    categories = _data.load_categories()
    rows = build(entries, categories)

    # verification: every module appears in exactly one tier (from Twin's
    # file), and n_modules sums to 42 across the three tiers.
    uniq_sizes = {t: next(r["n_modules"] for r in rows if r["tier"] == t) for t in TIERS}
    assert sum(uniq_sizes.values()) == 42, f"tier sizes don't sum to 42: {uniq_sizes}"

    write_csv(rows)
    write_fig(rows)

    print(f"Wrote {OUT_CSV}, {OUT_PNG}, {OUT_PDF}")
    print()
    for tier in TIERS:
        print(f"-- {tier} ({uniq_sizes[tier]} modules) --")
        for r in rows:
            if r["tier"] != tier:
                continue
            print(f"  {r['condition']:<22} {r['n_pass']:>4}/{r['n_valid']:<4} = {r['rate']:.3f}  "
                  f"95% CI [{r['ci_lo']:.3f}, {r['ci_hi']:.3f}]")


if __name__ == "__main__":
    main()
