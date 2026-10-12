"""Full-run (204 runs = 17 modules x 4 conditions x N=3) cost projection.

--a-priori : Set 3 mean input/output tokens per run per condition x list price
             (no cache discount, Set 3's tokenizers). Used for model selection.
--pilot    : after the pilot, per model, two projections, report the higher:
             (1) pilot's own mean USD per run, per condition, x 51;
             (2) Set 3's mean calls/run per condition x pilot mean USD per call
                 (per condition, falling back to pooled if a condition has no calls).
             90% upper bound: 2000-rep bootstrap over pilot runs (1) and calls (2).
INR = USD x rate x 1.18 GST.
"""
import argparse
import json
import os
import random
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import backends as B  # noqa: E402

SET4 = os.path.join(HERE, "..", "results", "set4_api")
RATE, RATE_NOTE = 96.0, "INR/USD 96.0, conservative: market ~95.9 (2026-09-26), Fed H.10 83.36 (2026-09-23)"
GST = 1.18
CONDS = ["baseline", "sem_adv", "sem_escalate", "sem_escalate_restart"]
PER_COND = 51
CANDIDATES = ("openai", "anthropic", "gemini", "moonshot")
# rejected alternatives, shown in the a-priori table for the selection record (same sources/date)
EXTRA_PRICES = {"claude-sonnet-5": (2.00, 0.20, 10.00), "gpt-5-chat-latest": (1.25, 0.125, 10.00),
                "gpt-4.1": (2.00, 0.50, 8.00), "gemini-2.5-flash-lite": (0.10, 0.01, 0.40)}


def inr(usd):
    return usd * RATE * GST


def a_priori():
    s3 = json.load(open(os.path.join(SET4, "set3_token_stats.json")))["per_condition"]
    tin = sum(s3[c]["mean_input_tokens_per_run"] for c in CONDS) * PER_COND
    tout = sum(s3[c]["mean_output_tokens_per_run"] for c in CONDS) * PER_COND
    print(f"Set 3 based full-run tokens: input {tin:,.0f}, output {tout:,.0f}; {RATE_NOTE}")
    print(f"per-model selection limit: INR 700 incl GST = USD {700 / GST / RATE:.2f}")
    prices = {**B.PRICES, **EXTRA_PRICES}
    for m, (pi, _, po) in sorted(prices.items(), key=lambda kv: kv[1][0] * tin + kv[1][2] * tout):
        usd = (tin * pi + tout * po) / 1e6
        print(f"  {m:24s} ${usd:6.2f}  INR {inr(usd):7.0f}  {'fits' if inr(usd) <= 700 else 'OVER 700'}")


def pilot(tag="pilot", ledger_dir="ledgers"):
    s3 = json.load(open(os.path.join(SET4, "set3_token_stats.json")))["per_condition"]
    rng = random.Random(0)
    grand = grand_ub = 0.0
    for provider in CANDIDATES:
        path = os.path.join(SET4, ledger_dir, f"{provider}_ledger.jsonl")
        if not os.path.exists(path):
            continue
        calls = [json.loads(l) for l in open(path) if l.strip()]
        calls = [c for c in calls if c.get("tag") == tag]
        if not calls:
            continue
        runs = {}
        for c in calls:
            runs.setdefault((c["condition"], c["module"], c["replicate"]), []).append(c)
        by_cond_runs = {k: [sum(x["cost_usd"] for x in v) for (cc, *_), v in runs.items() if cc == k] for k in CONDS}
        by_cond_calls = {k: [c["cost_usd"] for c in calls if c["condition"] == k and c["status"] == "ok"] for k in CONDS}
        pooled_calls = [c["cost_usd"] for c in calls if c["status"] == "ok"]

        def proj1(rs):
            return sum(PER_COND * sum(rs[k]) / len(rs[k]) for k in CONDS if rs[k])

        def proj2(cs):
            return sum(PER_COND * s3[k]["mean_calls_per_run"] * (sum(cs[k] or pooled_calls) / len(cs[k] or pooled_calls))
                       for k in CONDS)

        p1, p2 = proj1(by_cond_runs), proj2(by_cond_calls)
        boots = []
        for _ in range(2000):
            r = {k: [rng.choice(v) for v in [v] for _ in v] if v else [] for k, v in by_cond_runs.items()}
            c = {k: [rng.choice(v) for _ in v] if v else [] for k, v in by_cond_calls.items()}
            boots.append(max(proj1(r), proj2(c)))
        boots.sort()
        ub = boots[int(0.9 * len(boots))]
        model = calls[-1]["model_requested"]
        spent = sum(c["cost_usd"] for c in calls)
        print(f"{provider:9s} {model:22s} pilot runs {len(runs)} calls {len(calls)} spent ${spent:.4f} | "
              f"proj pilot ${p1:.2f} set3-calls ${p2:.2f} -> ${max(p1, p2):.2f} "
              f"(INR {inr(max(p1, p2)):.0f}), 90% UB ${ub:.2f} (INR {inr(ub):.0f})")
        grand += max(p1, p2)
        grand_ub += ub
    print(f"TOTAL projected ${grand:.2f} (INR {inr(grand):.0f}); 90% UB ${grand_ub:.2f} (INR {inr(grand_ub):.0f}); "
          f"fits INR 3000: {inr(grand_ub) <= 3000}. {RATE_NOTE}")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--pilot", action="store_true")
    ap.add_argument("--tag", default="pilot")
    ap.add_argument("--ledger-dir", default="ledgers")
    ap.add_argument("--per-cond", type=int, default=51, help="runs per condition (Set 4b: 19 x 3 = 57)")
    a = ap.parse_args()
    PER_COND = a.per_cond
    pilot(a.tag, a.ledger_dir) if a.pilot else a_priori()
