"""
phase2/set1_analysis/cost_by_tier.py -- deliverable 5: mean tool
invocations per condition, broken out by Twin's difficulty tier
(ceiling/recoverable/floor). The "escalation is smart about when to
spend" argument: if sem_escalate's cost saving is concentrated on
ceiling/floor modules (where the interpreter's tools mostly find nothing
actionable) and smaller on the recoverable band (where there's real
signal to escalate on), that's a materially different -- and more
interesting -- story than a flat reduction everywhere. Report whatever
the data actually shows.

Usage: python phase2/set1_analysis/cost_by_tier.py
Output: cost_by_tier.csv
"""
import csv
import os
import sys
from collections import defaultdict

_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, _HERE)
import _data  # noqa: E402

OUT_CSV = os.path.join(_HERE, "cost_by_tier.csv")
TIERS = ["ceiling", "recoverable", "floor"]


def main():
    entries = _data.load_master_log()
    categories = _data.load_categories()

    per_tier_cond = {t: {c: defaultdict(list) for c in _data.CONDITIONS} for t in TIERS}
    dropped = []
    for module, model, condition, rep in _data.iter_valid_runs(entries):
        tier = categories[module]["difficulty_tier"]
        cost = _data.load_run_cost(module, model, condition, rep)
        if cost is None:
            dropped.append((module, model, condition, rep))
            continue
        per_tier_cond[tier][condition]["tokens"].append(cost["tokens"])
        per_tier_cond[tier][condition]["tool_calls"].append(cost["tool_calls"])
        per_tier_cond[tier][condition]["iterations"].append(cost["iterations"])

    rows = []
    for tier in TIERS:
        for cond in _data.CONDITIONS:
            d = per_tier_cond[tier][cond]
            n = len(d["tool_calls"])
            mean_tool = sum(d["tool_calls"]) / n if n else float("nan")
            mean_tok = sum(d["tokens"]) / n if n else float("nan")
            mean_iter = sum(d["iterations"]) / n if n else float("nan")
            rows.append({
                "tier": tier, "condition": cond, "n_runs": n,
                "mean_tokens": mean_tok, "mean_tool_calls": mean_tool,
                "mean_iterations": mean_iter,
            })

    with open(OUT_CSV, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["tier", "condition", "n_runs", "mean_tokens_per_run",
                     "mean_tool_calls_per_run", "mean_iterations_per_run"])
        for r in rows:
            w.writerow([r["tier"], r["condition"], r["n_runs"],
                         f"{r['mean_tokens']:.2f}", f"{r['mean_tool_calls']:.4f}",
                         f"{r['mean_iterations']:.4f}"])

    print(f"Wrote {OUT_CSV} ({len(rows)} rows, {len(dropped)} unexpectedly dropped)")
    print()
    print(f"{'tier':<14}{'condition':<24}{'n':>6}{'tool calls/run':>18}")
    for r in rows:
        print(f"{r['tier']:<14}{r['condition']:<24}{r['n_runs']:>6}{r['mean_tool_calls']:>18.2f}")

    # sanity: baseline is 0.00 in every tier (structural, same check as cost_analysis.py)
    for r in rows:
        if r["condition"] == "baseline":
            assert r["mean_tool_calls"] == 0.0, f"baseline nonzero in tier {r['tier']}: {r}"

    # Reduction sem_adv -> sem_escalate, per tier
    print()
    by_tier_cond = {(r["tier"], r["condition"]): r for r in rows}
    for tier in TIERS:
        sa = by_tier_cond[(tier, "sem_adv")]["mean_tool_calls"]
        se = by_tier_cond[(tier, "sem_escalate")]["mean_tool_calls"]
        if sa:
            pct = (sa - se) / sa * 100
            print(f"  {tier}: sem_adv {sa:.2f} -> sem_escalate {se:.2f}  ({pct:.1f}% reduction)")


if __name__ == "__main__":
    main()
