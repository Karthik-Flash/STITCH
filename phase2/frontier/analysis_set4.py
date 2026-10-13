"""Set 4 pre-registered analysis (SET4_PREREG.md §5-7 + Amendment 1).

Inputs:  phase2/results/set4_api/full/<provider>/master_log.json (+ per-run dirs),
         phase2/results/set4_api/ledgers/<provider>_ledger.jsonl (tag == "full").
Outputs: phase2/results/set4_api/analysis/set4_analysis.json, *.csv, figures (.png/.pdf).
Money: INR = USD x 96 x 1.18 (Amendment A6).
Usage:   python phase2/frontier/analysis_set4.py
"""
import csv
import importlib.util
import json
import os
import sys
from collections import defaultdict

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
PHASE2 = os.path.dirname(HERE)
sys.path.insert(0, HERE)
from stats_set4 import boot_ci, fp, sg, signflip_p, wilson  # noqa: E402

SET4 = os.path.join(PHASE2, "results", "set4_api")
OUT = os.path.join(SET4, "analysis")
ROOT = os.path.join(SET4, "full")
CONDS = ["baseline", "sem_adv", "sem_escalate", "sem_escalate_restart"]
PROVIDERS = ["openai", "gemini", "moonshot", "anthropic"]
DISPLAY = {"gpt-4.1-mini-2025-04-14": "GPT-4.1 mini", "gemini-2.5-flash": "Gemini 2.5 Flash",
           "kimi-k2.6": "Kimi K2.6 (T=0.6)", "claude-haiku-4-5-20251001": "Claude Haiku 4.5"}
INR = 96.0 * 1.18
SET_REF = {"Set 1 recoverable": 16.6, "Set 1 ceiling": 75.1, "Set 3 recoverable": 27.6}
TRUNC = {"length", "max_tokens", "MAX_TOKENS"}


def _load(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


# set3_analysis/_data.py's own load_run_cost, pointed at each Set 4 provider directory
S3DATA = _load(os.path.join(PHASE2, "set3_analysis", "_data.py"), "set3_data_for_set4")


def load():
    runs, calls = [], []
    for p in PROVIDERS:
        ml = os.path.join(SET4, "full", p, "master_log.json")
        if os.path.exists(ml):
            for e in json.load(open(ml, encoding="utf-8")):
                runs.append(dict(e, provider=p))
        lg = os.path.join(SET4, "ledgers", f"{p}_ledger.jsonl")
        if os.path.exists(lg):
            calls += [json.loads(l) for l in open(lg, encoding="utf-8") if l.strip()]
    calls = [c for c in calls if c.get("tag") == "full"]
    return runs, calls


def main():
    import stats_set4
    if not stats_set4.verify():
        sys.exit("STOP (prereg A4): stats_set4 does not reproduce POSTHOC_CHECKS.md; analysis not run")
    os.makedirs(OUT, exist_ok=True)
    runs, calls = load()
    valid = [r for r in runs if not r.get("error")]
    models = [m for m in DISPLAY if any(r["model"] == m for r in valid)]
    res = {"runs_total": len(runs), "runs_errored": len(runs) - len(valid),
           "errored": [(r["model"], r["module"], r["condition"], r["run_replicate"], r["error"])
                       for r in runs if r.get("error")]}

    # 1. pass rates, pooled and per model, Wilson 95%
    res["pass_rates"] = {}
    for scope in ["pooled"] + models:
        for c in CONDS:
            rr = [r for r in valid if r["condition"] == c and (scope == "pooled" or r["model"] == scope)]
            k, n = sum(bool(r["pass"]) for r in rr), len(rr)
            lo, hi = wilson(k, n)
            res["pass_rates"][f"{scope}|{c}"] = {"k": k, "n": n, "rate": k / n if n else None, "lo": lo, "hi": hi}

    # 2. condition - baseline, (model, module) cells: bootstrap CI + sign-flip p (Set 3's exact method)
    cell = defaultdict(lambda: defaultdict(list))
    for r in valid:
        cell[(r["model"], r["module"])][r["condition"]].append(int(bool(r["pass"])))
    res["contrasts"] = {}
    for scope in ["pooled"] + models:
        for a in CONDS[1:]:
            d = {k: v for k, v in cell.items() if v[a] and v["baseline"] and (scope == "pooled" or k[0] == scope)}
            diffs = [100 * (sum(v[a]) / len(v[a]) - sum(v["baseline"]) / len(v["baseline"])) for _, v in sorted(d.items())]
            if not diffs:
                continue
            label = f"p2:set4_{scope}:{a}"
            lo, hi = boot_ci(diffs, label)
            p = signflip_p(diffs, label)
            res["contrasts"][f"{scope}|{a}"] = {
                "mean_pts": sum(diffs) / len(diffs), "lo": lo, "hi": hi, "p": p, "cells": len(diffs),
                "line": f"{a} - baseline: cell mean {sg(sum(diffs) / len(diffs))} pts [{sg(lo)}, {sg(hi)}], "
                        f"cells={len(diffs)}, sign-flip p={fp(p)}"}

    # 3. replicate trace: passes with/without semantic_fired; escalation rate
    res["trace"] = {}
    for scope in ["pooled"] + models:
        for c in CONDS:
            rr = [r for r in valid if r["condition"] == c and (scope == "pooled" or r["model"] == scope)]
            passes = [r for r in rr if r["pass"]]
            t = {"runs": len(rr), "passes": len(passes),
                 "sf_runs": sum(1 for r in rr if r.get("semantic_fired")),
                 "passes_with_sf": sum(1 for r in passes if r.get("semantic_fired")),
                 "passes_without_sf": sum(1 for r in passes if not r.get("semantic_fired")),
                 # stricter: a directive was actually delivered before the passing iteration
                 "passes_sf_before_pass": sum(1 for r in passes if fired_before_pass(r))}
            if c.startswith("sem_escalate"):
                esc = [r for r in rr if r.get("fired_escalate")]
                t.update(escalated=len(esc), escalation_rate=len(esc) / len(rr) if rr else None,
                         escalated_passes=sum(1 for r in esc if r["pass"]))
            res["trace"][f"{scope}|{c}"] = t

    # 4. tool invocations, sem_adv -> sem_escalate (set3_analysis/_data.py load_run_cost)
    res["tools"] = {}
    for scope in ["pooled"] + models:
        per = defaultdict(list)
        for r in valid:
            if scope != "pooled" and r["model"] != scope:
                continue
            S3DATA.RESULTS_ROOT = os.path.join(SET4, "full", r["provider"])
            cst = S3DATA.load_run_cost(r["module"], r["model"], r["condition"], r["run_replicate"])
            if cst:
                per[r["condition"]].append(cst["tool_calls"])
        sa = sum(per["sem_adv"]) / len(per["sem_adv"]) if per["sem_adv"] else None
        se = sum(per["sem_escalate"]) / len(per["sem_escalate"]) if per["sem_escalate"] else None
        res["tools"][scope] = {c: (sum(v) / len(v) if v else None) for c, v in per.items()}
        res["tools"][scope]["reduction_pct"] = (sa - se) / sa * 100 if sa else None

    # 5. tokens, cost, latency, truncation (ledger, tag=full; retried attempts included in cost)
    by_run = defaultdict(list)
    for c in calls:
        by_run[(c["model_requested"], c["module"], c["condition"], c["replicate"])].append(c)
    res["cost"], res["truncation"], res["latency"] = {}, {}, {}
    rows_csv = []
    for m in models:
        for c in CONDS:
            rr = [r for r in valid if r["model"] == m and r["condition"] == c]
            usd = [sum(x["cost_usd"] for x in by_run[(m, r["module"], c, r["run_replicate"])]) for r in rr]
            tok_in = [sum(x.get("input_tokens", 0) for x in by_run[(m, r["module"], c, r["run_replicate"])]) for r in rr]
            tok_out = [sum(x.get("output_tokens", 0) for x in by_run[(m, r["module"], c, r["run_replicate"])]) for r in rr]
            npass = sum(bool(r["pass"]) for r in rr)
            ok = [x for r in rr for x in by_run[(m, r["module"], c, r["run_replicate"])] if x.get("status") == "ok"]
            row = {"model": m, "condition": c, "runs": len(rr), "passes": npass,
                   "tokens_per_run": (sum(tok_in) + sum(tok_out)) / len(rr) if rr else None,
                   "input_tokens_per_run": sum(tok_in) / len(rr) if rr else None,
                   "output_tokens_per_run": sum(tok_out) / len(rr) if rr else None,
                   "tokens_per_pass": (sum(tok_in) + sum(tok_out)) / npass if npass else None,
                   "usd_total": sum(usd), "inr_per_run": sum(usd) * INR / len(rr) if rr else None,
                   "inr_per_pass": sum(usd) * INR / npass if npass else None,
                   "calls": len(ok), "latency_s_mean": sum(x["latency_s"] for x in ok) / len(ok) if ok else None,
                   "truncated": sum(1 for x in ok if str(x.get("finish_reason")) in TRUNC)}
            rows_csv.append(row)
            res["cost"][f"{m}|{c}"] = row
        base = res["cost"][f"{m}|baseline"]["tokens_per_run"]
        for c in CONDS[1:]:
            t = res["cost"][f"{m}|{c}"]["tokens_per_run"]
            res["cost"][f"{m}|{c}"]["token_overhead_vs_baseline_pct"] = (t / base - 1) * 100 if base else None
    res["failures"] = failures([r for r in valid if not r["pass"]])
    res["system_fingerprints"] = sorted({c.get("system_fingerprint") for c in calls if c.get("system_fingerprint")})
    res["fingerprint_counts"] = {fp_: sum(1 for c in calls if c.get("system_fingerprint") == fp_)
                                 for fp_ in res["system_fingerprints"]}
    res["spend_usd_full"] = sum(c["cost_usd"] for c in calls)
    res["spend_inr_full"] = res["spend_usd_full"] * INR

    with open(os.path.join(OUT, "set4_cost_table.csv"), "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(rows_csv[0].keys()) + ["token_overhead_vs_baseline_pct"])
        w.writeheader()
        w.writerows(rows_csv)
    json.dump(res, open(os.path.join(OUT, "set4_analysis.json"), "w", encoding="utf-8"), indent=2, default=str)

    fig_ladder(res, models)
    fig_cost(res, models)
    report(res, models)


def run_dir(root, r):
    safe = r["model"].replace(":", "_").replace(".", "")
    return os.path.join(root, r["provider"], r["module"], safe, r["condition"], f"rep{r['run_replicate']}")


def fired_before_pass(r, root=None):
    """True if the interpreter fired on an iteration earlier than the passing one, i.e. its
    directive was sent to the model before the pass."""
    d = run_dir(root or ROOT, r)
    k = r.get("iterations_to_pass") or 0
    if os.path.exists(os.path.join(d, "metrics.json")):
        its = json.load(open(os.path.join(d, "metrics.json")))["per_iter_detail"]
        return any(it["semantic_fired"] for it in its if it["iter"] < k)
    its = json.load(open(os.path.join(d, "run_log.json")))["iterations"]
    return any(it["interpreter_invoked"] for it in its if it["iteration"] < k)


def failures(failed, root=None):
    root = root or ROOT
    """Per failed run: err_type sequence over iterations, the dominant one, and the first
    error/fail line of the last iteration's sim log."""
    out = []
    for r in failed:
        d = run_dir(root, r)
        if os.path.exists(os.path.join(d, "metrics.json")):
            seq = [it["err_type"] for it in json.load(open(os.path.join(d, "metrics.json")))["per_iter_detail"]]
        else:
            seq = [it["err_type"] for it in json.load(open(os.path.join(d, "run_log.json")))["iterations"]]
        iters = sorted((int(x.split("_")[1]) for x in os.listdir(d) if x.startswith("iter_")))
        log = open(os.path.join(d, f"iter_{iters[-1]}", "sim_log.txt"), encoding="utf-8", errors="replace").read()
        key = next((l.strip() for l in log.splitlines()
                    if any(w in l.lower() for w in ("error", "fail", "timeout", "mismatch"))), "")
        dom = max(set(seq), key=seq.count) if seq else None
        out.append({"model": r["model"], "module": r["module"], "condition": r["condition"],
                    "replicate": r["run_replicate"], "iterations": len(seq), "err_types": seq,
                    "dominant": dom, "last_sim_line": key[:160]})
    return out


def fig_ladder(res, models):
    """Figure 5 update: the existing 4B-32B ladder rows + API baseline bars."""
    ladder = _load(os.path.join(PHASE2, "set3_analysis", "fig_capability_ladder_full.py"), "ladder_full")
    rows = ladder.build()
    for m in models:
        pr = res["pass_rates"][f"{m}|baseline"]
        rows.append({"label": DISPLAY[m], "run": "api", "temperature": 0.6 if m == "kimi-k2.6" else 0.1,
                     "n_pass": pr["k"], "n_total": pr["n"], "rate": pr["rate"], "ci_lo": pr["lo"], "ci_hi": pr["hi"]})
    rows.sort(key=lambda r: r["rate"])
    colors = {"twin": "#DD8452", "set3": "#4C72B0", "api": "#55A868"}
    x = np.arange(len(rows))
    fig, ax = plt.subplots(figsize=(14, 6.5))
    ax.bar(x, [r["rate"] for r in rows],
           yerr=[[r["rate"] - r["ci_lo"] for r in rows], [r["ci_hi"] - r["rate"] for r in rows]],
           capsize=5, color=[colors[r["run"]] for r in rows], edgecolor="black", linewidth=0.5,
           hatch=None)
    for i, r in enumerate(rows):
        ax.text(i, -0.28, f"T={r['temperature']}\n({r['n_pass']}/{r['n_total']})", ha="center", va="top",
                fontsize=7.5, transform=ax.get_xaxis_transform())
    from matplotlib.patches import Patch
    ax.legend(handles=[Patch(facecolor=colors["twin"], edgecolor="black", label="Twin (Set 2), T=0.5"),
                       Patch(facecolor=colors["set3"], edgecolor="black", label="Set 3, T=0.1"),
                       Patch(facecolor=colors["api"], edgecolor="black",
                             label="API, non-reasoning (Set 4), T=0.1")], loc="upper left")
    ax.set_xticks(x)
    ax.set_xticklabels([r["label"] for r in rows], rotation=25, ha="right")
    ax.set_ylabel("Pooled pass rate (recoverable band, Wilson 95% CI)")
    ax.set_ylim(0, 1.05)
    ax.set_title("Capability ladder, 4B to API models (baseline, 17 recoverable-band modules)\n"
                 "ORDINAL comparison only: temperature differs across colours")
    ax.grid(axis="y", linestyle=":", alpha=0.4)
    fig.tight_layout()
    fig.subplots_adjust(bottom=0.36)
    for ext in ("png", "pdf"):
        fig.savefig(os.path.join(OUT, f"fig5_capability_ladder_api.{ext}"), dpi=300)
    plt.close(fig)


def fig_cost(res, models):
    fig, ax = plt.subplots(figsize=(10, 5))
    w = 0.2
    for j, c in enumerate(CONDS):
        vals = [res["cost"][f"{m}|{c}"]["inr_per_pass"] or 0 for m in models]
        ax.bar(np.arange(len(models)) + (j - 1.5) * w, vals, w, label=c, edgecolor="black", linewidth=0.4)
    ax.set_xticks(np.arange(len(models)))
    ax.set_xticklabels([DISPLAY[m] for m in models])
    ax.set_ylabel("INR per passing module (incl. 18% GST, INR 96/USD)")
    ax.set_title("Set 4 cost per passing module, by condition (recoverable band)")
    ax.legend()
    ax.grid(axis="y", linestyle=":", alpha=0.4)
    fig.tight_layout()
    for ext in ("png", "pdf"):
        fig.savefig(os.path.join(OUT, f"fig_set4_inr_per_pass.{ext}"), dpi=300)
    plt.close(fig)


def report(res, models):
    print(f"runs {res['runs_total']}, errored {res['runs_errored']}")
    for scope in ["pooled"] + models:
        print(f"\n== {DISPLAY.get(scope, scope)}")
        for c in CONDS:
            p = res["pass_rates"][f"{scope}|{c}"]
            t = res["trace"][f"{scope}|{c}"]
            extra = f" esc_rate {t['escalation_rate']:.2f}" if "escalation_rate" in t and t["escalation_rate"] is not None else ""
            print(f"  {c:22s} {p['k']:3d}/{p['n']:3d} {100 * p['rate']:5.1f}% [{100 * p['lo']:.1f}, {100 * p['hi']:.1f}]"
                  f"  sf runs {t['sf_runs']}, passes w/ sf {t['passes_with_sf']} (fired before pass "
                  f"{t['passes_sf_before_pass']}), w/o sf {t['passes_without_sf']}{extra}"
                  + (f" escalated {t['escalated']} (passed {t['escalated_passes']})" if "escalated" in t else ""))
        for a in CONDS[1:]:
            if f"{scope}|{a}" in res["contrasts"]:
                print("  " + res["contrasts"][f"{scope}|{a}"]["line"])
        tr = res["tools"][scope]
        if tr.get("reduction_pct") is not None:
            print(f"  tool calls/run sem_adv {tr['sem_adv']:.2f} -> sem_escalate {tr['sem_escalate']:.2f}: "
                  f"{tr['reduction_pct']:.1f}% reduction (Set 1 16.6%, Set 3 27.6%)")
    print("\nfailures:")
    for f in res["failures"]:
        print(f"  {DISPLAY.get(f['model'], f['model'])} {f['module']} {f['condition']} rep{f['replicate']}: "
              f"{f['iterations']} iters, dominant {f['dominant']}, seq {f['err_types']} | {f['last_sim_line']}")
    print("\ncost (INR per run / per pass, tokens per run, overhead vs baseline, latency, truncated):")
    for m in models:
        for c in CONDS:
            x = res["cost"][f"{m}|{c}"]
            ov = x.get("token_overhead_vs_baseline_pct")
            print(f"  {DISPLAY[m]:18s} {c:22s} INR/run {x['inr_per_run']:.3f} INR/pass "
                  f"{x['inr_per_pass'] if x['inr_per_pass'] is None else round(x['inr_per_pass'], 3)} "
                  f"tok/run {x['tokens_per_run']:.0f} ovh {'' if ov is None else f'{ov:+.0f}%'} "
                  f"lat {x['latency_s_mean']:.1f}s trunc {x['truncated']}")
    print(f"\nOpenAI system fingerprints: {res['fingerprint_counts']}")
    print(f"full-run spend ${res['spend_usd_full']:.4f} = INR {res['spend_inr_full']:.0f}")


if __name__ == "__main__":
    main()
