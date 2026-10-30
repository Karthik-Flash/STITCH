#!/usr/bin/env python3
"""Generation speed per job and the --time arithmetic (laptop only). Writes reports/SPEED.md.

Sources (hpc_logs/ is local-only, never deployed or committed):
  gen_<job>.log           one-shot lines "tokens in/out A/B ... Ns": B / N (wall time, includes prompt eval; the first
                          call of a job also includes the model load)
  ollama_serve_<job>.log  llama-server "n_threads = ..." and per-call print_timing "eval time = X ms / N tokens"
                          (generation only) and "prompt eval time"
  oneshot_records/*/record.json  eval_count / eval_duration (generation only)
  Phase 3 32b serve log   phase3/results/final_batch_logs/ollama_serve_369810.log (same parse)
--time: remaining calls x (output tokens / generation rate + input tokens / prompt rate + tool time per call)
        + model load per process, x 1.5, at several generation rates.

Usage: python pipeline/speed.py [--logs hpc_logs]
"""
from __future__ import annotations

import argparse
import glob
import json
import os
import re
import statistics
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import budget  # noqa: E402
import make_tasks as MT  # noqa: E402

STUDY = os.path.dirname(HERE)
ARM_RUNS = 34 * 2
MARGIN = 1.5
RATES = (8.0, 15.0, 30.0)       # 8 = first-call exit threshold, 15 = warning threshold


def serve_stats(path: str) -> dict:
    text = open(path, encoding="utf-8", errors="replace").read()
    gen = [(float(ms), int(n)) for ms, n in re.findall(r"\|\s+eval time =\s+([\d.]+) ms /\s+(\d+) tokens", text)]
    pp = [(float(ms), int(n)) for ms, n in re.findall(r"prompt eval time =\s+([\d.]+) ms /\s+(\d+) tokens", text)]
    nt = re.findall(r"n_threads = \d+ \(n_threads_batch = \d+\) / \d+", text)
    gpu = re.findall(r"(?:CUDA0|device \d+): (NVIDIA [^,\n(]+)", text)
    rates = [n / (ms / 1e3) for ms, n in gen if ms > 0 and n >= 20]
    return {"calls": len(gen), "gen_tok": sum(n for _, n in gen), "gen_s": sum(ms for ms, _ in gen) / 1e3,
            "pp_tok": sum(n for _, n in pp), "pp_s": sum(ms for ms, _ in pp) / 1e3,
            "median": statistics.median(rates) if rates else None, "n_threads": nt[-1] if nt else "?",
            "gpu": gpu[0].strip() if gpu else "?"}


def gen_log(path: str) -> dict:
    text = open(path, encoding="utf-8", errors="replace").read()
    calls = [(m, int(i), int(o), float(s)) for m, i, o, d, s in      # done_reason None = the gate's mock run
             re.findall(r"^(\w+)\s+tokens in/out (\d+)/(\d+) done_reason (\S+) ([\d.]+)s", text, re.M) if d != "None"]
    arms = [(m, int(x)) for m, x in re.findall(r"^\[(?!mock\])\S+\] rep\d+ (\S+)\s+\S+\s+it=(\d+)", text, re.M)]
    gpu = re.findall(r"^GPU 0: (.+?) \(UUID", text, re.M)
    return {"calls": calls, "arms": arms, "gpu": gpu[0] if gpu else "?"}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--logs", default=os.path.join(STUDY, "hpc_logs"))
    a = ap.parse_args()
    md = ["# Generation speed and wall time (pipeline/speed.py)", "",
          "Generation rate = output tokens / generation time (llama-server print_timing `eval time`, or Ollama "
          "eval_duration); model load and prompt evaluation excluded. Wall rate = output tokens / wall seconds of the "
          "one-shot call (gen log), prompt evaluation included.", "",
          "| source | GPU | llama-server threads | calls | generation tok/s (pooled) | median per call | prompt tok/s |",
          "|---|---|---|---|---|---|---|"]
    serves = {"Phase 3 32b (job 369810)": budget.P3_32B_SERVE_LOG}
    serves.update({f"job {re.search(r'(\d+)', os.path.basename(p)).group(1)}": p
                   for p in sorted(glob.glob(os.path.join(a.logs, "ollama_serve_*.log")))})
    gens = {re.search(r"(\d+)", os.path.basename(p)).group(1): gen_log(p)
            for p in sorted(glob.glob(os.path.join(a.logs, "gen_*.log")))}
    p3_run = os.path.join(os.path.dirname(budget.P3_32B_SERVE_LOG), "p3_run_369810.log")
    gpu = {"Phase 3 32b (job 369810)": re.findall(r"^(NVIDIA [^,]+),", open(p3_run).read(), re.M)[0]}
    gpu.update({f"job {j}": g["gpu"] for j, g in gens.items()})
    pooled = {}
    for name, p in serves.items():
        s = serve_stats(p)
        pooled[name] = s
        md.append(f"| {name} serve log | {gpu.get(name, '?')} | {s['n_threads']} | {s['calls']} | "
                  f"{s['gen_tok'] / s['gen_s']:.2f} | {s['median']:.2f} | {s['pp_tok'] / s['pp_s']:.0f} |")
    for job, g in gens.items():
        c = g["calls"][1:]                       # first call of the job includes the model load
        md.append(f"| job {job} gen log, one-shot wall rate (first call excluded) | {g['gpu']} | - | {len(c)} | "
                  f"{sum(x[2] for x in c) / sum(x[3] for x in c):.2f} (wall) | "
                  f"{statistics.median(x[2] / x[3] for x in c):.2f} (wall) | - |")
    recs = [json.load(open(p)) for p in glob.glob(os.path.join(a.logs, "oneshot_records", "*", "record.json"))]
    meta = [r["llm_meta"] for r in recs if r.get("llm_meta", {}).get("eval_duration")]
    md.append(f"| oneshot_records (HPC record.json) | - | - | {len(meta)} | "
              f"{sum(m['eval_count'] for m in meta) / (sum(m['eval_duration'] for m in meta) / 1e9):.2f} | "
              f"{statistics.median(m['eval_count'] / (m['eval_duration'] / 1e9) for m in meta):.2f} | - |")

    # ---- remaining work, from the logs
    rows = MT.load_rows()
    done = {r["module"]: r for r in recs if r.get("status", "ok") == "ok" and r.get("output_sha256")}
    bud = {}
    for l in open(os.path.join(STUDY, "reports", "PREDEPLOY_BUDGET.md"), encoding="utf-8"):
        c = [x.strip() for x in l.split("|")]
        if len(c) > 7 and c[1] in rows and c[2].isdigit():
            bud[c[1]] = {"in": int(c[2]), "out": int(c[3]), "arms_in": int(c[5])}
    out_tok = {m: (done[m]["tokens_out"] if m in done else bud[m]["out"]) for m in rows}
    todo1 = sorted(m for m in rows if m not in done)
    smoke = [it for g in gens.values() for _, it in g["arms"]]
    arms_done = len(smoke)
    per_run = sum(smoke) / len(smoke)
    arm_mods = sorted(set(rows) - {m for g in gens.values() for m, _ in g["arms"]})
    tool_s = budget_tool_s()
    loads = [g["calls"][0][3] - g["calls"][0][2] / (pooled[f"job {j}"]["gen_tok"] / pooled[f"job {j}"]["gen_s"])
             for j, g in gens.items() if g["calls"] and f"job {j}" in pooled]
    load_s = max(loads) if loads else 120.0
    pp = min(s["pp_tok"] / s["pp_s"] for s in pooled.values())
    measured = pooled[max(k for k in pooled if k.startswith("job"))]
    tg_measured = measured["gen_tok"] / measured["gen_s"]
    one_out = sum(out_tok[m] for m in todo1)
    one_in = sum(bud[m]["in"] for m in todo1)
    arm_out = sum(out_tok[m] for m in arm_mods) * 2
    arm_in = sum(bud[m]["arms_in"] for m in arm_mods) * 2
    md += ["", "## Remaining work (inputs to --time)", "",
           f"- one-shot: {len(todo1)} modules left ({', '.join(todo1)}); output tokens {one_out} "
           f"(HPC records where finished, otherwise golden-size estimates from PREDEPLOY_BUDGET.md), input {one_in}",
           f"- arms: {ARM_RUNS - arms_done} of {ARM_RUNS} runs left (smoke finished {arms_done}); LLM calls per run "
           f"from the smoke log: {smoke} -> mean {per_run:.2f} (worst case 6)",
           f"- per arm call: output = the module's one-shot output size, input = arms prompt (PREDEPLOY_BUDGET.md); "
           f"summed over the remaining runs at 1 call each: output {arm_out:.0f}, input {arm_in:.0f} tokens",
           f"- tool time per call {tool_s:.1f} s (Phase 3: metrics wall per call minus serve-log LLM time per call); "
           f"prompt rate {pp:.0f} tok/s (slowest measured); model load {load_s:.0f} s per process, 2 processes",
           "", "| generation tok/s | one-shot h | arms h (expected) | arms h (worst, 6 calls) | total h expected | "
           "x 1.5 |", "|---|---|---|---|---|---|"]
    rec_time = None
    for tg in (tg_measured, *RATES):
        one = one_out / tg + one_in / pp + len(todo1) * tool_s
        arms1 = arm_out / tg + arm_in / pp + (ARM_RUNS - arms_done) * tool_s
        exp, worst = arms1 * per_run, arms1 * 6
        tot = (one + exp + 2 * load_s) / 3600
        label = f"{tg:.2f} (measured, job {max(k for k in pooled if k.startswith('job'))[4:]}, before the fix)" \
            if tg == tg_measured else f"{tg:.0f}"
        md.append(f"| {label} | {one / 3600:.2f} | {exp / 3600:.2f} | {worst / 3600:.2f} | {tot:.2f} | "
                  f"{tot * MARGIN:.2f} |")
        if tg == RATES[0]:
            rec_time = int(-(-tot * MARGIN // 1))
    md += ["", f"Formula per row: one-shot = out/tg + in/pp + calls x tool; arms = (out/tg + in/pp + runs x tool) x "
           f"calls per run; total = one-shot + arms + 2 x load; x {MARGIN} margin.",
           f"--time is set for the slowest speed the job accepts (8 tok/s; below it the first call exits 3): "
           f"--time={rec_time}:00:00. A run that ends early is resumed by resubmitting."]
    out = os.path.join(STUDY, "reports", "SPEED.md")
    open(out, "w", encoding="utf-8", newline="\n").write("\n".join(md) + "\n")
    print("\n".join(md))
    print(f"wrote {out}")
    return 0


def budget_tool_s() -> float:
    gin = [budget.dur(l.split("|")[2]) for l in open(budget.P3_32B_SERVE_LOG, encoding="utf-8", errors="replace")
           if '"/api/chat"' in l and "| 200 |" in l]
    ms = [json.load(open(p)) for p in glob.glob(os.path.join(budget.P3_32B_RESULTS, "*", "*", "rep*", "metrics.json"))]
    return sum(m["wall_s"] for m in ms) / sum(m["llm_calls"] for m in ms) - statistics.mean(gin)


if __name__ == "__main__":
    sys.exit(main())
