"""Set 4b (floor tier) pre-registered analysis: Q1-Q4, cost, truncation (SET4_PREREG.md, Set 4b).

Tier rule reused from Twin's categorize.py definition (max pass rate over model-conditions):
floor < 20% <= recoverable < 80% <= ceiling, applied here to baseline pass rate per model.
Outputs phase2/results/set4_api/analysis_4b/set4b_analysis.json (+ stdout tables).
"""
import json
import os
import sys
from collections import defaultdict

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import analysis_set4 as A  # noqa: E402
import stats_set4  # noqa: E402

TAG = "floor_full"
A.ROOT = os.path.join(A.SET4, TAG)
OUT = os.path.join(A.SET4, "analysis_4b")
PROVIDERS = ["openai", "gemini", "anthropic"]


def tier(rate):
    return "floor" if rate < 0.2 else ("recoverable" if rate < 0.8 else "ceiling")


def main():
    if not stats_set4.verify():
        sys.exit("STOP (prereg A4/A9): stats_set4 does not reproduce POSTHOC_CHECKS.md")
    os.makedirs(OUT, exist_ok=True)
    runs, calls = [], []
    for p in PROVIDERS:
        ml = os.path.join(A.ROOT, p, "master_log.json")
        if os.path.exists(ml):
            runs += [dict(e, provider=p) for e in json.load(open(ml, encoding="utf-8"))]
        for lg in (os.path.join(A.SET4, "ledgers_4b", f"{p}_ledger.jsonl"),        # original Set 4b spend
                   os.path.join(A.PHASE2, "results", "p3_api", "ledgers", f"{p}_ledger.jsonl")):  # completion (Part B)
            if os.path.exists(lg):
                calls += [json.loads(l) for l in open(lg, encoding="utf-8") if l.strip()]
    calls = [c for c in calls if c.get("tag") == TAG]
    valid = [r for r in runs if not r.get("error")]
    models = [m for m in A.DISPLAY if any(r["model"] == m for r in valid)]
    modules = sorted({r["module"] for r in valid}, key=str.lower)
    res = {"runs": len(runs), "errored": len(runs) - len(valid), "models": models}
    res["coverage"] = {m: {"valid": sum(1 for r in valid if r["model"] == m),
                           "errored": sum(1 for r in runs if r["model"] == m and r.get("error"))} for m in models}

    # Q1: baseline passes per module x model, and the tier each module lands in per model
    q1 = {}
    for mod in modules:
        q1[mod] = {}
        for m in models:
            rr = [r for r in valid if r["module"] == mod and r["model"] == m and r["condition"] == "baseline"]
            k = sum(bool(r["pass"]) for r in rr)
            q1[mod][m] = {"k": k, "n": len(rr), "tier": tier(k / len(rr)) if rr else None}
    res["Q1"] = q1

    # Q2: interpreter on floor failures; passes that had a directive delivered before passing
    q2 = {}
    base_zero = {(m, mod) for mod in modules for m in models if q1[mod][m]["n"] and q1[mod][m]["k"] == 0}
    for c in A.CONDS:
        rr = [r for r in valid if r["condition"] == c]
        fails = [r for r in rr if not r["pass"]]
        passes = [r for r in rr if r["pass"]]
        fbp = [r for r in passes if A.fired_before_pass(r)]
        q2[c] = {"runs": len(rr), "fails": len(fails),
                 "fails_with_sf": sum(1 for r in fails if r.get("semantic_fired")),
                 "passes": len(passes), "passes_sf_before_pass": len(fbp),
                 "passes_sf_before_pass_where_baseline_0of3": [
                     (r["model"], r["module"], r["run_replicate"]) for r in fbp if (r["model"], r["module"]) in base_zero]}
        if c.startswith("sem_escalate"):
            q2[c]["escalated"] = sum(1 for r in rr if r.get("fired_escalate"))
    res["Q2"] = q2

    # Q3: condition vs baseline on cells still failing (baseline rate < 1), Set 3's cell method
    cell = defaultdict(lambda: defaultdict(list))
    for r in valid:
        cell[(r["model"], r["module"])][r["condition"]].append(int(bool(r["pass"])))
    q3 = {}
    for scope in ["pooled"] + models:
        for a in A.CONDS[1:]:
            d = {k: v for k, v in cell.items() if v[a] and v["baseline"]
                 and sum(v["baseline"]) < len(v["baseline"]) and (scope == "pooled" or k[0] == scope)}
            diffs = [100 * (sum(v[a]) / len(v[a]) - sum(v["baseline"]) / len(v["baseline"])) for _, v in sorted(d.items())]
            if not diffs:
                continue
            label = f"p2:set4b_{scope}:{a}"
            lo, hi = stats_set4.boot_ci(diffs, label)
            p = stats_set4.signflip_p(diffs, label)
            q3[f"{scope}|{a}"] = {"mean_pts": sum(diffs) / len(diffs), "lo": lo, "hi": hi, "p": p, "cells": len(diffs)}
    res["Q3"] = q3

    # Q4: failed in every run by every model under every condition
    q4 = [mod for mod in modules
          if all(not r["pass"] for r in valid if r["module"] == mod)
          and {r["model"] for r in valid if r["module"] == mod} == set(models)]
    res["Q4"] = q4
    # brief B5 variants: per module, passes/valid runs per model; zero over GPT+Haiku, and zero over all three
    per = {mod: {m: [sum(bool(r["pass"]) for r in valid if r["module"] == mod and r["model"] == m),
                     sum(1 for r in valid if r["module"] == mod and r["model"] == m)] for m in models} for mod in modules}
    gh = [m for m in models if not m.startswith("gemini")]
    res["Q4_table"] = per
    res["Q4_zero_gpt_haiku"] = [mod for mod in modules if all(per[mod][m][1] for m in gh) and not any(per[mod][m][0] for m in gh)]
    res["Q4_zero_all_three"] = [mod for mod in modules if all(per[mod][m][1] for m in models) and not any(per[mod][m][0] for m in models)]
    res["Q4_zero_all_available"] = [mod for mod in modules if not any(per[mod][m][0] for m in models)]
    res["Q4_failures"] = A.failures([r for r in valid if r["module"] in set(q4) | set(res["Q4_zero_all_available"])])

    # pass rate per condition per model; cost, truncation
    res["pass_rates"] = {f"{m}|{c}": [sum(bool(r["pass"]) for r in valid if r["model"] == m and r["condition"] == c),
                                      sum(1 for r in valid if r["model"] == m and r["condition"] == c)]
                         for m in models for c in A.CONDS}
    by_run = defaultdict(float)
    for c in calls:
        by_run[(c["model_requested"], c["module"], c["condition"], c["replicate"])] += c["cost_usd"]
    ok = [c for c in calls if c.get("status") == "ok"]
    res["cost"] = {}
    for m in models:
        for c in A.CONDS:
            rr = [r for r in valid if r["model"] == m and r["condition"] == c]
            usd = sum(by_run[(m, r["module"], c, r["run_replicate"])] for r in rr)
            k = sum(bool(r["pass"]) for r in rr)
            res["cost"][f"{m}|{c}"] = {"usd": usd, "inr_per_run": usd * A.INR / len(rr) if rr else None,
                                       "inr_per_pass": usd * A.INR / k if k else None,
                                       "truncated": sum(1 for x in ok if x["model_requested"] == m and x["condition"] == c
                                                        and str(x.get("finish_reason")) in A.TRUNC)}
    res["spend_usd"] = sum(c["cost_usd"] for c in calls)
    res["reasoning_calls"] = sum(1 for c in ok if c.get("reasoning_tokens", 0) > 0)
    json.dump(res, open(os.path.join(OUT, "set4b_analysis.json"), "w", encoding="utf-8"), indent=2, default=str)
    report(res, models, modules)


def report(res, models, modules):
    short = {m: A.DISPLAY[m].split(" (")[0] for m in models}
    print(f"runs {res['runs']}, errored {res['errored']}, reasoning calls {res['reasoning_calls']}, "
          f"spend ${res['spend_usd']:.4f} = INR {res['spend_usd'] * A.INR:.1f}")
    planned = 19 * len(A.CONDS) * 3
    print("\ncoverage (of %d planned runs per model):" % planned)
    for m in models:
        cv = res["coverage"][m]
        print(f"  {short[m]:18s} valid {cv['valid']}/{planned}, errored {cv['errored']}, "
              f"not run {planned - cv['valid'] - cv['errored']}")
    print("\nQ1 baseline passes /3 (tier at this model):")
    print("  " + f"{'module':18s}" + "".join(f"{short[m]:>22s}" for m in models))
    for mod in modules:
        print("  " + f"{mod:18s}" + "".join(f"{str(res['Q1'][mod][m]['k']) + '/' + str(res['Q1'][mod][m]['n']) + ' ' + str(res['Q1'][mod][m]['tier']):>22s}" for m in models))
    print("\nQ2 interpreter on floor:")
    for c, q in res["Q2"].items():
        print(f"  {c:22s} {q}")
    print("\nQ3 condition - baseline on cells with baseline < 3/3:")
    for k, q in res["Q3"].items():
        print(f"  {k:50s} {stats_set4.sg(q['mean_pts'])} [{stats_set4.sg(q['lo'])}, {stats_set4.sg(q['hi'])}] "
              f"cells={q['cells']} p={stats_set4.fp(q['p'])}")
    print("\npass rate per condition per model:")
    for m in models:
        print(f"  {short[m]:18s} " + "  ".join(f"{c} {res['pass_rates'][f'{m}|{c}'][0]}/{res['pass_rates'][f'{m}|{c}'][1]}" for c in A.CONDS))
    print("\ncost INR per run / per pass, truncated:")
    for m in models:
        for c in A.CONDS:
            x = res["cost"][f"{m}|{c}"]
            print(f"  {short[m]:18s} {c:22s} {x['inr_per_run']:.3f} / "
                  f"{'-' if x['inr_per_pass'] is None else round(x['inr_per_pass'], 3)}  trunc {x['truncated']}")
    print("\nQ4 passes/valid runs per model (all conditions):")
    for mod, row in res["Q4_table"].items():
        print(f"  {mod:18s} " + "  ".join(f"{short[m]} {row[m][0]}/{row[m][1]}" for m in models))
    print(f"Q4 strict (every model ran it, all failed): {res['Q4']}")
    print(f"Q4 zero over GPT + Haiku (both ran it): {res['Q4_zero_gpt_haiku']}")
    print(f"Q4 zero over all three (all ran it): {res['Q4_zero_all_three']}")
    print(f"Q4 zero over whatever ran it: {res['Q4_zero_all_available']}")
    for f in res["Q4_failures"]:
        print(f"  {f['module']} {short[f['model']]} {f['condition']} r{f['replicate']}: dominant {f['dominant']} | {f['last_sim_line']}")


if __name__ == "__main__":
    main()
