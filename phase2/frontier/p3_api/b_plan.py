"""Part B plan: remaining Set 4b runs per (model, module), priority order and projected cost.

Projection (brief B2): calls/run on that exact module = max over the OTHER models of their mean iterations per run
there (Set 4b master logs) x this model's own mean USD per call in Set 4b (ledgers_4b, tag floor_full, ok calls)
x remaining runs x 1.3. Priority (B3): modules ordered by pooled Set 4b pass rate over the models that ran them,
ascending (zero / near-zero first). Writes phase2/results/p3_api/b_plan.json and prints the table.
"""
import collections
import json
import os

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(os.path.dirname(os.path.dirname(HERE)))
S4 = os.path.join(REPO, "phase2", "results", "set4_api")
OUT = os.path.join(REPO, "phase2", "results", "p3_api", "b_plan.json")
FLOOR = ["LIFObuffer", "accu", "adder_16bit", "adder_32bit", "adder_bcd", "adder_pipe_64bit", "alu", "barrel_shifter",
         "counter_12", "div_16bit", "float_multi", "freq_divbyfrac", "fsm", "multi_pipe_4bit", "multi_pipe_8bit",
         "parallel2serial", "pulse_detect", "serial2parallel", "traffic_light"]
MODELS = {"openai": "gpt-4.1-mini-2025-04-14", "anthropic": "claude-haiku-4-5-20251001", "gemini": "gemini-2.5-flash"}
TODO = ("openai", "anthropic")


def main():
    logs = {p: json.load(open(os.path.join(S4, "floor_full", p, "master_log.json"))) for p in MODELS}
    done = {p: collections.Counter(e["module"] for e in logs[p]) for p in MODELS}
    passes, runs = collections.Counter(), collections.Counter()
    iters = collections.defaultdict(list)
    for p, entries in logs.items():
        for e in entries:
            if e.get("error"):
                continue
            passes[e["module"]] += bool(e["pass"])
            runs[e["module"]] += 1
            iters[(p, e["module"])].append(e["total_iterations"])
    order = sorted(FLOOR, key=lambda m: (passes[m] / runs[m] if runs[m] else 0, m.lower()))
    plan = {}
    for p in TODO:
        led = [json.loads(l) for l in open(os.path.join(S4, "ledgers_4b", f"{p}_ledger.jsonl")) if l.strip()]
        ok = [c for c in led if c.get("tag") == "floor_full" and c["status"] == "ok"]
        usd_call = sum(c["cost_usd"] for c in ok) / len(ok)
        rows, cum = [], 0.0
        for m in order:
            remaining = 12 - done[p][m]
            if remaining <= 0:
                continue
            others = [sum(v) / len(v) for (q, mm), v in iters.items() if mm == m and q != p and v]
            cpr = max(others)
            cost = remaining * cpr * usd_call * 1.3
            cum += cost
            rows.append({"module": m, "remaining_runs": remaining, "calls_per_run_max_other": round(cpr, 2),
                         "pooled_pass_rate": round(passes[m] / runs[m], 3), "projected_usd": round(cost, 4),
                         "cumulative_usd": round(cum, 4)})
        plan[p] = {"model": MODELS[p], "usd_per_call_own": usd_call, "remaining_runs": sum(r["remaining_runs"] for r in rows),
                   "projected_total_usd": round(cum, 4), "modules": rows}
    json.dump({"order": order, "plan": plan}, open(OUT, "w"), indent=1)
    for p, v in plan.items():
        print(f"{p}: {v['remaining_runs']} runs, own USD/call {v['usd_per_call_own']:.5f}, projected ${v['projected_total_usd']:.2f}")
        for r in v["modules"]:
            print(f"   {r['module']:16s} runs {r['remaining_runs']:2d} pass {r['pooled_pass_rate']:.2f} "
                  f"calls/run {r['calls_per_run_max_other']:.2f} ${r['projected_usd']:.3f} cum ${r['cumulative_usd']:.3f}")


if __name__ == "__main__":
    main()
