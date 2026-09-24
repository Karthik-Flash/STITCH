#!/usr/bin/env python3
"""
summarize_p3.py -- turn results/phase3/**/metrics.json (+ compose_results.jsonl) into the Phase 3 tables.

Discipline carried over from Phases 1-2 (reSTITCH.md Part 1.2):
  * every claim cell reports N and semantic_fired (sf) in the same row
  * an interpreter "win" is a clean_pass replicate WITH sf=1; clean passes with sf=0 are reported separately
  * Wilson 95% CIs on every rate; errors are counted, never dropped silently

Usage: python phase3/runner/summarize_p3.py --results results/phase3 [--compose results/phase3/compose_results.jsonl] --out results/phase3/SUMMARY.md
"""
import argparse
import glob
import json
import math
import os
from collections import defaultdict

CONDS = ["baseline", "raw_adv", "sem_adv_v2", "sem_adv_v3", "sem_esc_restart_v3"]


def wilson(k, n, z=1.96):
    if n == 0:
        return (float("nan"), float("nan"))
    p = k / n
    d = 1 + z * z / n
    c = (p + z * z / (2 * n)) / d
    h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
    return (max(0, c - h), min(1, c + h))


def fmt(k, n):
    if n == 0:
        return "--"
    lo, hi = wilson(k, n)
    return f"{k}/{n} ({100*k/n:.0f}%, {100*lo:.0f}-{100*hi:.0f})"


def load(results):
    runs, errs = [], []
    for f in glob.glob(os.path.join(results, "**", "metrics.json"), recursive=True):
        runs.append(json.load(open(f)))
    for f in glob.glob(os.path.join(results, "**", "error.json"), recursive=True):
        errs.append(json.load(open(f)))
    return runs, errs


def table(rows, header):
    out = ["| " + " | ".join(header) + " |", "|" + "---|" * len(header)]
    out += ["| " + " | ".join(str(c) for c in r) + " |" for r in rows]
    return "\n".join(out)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--results", required=True)
    ap.add_argument("--compose")
    ap.add_argument("--out")
    a = ap.parse_args()
    runs, errs = load(a.results)
    tasks_meta = {}
    for m in glob.glob(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "tasks", "*", "meta.json")):
        j = json.load(open(m)); tasks_meta[j["top"]] = j
    conds = [c for c in CONDS if any(r["condition"] == c for r in runs)]
    md = [f"# Phase 3 summary\n\nruns: {len(runs)}   errors: {len(errs)}   models: "
          f"{sorted({r['model'] for r in runs})}\n"]
    if runs:
        md.append(f"interpreter base sha256 (LF): {sorted({r['base_interp_sha256_lf'] for r in runs})}   "
                  f"v3: {sorted({r['interp_v3_version'] for r in runs})}\n")

    # T1: headline by condition
    rows = []
    for c in conds:
        R = [r for r in runs if r["condition"] == c]
        n = len(R)
        rows.append([c, n, fmt(sum(r["func_pass"] for r in R), n), fmt(sum(r["clean_pass"] for r in R), n),
                     fmt(sum(r["silent_structural_pass"] for r in R), n),
                     fmt(sum(r["clean_pass"] and r["semantic_fired"] for r in R), n),
                     sum(r["semantic_fired"] for r in R),
                     f"{sum(r['tool_feedback_iters'] for r in R)/max(n,1):.2f}",
                     f"{sum(r['tokens_in']+r['tokens_out'] for r in R)/max(n,1):.0f}"])
    md.append("## T1. Pooled by condition\n\n" + table(rows, ["condition", "N", "func_pass", "clean_pass (primary)",
              "silent structural pass", "clean_pass AND sf=1", "sf runs", "tool-feedback iters/run", "tokens/run"]))

    # T2: sim-silent vs sim-visible
    rows = []
    for c in conds:
        for silent in (True, False):
            R = [r for r in runs if r["condition"] == c and tasks_meta.get(r["task"], {}).get("sim_silent") == silent]
            rows.append([c, "sim-silent" if silent else "sim-visible", len(R), fmt(sum(r["clean_pass"] for r in R), len(R)),
                         fmt(sum(r["silent_structural_pass"] for r in R), len(R)), sum(r["semantic_fired"] for r in R)])
    md.append("\n\n## T2. Sim-silent vs sim-visible defects\n\n" + table(rows, ["condition", "task type", "N",
              "clean_pass", "silent structural pass", "sf runs"]))

    # T3: per task x condition (clean k/n, sf count)
    rows = []
    for t in sorted({r["task"] for r in runs}):
        row = [t, "/".join(tasks_meta.get(t, {}).get("defect_classes", []))[:40]]
        for c in conds:
            R = [r for r in runs if r["task"] == t and r["condition"] == c]
            row.append(f"{sum(r['clean_pass'] for r in R)}/{len(R)} sf{sum(r['semantic_fired'] for r in R)}" if R else "--")
        rows.append(row)
    md.append("\n\n## T3. clean_pass per task (k/N, sf = runs where the interpreter fired)\n\n" +
              table(rows, ["task", "defect"] + conds))

    # T4: v2 vs v3 attribution, paired by (model, task, rep)
    idx = {(r["model"], r["task"], r["rep"], r["condition"]): r for r in runs}
    pairs = [(idx[k2], idx[(k2[0], k2[1], k2[2], "sem_adv_v3")]) for k2 in idx
             if k2[3] == "sem_adv_v2" and (k2[0], k2[1], k2[2], "sem_adv_v3") in idx]
    if pairs:
        both = sum(a["clean_pass"] and b["clean_pass"] for a, b in pairs)
        v3only = [b for a, b in pairs if b["clean_pass"] and not a["clean_pass"]]
        v2only = [a for a, b in pairs if a["clean_pass"] and not b["clean_pass"]]
        md.append("\n\n## T4. v2 vs v3 (same model/task/rep; NOTE: independent draws, not replays)\n\n"
                  f"pairs={len(pairs)}  both clean={both}  v3-only={len(v3only)} (of which sf=1: "
                  f"{sum(b['semantic_fired'] for b in v3only)})  v2-only={len(v2only)} (of which sf=1: "
                  f"{sum(a['semantic_fired'] for a in v2only)})\n\nv3-only by class fired: " +
                  json.dumps(dict(sorted(_count(b["classes_fired"] for b in v3only).items()))))
        # interpreter reachability: did v2 even fire on the task's defect?
        rows = []
        for t in sorted({a["task"] for a, _ in pairs}):
            P = [(a, b) for a, b in pairs if a["task"] == t]
            rows.append([t, f"{sum(a['semantic_fired'] for a, _ in P)}/{len(P)}", f"{sum(b['semantic_fired'] for _, b in P)}/{len(P)}",
                         f"{sum(a['clean_pass'] for a, _ in P)}/{len(P)}", f"{sum(b['clean_pass'] for _, b in P)}/{len(P)}"])
        md.append("\n\n" + table(rows, ["task", "v2 fired", "v3 fired", "v2 clean", "v3 clean"]))

    # T5: per model x condition
    rows = []
    for mdl in sorted({r["model"] for r in runs}):
        rows.append([mdl] + [fmt(sum(r["clean_pass"] for r in runs if r["model"] == mdl and r["condition"] == c),
                                 sum(1 for r in runs if r["model"] == mdl and r["condition"] == c)) for c in conds])
    md.append("\n\n## T5. clean_pass by model\n\n" + table(rows, ["model"] + conds))

    # T6: latch counts before/after
    rows = []
    for c in conds:
        R = [r for r in runs if r["condition"] == c and r["latch_count_before"]]
        if R:
            rows.append([c, len(R), sum(r["latch_count_before"] for r in R),
                         sum((r["latch_count_after"] or 0) for r in R),
                         sum(1 for r in R if r["latch_count_after"] == 0 and r["final_yosys_ok"])])
    md.append("\n\n## T6. Latch events on latch-bearing tasks (sum over runs)\n\n" +
              table(rows, ["condition", "runs", "latch_count_before", "latch_count_after", "runs ending latch-free"]))

    # T7: composition
    if a.compose and os.path.exists(a.compose):
        C = [json.loads(l) for l in open(a.compose) if l.strip()]
        rows = []
        for d in sorted({c["design"] for c in C}):
            for c in conds:
                X = [x for x in C if x["design"] == d and x.get("condition") == c]
                if X:
                    cells = [x.get("latch_cells_excl_crashed") for x in X if x.get("latch_cells_excl_crashed") is not None]
                    rows.append([d, c, len(X), fmt(sum(x["top_level_synthesis_pass"] for x in X), len(X)),
                                 f"{sum(cells)/len(cells):.0f}" if cells else "--"])
        md.append("\n\n## T7. Composition: repaired leaves spliced into the real designs\n\n"
                  "Bounds (phase3/evidence/compose_bounds.jsonl): mesh2x2 crash/2880 -> PASS/0; mesh3x3 crash/6480 -> PASS/0; "
                  "mpsoc crash/269 -> PASS/122 (remaining cells are in modules outside the task set).\n\n" +
                  table(rows, ["design", "condition", "groups (model x rep)", "top_level_synthesis_pass", "mean latch cells"]))
    if errs:
        md.append("\n\n## Errors\n\n" + "\n".join(f"- {e.get('model')} {e.get('condition')} {e.get('task')} rep{e.get('rep')}: "
                                                  f"{e.get('error','')[:120]}" for e in errs))
    text = "\n".join(md) + "\n"
    print(text)
    if a.out:
        open(a.out, "w").write(text)


def _count(lists):
    d = defaultdict(int)
    for L in lists:
        for x in L:
            d[x] += 1
    return d


if __name__ == "__main__":
    main()
