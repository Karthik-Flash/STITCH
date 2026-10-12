"""Set 3 per-call and per-run token statistics (read-only over saved runs).

Used for: max_tokens (2x longest single completion, rounded up to 256),
Set-3-based cost projection (mean calls/run and tokens/call per condition),
and checking whether Ollama's prompt counts behave like API input counts
(multi-turn prompts must grow monotonically if the whole history is counted).
Writes phase2/results/set4_api/set3_token_stats.json.
"""
import glob
import json
import math
import os
import statistics as st

HERE = os.path.dirname(os.path.abspath(__file__))
S3 = os.path.join(HERE, "..", "results", "set3_run")
OUT = os.path.join(HERE, "..", "results", "set4_api", "set3_token_stats.json")


def runs():
    for p in glob.glob(os.path.join(S3, "*", "*", "*", "rep*", "*.json")):
        name = os.path.basename(p)
        if name not in ("metrics.json", "run_log.json"):
            continue
        d = json.load(open(p, encoding="utf-8"))
        cond = p.split(os.sep)[-3]
        if name == "metrics.json":
            calls = [(it["prompt_tokens"], it["completion_tokens"]) for it in d["per_iter_detail"]]
        else:
            calls = [(it["prompt_tokens"], it["completion_tokens"]) for it in d["iterations"]]
        yield cond, calls, p


def main():
    by_cond, all_ct, nonmono, multi, rows = {}, [], 0, 0, []
    for cond, calls, path in runs():
        by_cond.setdefault(cond, []).append(calls)
        all_ct += [c for _, c in calls]
        if len(calls) > 1:
            multi += 1
            if any(b[0] < a[0] for a, b in zip(calls, calls[1:])):
                nonmono += 1
        rows.append((max(c for _, c in calls), path))
    rows.sort(reverse=True)
    longest = max(all_ct)
    out = {
        "runs": sum(len(v) for v in by_cond.values()),
        "calls": len(all_ct),
        "completion_tokens_max": longest,
        "completion_tokens_p99": sorted(all_ct)[int(0.99 * (len(all_ct) - 1))],
        "completion_tokens_p999": sorted(all_ct)[int(0.999 * (len(all_ct) - 1))],
        "top5_longest": [(c, os.path.relpath(p, S3)) for c, p in rows[:5]],
        "max_tokens_2x_rounded_256": math.ceil(2 * longest / 256) * 256,
        "multi_call_runs": multi,
        "multi_call_runs_with_prompt_count_decreasing": nonmono,
        "per_condition": {},
    }
    for cond, rs in sorted(by_cond.items()):
        n = len(rs)
        out["per_condition"][cond] = {
            "runs": n,
            "mean_calls_per_run": sum(len(r) for r in rs) / n,
            "mean_input_tokens_per_run": sum(p for r in rs for p, _ in r) / n,
            "mean_output_tokens_per_run": sum(c for r in rs for _, c in r) / n,
            "mean_output_tokens_per_call": st.mean(c for r in rs for _, c in r),
        }
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    json.dump(out, open(OUT, "w", encoding="utf-8"), indent=2)
    print(json.dumps(out, indent=2))


if __name__ == "__main__":
    main()
