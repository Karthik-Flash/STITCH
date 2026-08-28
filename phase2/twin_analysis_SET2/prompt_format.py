"""
phase2/twin_analysis/prompt_format.py -- prompt-format effect check:
RTLCoder native vs. RTLCoder shared, aggregated across all 42 modules
(pooled rate, for context) and per-module on the recoverable band (the
actual win/tie/loss verdict, matching Table 2's method and thresholds
for consistency: delta = native_passes - shared_passes in {-3..3},
native wins if delta>=+2, shared wins if delta<=-2, tied if |delta|<=1).

Usage: python phase2/twin_analysis/prompt_format.py
Output: prompt_format_verdict.md
"""
import os
import sys

_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, _HERE)
import _data  # noqa: E402

OUT_MD = os.path.join(_HERE, "prompt_format_verdict.md")

RTLCODER_NATIVE = ("rtlcoder-deepseek-v1.1", "native")
RTLCODER_SHARED = ("rtlcoder-deepseek-v1.1", "shared")


def _verdict(delta):
    if delta >= 2:
        return "native wins"
    if delta <= -2:
        return "shared wins"
    return "tied"


def main():
    entries = _data.load_master_log()
    counts = _data.pivot_pass_counts(entries)
    categories = _data.load_categories()
    all_modules = sorted(categories.keys())
    recoverable = sorted(m for m in all_modules if categories[m]["difficulty_tier"] == "recoverable")

    # Aggregate across ALL 42 modules (context).
    native_all = sum(counts.get((m,) + RTLCODER_NATIVE, 0) for m in all_modules)
    shared_all = sum(counts.get((m,) + RTLCODER_SHARED, 0) for m in all_modules)
    n_all = len(all_modules) * _data.N_REPLICATES

    # Per-module, recoverable band only (the actual verdict).
    rows = []
    for m in recoverable:
        native_p = counts.get((m,) + RTLCODER_NATIVE, 0)
        shared_p = counts.get((m,) + RTLCODER_SHARED, 0)
        delta = native_p - shared_p
        rows.append((m, native_p, shared_p, delta, _verdict(delta)))

    native_wins = sum(1 for r in rows if r[4] == "native wins")
    shared_wins = sum(1 for r in rows if r[4] == "shared wins")
    ties = sum(1 for r in rows if r[4] == "tied")
    total = len(rows)

    if native_wins > shared_wins:
        one_liner = (f"Native prompting has a modest edge over the shared harness prompt "
                     f"({native_wins} vs {shared_wins} module wins, {ties} tied) -- "
                     f"format is not fully neutral.")
    elif shared_wins > native_wins:
        one_liner = (f"The shared harness prompt has a modest edge over RTLCoder's native "
                     f"format ({shared_wins} vs {native_wins} module wins, {ties} tied) -- "
                     f"format is not fully neutral.")
    else:
        one_liner = (f"Native and shared prompting are effectively tied "
                     f"({native_wins} vs {shared_wins} module wins, {ties} tied) -- "
                     f"prompt format looks neutral on this comparison.")

    top3 = sorted(rows, key=lambda r: abs(r[3]), reverse=True)[:3]

    lines = []
    lines.append("# Prompt-format effect check -- RTLCoder native vs. shared")
    lines.append("")
    lines.append(f"All-42-module aggregate (context, not the verdict): native "
                 f"{native_all}/{n_all} vs. shared {shared_all}/{n_all} pooled passes.")
    lines.append("")
    lines.append(f"**Verdict basis**: recoverable-band modules only (n={total}), same "
                 f"delta/threshold method as Table 2 (native wins if "
                 f"delta>=+2, shared wins if delta<=-2, tied if |delta|<=1; "
                 f"delta = native_passes - shared_passes, each pass count out of N=3).")
    lines.append("")
    lines.append(f"- Native wins: **{native_wins}**")
    lines.append(f"- Shared wins: **{shared_wins}**")
    lines.append(f"- Tied: **{ties}**")
    lines.append("")
    lines.append(f"**One-line verdict**: {one_liner}")
    lines.append("")
    lines.append("**Modules where the sign matters most (top 3 |delta|)**:")
    lines.append("")
    lines.append("| Module | native | shared | delta | verdict |")
    lines.append("|---|---|---|---|---|")
    for m, native_p, shared_p, delta, verdict in top3:
        lines.append(f"| {m} | {native_p}/3 | {shared_p}/3 | {delta:+d} | {verdict} |")
    lines.append("")

    with open(OUT_MD, "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")

    print(f"Wrote {OUT_MD}")
    print(one_liner)
    print(f"native wins={native_wins} shared wins={shared_wins} ties={ties} (n={total})")


if __name__ == "__main__":
    main()
