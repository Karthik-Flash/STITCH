"""Part A full-run projection per model (198 runs): the higher of (i) pilot USD/run x 198 and (ii) Phase 3 14B mean
calls/run per condition x pilot USD/call (per condition, pooled if a condition made no call) x 33; plus a 90%
bootstrap upper bound; cap = min(sub-cap, 1.5 x projection). INR = USD x 96 x 1.18."""
import glob
import json
import os
import random

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(os.path.dirname(os.path.dirname(HERE)))
P3A = os.path.join(REPO, "phase2", "results", "p3_api")
SUBCAP = {"openai": 1.5, "anthropic": 3.5}
CONDS = ["baseline", "raw_adv", "sem_adv_v2", "sem_adv_v3", "sem_esc_restart_v3", "baseline_gate"]
INR = 96 * 1.18


def main():
    c14 = json.load(open(os.path.join(P3A, "p3_14b_calls.json")))["per_condition"]
    rng = random.Random(0)
    for prov in SUBCAP:
        pil = os.path.join(P3A, "pilot", prov)
        runs = [json.load(open(f)) for f in glob.glob(os.path.join(pil, "*", "*", "*", "rep*", "metrics.json"))]
        led = os.path.join(P3A, "ledgers", f"{prov}_ledger.jsonl")
        calls = [json.loads(l) for l in open(led)] if os.path.exists(led) else []
        calls = [c for c in calls if c.get("tag") == "p3_pilot"]
        run_cost = {}
        for r in runs:
            run_cost[(r["task"], r["condition"], r["rep"])] = sum(
                c["cost_usd"] for c in calls if (c["module"], c["condition"], c["replicate"]) == (r["task"], r["condition"], r["rep"]))
        ok = [c for c in calls if c["status"] == "ok"]
        per_call = {k: [c["cost_usd"] for c in ok if c["condition"] == k] for k in CONDS}
        pooled = [c["cost_usd"] for c in ok]

        def p1(costs):
            return sum(costs) / len(costs) * 198

        def p2(pc, pool):
            return sum(33 * c14[k]["mean_calls"] * (sum(pc[k] or pool) / len(pc[k] or pool)) for k in CONDS)

        rc = list(run_cost.values())
        a, b = p1(rc), p2(per_call, pooled)
        boots = sorted(max(p1([rng.choice(rc) for _ in rc]),
                           p2({k: [rng.choice(v) for _ in v] for k, v in per_call.items()}, [rng.choice(pooled) for _ in pooled]))
                       for _ in range(2000))
        proj, ub = max(a, b), boots[int(0.9 * len(boots))]
        cap = min(SUBCAP[prov], 1.5 * proj)
        spent = sum(c["cost_usd"] for c in calls)
        print(f"{prov:9s} pilot runs {len(runs)} calls {len(calls)} (ok {len(ok)}) spent ${spent:.4f} | "
              f"pilot-based ${a:.2f} 14B-calls-based ${b:.2f} -> ${proj:.2f} (INR {proj * INR:.0f}), "
              f"90% UB ${ub:.2f} | Part A cap ${cap:.2f} (sub-cap {SUBCAP[prov]}) | "
              f"reasoning>0 {sum(1 for c in ok if c.get('reasoning_tokens', 0) > 0)} "
              f"trunc {sum(1 for c in ok if str(c.get('finish_reason')) in ('length', 'max_tokens'))}")


if __name__ == "__main__":
    main()
