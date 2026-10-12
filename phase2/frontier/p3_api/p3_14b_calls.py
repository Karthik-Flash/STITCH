"""Read-only: Phase 3 qwen2.5-coder:14b calls and tokens per run (phase3/results, all 6 conditions), per
condition and per task, with each task's stratum. Used to pick the Part A pilot tasks and for the
14B-call-count projection. Writes phase2/results/p3_api/p3_14b_calls.json."""
import collections
import glob
import json
import os

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(os.path.dirname(os.path.dirname(HERE)))
RES = os.path.join(REPO, "phase3", "results")
OUT = os.path.join(REPO, "phase2", "results", "p3_api", "p3_14b_calls.json")

runs = [json.load(open(f)) for d in ("phase3_run", "phase3_gate_ctrl")
        for f in glob.glob(os.path.join(RES, d, "qwen2.5-coder_14b", "*", "*", "rep*", "metrics.json"))]
silent = {t: json.load(open(os.path.join(REPO, "phase3", "tasks", t, "meta.json")))["sim_silent"]
          for t in {r["task"] for r in runs}}
by_cond, by_task = collections.defaultdict(list), collections.defaultdict(list)
for r in runs:
    by_cond[r["condition"]].append(r)
    by_task[r["task"]].append(r)
mean = lambda xs: sum(xs) / len(xs) if xs else 0.0  # noqa: E731
out = {"runs": len(runs),
       "per_condition": {c: {"runs": len(v), "mean_calls": mean([r["llm_calls"] for r in v]),
                             "mean_tokens_in": mean([r["tokens_in"] for r in v]),
                             "mean_tokens_out": mean([r["tokens_out"] for r in v])} for c, v in sorted(by_cond.items())},
       "per_task": {t: {"sim_silent": silent[t], "runs": len(v), "mean_calls": mean([r["llm_calls"] for r in v])}
                    for t, v in sorted(by_task.items())}}
os.makedirs(os.path.dirname(OUT), exist_ok=True)
json.dump(out, open(OUT, "w"), indent=1)
print(f"runs {out['runs']}")
for c, v in out["per_condition"].items():
    print(f"  {c:20s} n={v['runs']:3d} calls/run {v['mean_calls']:.2f} tok_in {v['mean_tokens_in']:.0f} tok_out {v['mean_tokens_out']:.0f}")
for t, v in sorted(out["per_task"].items(), key=lambda kv: (kv[1]["sim_silent"], -kv[1]["mean_calls"])):
    print(f"  {'silent ' if v['sim_silent'] else 'visible'} {t:16s} calls/run {v['mean_calls']:.2f}")
