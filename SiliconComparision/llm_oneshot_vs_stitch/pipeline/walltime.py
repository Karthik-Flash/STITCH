#!/usr/bin/env python3
"""--time for one gen_job.slurm run over several studies (laptop only; needs iverilog, yosys, verilator and the
2x2 HPC logs in hpc_logs/). Writes <study>/reports/WALLTIME.md for every study given.

Per NEW module (tasks/ of the study) and LLM call: output tokens / generation rate + input tokens / prompt rate +
tool time. Tokens from reports/PREDEPLOY_BUDGET.md (one-shot: prompt and golden-size answer; arm calls: the arms
prompt and the same answer). Worst case: 6 calls per arm run, 2 arm runs per module. Tool time per call = the
Phase 3 mean (speed.budget_tool_s) or, if larger, the measured p3_eval of the golden in its task (loop tb, lint,
synth); plus 3 sign-off simulations per module (summarize.py scores 3 finals). Generation rate: the median per call of
2x2 job 424063 (reports/RUN_HISTORY.md, 67.9 tok/s); prompt rate: that job's serve log. Model load 100 s per
process, 2 processes per study. Total x 1.5, capped at the partition's 24 h.
Usage: python pipeline/walltime.py mesh3x3 ni
"""
from __future__ import annotations

import json
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
GEN_TOK_S, MARGIN, CAP_H, LOAD_S, CALLS, ARM_RUNS = 67.9, 1.5, 24, 100.0, 6, 2
SERVE_LOG = os.path.join(ROOT, "hpc_logs", "ollama_serve_424063.log")


def measure(study: str) -> dict:
    """Per NEW module of the study: tokens from PREDEPLOY_BUDGET.md and measured tool seconds (child process, so
    --study is applied before p3_bridge is imported)."""
    code = ("import sys, os, json, time, tempfile; sys.path.insert(0, sys.argv[1]); import p3_bridge as B; out = {}\n"
            "for m in sorted(os.listdir(os.path.join(B.STUDY, 'tasks'))):\n"
            "  td = os.path.join(B.STUDY, 'tasks', m); top = json.load(open(os.path.join(td, 'meta.json')))['top']\n"
            "  t = time.time(); B.evaluate(os.path.join(td, 'golden.v'), td, top); ev = time.time() - t\n"
            "  with tempfile.TemporaryDirectory() as wd:\n"
            "    t = time.time(); B.simulate_with(os.path.join(td, 'golden.v'), os.path.join(td, 'tb_signoff.v'), td, wd)\n"
            "    so = time.time() - t\n"
            "  out[m] = [ev, so]\n"
            "print(json.dumps(out))")
    p = subprocess.run([sys.executable, "-c", code, HERE, "--study", study], capture_output=True, text=True,
                       check=True)
    secs = json.loads(p.stdout.strip().splitlines()[-1])
    bud = {}
    for l in open(os.path.join(ROOT, study, "reports", "PREDEPLOY_BUDGET.md"), encoding="utf-8"):
        c = [x.strip() for x in l.split("|")]
        if len(c) > 7 and c[1] in secs and c[2].isdigit():
            bud[c[1]] = {"in": int(c[2]), "out": int(c[3]), "arms_in": int(c[5])}
    return {m: {**bud[m], "eval_s": secs[m][0], "signoff_s": secs[m][1]} for m in secs}


def main() -> int:
    studies = sys.argv[1:] or ["mesh3x3", "ni"]
    sys.path.insert(0, HERE)
    import speed  # noqa: E402  (imports make_tasks -> studies: 2x2 by default, only its helpers are used)
    s = speed.serve_stats(SERVE_LOG)
    pp = s["pp_tok"] / s["pp_s"]
    p3_tool = speed.budget_tool_s()
    rows, total = [], 0.0
    for st in studies:
        for m, b in measure(st).items():
            tool = max(p3_tool, b["eval_s"])
            one = b["out"] / GEN_TOK_S + b["in"] / pp + tool
            arms = ARM_RUNS * CALLS * (b["out"] / GEN_TOK_S + b["arms_in"] / pp + tool)
            sec = one + arms + 3 * b["signoff_s"]
            total += sec
            rows.append(f"| {st} | {m} | {b['in']} / {b['out']} | {b['arms_in']} | {b['eval_s']:.1f} | "
                        f"{b['signoff_s']:.1f} | {one / 3600:.2f} | {arms / 3600:.2f} | {sec / 3600:.2f} |")
    total += 2 * len(studies) * LOAD_S
    hours = total / 3600
    want = int(-(-hours * MARGIN // 1))
    md = ["# Wall time for STUDIES=\"" + " ".join(studies) + "\" (pipeline/walltime.py)", "",
          f"Generation {GEN_TOK_S} tok/s (2x2 job 424063, median per call, reports/RUN_HISTORY.md); prompt "
          f"{pp:.0f} tok/s (job 424063 serve log); Phase 3 tool time per call {p3_tool:.1f} s; model load "
          f"{LOAD_S:.0f} s per process, {2 * len(studies)} processes. Worst case: {CALLS} LLM calls in each of the "
          f"{ARM_RUNS} arm runs per module. eval = measured p3_eval of the golden in its task (tool time per call is "
          "the larger of eval and the Phase 3 mean); signoff = one tb_signoff.v simulation (3 per module in "
          "summarize.py).", "",
          "| study | module | one-shot in / out tokens | arms in tokens | eval s | signoff s | one-shot h | arms h "
          "(worst) | total h |", "|---|---|---|---|---|---|---|---|---|", *rows, "",
          f"Total (worst case, loads included): {hours:.2f} h; x {MARGIN} = {hours * MARGIN:.2f} h; "
          f"--time={min(want, CAP_H)}:00:00" + (f" (capped at {CAP_H} h)" if want > CAP_H else "") + ".",
          "A run that ends early is resumed by resubmitting the same command."]
    for st in studies:
        out = os.path.join(ROOT, st, "reports", "WALLTIME.md")
        open(out, "w", encoding="utf-8", newline="\n").write("\n".join(md) + "\n")
        print(f"wrote {out}")
    print("\n".join(md))
    return 0


if __name__ == "__main__":
    sys.exit(main())
