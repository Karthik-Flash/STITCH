"""
phase2/set3_analysis/set3_cost_by_tier.py -- deliverable 4: mean
Verilator+Yosys calls/run and mean tokens/run per condition, for Set 3's
3 larger models, recoverable band only (the only band Set 3 ran).
Compares the sem_adv -> sem_escalate tool-call reduction against Set 1's
recoverable-band figure (16.6%, phase2/set1_analysis/cost_by_tier.csv)
-- does the cost discipline (escalation spends less than always-on
tooling) hold at 14B-32B scale? Reported honestly either way.

Usage: python phase2/set3_analysis/set3_cost_by_tier.py
Output: set3_cost_by_tier.csv
"""
import csv
import os
import sys
from collections import defaultdict

_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, _HERE)
import _data  # noqa: E402

OUT_CSV = os.path.join(_HERE, "set3_cost_by_tier.csv")

SET1_RECOVERABLE_REDUCTION_PCT = 16.6  # phase2/SET1_ANALYSIS.md's "Cost by tier" section


def main():
    entries = _data.load_master_log()

    per_cond = {c: defaultdict(list) for c in _data.CONDITIONS}
    dropped = []
    for module, model, condition, rep in _data.iter_valid_runs(entries):
        cost = _data.load_run_cost(module, model, condition, rep)
        if cost is None:
            dropped.append((module, model, condition, rep))
            continue
        per_cond[condition]["tokens"].append(cost["tokens"])
        per_cond[condition]["tool_calls"].append(cost["tool_calls"])
        per_cond[condition]["iterations"].append(cost["iterations"])

    rows = []
    for cond in _data.CONDITIONS:
        d = per_cond[cond]
        n = len(d["tool_calls"])
        mean_tok = sum(d["tokens"]) / n
        mean_tool = sum(d["tool_calls"]) / n
        mean_iter = sum(d["iterations"]) / n
        rows.append({"condition": cond, "n_runs": n, "mean_tokens": mean_tok,
                     "mean_tool_calls": mean_tool, "mean_iterations": mean_iter})

    with open(OUT_CSV, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["condition", "n_runs", "mean_tokens_per_run",
                     "mean_tool_calls_per_run", "mean_iterations_per_run"])
        for r in rows:
            w.writerow([r["condition"], r["n_runs"], f"{r['mean_tokens']:.2f}",
                         f"{r['mean_tool_calls']:.4f}", f"{r['mean_iterations']:.4f}"])

    by_cond = {r["condition"]: r for r in rows}
    baseline_calls = by_cond["baseline"]["mean_tool_calls"]
    assert baseline_calls == 0.0, f"baseline mean tool calls/run must be exactly 0.00, got {baseline_calls}"

    sa = by_cond["sem_adv"]["mean_tool_calls"]
    se = by_cond["sem_escalate"]["mean_tool_calls"]
    reduction_pct = (sa - se) / sa * 100

    print(f"Wrote {OUT_CSV} ({len(rows)} rows, {len(dropped)} unexpectedly dropped)")
    if dropped:
        print("  Unexpectedly dropped cells:", dropped, file=sys.stderr)
    print()
    print(f"{'condition':<24}{'tokens/run':>12}{'tool calls/run':>16}{'iters/run':>12}")
    for r in rows:
        print(f"{r['condition']:<24}{r['mean_tokens']:>12.0f}{r['mean_tool_calls']:>16.2f}{r['mean_iterations']:>12.2f}")
    print()
    print(f"Set 3 recoverable-band tool-call reduction (sem_adv -> sem_escalate): {reduction_pct:.1f}%")
    print(f"Set 1 recoverable-band tool-call reduction (from phase2/SET1_ANALYSIS.md): {SET1_RECOVERABLE_REDUCTION_PCT:.1f}%")
    if reduction_pct >= SET1_RECOVERABLE_REDUCTION_PCT:
        print("-> cost discipline HOLDS (at least as strong) at 14B-32B scale.")
    else:
        print("-> cost discipline is WEAKER at 14B-32B scale than at 4B-8B -- report honestly.")


if __name__ == "__main__":
    main()
