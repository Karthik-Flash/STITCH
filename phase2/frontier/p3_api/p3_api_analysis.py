"""Part A analysis (P3_API_PREREG.md): per API model, as-run metrics (func_pass, clean_pass, silent structural pass),
calls and tokens per run by condition x stratum; the four primary contrasts on clean_pass (as run; signoff_clean is
scored offline by the Phase 3 agent) with the Phase 3 cell bootstrap / sign-flip (stats_set4.py, verified); baseline_gate
runs not clean while would_fire=1; INR per clean pass (ledger, tag p3_full). Writes
phase2/results/p3_api/analysis/p3_api_analysis.json and prints the tables."""
import collections
import glob
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
FRONTIER = os.path.dirname(HERE)
REPO = os.path.dirname(os.path.dirname(FRONTIER))
sys.path.insert(0, FRONTIER)
import stats_set4 as S  # noqa: E402

P3A = os.path.join(REPO, "phase2", "results", "p3_api")
OUT = os.path.join(P3A, "analysis")
CONDS = ["baseline", "raw_adv", "sem_adv_v2", "sem_adv_v3", "sem_esc_restart_v3", "baseline_gate"]
CONTRASTS = [("sem_esc_restart_v3", "baseline_gate", ("pooled", "silent", "visible")),
             ("sem_adv_v3", "baseline_gate", ("pooled", "silent", "visible")),
             ("baseline_gate", "raw_adv", ("pooled", "silent", "visible")),
             ("baseline_gate", "baseline", ("visible",))]
INR = 96 * 1.18


def main():
    if not S.verify():
        sys.exit("STOP: stats_set4 does not reproduce the published numbers")
    os.makedirs(OUT, exist_ok=True)
    silent = {t: json.load(open(os.path.join(REPO, "phase3", "tasks", t, "meta.json")))["sim_silent"]
              for t in os.listdir(os.path.join(REPO, "phase3", "tasks"))
              if os.path.isdir(os.path.join(REPO, "phase3", "tasks", t))}
    res = {}
    for prov in ("openai", "anthropic", "gemini"):
        runs = [json.load(open(f)) for f in glob.glob(os.path.join(P3A, "full", prov, "*", "*", "*", "rep*", "metrics.json"))]
        if not runs:
            continue
        model = runs[0]["model"]
        errs = [f for f in glob.glob(os.path.join(P3A, "full", prov, "*", "*", "*", "rep*", "error.json"))
                if not os.path.exists(os.path.join(os.path.dirname(f), "metrics.json"))]
        led = os.path.join(P3A, "ledgers", f"{prov}_ledger.jsonl")
        calls = [json.loads(l) for l in open(led) if l.strip()] if os.path.exists(led) else []
        calls = [c for c in calls if c.get("tag") == "p3_full"]
        r = {"model": model, "runs": len(runs), "errored_unresolved": len(errs), "table": {}, "contrasts": {},
             "gate_fail_would_fire": [], "spend_usd": sum(c["cost_usd"] for c in calls),
             "truncated": sum(1 for c in calls if str(c.get("finish_reason")) in ("length", "max_tokens", "MAX_TOKENS")),
             "reasoning_calls": sum(1 for c in calls if c.get("reasoning_tokens", 0) > 0)}
        cost_run = collections.defaultdict(float)
        for c in calls:
            cost_run[(c["module"], c["condition"], c["replicate"])] += c["cost_usd"]
        for cond in CONDS:
            for st in ("pooled", "silent", "visible"):
                rr = [x for x in runs if x["condition"] == cond and
                      (st == "pooled" or silent[x["task"]] == (st == "silent"))]
                if not rr:
                    continue
                n = len(rr)
                usd = sum(cost_run[(x["task"], cond, x["rep"])] for x in rr)
                clean = sum(bool(x["clean_pass"]) for x in rr)
                r["table"][f"{cond}|{st}"] = {
                    "n": n, "func_pass": sum(bool(x["func_pass"]) for x in rr), "clean_pass": clean,
                    "silent_structural_pass": sum(bool(x["silent_structural_pass"]) for x in rr),
                    "calls_per_run": sum(x["llm_calls"] for x in rr) / n,
                    "tokens_per_run": sum(x["tokens_in"] + x["tokens_out"] for x in rr) / n,
                    "inr_per_clean_pass": usd * INR / clean if clean else None, "usd": usd}
        cell = collections.defaultdict(lambda: collections.defaultdict(list))
        for x in runs:
            cell[x["task"]][x["condition"]].append(int(bool(x["clean_pass"])))
        for a, b, strata in CONTRASTS:
            for st in strata:
                d = [100 * (sum(v[a]) / len(v[a]) - sum(v[b]) / len(v[b])) for t, v in sorted(cell.items())
                     if v[a] and v[b] and (st == "pooled" or silent[t] == (st == "silent"))]
                if not d:
                    continue
                label = f"p3api:{model}:{a}-{b}:{st}"
                lo, hi = S.boot_ci(d, label)
                r["contrasts"][f"{a} - {b} | {st}"] = {"mean_pts": sum(d) / len(d), "lo": lo, "hi": hi,
                                                       "p": S.signflip_p(d, label), "cells": len(d)}
        r["gate_fail_would_fire"] = sorted((x["task"], x["rep"], x.get("would_class")) for x in runs
                                           if x["condition"] == "baseline_gate" and not x["clean_pass"] and x.get("would_fire"))
        res[prov] = r
    json.dump(res, open(os.path.join(OUT, "p3_api_analysis.json"), "w"), indent=1, default=str)
    for prov, r in res.items():
        print(f"\n=== {r['model']}: {r['runs']} runs, unresolved errors {r['errored_unresolved']}, "
              f"spend ${r['spend_usd']:.4f} (INR {r['spend_usd'] * INR:.1f}), truncated {r['truncated']}, reasoning {r['reasoning_calls']}")
        print(f"  {'condition':20s} {'stratum':8s} {'n':>3s} {'func':>5s} {'clean':>6s} {'silentSP':>8s} {'calls':>6s} {'tokens':>7s} {'INR/clean':>9s}")
        for k, v in r["table"].items():
            c, st = k.split("|")
            ipc = "-" if v["inr_per_clean_pass"] is None else f"{v['inr_per_clean_pass']:.3f}"
            print(f"  {c:20s} {st:8s} {v['n']:3d} {v['func_pass']:5d} {v['clean_pass']:6d} {v['silent_structural_pass']:8d} "
                  f"{v['calls_per_run']:6.2f} {v['tokens_per_run']:7.0f} {ipc:>9s}")
        print("  primary contrasts (clean_pass as run, points, cell bootstrap 95% CI, sign-flip p):")
        for k, v in r["contrasts"].items():
            print(f"    {k:45s} {S.sg(v['mean_pts'])} [{S.sg(v['lo'])}, {S.sg(v['hi'])}] cells={v['cells']} p={S.fp(v['p'])}")
        print(f"  baseline_gate not clean while would_fire=1: {r['gate_fail_would_fire']}")


if __name__ == "__main__":
    main()
