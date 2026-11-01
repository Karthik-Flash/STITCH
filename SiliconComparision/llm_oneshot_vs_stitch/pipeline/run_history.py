#!/usr/bin/env python3
"""Per-job run history from the cluster logs (hpc_logs/, git-ignored). Writes reports/RUN_HISTORY.md.

Per job: node, GPU, llama-server threads, LLM calls and generation tok/s (serve log, pipeline/speed.py parsers),
first and last gen-log timestamps (node-local clock) and their difference, and whether the job printed JOB DONE.
Usage: python pipeline/run_history.py
"""
from __future__ import annotations

import datetime as dt
import glob
import json
import os
import re
import statistics
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import analysis_common as A  # noqa: E402
import speed  # noqa: E402

STAMP = re.compile(r"^== \w{3} (\w{3} +\d+ [\d:]+) (\w+) (\d{4})", re.M)


# The job log stays on the cluster for mesh3x3 and ni; its sacct line, as reported by the user.
SACCT = {"426786": "exit 0, elapsed 01:08:57 (sacct, reported by the user)"}


def from_records() -> list[str]:
    """No hpc_logs/ (mesh3x3, ni): rates from Ollama's own eval_count / eval_duration of every LLM call of this
    study (one-shot record.json llm_meta, arm iter*/llm_meta.json), node and threads from the run manifest."""
    rates = []
    for m in A.modules():
        r = json.load(open(os.path.join(A.STUDY, "runs", "oneshot", m, "record.json")))["llm_meta"]
        rates.append((r["eval_count"], r["eval_duration"] / 1e9))
        for arm in ("simloop", "stitch"):
            for d in A.iter_dirs(arm, m)[1:]:
                j = json.load(open(os.path.join(d, "llm_meta.json")))
                rates.append((j["eval_count"], j["eval_duration"] / 1e9))
    per = [n / s for n, s in rates if s > 0 and n >= 20]
    md = ["# Run history (pipeline/run_history.py)", "",
          "The job log and serve log stayed on the cluster (not in the results archive), so the rates come from "
          "Ollama's own counters of every LLM call of this study (eval_count / eval_duration: generation only, prompt "
          "evaluation and model load excluded). mesh3x3 and ni ran in the same job.", "",
          "| job | node | GPU | llama-server threads | calls (this study) | tok/s pooled | tok/s range per call | "
          "job end |", "|---|---|---|---|---|---|---|---|"]
    for j, d in sorted(A.manifests().items()):
        md.append(f"| {j} | {d['hostname'].split('.')[0]} | {d['gpu'][0]['name']} | "
                  f"{d['cpu_threads']['LLAMA_ARG_THREADS']} | {len(rates)} | "
                  f"{sum(n for n, _ in rates) / sum(s for _, s in rates):.2f} | {min(per):.1f}-{max(per):.1f} (median "
                  f"{statistics.median(per):.1f}) | {SACCT.get(j, '?')} |")
    return md


def main() -> int:
    if not glob.glob(os.path.join(A.LOGS, "gen_*.log")):
        md = from_records()
        A.write_report("RUN_HISTORY.md", md)
        print("\n".join(md))
        return 0
    md = ["# Run history (pipeline/run_history.py)", "",
          "From hpc_logs/ (gen_<job>.log, ollama_serve_<job>.log). Times are the node's local clock (not comparable "
          "across nodes); a job without JOB DONE ended after its last stamp (no end time). tok/s = generation rate "
          "from the serve log (prompt evaluation and model load excluded).", "",
          "| job | node | GPU | llama-server threads | calls | tok/s pooled | tok/s range per call | first / last `==` stamp "
          "| time between stamps | JOB DONE |", "|---|---|---|---|---|---|---|---|---|---|"]
    for p in sorted(glob.glob(os.path.join(A.LOGS, "gen_*.log"))):
        job = re.search(r"(\d+)", os.path.basename(p)).group(1)
        text = open(p, encoding="utf-8", errors="replace").read()
        node = re.search(r"node (\S+)", text).group(1)
        st = [dt.datetime.strptime(f"{d} {y}", "%b %d %H:%M:%S %Y") for d, _, y in STAMP.findall(text)]
        tz = STAMP.findall(text)[0][1]
        s = speed.serve_stats(os.path.join(A.LOGS, f"ollama_serve_{job}.log"))
        txt = open(os.path.join(A.LOGS, f"ollama_serve_{job}.log"), encoding="utf-8", errors="replace").read()
        rates = [n / (ms / 1e3) for ms, n in ((float(a), int(b)) for a, b in
                 re.findall(r"\|\s+eval time =\s+([\d.]+) ms /\s+(\d+) tokens", txt)) if ms > 0 and n >= 20]
        md.append(f"| {job} | {node} | {speed.gen_log(p)['gpu']} | {s['n_threads']} | {s['calls']} | "
                  f"{s['gen_tok'] / s['gen_s']:.2f} | {min(rates):.1f}-{max(rates):.1f} (median "
                  f"{statistics.median(rates):.1f}) | {st[0]:%H:%M:%S} / {st[-1]:%H:%M:%S} {tz} | {st[-1] - st[0]} | "
                  f"{'yes' if 'JOB DONE' in text else 'no'} |")
    A.write_report("RUN_HISTORY.md", md)
    print("\n".join(md))
    return 0


if __name__ == "__main__":
    sys.exit(main())
