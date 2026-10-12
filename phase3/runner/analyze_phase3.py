#!/usr/bin/env python3
"""
analyze_phase3.py -- Phase 3 analysis. Every number in phase3/evidence/<run>/PHASE3_RESULTS.md comes from this script.

Source of truth: the metrics.json files under --results (one per run). master_log.json is NOT used for results; it is
read only to confirm that each error.json was superseded by a later successful re-run of the same cell.

Conventions
  * Wilson 95% CI and N on every rate.
  * "sf" = semantic_fired. An interpreter win = clean_pass AND semantic_fired in the same run (sem_* conditions only).
  * Paired contrasts match runs on (model, task, rep). Runs are INDEPENDENT DRAWS (no shared seed), so the matching is
    a stratification, not a replay. Two uncertainty views are reported:
      - exact McNemar/sign p on discordant pairs: run-level, valid for "these 66 (model, task) cells";
      - cell-cluster bootstrap CI + sign-flip p over (model, task) cells: treats cells as the sampling unit, so it
        respects the fact that the 3 replicates in a cell are correlated.
  * Bootstrap/permutation are seeded (SEED) and independent of call order, so reruns reproduce byte for byte.

Usage (repo root):  python phase3/runner/analyze_phase3.py [--results phase3/results/<run>]
Outputs go to phase3/evidence/<run>/ (PHASE3_RESULTS.md, phase3_analysis.json, phase3_tables.md, phase3_regressions.csv,
figures/). A new run directory therefore never overwrites an earlier run's evidence.
"""
import argparse
import csv
import glob
import json
import math
import os
import re
import zlib
from collections import Counter, defaultdict

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
P3 = os.path.dirname(HERE)
CONDS = ["baseline", "raw_adv", "sem_adv_v2", "sem_adv_v3", "sem_esc_restart_v3"]
MODELS = ["llama3.2:3b", "gemma3:4b", "deepseek-coder:6.7b", "qwen2.5-coder:7b", "llama3.1:latest", "qwen2.5-coder:14b"]
SEED, BOOT, PERM = 20260925, 10000, 20000


# ----------------------------------------------------------------------------- statistics
def wilson(k, n, z=1.96):
    if n == 0:
        return (float("nan"), float("nan"))
    p = k / n
    d = 1 + z * z / n
    c = (p + z * z / (2 * n)) / d
    h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
    return max(0.0, c - h), min(1.0, c + h)


def rate(k, n):
    lo, hi = wilson(k, n)
    if n == 0:
        return {"k": k, "n": n, "pct": float("nan"), "lo": float("nan"), "hi": float("nan"), "fmt": "--"}
    return {"k": k, "n": n, "pct": 100 * k / n, "lo": 100 * lo, "hi": 100 * hi,
            "fmt": f"{k}/{n} ({100*k/n:.0f}%, {100*lo:.0f}–{100*hi:.0f})"}


def mcnemar_p(b, c):
    n = b + c
    if n == 0:
        return 1.0
    return min(1.0, 2 * sum(math.comb(n, i) for i in range(min(b, c) + 1)) / 2 ** n)


def holm(ps):
    order = sorted(range(len(ps)), key=lambda i: ps[i])
    adj, run = [0.0] * len(ps), 0.0
    for rank, i in enumerate(order):
        run = max(run, (len(ps) - rank) * ps[i])
        adj[i] = min(1.0, run)
    return adj


def _rng(label):
    return np.random.default_rng([SEED, zlib.crc32(label.encode())])


def boot_ci(vals, label):
    v = np.asarray(vals, float)
    if len(v) == 0:
        return float("nan"), float("nan")
    m = v[_rng("ci:" + label).integers(0, len(v), (BOOT, len(v)))].mean(1)
    return float(np.percentile(m, 2.5)), float(np.percentile(m, 97.5))


def signflip_p(d, label):
    d = np.asarray(d, float)
    if not np.any(d):
        return 1.0
    s = _rng("p:" + label).choice([-1.0, 1.0], size=(PERM, len(d)))
    return float((1 + np.sum(np.abs((s * d).mean(1)) >= abs(d.mean()) - 1e-12)) / (PERM + 1))


def fp(p):
    return "<0.001" if p < 0.001 else f"{p:.3f}"


def sg(x, nd=1):
    return f"{x:+.{nd}f}"


def slug(s):
    return re.sub(r"[^A-Za-z0-9]+", "_", s).strip("_")


# ----------------------------------------------------------------------------- load
def load(results, tasks_dir):
    runs = []
    for f in sorted(glob.glob(os.path.join(results, "*", "*", "*", "rep*", "metrics.json"))):
        runs.append(json.load(open(f)))
        runs[-1]["_dir"] = os.path.dirname(f)
    meta = {}
    for f in glob.glob(os.path.join(tasks_dir, "*", "meta.json")):
        j = json.load(open(f))
        meta[j["top"]] = j
    for r in runs:
        m = meta[r["task"]]
        pi = r["per_iter"]
        fin = pi[-1]
        assert fin["clean_pass"] == r["clean_pass"] and fin["func_pass"] == r["func_pass"]
        r["silent"] = bool(m["sim_silent"])
        r["cls"] = "+".join(m["expected_v3_classes"])
        r["tokens"] = r["tokens_in"] + r["tokens_out"]
        r["sf_clean"] = bool(r["clean_pass"] and r["semantic_fired"])
        r["escalated"] = r["escalated_at"] is not None
        r["first_clean"] = next((p["iter"] for p in pi if p["clean_pass"]), None)
        r["func_ever"] = any(p["func_pass"] for p in pi)
        r["func_regress"] = r["func_ever"] and not r["func_pass"]
        r["broke_input"] = bool(r["input_func_pass"]) and not r["func_pass"]
        if not fin["compile_ok"]:
            r["final_cat"] = "compile_error"
        elif fin["sim_outcome"] != "PASS":
            r["final_cat"] = "sim_fail"
        elif fin["clean_pass"]:
            r["final_cat"] = "clean"
        else:
            r["final_cat"] = "silent_structural"
        r["traj"] = "".join("C" if p["clean_pass"] else ("F" if p["func_pass"] else "x") for p in pi)
    return runs, meta


def md_table(header, rows):
    out = ["| " + " | ".join(header) + " |", "|" + "---|" * len(header)]
    out += ["| " + " | ".join(str(c) for c in r) + " |" for r in rows]
    return "\n".join(out)


# ----------------------------------------------------------------------------- analysis
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--results", default=os.path.join(P3, "results", "phase3_run"))
    ap.add_argument("--tasks", default=os.path.join(P3, "tasks"))
    ap.add_argument("--bounds", default=os.path.join(P3, "evidence", "compose_bounds.jsonl"))
    ap.add_argument("--evidence", default=None, help="output dir; default phase3/evidence/<results dir name>/")
    ap.add_argument("--templates", default=os.path.join(HERE, "templates"))
    ap.add_argument("--no-figs", action="store_true")
    ap.add_argument("--more-results", nargs="*", default=[], help="--final/--score-signoff: further run dirs")
    ap.add_argument("--final", action="store_true", help="pre-registered final-batch analysis (PREREG_FINAL.md)")
    ap.add_argument("--posthoc-signoff", action="store_true", help="POSTHOC_SIGNOFF.md for the --results run")
    ap.add_argument("--score-signoff", action="store_true", help="simulate candidates vs tb_signoff.v into the cache")
    a = ap.parse_args()
    if a.final or a.posthoc_signoff or a.score_signoff:
        return final_main(a)
    a.evidence = a.evidence or os.path.join(P3, "evidence", os.path.basename(os.path.normpath(a.results)))
    os.makedirs(a.evidence, exist_ok=True)

    runs, meta = load(a.results, a.tasks)
    IDX = {(r["model"], r["task"], r["rep"], r["condition"]): r for r in runs}
    assert len(runs) == len(IDX) == 990, (len(runs), len(IDX))
    tasks = sorted(meta)
    silent_tasks = [t for t in tasks if meta[t]["sim_silent"]]
    visible_tasks = [t for t in tasks if not meta[t]["sim_silent"]]
    assert len(silent_tasks) == 6 and len(visible_tasks) == 5
    R = {}          # nested results, flattened into template keys and dumped as JSON
    TBL = {}        # markdown tables by key

    def sub(cond=None, model=None, task=None, stratum=None):
        out = runs
        if cond:
            out = [r for r in out if r["condition"] == cond]
        if model:
            out = [r for r in out if r["model"] == model]
        if task:
            out = [r for r in out if r["task"] == task]
        if stratum == "silent":
            out = [r for r in out if r["silent"]]
        if stratum == "visible":
            out = [r for r in out if not r["silent"]]
        return out

    def cnt(rs, f):
        return sum(bool(f(r)) for r in rs)

    def mean(rs, f):
        return sum(f(r) for r in rs) / len(rs) if rs else float("nan")

    def cell_means(rs, f):
        d = defaultdict(list)
        for r in rs:
            d[r["cell"] if "cell" in r else (r["model"], r["task"])].append(f(r))
        return {k: sum(v) / len(v) for k, v in d.items()}

    def contrast(A, B, pred=None, get=lambda r: r["clean_pass"], label="", cluster=True):
        keys = sorted(k[:3] for k in IDX if k[3] == A and (pred is None or pred(IDX[k])))
        a_ = [int(bool(get(IDX[k + (A,)]))) for k in keys]
        b_ = [int(bool(get(IDX[k + (B,)]))) for k in keys]
        both = sum(x and y for x, y in zip(a_, b_))
        ao = sum(x and not y for x, y in zip(a_, b_))
        bo = sum(y and not x for x, y in zip(a_, b_))
        n = len(keys)
        out = {"A": A, "B": B, "n": n, "rA": rate(sum(a_), n), "rB": rate(sum(b_), n), "both": both, "A_only": ao,
               "B_only": bo, "neither": n - both - ao - bo, "delta": 100 * (sum(a_) - sum(b_)) / n if n else float("nan"),
               "p": mcnemar_p(ao, bo)}
        out["delta_fmt"] = sg(out["delta"])
        out["disc"] = f"{ao}/{bo}"
        out["p_fmt"] = fp(out["p"])
        if cluster:
            cells = defaultdict(lambda: [0, 0, 0])
            for k, x, y in zip(keys, a_, b_):
                c = cells[k[:2]]
                c[0] += x; c[1] += y; c[2] += 1
            d = [100 * (c[0] - c[1]) / c[2] for _, c in sorted(cells.items())]
            lo, hi = boot_ci(d, f"{label}:{A}-{B}")
            out.update({"cells": len(d), "cl_lo": lo, "cl_hi": hi, "cl_p": signflip_p(d, f"{label}:{A}-{B}"),
                        "cl_fmt": f"[{sg(lo)}, {sg(hi)}]", "cl_p_fmt": fp(signflip_p(d, f"{label}:{A}-{B}"))})
        return out

    def cont_contrast(A, B, get, pred=None, label=""):
        keys = sorted(k[:3] for k in IDX if k[3] == A and (pred is None or pred(IDX[k])))
        cells = defaultdict(list)
        for k in keys:
            cells[k[:2]].append(get(IDX[k + (A,)]) - get(IDX[k + (B,)]))
        d = [sum(v) / len(v) for _, v in sorted(cells.items())]
        lo, hi = boot_ci(d, f"cont:{label}:{A}-{B}")
        return {"mean_diff": float(np.mean(d)), "cl_lo": lo, "cl_hi": hi}

    # ------------------------------------------------------------------ T0 provenance
    R["prov"] = {"runs": len(runs), "models": len(MODELS), "tasks": len(tasks), "conds": len(CONDS),
                 "reps": sorted({r["rep"] for r in runs}), "protocol": sorted({r["protocol"] for r in runs}),
                 "v3": sorted({r["interp_v3_version"] for r in runs}), "temperature": sorted({r["temperature"] for r in runs}),
                 "max_iters": sorted({r["max_iters"] for r in runs}), "sem_include_raw": sorted({r["sem_include_raw"] for r in runs}),
                 "sha": sorted({r["base_interp_sha256_lf"] for r in runs}),
                 "ts_first": min(r["timestamp"] for r in runs), "ts_last": max(r["timestamp"] for r in runs)}
    mans = {}
    for f in sorted(glob.glob(os.path.join(a.results, "run_manifest_*.json"))):
        j = json.load(open(f))
        mans[j["model"]] = j
    tool = {m: (j["toolchain"]["yosys"].split(" (")[0], j["toolchain"]["verilator"].split(" ")[1], j["host"].split(".")[0])
            for m, j in mans.items()}
    R["prov"]["toolchains"] = sorted({(v[0], v[1]) for v in tool.values()}, key=str)
    R["prov"]["toolchain_str"] = "; ".join(f"{y}, Verilator {v}" for y, v in R["prov"]["toolchains"])
    R["prov"]["toolchain_uniform"] = len({(v[0], v[1]) for v in tool.values()}) == 1
    ml = json.load(open(os.path.join(a.results, "master_log.json")))
    errs = [(i, x) for i, x in enumerate(ml) if "error" in x]
    sup = 0
    for i, x in errs:
        k = (x["model"], x["condition"], x["task"], x["rep"])
        sup += any(j > i and "error" not in y and (y["model"], y["condition"], y["task"], y["rep"]) == k for j, y in enumerate(ml))
    R["prov"]["error_entries"], R["prov"]["errors_superseded"], R["prov"]["master_log_entries"] = len(errs), sup, len(ml)
    R["prov"]["error_models"] = sorted({x["model"] for _, x in errs})
    TBL["t0"] = md_table(["model", "Yosys", "Verilator", "node (last invocation)"],
                         [[m] + list(tool[m]) for m in MODELS if m in tool])

    # ------------------------------------------------------------------ T1 pooled
    rows, R["pool"] = [], {}
    for c in CONDS:
        rs = sub(c)
        cm = cell_means(rs, lambda r: 100 * r["clean_pass"])
        lo, hi = boot_ci(list(cm.values()), f"pool:{c}")
        d = {"n": len(rs), "func": rate(cnt(rs, lambda r: r["func_pass"]), len(rs)),
             "clean": rate(cnt(rs, lambda r: r["clean_pass"]), len(rs)),
             "silent": rate(cnt(rs, lambda r: r["silent_structural_pass"]), len(rs)),
             "sfclean": rate(cnt(rs, lambda r: r["sf_clean"]), len(rs)), "sf": cnt(rs, lambda r: r["semantic_fired"]),
             "calls": mean(rs, lambda r: r["llm_calls"]), "toolfb": mean(rs, lambda r: r["tool_feedback_iters"]),
             "tokens": mean(rs, lambda r: r["tokens"]), "cl_lo": lo, "cl_hi": hi,
             "budget": cnt(rs, lambda r: r["stop_reason"] == "budget"), "zero_call": cnt(rs, lambda r: r["llm_calls"] == 0)}
        d["cl_fmt"] = f"[{lo:.0f}–{hi:.0f}]"
        R["pool"][c] = d
        rows.append([c, d["n"], d["func"]["fmt"], d["clean"]["fmt"], d["cl_fmt"], d["silent"]["fmt"], d["sfclean"]["fmt"],
                     d["sf"], f"{d['calls']:.2f}", f"{d['toolfb']:.2f}", f"{d['tokens']:.0f}"])
    H1 = ["condition", "N", "func_pass", "clean_pass (Wilson 95%)", "clean cluster 95% CI", "silent structural pass",
          "clean AND sf", "sf runs", "LLM calls/run", "tool-feedback rounds/run", "tokens/run"]
    TBL["t1"] = md_table(H1, rows)

    # ------------------------------------------------------------------ T2 strata
    rows, R["strat"] = [], {}
    for st in ("silent", "visible"):
        R["strat"][st] = {}
        for c in CONDS:
            rs = sub(c, stratum=st)
            cm = cell_means(rs, lambda r: 100 * r["clean_pass"])
            lo, hi = boot_ci(list(cm.values()), f"strat:{st}:{c}")
            d = {"n": len(rs), "clean": rate(cnt(rs, lambda r: r["clean_pass"]), len(rs)),
                 "func": rate(cnt(rs, lambda r: r["func_pass"]), len(rs)),
                 "silent": rate(cnt(rs, lambda r: r["silent_structural_pass"]), len(rs)),
                 "sf": cnt(rs, lambda r: r["semantic_fired"]), "sfclean": rate(cnt(rs, lambda r: r["sf_clean"]), len(rs)),
                 "calls": mean(rs, lambda r: r["llm_calls"]), "zero_call": cnt(rs, lambda r: r["llm_calls"] == 0),
                 "cl_fmt": f"[{lo:.0f}–{hi:.0f}]"}
            R["strat"][st][c] = d
            rows.append([c, "sim-silent (6 tasks)" if st == "silent" else "sim-visible (5 tasks)", d["n"], d["clean"]["fmt"], d["cl_fmt"],
                         d["silent"]["fmt"], d["sf"], d["sfclean"]["fmt"], f"{d['calls']:.2f}", d["zero_call"]])
    TBL["t2"] = md_table(["condition", "stratum", "N", "clean_pass", "clean cluster CI", "silent structural pass", "sf runs",
                          "clean AND sf", "LLM calls/run", "runs with 0 LLM calls"], rows)
    # per-task view of the sim-silent tasks (T2b)
    rows = []
    R["silent_tasks"] = {}
    for t in silent_tasks:
        b = sub("baseline", task=t)
        d = {"baseline_silent": rate(cnt(b, lambda r: r["silent_structural_pass"]), len(b)),
             "baseline_zero_call": cnt(b, lambda r: r["llm_calls"] == 0)}
        for c in CONDS[1:]:
            d[c] = rate(cnt(sub(c, task=t), lambda r: r["clean_pass"]), len(sub(c, task=t)))
        R["silent_tasks"][t] = d
        rows.append([t, meta[t]["defect_classes"][0][:34], d["baseline_silent"]["fmt"], d["baseline_zero_call"]] + [d[c]["fmt"] for c in CONDS[1:]])
    TBL["t2b"] = md_table(["task", "defect", "baseline: silent structural pass", "baseline runs with 0 LLM calls"] +
                          [c + " clean" for c in CONDS[1:]], rows)

    # ------------------------------------------------------------------ T3 contrasts
    R["con"] = {}
    specs = [("v3_raw", "sem_adv_v3", "raw_adv"), ("v2_raw", "sem_adv_v2", "raw_adv"), ("v3_v2", "sem_adv_v3", "sem_adv_v2"),
             ("esc_v3", "sem_esc_restart_v3", "sem_adv_v3"), ("esc_raw", "sem_esc_restart_v3", "raw_adv"),
             ("raw_base", "raw_adv", "baseline"), ("v3_base", "sem_adv_v3", "baseline"), ("esc_base", "sem_esc_restart_v3", "baseline")]
    rows = []
    for key, A, B in specs:
        R["con"][key] = {}
        for st, pred in (("all", None), ("silent", lambda r: r["silent"]), ("visible", lambda r: not r["silent"])):
            d = contrast(A, B, pred, label=f"con:{key}:{st}")
            R["con"][key][st] = d
            rows.append([f"{A} vs {B}", st, d["n"], d["rA"]["fmt"], d["rB"]["fmt"], d["delta_fmt"], d["cl_fmt"],
                         d["disc"], d["p_fmt"], d["cl_p_fmt"]])
    H3 = ["contrast (A vs B)", "stratum", "pairs", "A clean", "B clean", "Δ pts (A−B)", "cell-cluster 95% CI",
          "A-only/B-only", "McNemar p", "cluster sign-flip p"]
    TBL["t3"] = md_table(H3, rows)
    # T3b per model, T3c per task (v3 vs raw), Holm within family
    for fam, items, keyf, name in (("model", MODELS, "model", "t3b"), ("task", tasks, "task", "t3c")):
        R["con"]["v3_raw_by_" + fam] = {}
        ds = [contrast("sem_adv_v3", "raw_adv", lambda r, it=it: r[keyf] == it, label=f"{fam}:{it}", cluster=False) for it in items]
        adj = holm([d["p"] for d in ds])
        rows = []
        for it, d, ad in zip(items, ds, adj):
            d["holm"] = ad
            d["holm_fmt"] = fp(ad)
            R["con"]["v3_raw_by_" + fam][slug(it)] = d
            rows.append([it, d["n"], d["rA"]["fmt"], d["rB"]["fmt"], d["delta_fmt"], d["disc"], d["p_fmt"], fp(ad)])
        TBL[name] = md_table([fam, "pairs", "sem_adv_v3 clean", "raw_adv clean", "Δ pts", "v3-only/raw-only", "McNemar p",
                              f"Holm p (family of {len(items)})"], rows)

    # ------------------------------------------------------------------ T4 upgrade v2 -> v3
    focus = {"register_1bit": "v2 silent", "ni_flit_pack": "v2 silent", "register_4bit": "v2 misleading", "register_32bit": "v2 misleading"}
    rows, R["up"] = [], {}
    for t in tasks:
        d = {"class": "+".join(meta[t]["expected_v3_classes"]), "silent": meta[t]["sim_silent"], "focus": focus.get(t, "")}
        for c in ("sem_adv_v2", "sem_adv_v3"):
            rs = sub(c, task=t)
            d[c + "_fired_input"] = cnt(rs, lambda r: r["per_iter"][0].get("feedback_semantic_fired"))
            variants = Counter(tuple(r["per_iter"][0].get("feedback_classes", [])) for r in rs)
            d[c + "_input_classes"] = "+".join(variants.most_common(1)[0][0]) or "(none)"
            d[c + "_input_deterministic"] = len(variants) == 1
            d[c + "_clean"] = rate(cnt(rs, lambda r: r["clean_pass"]), len(rs))
            d[c + "_sfclean"] = cnt(rs, lambda r: r["sf_clean"])
            d[c + "_nosf_clean"] = cnt(rs, lambda r: r["clean_pass"] and not r["semantic_fired"])
            exp = set(meta[t]["expected_v2_classes" if c == "sem_adv_v2" else "expected_v3_classes"])
            d[c + "_targeted_clean"] = cnt(rs, lambda r: r["clean_pass"] and exp & set(r["classes_fired"]))
        d["raw_clean"] = rate(cnt(sub("raw_adv", task=t), lambda r: r["clean_pass"]), 18)
        d["base_clean"] = rate(cnt(sub("baseline", task=t), lambda r: r["clean_pass"]), 18)
        d["contrast"] = contrast("sem_adv_v3", "sem_adv_v2", lambda r: r["task"] == t, label=f"up:{t}", cluster=False)
        R["up"][t] = d
        rows.append([t + (" *" if d["focus"] else ""), d["class"], d["focus"] or "-", f"{d['sem_adv_v2_fired_input']}/18", f"{d['sem_adv_v3_fired_input']}/18",
                     d["sem_adv_v2_input_classes"], d["sem_adv_v3_input_classes"], d["base_clean"]["fmt"], d["raw_clean"]["fmt"],
                     f"{d['sem_adv_v2_clean']['fmt']} [sf {d['sem_adv_v2_sfclean']}, no-sf {d['sem_adv_v2_nosf_clean']}]",
                     d["sem_adv_v3_clean"]["fmt"], d["contrast"]["disc"], d["contrast"]["p_fmt"]])
    TBL["t4"] = md_table(["task (* = focus)", "class", "v2 status", "v2 fired on input", "v3 fired on input", "v2 classes on input",
                          "v3 classes on input", "baseline clean", "raw_adv clean", "sem_adv_v2 clean", "sem_adv_v3 clean",
                          "v3-only/v2-only", "McNemar p"], rows)
    # class summary (sf-gated wins per class)
    classes = sorted({d["class"] for d in R["up"].values()})
    rows, R["cls"] = [], {}
    for k in classes:
        ts = [t for t in tasks if R["up"][t]["class"] == k]
        d = {"tasks": ts}
        for c in ("baseline", "raw_adv", "sem_adv_v2", "sem_adv_v3", "sem_esc_restart_v3"):
            rs = [r for r in runs if r["condition"] == c and r["task"] in ts]
            d[c] = {"clean": rate(cnt(rs, lambda r: r["clean_pass"]), len(rs)), "sfclean": rate(cnt(rs, lambda r: r["sf_clean"]), len(rs))}
        R["cls"][slug(k)] = d
        rows.append([k, ", ".join(ts), d["baseline"]["clean"]["fmt"], d["raw_adv"]["clean"]["fmt"], d["sem_adv_v2"]["sfclean"]["fmt"],
                     d["sem_adv_v3"]["sfclean"]["fmt"], d["sem_esc_restart_v3"]["sfclean"]["fmt"], d["sem_esc_restart_v3"]["clean"]["fmt"]])
    TBL["t4b"] = md_table(["defect class (v3 expected)", "tasks", "baseline clean", "raw_adv clean", "sem_adv_v2 sf-gated wins",
                           "sem_adv_v3 sf-gated wins", "sem_esc sf-gated wins", "sem_esc clean (any)"], rows)
    R["up_pool_focus"] = {c: rate(cnt([r for r in runs if r["condition"] == c and r["task"] in focus], lambda r: r["clean_pass"]),
                                  len([r for r in runs if r["condition"] == c and r["task"] in focus])) for c in CONDS}
    R["up_focus_contrast"] = contrast("sem_adv_v3", "sem_adv_v2", lambda r: r["task"] in focus, label="upfocus")
    R["up_notfocus_contrast"] = contrast("sem_adv_v3", "sem_adv_v2", lambda r: r["task"] not in focus, label="upnotfocus")
    R["up_pooled_contrast"] = R["con"]["v3_v2"]["all"]

    # ------------------------------------------------------------------ T5 escalation + cost
    R["esc"] = {}
    for c in CONDS:
        rs = sub(c)
        clean = cnt(rs, lambda r: r["clean_pass"])
        R["esc"][c] = {"calls": mean(rs, lambda r: r["llm_calls"]), "tokens": mean(rs, lambda r: r["tokens"]),
                       "toolfb": mean(rs, lambda r: r["tool_feedback_iters"]), "clean": rate(clean, len(rs)),
                       "tok_per_clean": sum(r["tokens"] for r in rs) / clean if clean else float("nan"),
                       "calls_per_clean": sum(r["llm_calls"] for r in rs) / clean if clean else float("nan")}
    rows = [[c, R["esc"][c]["clean"]["fmt"], f"{R['esc'][c]['calls']:.2f}", f"{R['esc'][c]['toolfb']:.2f}", f"{R['esc'][c]['tokens']:.0f}",
             f"{R['esc'][c]['calls_per_clean']:.2f}", f"{R['esc'][c]['tok_per_clean']:.0f}"] for c in CONDS]
    TBL["t5"] = md_table(["condition", "clean_pass", "LLM calls/run", "tool-feedback rounds/run", "tokens/run",
                          "LLM calls per clean pass", "tokens per clean pass"], rows)
    R["cost"] = {}
    for key, A, B in (("v3_raw", "sem_adv_v3", "raw_adv"), ("esc_v3", "sem_esc_restart_v3", "sem_adv_v3")):
        R["cost"][key] = {m: cont_contrast(A, B, g, label=m) for m, g in
                          (("calls", lambda r: r["llm_calls"]), ("tokens", lambda r: r["tokens"]), ("toolfb", lambda r: r["tool_feedback_iters"]))}
        for m in R["cost"][key]:
            d = R["cost"][key][m]
            d["fmt"] = f"{d['mean_diff']:+.2f} [{d['cl_lo']:+.2f}, {d['cl_hi']:+.2f}]"
            if m == "tokens":
                d["fmt"] = f"{d['mean_diff']:+.0f} [{d['cl_lo']:+.0f}, {d['cl_hi']:+.0f}]"
    R["cost"]["pct_calls_v3_raw"] = 100 * (R["esc"]["sem_adv_v3"]["calls"] / R["esc"]["raw_adv"]["calls"] - 1)
    R["cost"]["pct_tokens_v3_raw"] = 100 * (R["esc"]["sem_adv_v3"]["tokens"] / R["esc"]["raw_adv"]["tokens"] - 1)
    R["cost"]["pct_toolfb_esc_v3"] = 100 * (R["esc"]["sem_esc_restart_v3"]["toolfb"] / R["esc"]["sem_adv_v3"]["toolfb"] - 1)
    R["cost"]["pct_calls_esc_v3"] = 100 * (R["esc"]["sem_esc_restart_v3"]["calls"] / R["esc"]["sem_adv_v3"]["calls"] - 1)
    R["cost"]["pct_tokens_esc_v3"] = 100 * (R["esc"]["sem_esc_restart_v3"]["tokens"] / R["esc"]["sem_adv_v3"]["tokens"] - 1)
    E = sub("sem_esc_restart_v3")
    Es = [r for r in E if r["silent"]]
    R["gate"] = {"silent_n": len(Es), "silent_clean": rate(cnt(Es, lambda r: r["clean_pass"]), len(Es)),
                 "silent_clean_no_sf": rate(cnt(Es, lambda r: r["clean_pass"] and not r["semantic_fired"]), len(Es)),
                 "silent_sf_clean": rate(cnt(Es, lambda r: r["sf_clean"]), len(Es))}
    R["escprof"] = {"escalated": rate(cnt(E, lambda r: r["escalated"]), len(E)), "restarted": cnt(E, lambda r: r["restarted"]),
                    "clean_no_sf": cnt(E, lambda r: r["clean_pass"] and not r["semantic_fired"]),
                    "clean_total": cnt(E, lambda r: r["clean_pass"]), "sf_clean": cnt(E, lambda r: r["sf_clean"]),
                    "escalated_no_fire": cnt(E, lambda r: r["escalated"] and not r["semantic_fired"])}
    rows = []
    for flag in (False, True):
        rs = [r for r in E if r["escalated"] == flag]
        d = {"n": len(rs), "clean": rate(cnt(rs, lambda r: r["clean_pass"]), len(rs)), "sf": cnt(rs, lambda r: r["semantic_fired"]),
             "calls": mean(rs, lambda r: r["llm_calls"]), "tokens": mean(rs, lambda r: r["tokens"])}
        R["escprof"]["esc" if flag else "noesc"] = d
        rows.append(["escalated" if flag else "not escalated (generic gate message only)", d["n"], d["clean"]["fmt"], d["sf"],
                     f"{d['calls']:.2f}", f"{d['tokens']:.0f}"])
    TBL["t5b"] = md_table(["sem_esc_restart_v3 runs", "N", "clean_pass", "sf runs", "LLM calls/run", "tokens/run"], rows)

    # ------------------------------------------------------------------ T6 model ladder
    R["ladder"] = {}
    rowsA, rowsB = [], []
    for m in MODELS:
        R["ladder"][slug(m)] = {}
        for st in ("silent", "visible"):
            d = {}
            for c in CONDS:
                rs = sub(c, model=m, stratum=st)
                d[c] = rate(cnt(rs, lambda r: r["clean_pass"]), len(rs))
            R["ladder"][slug(m)][st] = d
            rowsA.append([m, st] + [d[c]["fmt"] for c in CONDS])
    TBL["t6"] = md_table(["model", "stratum"] + CONDS, rowsA)
    fam = {}
    for key, A, B, st in (("v3_raw", "sem_adv_v3", "raw_adv", None), ("esc_v3", "sem_esc_restart_v3", "sem_adv_v3", None),
                          ("raw_base", "raw_adv", "baseline", "visible"), ("v3_base", "sem_adv_v3", "baseline", "visible"),
                          ("esc_base", "sem_esc_restart_v3", "baseline", "visible")):
        ds = []
        for m in MODELS:
            pred = (lambda r, m=m, st=st: r["model"] == m and (st is None or (not r["silent"]) == (st == "visible")))
            ds.append(contrast(A, B, pred, label=f"lad:{key}:{m}", cluster=False))
        adj = holm([d["p"] for d in ds])
        for m, d, ad in zip(MODELS, ds, adj):
            d["holm"] = ad
            d["holm_fmt"] = fp(ad)
            d["verdict"] = ("helps" if d["delta"] > 0 else "hurts") if d["p"] < 0.05 else "no detectable difference"
            R["ladder"][slug(m)][key] = d
    for m in MODELS:
        L = R["ladder"][slug(m)]
        rowsB.append([m] + [f"{L[k]['delta_fmt']} ({L[k]['disc']}), p={L[k]['p_fmt']}, {L[k]['verdict']}" for k in
                            ("raw_base", "v3_raw", "esc_v3", "esc_base")])
    TBL["t6b"] = md_table(["model", "raw_adv − baseline (sim-visible only)", "sem_adv_v3 − raw_adv (all tasks)",
                           "sem_esc − sem_adv_v3 (all tasks)", "sem_esc − baseline (sim-visible only)"], rowsB)

    # ------------------------------------------------------------------ T7 composition
    comp = [json.loads(l) for l in open(os.path.join(a.results, "compose_results.jsonl")) if l.strip()]
    bounds = [json.loads(l) for l in open(a.bounds) if l.strip()]
    bnd = {(b["design"], bool(b["repaired_modules"])): b for b in bounds}
    req = {d: set(bnd[(d, True)]["repaired_modules"]) for d in ("mesh2x2", "mesh3x3", "mpsoc")}
    assert len({(c["design"], c["model"], c["condition"], c["rep"]) for c in comp}) == len(comp) == 270
    for c in comp:
        b = bnd[(c["design"], True)]["latch_cells_excl_crashed"]
        c["at_bound"] = bool(c["top_level_synthesis_pass"] and c["top_latch_cells"] is not None and c["top_latch_cells"] <= b)
        c["all_leaves"] = req[c["design"]] <= set(c["leaf_clean"]) and all(c["leaf_clean"][m] for m in req[c["design"]])
    R["comp"] = {"bounds": {d: {"unrepaired_cells": bnd[(d, False)]["latch_cells_excl_crashed"], "repaired_cells": bnd[(d, True)]["latch_cells_excl_crashed"],
                                "unrepaired_pass": bnd[(d, False)]["top_level_synthesis_pass"], "repaired_pass": bnd[(d, True)]["top_level_synthesis_pass"]}
                           for d in req}}
    rows = []
    for d in ("mesh2x2", "mesh3x3", "mpsoc"):
        R["comp"][d] = {}
        for c in CONDS:
            X = [x for x in comp if x["design"] == d and x["condition"] == c]
            cells = [x["latch_cells_excl_crashed"] for x in X if x["latch_cells_excl_crashed"] is not None]
            o = {"n": len(X), "pass": rate(cnt(X, lambda x: x["top_level_synthesis_pass"]), len(X)),
                 "at_bound": rate(cnt(X, lambda x: x["at_bound"]), len(X)), "all_leaves": rate(cnt(X, lambda x: x["all_leaves"]), len(X)),
                 "mean_cells": float(np.mean(cells)), "median_cells": float(np.median(cells)), "max_cells": max(cells)}
            R["comp"][d][c] = o
            rows.append([d, c, o["n"], o["pass"]["fmt"], o["at_bound"]["fmt"], o["all_leaves"]["fmt"], f"{o['mean_cells']:.0f}",
                         f"{o['median_cells']:.0f}", o["max_cells"]])
    TBL["t7"] = md_table(["design", "condition", "groups (model x rep)", "top-level synthesis pass", "pass AND latch cells ≤ golden bound",
                          "all composed leaves clean_pass", "mean latch cells", "median", "max"], rows)
    TBL["t7bounds"] = md_table(["design", "unrepaired reference", "all golden repairs"],
                               [[d, f"pass={R['comp']['bounds'][d]['unrepaired_pass']}, {R['comp']['bounds'][d]['unrepaired_cells']} cells (crashed file excluded)",
                                 f"pass={R['comp']['bounds'][d]['repaired_pass']}, {R['comp']['bounds'][d]['repaired_cells']} cells"] for d in req])
    # does leaf-level clean predict composition?
    pred = {}
    for d in ("mesh2x2", "mesh3x3", "mpsoc"):
        X = [x for x in comp if x["design"] == d and x["all_leaves"]]
        pred[d] = {"n": len(X), "pass": cnt(X, lambda x: x["top_level_synthesis_pass"]), "at_bound": cnt(X, lambda x: x["at_bound"])}
    R["comp"]["leaf_predicts"] = pred
    pairs = {}
    for d in ("mesh2x2", "mpsoc"):
        pairs[d] = {}
        for key, A, B in (("v3_raw", "sem_adv_v3", "raw_adv"), ("v3_v2", "sem_adv_v3", "sem_adv_v2"), ("esc_v3", "sem_esc_restart_v3", "sem_adv_v3"),
                          ("v3_base", "sem_adv_v3", "baseline")):
            for met in ("top_level_synthesis_pass", "at_bound"):
                ga = {(x["model"], x["rep"]): x[met] for x in comp if x["design"] == d and x["condition"] == A}
                gb = {(x["model"], x["rep"]): x[met] for x in comp if x["design"] == d and x["condition"] == B}
                ao = sum(ga[k] and not gb[k] for k in ga); bo = sum(gb[k] and not ga[k] for k in ga)
                pairs[d][f"{key}_{met}"] = {"A_only": ao, "B_only": bo, "p": mcnemar_p(ao, bo), "p_fmt": fp(mcnemar_p(ao, bo)),
                                            "disc": f"{ao}/{bo}"}
    R["comp"]["pairs"] = pairs
    fails = Counter()
    for x in comp:
        if not x["top_level_synthesis_pass"]:
            e = x["yosys_error"] or "no ERROR line (leaf file crashes Yosys or exit status)"
            fails[(x["condition"], "register_1bit unrepaired: multiple edge events" if "Multiple edge" in e else
                   ("async reset non-constant" if "Async reset" in e else e))] += 1
    rows = [[c, cause, n] for (c, cause), n in sorted(fails.items(), key=lambda kv: (CONDS.index(kv[0][0]), -kv[1]))]
    TBL["t7c"] = md_table(["condition", "top-level failure cause (all three designs, 54 group-designs per condition)", "count"], rows)

    # ------------------------------------------------------------------ T8 regressions
    reg = [r for r in runs if r["func_regress"]]
    score = lambda p: 2 if p["clean_pass"] else (1 if p["func_pass"] else 0)
    reg_score = [r for r in runs if score(r["per_iter"][-1]) < max(score(p) for p in r["per_iter"])]
    R["reg"] = {"clean_then_worse": cnt(runs, lambda r: r["first_clean"] is not None and not r["clean_pass"]),
                "func_regress_total": len(reg), "score_regress_total": len(reg_score),
                "same_set": {id(r) for r in reg} == {id(r) for r in reg_score}, "by_cond": {}}
    rows = []
    for c in CONDS:
        rs = sub(c)
        pas = [r for r in rs if r["input_func_pass"]]
        d = {"regress": cnt(rs, lambda r: r["func_regress"]), "broke_input": rate(cnt(pas, lambda r: r["broke_input"]), len(pas)),
             "input_passing_runs": len(pas), "n": len(rs), "regress_rate": rate(cnt(rs, lambda r: r["func_regress"]), len(rs)),
             "keepbest_func": rate(cnt(rs, lambda r: r["func_ever"]), len(rs))}
        R["reg"]["by_cond"][c] = d
        rows.append([c, d["n"], d["regress"], d["regress_rate"]["fmt"], d["broke_input"]["fmt"] if pas else "-", d["keepbest_func"]["fmt"],
                     rate(cnt(rs, lambda r: r["func_pass"]), len(rs))["fmt"]])
    TBL["t8"] = md_table(["condition", "N", "runs that lost a simulation pass (functional regressions)", "as % of runs",
                          "of runs whose INPUT passed simulation: final fails simulation", "func_pass if best-so-far were kept (post hoc)",
                          "func_pass as run"], rows)
    R["reg"]["by_model"] = {slug(m): {c: cnt(sub(c, model=m), lambda r: r["func_regress"]) for c in CONDS[1:]} for m in MODELS}
    TBL["t8b"] = md_table(["model"] + CONDS[1:], [[m] + [f"{R['reg']['by_model'][slug(m)][c]}/{len(sub(c, model=m))}" for c in CONDS[1:]] for m in MODELS])
    R["reg"]["by_task"] = {t: {c: cnt(sub(c, task=t), lambda r: r["func_regress"]) for c in CONDS[1:]} for t in tasks}
    TBL["t8c"] = md_table(["task"] + CONDS[1:], [[t] + [f"{R['reg']['by_task'][t][c]}/{len(sub(c, task=t))}" for c in CONDS[1:]] for t in tasks])
    reg_sorted = sorted(reg, key=lambda r: (CONDS.index(r["condition"]), MODELS.index(r["model"]), r["task"], r["rep"]))
    TBL["t8list"] = md_table(["#", "condition", "model", "task", "rep", "input passes sim", "per-iteration trajectory (C clean, F sim-pass only, x fail)"],
                             [[i + 1, r["condition"], r["model"], r["task"], r["rep"], "yes" if r["input_func_pass"] else "no", r["traj"]] for i, r in enumerate(reg_sorted)])
    with open(os.path.join(a.evidence, "phase3_regressions.csv"), "w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh)
        w.writerow(["condition", "model", "task", "rep", "input_func_pass", "trajectory", "final_category"])
        for r in reg_sorted:
            w.writerow([r["condition"], r["model"], r["task"], r["rep"], r["input_func_pass"], r["traj"], r["final_cat"]])

    # ------------------------------------------------------------------ T9 final outcome categories
    cats = ["clean", "silent_structural", "sim_fail", "compile_error"]
    R["cat"], rows = {}, []
    for st in ("all", "silent", "visible"):
        R["cat"][st] = {}
        for c in CONDS:
            rs = sub(c, stratum=None if st == "all" else st)
            R["cat"][st][c] = {k: rate(cnt(rs, lambda r, k=k: r["final_cat"] == k), len(rs)) for k in cats}
            rows.append([st, c, len(rs)] + [R["cat"][st][c][k]["fmt"] for k in cats])
    TBL["t9"] = md_table(["tasks", "condition", "N"] + ["final: " + k for k in cats], rows)
    ce = [r for r in runs if r["final_cat"] == "compile_error"]
    R["ce"] = {"total": len(ce), "by_model": {slug(m): cnt(ce, lambda r, m=m: r["model"] == m) for m in MODELS}}
    fenced = 0
    for r in ce:
        rp = os.path.join(a.results, r["model"].replace(":", "_"), r["condition"], r["task"], f"rep{r['rep']}",
                          f"iter{r['per_iter'][-1]['iter']}", "response.txt")
        if os.path.exists(rp) and open(rp, encoding="utf-8", errors="ignore").read().count("```") >= 2:
            fenced += 1
    R["ce"]["fenced"] = f"{fenced}/{len(ce)}"
    non = {c: [r for r in sub(c) if not r["clean_pass"]] for c in CONDS}
    R["nonclean"] = {c: {"n": len(v), "structural": cnt(v, lambda r: r["final_cat"] == "silent_structural"),
                         "functional": cnt(v, lambda r: r["final_cat"] in ("sim_fail", "compile_error"))} for c, v in non.items()}

    # ------------------------------------------------------------------ T10 cumulative clean by call
    R["cum"], rows = {}, []
    for c in CONDS:
        rs = sub(c)
        R["cum"][c] = [rate(cnt(rs, lambda r, k=k: r["first_clean"] is not None and r["first_clean"] <= k), len(rs)) for k in range(0, 7)]
        rows.append([c] + [R["cum"][c][k]["fmt"] for k in range(0, 7)])
    TBL["t10"] = md_table(["condition"] + [f"clean by LLM call {k}" for k in range(0, 7)], rows)

    # ------------------------------------------------------------------ T11 latch events
    rows, R["latch"] = [], {}
    for c in CONDS:
        rs = [r for r in sub(c) if r["latch_count_before"]]
        d = {"n": len(rs), "before": sum(r["latch_count_before"] for r in rs), "after": sum((r["latch_count_after"] or 0) for r in rs),
             "free": cnt(rs, lambda r: r["latch_count_after"] == 0 and r["final_yosys_ok"])}
        d["free_rate"] = rate(d["free"], d["n"])
        R["latch"][c] = d
        rows.append([c, d["n"], d["before"], d["after"], d["free_rate"]["fmt"]])
    TBL["t11"] = md_table(["condition", "runs on latch-bearing tasks", "latch events on inputs (sum)", "latch events in final RTL (sum)",
                           "runs ending latch-free with Yosys OK"], rows)

    # ------------------------------------------------------------------ T12 dependence between replicates
    rows, R["dep"] = [], {}
    for c in CONDS:
        cm = defaultdict(list)
        for r in sub(c):
            cm[(r["model"], r["task"])].append(int(r["clean_pass"]))
        un = sum(len(set(v)) == 1 for v in cm.values())
        wil = R["pool"][c]["clean"]["hi"] - R["pool"][c]["clean"]["lo"]
        R["dep"][c] = {"cells": len(cm), "unanimous": rate(un, len(cm)), "ratio": (R["pool"][c]["cl_hi"] - R["pool"][c]["cl_lo"]) / wil}
        rows.append([c, len(cm), R["dep"][c]["unanimous"]["fmt"], f"{R['dep'][c]['ratio']:.2f}"])
    TBL["t12"] = md_table(["condition", "(model, task) cells", "cells where all 3 replicates agree on clean_pass",
                           "cell-cluster CI width / Wilson CI width (pooled clean_pass)"], rows)

    # ------------------------------------------------------------------ per-task table (SUMMARY-style, k/N sf)
    rows = []
    for t in tasks:
        row = [t, "silent" if meta[t]["sim_silent"] else "visible", R["up"][t]["class"]]
        for c in CONDS:
            rs = sub(c, task=t)
            row.append(f"{cnt(rs, lambda r: r['clean_pass'])}/{len(rs)} (sf {cnt(rs, lambda r: r['semantic_fired'])})")
        rows.append(row)
    TBL["t3d"] = md_table(["task", "stratum", "class"] + CONDS, rows)

    # ------------------------------------------------------------------ outputs
    def flat(d, pre=""):
        for k, v in d.items():
            key = f"{pre}.{k}" if pre else str(k)
            if isinstance(v, dict):
                yield from flat(v, key)
            elif isinstance(v, (list, tuple)):
                if all(not isinstance(x, (dict, list)) for x in v):
                    yield key, ", ".join(str(x) for x in v)
                for i, x in enumerate(v):
                    if isinstance(x, dict):
                        yield from flat(x, f"{key}.{i}")
            else:
                yield key, v

    reg_tbl = {("tbl_" + k): v for k, v in TBL.items()}
    V = {}
    for k, v in flat(R):
        V[k] = (f"{v:.1f}" if isinstance(v, float) else str(v))
    V.update(reg_tbl)

    def render(tmpl):
        def rep(m):
            k = m.group(1).strip()
            if k not in V:
                raise KeyError(f"template key not found: {k}")
            return V[k]
        return re.sub(r"<<([^<>]+)>>", rep, tmpl)

    json.dump(R, open(os.path.join(a.evidence, "phase3_analysis.json"), "w", encoding="utf-8"), indent=1, default=str)
    tmpl = open(os.path.join(a.templates, "PHASE3_RESULTS.md.tmpl"), encoding="utf-8").read()
    open(os.path.join(a.evidence, "PHASE3_RESULTS.md"), "w", newline="\n", encoding="utf-8").write(render(tmpl))
    open(os.path.join(a.evidence, "phase3_tables.md"), "w", newline="\n", encoding="utf-8").write(
        "# Phase 3 tables (generated by analyze_phase3.py)\n\n" + "\n\n".join(f"## {k}\n\n{v}" for k, v in TBL.items()) + "\n")
    print(f"analysed {len(runs)} runs; tables: {len(TBL)}; template keys: {len(V)}")
    if not a.no_figs:
        import phase3_figures
        phase3_figures.make(R, runs, os.path.join(a.evidence, "figures"), rate)
    print("outputs in", a.evidence)


# ============================================================================= final batch (PREREG_FINAL.md)
# Additive: main() above is unchanged and still reproduces evidence/phase3_run/ byte for byte. Everything below is the
# pre-registered analysis of the final batch (baseline_gate control arm + qwen2.5-coder:32b) and the POST HOC sign-off
# re-score of the 990 runs.
import hashlib  # noqa: E402

COND6 = CONDS + ["baseline_gate"]
M32 = "qwen2.5-coder:32b"
SIGNOFF_CACHE = os.path.join(P3, "evidence", "signoff_cache.json")
PRIMARY = [("esc_gate", "sem_esc_restart_v3", "baseline_gate", ("all", "silent", "visible")),
           ("v3_gate", "sem_adv_v3", "baseline_gate", ("all", "silent", "visible")),
           ("gate_raw", "baseline_gate", "raw_adv", ("all", "silent", "visible")),
           ("gate_base", "baseline_gate", "baseline", ("visible",))]
RESTATED = [("v2_raw", "sem_adv_v2", "raw_adv", ("all", "silent", "visible")),
            ("v3_raw", "sem_adv_v3", "raw_adv", ("all", "silent", "visible")),
            ("v3_v2", "sem_adv_v3", "sem_adv_v2", ("all", "silent", "visible")),
            ("esc_v3", "sem_esc_restart_v3", "sem_adv_v3", ("all", "silent", "visible")),
            ("esc_raw", "sem_esc_restart_v3", "raw_adv", ("all", "silent", "visible")),
            ("esc_base", "sem_esc_restart_v3", "baseline", ("visible",))]
STRATUM = {"all": lambda r: True, "silent": lambda r: r["silent"], "visible": lambda r: not r["silent"]}


def _lf(p):
    return open(p, "rb").read().replace(b"\r\n", b"\n")


def _signoff_sim(cand, tb):
    import shutil
    import tempfile
    from p3_eval import simulate
    with tempfile.TemporaryDirectory() as d:
        shutil.copy(cand, os.path.join(d, "dut.v"))
        shutil.copy(tb, os.path.join(d, "tb.v"))
        return simulate(["dut.v"], "tb.v", d)["outcome"]


def apply_signoff(runs, tasks_dir, allow_sim, cache_path=SIGNOFF_CACHE):
    """Offline sign-off oracle. tasks/<t>/tb_signoff.v is never seen by the runner or a prompt; it only scores
    candidates after the fact. Byte-identical (LF) to tb.v -> signoff_func = the logged func_pass. Otherwise every
    candidate is simulated once and cached by (sha256 tb_signoff.v, sha256 candidate), so this needs no simulator
    once the cache is filled (--score-signoff, under WSL)."""
    cache = json.load(open(cache_path)) if os.path.exists(cache_path) else {}
    so = {}
    for t in sorted({r["task"] for r in runs}):
        s = os.path.join(tasks_dir, t, "tb_signoff.v")
        assert os.path.exists(s), f"missing {s}"
        so[t] = None if _lf(s) == _lf(os.path.join(tasks_dir, t, "tb.v")) else (s, hashlib.sha256(_lf(s)).hexdigest())
    missing, dirty, superset_violations = 0, False, 0
    for r in runs:
        for p in r["per_iter"]:
            if so[r["task"]] is None:
                p["signoff_func"] = bool(p["func_pass"])
            else:
                s, key = so[r["task"]]
                cand = os.path.join(r["_dir"], f"iter{p['iter']}", "dut.v")
                ck = hashlib.sha256(open(cand, "rb").read()).hexdigest()
                c = cache.setdefault(key, {})
                if ck not in c:
                    if not allow_sim:
                        missing += 1
                        continue
                    c[ck], dirty = _signoff_sim(cand, s), True
                p["signoff_func"] = c[ck] == "PASS"
                superset_violations += p["signoff_func"] and not p["func_pass"]
            p["signoff_clean"] = bool(p["signoff_func"] and p["struct_clean"])
    if dirty:
        json.dump(cache, open(cache_path, "w"), indent=0, sort_keys=True)
    if missing:
        raise SystemExit(f"{missing} candidates are not in {cache_path}: run --score-signoff under WSL first")
    for r in runs:
        f = r["per_iter"][-1]
        r["signoff_func"], r["signoff_clean"] = f["signoff_func"], f["signoff_clean"]
        r["signed_off_defective"] = bool(r["func_pass"]) and not r["signoff_clean"]
        r["first_so_clean"] = next((p["iter"] for p in r["per_iter"] if p["signoff_clean"]), None)
    return {t: (v[1] if v else "identical to tb.v") for t, v in so.items()}, superset_violations


def load_many(dirs, tasks_dir):
    runs, src, meta = [], {}, None
    for d in dirs:
        rs, meta = load(d, tasks_dir)
        for r in rs:
            k = (r["model"], r["condition"])
            assert src.setdefault(k, d) == d, f"{k} is in both {src[k]} and {d}: one results dir per (model, condition)"
            r["_src"] = os.path.basename(os.path.normpath(d))
        runs += rs
    idx = {(r["model"], r["task"], r["rep"], r["condition"]): r for r in runs}
    assert len(idx) == len(runs), "duplicate (model, task, rep, condition)"
    return runs, meta, idx


def pcontrast(idx, A, B, get, keep, label):
    """Runs paired on (model, task, rep); cells = (model, task). Cell-mean difference in pts with cell bootstrap 95% CI
    and sign-flip p (the sampling unit), plus run-level exact McNemar p (used for Holm within families)."""
    keys = sorted(k[:3] for k in idx if k[3] == A and k[:3] + (B,) in idx and keep(idx[k]))
    if not keys:
        return None
    a_ = [int(bool(get(idx[k + (A,)]))) for k in keys]
    b_ = [int(bool(get(idx[k + (B,)]))) for k in keys]
    cells = defaultdict(list)
    for k, x, y in zip(keys, a_, b_):
        cells[k[:2]].append(x - y)
    d = [100 * sum(v) / len(v) for _, v in sorted(cells.items())]
    lo, hi = boot_ci(d, label)
    ao = sum(x and not y for x, y in zip(a_, b_))
    bo = sum(y and not x for x, y in zip(a_, b_))
    n = len(keys)
    return {"n": n, "cells": len(d), "A": rate(sum(a_), n)["fmt"], "B": rate(sum(b_), n)["fmt"],
            "delta": float(np.mean(d)), "lo": lo, "hi": hi, "p": signflip_p(d, label), "mcnemar": mcnemar_p(ao, bo),
            "disc": f"{ao}/{bo}"}


def _cfmt(c):
    return "--" if c is None else f"{sg(c['delta'])} [{sg(c['lo'])}, {sg(c['hi'])}]"


DEFAULT_ADVICE = {   # feedback text that tells the model to add a default assignment (counted, not interpreted)
    "'<safe value>' at the top (production LATCH text; v2 and v3 both emit it)": re.compile(r"<safe value>"),
    "'= 0;' as first statements (v3 LATCH builder text)": re.compile(r"Make these the FIRST statements inside that always"),
    "other default advice": re.compile(r"(?i)add\s+a\s+`?default|default branch|default at the top"),
}


def feedback_texts(r):
    out = []
    for p in sorted(glob.glob(os.path.join(r["_dir"], "iter*", "prompt.txt"))):
        t = open(p, encoding="utf-8", errors="ignore").read()
        if "VERIFICATION FEEDBACK ON THE CURRENT RTL:" in t:
            out.append(t.split("VERIFICATION FEEDBACK ON THE CURRENT RTL:", 1)[1].split("\nReturn the COMPLETE module")[0])
    return out


def gap_advice_block(runs, conds, J):
    """Secondary, exploratory (PREREG amendment A1). On the two tasks with a spec-complete sign-off testbench: runs
    whose final RTL passed the loop (clean_pass) but fails sign-off ('gap runs'), next to the signoff_clean runs, by
    condition, with how many received default-assignment advice in any feedback round. Counts only."""
    rows = []
    for t in ("Address_select", "mem_wb_mux"):
        for grp, keep in (("six models", lambda r: r["model"] in MODELS), (M32, lambda r: r["model"] == M32)):
            for c in conds:
                rs = [r for r in runs if r["task"] == t and r["condition"] == c and keep(r)]
                if not rs:
                    continue
                for kind, sel in (("gap (loop clean, sign-off fails)", [r for r in rs if r["clean_pass"] and not r["signoff_clean"]]),
                                  ("signoff_clean", [r for r in rs if r["signoff_clean"]])):
                    fb = {id(r): "\n".join(feedback_texts(r)) for r in sel}
                    hits = [sum(bool(rx.search(fb[id(r)])) for r in sel) for rx in DEFAULT_ADVICE.values()]
                    anyh = sum(any(rx.search(fb[id(r)]) for rx in DEFAULT_ADVICE.values()) for r in sel)
                    J.setdefault(t, {}).setdefault(grp, {}).setdefault(c, {})[kind] = {"n": len(sel), "any": anyh,
                                                                                      **dict(zip(DEFAULT_ADVICE, hits))}
                    rows.append([t, grp, c, kind, f"{len(sel)}/{len(rs)}", anyh] + hits)
    return md_table(["task", "models", "condition", "runs", "N / runs", "with any default advice"] + list(DEFAULT_ADVICE), rows)


def reading(pool):
    """Pre-registered readings (PREREG_FINAL.md), decided on the pooled 6-model signoff_clean contrasts."""
    c1, c2 = pool["esc_gate"], pool["v3_gate"]
    out = []
    if c1["lo"] > 0 and c2["lo"] > 0:
        out.append("R1: contrasts 1 and 2 CIs exclude 0 (gate lower) -> the detail in the feedback adds value beyond the verdict.")
    if c1["lo"] <= 0 <= c1["hi"]:
        out.append("R2: contrast 1 CI includes 0 -> the verdict carries most of escalation's gain.")
    if c2["hi"] < 0:
        out.append("R3: gate above always-on v3 -> terse beats verbose on some models; escalation is the recommended design.")
    return out or ["No pre-registered reading applies; the result is reported as observed, without a pre-registered interpretation."]


def cond_table(rs_all, conds, label):
    rows = []
    for c in conds:
        rs = [r for r in rs_all if r["condition"] == c]
        if not rs:
            continue
        n = len(rs)
        cm = defaultdict(list)
        for r in rs:
            cm[(r["model"], r["task"])].append(100 * r["signoff_clean"])
        lo, hi = boot_ci([sum(v) / len(v) for _, v in sorted(cm.items())], f"final:{label}:{c}")
        k = lambda f: sum(bool(f(r)) for r in rs)
        so = k(lambda r: r["signoff_clean"])
        rows.append([c, n, rate(k(lambda r: r["func_pass"]), n)["fmt"], rate(k(lambda r: r["signoff_func"]), n)["fmt"],
                     rate(so, n)["fmt"], f"[{lo:.0f}–{hi:.0f}]", rate(k(lambda r: r["clean_pass"]), n)["fmt"],
                     rate(k(lambda r: r["signed_off_defective"]), n)["fmt"],
                     rate(k(lambda r: r["silent_structural_pass"]), n)["fmt"],
                     rate(k(lambda r: r["first_so_clean"] is not None and r["first_so_clean"] <= 1), n)["fmt"],
                     f"{np.mean([r['llm_calls'] for r in rs]):.2f}", f"{np.mean([r['tool_feedback_iters'] for r in rs]):.2f}",
                     f"{np.mean([r['tokens'] for r in rs]):.0f}",
                     f"{sum(r['tokens'] for r in rs) / so:.0f}" if so else "--"])
    return md_table(["condition", "N", "loop_pass (tb.v)", "signoff_func", "**signoff_clean**", "signoff_clean cell CI",
                     "clean_pass as run (tb.v)", "signed_off_defective", "silent structural pass (old metric)",
                     "signoff_clean by LLM call 1", "LLM calls/run", "tool-feedback rounds/run", "tokens/run",
                     "tokens per signoff_clean"], rows)


def contrast_block(idx, specs, keep_model, label, J, metric="signoff_clean"):
    rows = []
    for key, A, B, strata in specs:
        for st in strata:
            keep = lambda r, st=st: keep_model(r) and STRATUM[st](r)
            c = pcontrast(idx, A, B, lambda r: r[metric], keep, f"{label}:{key}:{st}")
            # main()'s label, so on the same runs the as-run column reproduces PHASE3_RESULTS.md exactly
            s = pcontrast(idx, A, B, lambda r: r["clean_pass"], keep, f"con:{key}:{st}:{A}-{B}")
            J.setdefault(key, {})[st] = {metric: c, "clean_pass_as_run": s}
            if c:
                rows.append([f"{A} − {B}", st, c["n"], c["cells"], c["A"], c["B"], _cfmt(c), fp(c["p"]), c["disc"],
                             fp(c["mcnemar"]), _cfmt(s)])
    return md_table(["contrast (A − B)", "tasks", "pairs", "cells", f"A {metric}", f"B {metric}",
                     "Δ pts, cell 95% CI", "sign-flip p", "A-only/B-only", "McNemar p",
                     "sensitivity: as-run clean_pass Δ [CI]"], rows)


def family_block(idx, specs, keep_model, fam, items, label, J):
    """Secondary: per-model or per-task contrasts, run-level McNemar, Holm within each (contrast, family)."""
    rows = []
    for key, A, B, strata in specs:
        st = strata[0] if strata == ("visible",) else "all"
        items_ = [it for it in items if any(k[3] == A and (k[0] if fam == "model" else k[1]) == it for k in idx)]
        cs = [pcontrast(idx, A, B, lambda r: r["signoff_clean"],
                        lambda r, it=it: keep_model(r) and STRATUM[st](r) and r[fam] == it, f"{label}:{fam}:{key}:{it}")
              for it in items_]
        pairs = [(it, c) for it, c in zip(items_, cs) if c]
        adj = holm([c["mcnemar"] for _, c in pairs]) if pairs else []
        for (it, c), h in zip(pairs, adj):
            c["holm"] = h
            J.setdefault(f"{key}_by_{fam}", {})[it] = c
            rows.append([f"{A} − {B}", st, it, c["n"], c["A"], c["B"], sg(c["delta"]), c["disc"], fp(c["mcnemar"]),
                         f"{fp(h)} (family of {len(pairs)})"])
    return md_table(["contrast", "tasks", fam, "pairs", "A signoff_clean", "B signoff_clean", "Δ pts", "A-only/B-only",
                     "McNemar p", "Holm p"], rows)


def oracle_changes(runs, conds):
    rows, lst = [], []
    for t in sorted({r["task"] for r in runs}):
        ch = [r for r in runs if r["task"] == t and bool(r["clean_pass"]) != bool(r["signoff_clean"])]
        row = [t]
        for c in conds:
            rs = [r for r in runs if r["task"] == t and r["condition"] == c]
            row.append(f"{sum(r['clean_pass'] for r in rs)} → {sum(r['signoff_clean'] for r in rs)} /{len(rs)}" if rs else "--")
        rows.append(row)
        lst += [[t, r["condition"], r["model"], r["rep"], "clean → not clean" if r["clean_pass"] else "not clean → clean"]
                for r in sorted(ch, key=lambda r: (r["condition"], r["model"], r["rep"]))]
    return (md_table(["task"] + [f"{c}: clean_pass → signoff_clean" for c in conds], rows),
            md_table(["task", "condition", "model", "rep", "change"], lst) if lst else "No run changed.")


def composition_block(dirs, models):
    comp = []
    for d in dirs:
        f = os.path.join(d, "compose_results.jsonl")
        if os.path.exists(f):
            comp += [json.loads(l) for l in open(f) if l.strip()]
    comp = [c for c in comp if c["model"] in models]
    if not comp:
        return "No compose_results.jsonl in the results directories yet."
    rows = []
    for d in ("mesh2x2", "mesh3x3", "mpsoc"):
        row = [d]
        for c in COND6:
            X = [x for x in comp if x["design"] == d and x["condition"] == c]
            row.append(rate(sum(bool(x["top_level_synthesis_pass"]) for x in X), len(X))["fmt"] if X else "--")
        rows.append(row)
    return md_table(["design (top-level synthesis pass, groups = model x rep)"] + COND6, rows)


def final_main(a):
    dirs = [a.results] + list(a.more_results)
    runs, meta, idx = load_many(dirs, a.tasks)
    if a.score_signoff:
        so, viol = apply_signoff(runs, a.tasks, allow_sim=True)
        print(f"sign-off cache filled for {len(runs)} runs; tb_signoff differs on: "
              f"{[t for t, v in so.items() if v != 'identical to tb.v']}; candidates passing tb_signoff but failing tb.v: {viol}")
        return
    so, viol = apply_signoff(runs, a.tasks, allow_sim=False)
    for r in runs:   # PREREG amendment A1: processor-level sensitivity, Address_select signed off by its tb.v
        r["signoff_clean_proc"] = bool(r["clean_pass"]) if r["task"] == "Address_select" else r["signoff_clean"]
    posthoc = a.posthoc_signoff
    evid = a.evidence or (os.path.join(P3, "evidence", os.path.basename(os.path.normpath(a.results))) if posthoc
                          else os.path.join(P3, "evidence", "phase3_final"))
    os.makedirs(evid, exist_ok=True)
    conds = [c for c in COND6 if any(r["condition"] == c for r in runs)]
    m6 = lambda r: r["model"] in MODELS
    m7 = lambda r: r["model"] in MODELS + [M32]
    J, L = {"dirs": dirs, "signoff_tb": so}, []
    # ---- provenance and protocol checks
    mock = sorted({r["model"] for r in runs if r.get("provenance", {}).get("model_digest") == "mock"})
    by_src = Counter((r["_src"], r["model"], r["condition"]) for r in runs)
    drift = []
    for r in runs:
        p = r.get("provenance")
        if p:
            for f in ("tb.v", "spec.md", "input.v", "meta.json"):
                if p[f"{f.replace('.', '_')}_sha256_lf"] != hashlib.sha256(_lf(os.path.join(a.tasks, r["task"], f))).hexdigest():
                    drift.append((r["_src"], r["model"], r["condition"], r["task"], r["rep"], f))
    prot = {k: sorted({str(r[k]) for r in runs}) for k in ("protocol", "interp_v3_version", "base_interp_sha256_lf",
                                                          "temperature", "max_iters", "sem_include_raw")}
    J["provenance"] = {"mock_models": mock, "task_file_drift": drift, "protocol": prot, "superset_violations": viol}
    title = ("# POST HOC: the 990 Phase 3 runs under the sign-off oracle" if posthoc else
             "# Phase 3 final batch: pre-registered analysis (PREREG_FINAL.md)")
    L += [title, "", "Generated by `phase3/runner/analyze_phase3.py " + ("--posthoc-signoff" if posthoc else "--final") +
          "`. Every number below comes from the `metrics.json` files of the listed directories and "
          "`phase3/evidence/signoff_cache.json`.", ""]
    if mock:
        L += [f"**MOCK DATA: {len(mock)} model(s) ran with the mock backend ({', '.join(mock)}). Not a result.**", ""]
    if posthoc:
        L += ["**POST HOC for these 990 runs.** The sign-off oracle (`tasks/<task>/tb_signoff.v`) was introduced on "
              "2026-09-28, after the equivalence audit (`POSTHOC_CHECKS.md`, `preflight_final/`) found testbench gaps on "
              "mem_wb_mux and Address_select, and before any result of the final batch existed. The loop never saw it: every run's "
              "feedback came from `tb.v`, so this re-score is exactly what a re-run with the sign-off oracle would "
              "report for these trajectories.", ""]
    L += ["## Provenance", "", md_table(["results dir", "model", "condition", "runs"],
                                        [list(k) + [v] for k, v in sorted(by_src.items())]), "",
          f"Protocol fields over all runs: {json.dumps(prot)}.", "",
          f"Sign-off testbench per task (sha256 LF, or identical to tb.v): {json.dumps(so)}.", "",
          f"Candidates that pass tb_signoff.v but fail tb.v (must be 0): {viol}. New runs whose recorded task-file hash "
          f"differs from the task files analysed here (must be empty): {drift or 'none'}.", "",
          "## Metrics", "",
          "- `loop_pass`: the in-loop testbench tb.v passes (= the logged `func_pass`).",
          "- `signoff_func`: tb_signoff.v passes. `signoff_clean` = signoff_func AND structurally clean (the "
          "clean_pass structural rule). **Primary metric.**",
          "- `signed_off_defective`: loop_pass AND NOT signoff_clean (replaces the old `silent structural pass` = "
          "loop_pass AND NOT structurally clean, which is kept for continuity).",
          "- `clean_pass as run`: loop_pass AND structurally clean, the metric of the first write-up (sensitivity).", ""]
    hl = "six original models" + ("" if posthoc else " (headline; qwen2.5-coder:32b reported separately below)")
    L += [f"## Pooled, {hl}", "", cond_table([r for r in runs if m6(r)], conds, "pool6"), ""]
    for st in ("silent", "visible"):
        L += [f"### {'sim-silent' if st == 'silent' else 'sim-visible'} tasks", "",
              cond_table([r for r in runs if m6(r) and STRATUM[st](r)], conds, f"{st}6"), ""]
    have_gate = "baseline_gate" in conds
    if have_gate:
        J["primary"] = {}
        L += ["## Primary contrasts (signoff_clean, six models)", "",
              contrast_block(idx, PRIMARY, m6, "final6", J["primary"]), ""]
        J["readings"] = reading({k: J["primary"][k]["all"]["signoff_clean"] for k in ("esc_gate", "v3_gate")})
        L += ["**Pre-registered reading (pooled):** " + " ".join(J["readings"]), ""]
        J["primary_proc"] = {}
        L += ["### Pre-declared sensitivity: processor-level view (PREREG amendment A1)", "",
              "Address_select is signed off by its tb.v: in the MPSoC, MuxPC reads J_addr only when PCsrc = 2'b01, the "
              "case tb.v checks. Every other task as in the primary analysis.", "",
              contrast_block(idx, PRIMARY, m6, "final6proc", J["primary_proc"], metric="signoff_clean_proc"), "",
              "Reading these contrasts would give (reported, not used; the primary reading above stands): " +
              " ".join(reading({k: J["primary_proc"][k]["all"]["signoff_clean_proc"] for k in ("esc_gate", "v3_gate")})), ""]
    J["restated"] = {}
    L += ["## " + ("Contrasts under the sign-off oracle" if posthoc else "Re-stated contrasts (signoff_clean, six models)"), "",
          contrast_block(idx, RESTATED, m6, "final6" if not posthoc else "posthoc6", J["restated"]), ""]
    if not posthoc:
        specs = PRIMARY if have_gate else []
        L += ["## Secondary (labelled secondary; not used for the pre-registered readings)", ""]
        if specs:
            J["by_model"], J["by_task"] = {}, {}
            L += ["### Primary contrasts per model (Holm within each contrast)", "",
                  family_block(idx, specs, m6, "model", MODELS, "sec", J["by_model"]), "",
                  "### Primary contrasts per task (Holm within each contrast)", "",
                  family_block(idx, specs, m6, "task", sorted(meta), "sec", J["by_task"]), ""]
            G = [r for r in runs if m6(r) and r["condition"] == "baseline_gate"]
            fail = [r for r in G if not r["signoff_clean"]]
            rows = [[t, sum(r["task"] == t for r in G), sum(r["task"] == t for r in fail),
                     sum(r["task"] == t and r.get("would_fire") for r in fail),
                     sum(r["task"] == t and r.get("would_fire_final") for r in fail),
                     sum(r["task"] == t and r.get("would_fire") for r in G if r["signoff_clean"])] for t in sorted(meta)]
            rows.append(["all", len(G), len(fail), sum(bool(r.get("would_fire")) for r in fail),
                         sum(bool(r.get("would_fire_final")) for r in fail),
                         sum(bool(r.get("would_fire")) for r in G if r["signoff_clean"])])
            J["would_fire"] = rows[-1]
            L += ["### baseline_gate: where the bare verdict was not enough", "",
                  "`would_fire` = v3 fires on at least one RTL the gate verdict was given on (logged, never fed back); "
                  "`would_fire_final` = v3 fires on the returned RTL.", "",
                  md_table(["task", "baseline_gate runs", "not signoff_clean", "... with would_fire",
                            "... with would_fire_final", "signoff_clean with would_fire"], rows), ""]
        J["gap_advice"] = {}
        L += ["### Gap runs and default-assignment advice (secondary, exploratory; PREREG amendment A1)", "",
              "Runs on the two tasks with a spec-complete sign-off testbench. A run counts as receiving advice when any "
              "of its feedback rounds contains the pattern (directive or raw tool text). Counts only.", "",
              gap_advice_block(runs, conds, J["gap_advice"]), ""]
        cum = []
        for c in conds:
            rs = [r for r in runs if m6(r) and r["condition"] == c]
            cum.append([c] + [rate(sum(r["first_so_clean"] is not None and r["first_so_clean"] <= k for r in rs), len(rs))["fmt"]
                              for k in range(7)])
        L += ["### Cumulative signoff_clean by LLM call (six models)", "",
              md_table(["condition"] + [f"by call {k}" for k in range(7)], cum), ""]
        R32 = [r for r in runs if r["model"] == M32]
        if R32:
            L += ["### qwen2.5-coder:32b (separate model row)", "", cond_table(R32, conds, "m32"), ""]
            for st in ("silent", "visible"):
                L += [f"qwen2.5-coder:32b, {'sim-silent' if st == 'silent' else 'sim-visible'} tasks", "",
                      cond_table([r for r in R32 if STRATUM[st](r)], conds, f"m32{st}"), ""]
            J["pool7"] = {}
            L += ["### Seven-model sensitivity pool (six models + qwen2.5-coder:32b)", "",
                  contrast_block(idx, (PRIMARY if have_gate else []) + RESTATED, m7, "final7", J["pool7"]), ""]
        L += ["### Composition (top-level synthesis pass)", "", "Six models:", "", composition_block(dirs, MODELS), ""]
        if R32:
            L += ["qwen2.5-coder:32b:", "", composition_block(dirs, [M32]), ""]
    t1, t2 = oracle_changes([r for r in runs if m6(r) or posthoc], conds)
    L += ["## Oracle sensitivity: tb.v vs tb_signoff.v, per task", "", t1, "", "Runs whose verdict changed:", "", t2, ""]
    if not posthoc:
        L += ["No task was re-run with a corrected testbench (Option A, two oracles): the loop testbench is unchanged, "
              "so the sign-off re-score is exact and the planned 're-scored lower bound vs re-run' column does not arise.", ""]
    name = "POSTHOC_SIGNOFF" if posthoc else "PHASE3_FINAL"
    open(os.path.join(evid, name + ".md"), "w", newline="\n", encoding="utf-8").write("\n".join(L))
    json.dump(J, open(os.path.join(evid, name.lower() + ".json"), "w", encoding="utf-8"), indent=1, default=str)
    print(f"{name}: {len(runs)} runs from {len(dirs)} dir(s) -> {evid}")
    if not posthoc and not a.no_figs:
        import phase3_figures
        comp = [json.loads(l) for d in dirs if os.path.exists(os.path.join(d, "compose_results.jsonl"))
                for l in open(os.path.join(d, "compose_results.jsonl")) if l.strip()]
        phase3_figures.make_v2([r for r in runs if m6(r)], [c for c in comp if c["model"] in MODELS],
                               os.path.join(evid, "figures"), rate)


if __name__ == "__main__":
    main()
