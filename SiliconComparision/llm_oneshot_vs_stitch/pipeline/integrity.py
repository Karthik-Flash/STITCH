#!/usr/bin/env python3
"""Integrity of the extracted HPC results (no regeneration). Writes reports/INTEGRITY.md.

One-shot: 34 records, status ok, outputs/oneshot/<m>.v sha256 == record output_sha256. The job that produced each
record = the job whose gen log has the matching one-shot line (same tokens in/out and wall seconds).
Arms: 68 runs with metrics.json, no error.json; final_candidate (cluster path mapped to local) equals
outputs/<arm>/<m>.v. Job = the run's provenance node -> run manifest (job id, GPU, deployed commit).
Usage: python pipeline/integrity.py
"""
from __future__ import annotations

import collections
import glob
import json
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import analysis_common as A  # noqa: E402

ARCHIVE_SHA = {"2x2": "93c24d50a0c7aa7e8733c60dbb1096df719828933e55d5a60c5d4954c2c10ace",
               "mesh3x3": "7cb51ed4bd3ca5fbf5215190f2752f3df72cca5d2e2185dedf91d064c5976aa3",   # one archive for
               "ni": "7cb51ed4bd3ca5fbf5215190f2752f3df72cca5d2e2185dedf91d064c5976aa3"}[A.NAME]  # mesh3x3 + ni


def gen_log_lines() -> dict:
    """job -> {module: (tokens_in, tokens_out, wall_s)} from the real (non-mock) one-shot lines of each gen log."""
    out = {}
    for p in sorted(glob.glob(os.path.join(A.LOGS, "gen_*.log"))):
        job = re.search(r"gen_(\d+)\.log", p).group(1)
        out[job] = {m: (int(i), int(o), float(s)) for m, i, o, d, s in re.findall(
            r"^(\w+)\s+tokens in/out (\d+)/(\d+) done_reason (\S+) ([\d.]+)s", open(p, errors="replace").read(), re.M)
            if d != "None"}
    return out


def main() -> int:
    mods = A.modules()
    man, nodes, logs = A.manifests(), A.node_job(), gen_log_lines()
    problems, one_rows, per_job = [], [], collections.Counter()
    for m in mods:
        rp = os.path.join(A.STUDY, "runs", "oneshot", m, "record.json")
        out = A.final_file("oneshot", m)
        if not os.path.exists(rp):
            problems.append(f"one-shot {m}: no record.json")
            continue
        r = json.load(open(rp))
        ok_sha = os.path.exists(out) and A.sha(out) == r.get("output_sha256")
        jobs = [j for j, d in logs.items() if m in d and d[m] == (r["tokens_in"], r["tokens_out"], r["wall_s"])]
        if not logs and len(man) == 1:   # gen log not in the archive (mesh3x3, ni): the study's only run manifest
            jobs = list(man)
        job = jobs[-1] if jobs else "?"
        gpu = man[job]["gpu"][0]["name"] if job in man else "?"
        commit = man[job]["git_commit"][:7] if job in man else "?"
        if r.get("status", "ok") != "ok" or not ok_sha or job == "?":
            problems.append(f"one-shot {m}: status={r.get('status', 'ok (no field)')} sha_match={ok_sha} job={job}")
        per_job[("one-shot", job, gpu, commit)] += 1
        one_rows.append(f"| {m} | {r.get('status', 'ok (no field)')} | {ok_sha} | {r['tokens_out']} | "
                        f"{r.get('done_reason')} | {job} | {gpu} | {commit} |")
    arm_rows = []
    for arm in ("simloop", "stitch"):
        for m in mods:
            rd = A.run_dir(arm, m)
            met = A.metrics(arm, m)
            if met is None:
                problems.append(f"{arm} {m}: no metrics.json" + (" (error.json present)" if os.path.exists(
                    os.path.join(rd, "error.json")) else ""))
                continue
            node = met["provenance"]["node"].split(".")[0]
            job, gpu, commit = nodes.get(node, ("?", "?", "?"))
            fin = A.local(met["final_candidate"])
            same = os.path.exists(fin) and A.sha(fin) == A.sha(A.final_file(arm, m))
            metas = [os.path.exists(os.path.join(d, "llm_meta.json")) for d in A.iter_dirs(arm, m)[1:]]
            if not same or job == "?" or len(metas) != met["llm_calls"] or not all(metas):
                problems.append(f"{arm} {m}: final_matches_output={same} job={job} "
                                f"llm_meta {sum(metas)}/{met['llm_calls']}")
            failed = glob.glob(rd + ".failed_*")
            per_job[(arm, job, gpu, commit[:7])] += 1
            arm_rows.append(f"| {m} | {arm} | {met['llm_calls']} | {met['stop_reason']} | {same} | {job} | {gpu} | "
                            f"{commit[:7]} | {len(failed)} |")
    md = ["# Integrity of the HPC results (pipeline/integrity.py)", "",
          f"Archive extracted into the study folder: sha256 `{ARCHIVE_SHA}` (excludes *.vvp/*.vcd; value as "
          "recorded at download, the archive itself is not in the repository).", "",
          *([] if logs else ["No gen log in hpc_logs/ (the job log stayed on the cluster): each one-shot record is "
                             "attributed to the study's only run manifest. The manifest's git_commit is `UNKNOWN`: "
                             "preflight.py looked for DEPLOYED_COMMIT.txt in the study sub-folder instead of the study "
                             "root (fixed after this job). The deployed commit, 0fa68c9, was checked on the cluster "
                             "(DEPLOYED_COMMIT.txt, reported by the user).", ""]),
          "## Summary", "",
          f"- one-shot records: {sum(os.path.exists(os.path.join(A.STUDY, 'runs', 'oneshot', m, 'record.json')) for m in mods)} "
          f"of {len(mods)}; arm runs with metrics.json: {len(arm_rows)} of {2 * len(mods)}",
          f"- problems: {len(problems)}" + ("" if problems else " (nothing missing, errored or mismatched)")]
    md += [f"  - {p}" for p in problems]
    md += ["", "| part | job | GPU | deployed commit | count |", "|---|---|---|---|---|"]
    md += [f"| {k[0]} | {k[1]} | {k[2]} | {k[3]} | {v} |" for k, v in sorted(per_job.items())]
    md += ["", "Jobs (run manifests):", ""]
    md += [f"- {j}: {d['hostname']}, {d['gpu'][0]['name']}, commit {d['git_commit'][:7]}, GEN_TASKS {d['gen_tasks']}, "
           f"threads {d.get('cpu_threads') or 'not set (before 62b4131)'}" for j, d in sorted(man.items())]
    # The runner copies the task testbenches into every iteration dir; those copies are git-ignored, so check them here.
    tb_same, tb_diff = 0, []
    for arm in ("simloop", "stitch"):
        for m in A.modules():
            for d in A.iter_dirs(arm, m):
                for f in glob.glob(os.path.join(d, "tb*.v")):
                    t = os.path.join(A.STUDY, "tasks", m, os.path.basename(f))
                    if os.path.exists(t) and A.sha(t) == A.sha(f):
                        tb_same += 1
                    else:
                        tb_diff.append(A.rel(f))
    problems += [f"iteration tb copy differs from tasks/: {p}" for p in tb_diff]
    md += ["", f"Iteration testbench copies (runs/arms/results/**/iter*/tb*.v, git-ignored): {tb_same} byte-identical "
           f"to tasks/<m>/, {len(tb_diff)} differ."]
    md += ["", "## One-shot records", "", "| module | status | output sha256 = record | tokens out | done_reason | "
           "job | GPU | commit |", "|---|---|---|---|---|---|---|---|", *one_rows,
           "", "## Arm runs", "", "| module | arm | LLM calls | stop | final = outputs/<arm> | job | GPU | commit | "
           "earlier failed attempts |", "|---|---|---|---|---|---|---|---|---|", *arm_rows]
    A.write_report("INTEGRITY.md", md)
    print("\n".join(md[:20 + len(problems)]))
    return 0 if not problems else 1


if __name__ == "__main__":
    sys.exit(main())
