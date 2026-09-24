#!/usr/bin/env python3
"""
compose.py -- Phase 3 E3: re-integrate repaired leaf modules into the REAL composed designs and re-synthesise.

Designs (all from p20230031/RISC-V; compile-only sanitisation documented in designs/SANITISATION.md):
  mpsoc    : designs/mpsoc_ref,   top `main`            (processor side; NoC is dead logic at this top)
  mesh2x2  : designs/mesh2x2_ref, top `top_2x2_router`  (N = 4 routers)
  mesh3x3  : designs/mesh3x3_ref, top `top_3x3_router`  (N = 9 routers, 28/33 leaf files identical to 2x2)

A "repair set" maps module name -> candidate .v (e.g. the final dut.v of one model/condition/replicate).
Each module is replaced BY MODULE (its definition is removed from whichever reference file holds it), so
modules that share a file (execute_mux in execution_unit.v) are handled correctly. Modules without a
candidate stay as in the reference -- including defective ones outside the Phase 3 task set.

Usage:
  python phase3/runner/compose.py --design mesh2x2 --repairs register_1bit=path.v register_4bit=path.v ...
  python phase3/runner/compose.py --design all --golden            # upper bound: every task's golden.v
  python phase3/runner/compose.py --design all --none              # lower bound: reference as-is
  python phase3/runner/compose.py --from-results RESULTS_DIR --out compose_results.jsonl   # every (model,cond,rep)
"""
from __future__ import annotations

import argparse
import glob
import json
import os
import re
import shutil
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
PHASE3_ROOT = os.path.dirname(HERE)                      # <repo>/phase3  (or /scratch/.../Phase3_HPC/phase3)
REPO_ROOT = os.path.dirname(PHASE3_ROOT)
INTERP_DIR = (os.environ.get("STITCH_INTERPRETER_DIR") or os.environ.get("STITCH_INTERP_DIR")
              or os.path.join(REPO_ROOT, "src", "interpreter"))
sys.path.insert(0, HERE)
from p3_eval import synth  # noqa: E402

DESIGNS = {
    "mpsoc":   ("designs/mpsoc_ref", "main"),
    "mesh2x2": ("designs/mesh2x2_ref", "top_2x2_router"),
    "mesh3x3": ("designs/mesh3x3_ref", "top_3x3_router"),
}
TASKS_DIR = os.path.join(PHASE3_ROOT, "tasks")


def task_meta():
    out = {}
    for m in glob.glob(os.path.join(TASKS_DIR, "*", "meta.json")):
        j = json.load(open(m))
        if j.get("track") == "R":
            out[j["top"]] = j
    return out


def strip_module(src: str, mod: str) -> str:
    return re.sub(rf"^\s*module\s+{re.escape(mod)}\b.*?^\s*endmodule\b", "", src, flags=re.S | re.M)


def compose(design: str, repairs: dict, timeout: int = 1800) -> dict:
    ref, top = DESIGNS[design]
    ref = os.path.join(PHASE3_ROOT, ref)
    wd = tempfile.mkdtemp(prefix=f"compose_{design}_")
    try:
        for f in glob.glob(os.path.join(ref, "*.v")):
            shutil.copy(f, wd)
        used = {}
        for mod, cand in repairs.items():
            hit = False
            for f in glob.glob(os.path.join(wd, "*.v")):
                s = open(f).read()
                if re.search(rf"^\s*module\s+{re.escape(mod)}\b", s, re.M):
                    open(f, "w").write(strip_module(s, mod)); hit = True
            if hit:
                shutil.copy(cand, os.path.join(wd, f"__repaired_{mod}.v")); used[mod] = cand
        files = sorted(os.path.basename(f) for f in glob.glob(os.path.join(wd, "*.v")))
        y = synth(files, top, wd, timeout=timeout)
        return {"design": design, "top": top, "repaired_modules": sorted(used),
                "top_level_synthesis_pass": y["ok"], "yosys_error": y["error"],
                "top_latch_cells": y["latch_cells"] if y["ok"] else None,
                "top_latch_events": y["latch_events"], "top_loops": y["loops"]}
    finally:
        shutil.rmtree(wd, ignore_errors=True)


def compose_blackboxed(design: str, repairs: dict) -> dict:
    """When full synthesis crashes, count latch cells in everything else (crashing leaf read with -lib)."""
    r = compose(design, repairs)
    if r["top_level_synthesis_pass"]:
        r["latch_cells_excl_crashed"] = r["top_latch_cells"]
        return r
    ref, top = DESIGNS[design]
    ref = os.path.join(PHASE3_ROOT, ref)
    wd = tempfile.mkdtemp(prefix=f"composebb_{design}_")
    try:
        for f in glob.glob(os.path.join(ref, "*.v")):
            shutil.copy(f, wd)
        for mod, cand in repairs.items():
            for f in glob.glob(os.path.join(wd, "*.v")):
                s = open(f).read()
                if re.search(rf"^\s*module\s+{re.escape(mod)}\b", s, re.M):
                    open(f, "w").write(strip_module(s, mod))
                    shutil.copy(cand, os.path.join(wd, f"__repaired_{mod}.v"))
        files = sorted(os.path.basename(f) for f in glob.glob(os.path.join(wd, "*.v")))
        import subprocess
        bad = []
        for f in files:                                  # files that crash Yosys on their own
            p = subprocess.run([os.environ.get("STITCH_YOSYS", "yosys"), "-q", "-p", f"read_verilog {f}; proc"], cwd=wd, capture_output=True, text=True)
            if "ERROR" in (p.stdout + p.stderr):
                bad.append(f)
        good = [f for f in files if f not in bad]
        y = synth(good, top, wd, lib_files=bad)
        r["crashing_files"] = bad
        r["latch_cells_excl_crashed"] = y["latch_cells"] if y["ok"] else None
        return r
    finally:
        shutil.rmtree(wd, ignore_errors=True)


def designs_for(modules):
    meta = task_meta()
    ds = set()
    for m in modules:
        c = (meta.get(m) or {}).get("compose") or {}
        if c.get("design") == "mpsoc":
            ds.add("mpsoc")
        elif c.get("design") == "mesh":
            ds |= {"mesh2x2", "mesh3x3", "mpsoc"}     # mpsoc_ref contains the whole router tree too
    return sorted(ds)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--design", default="all")
    ap.add_argument("--repairs", nargs="*", default=[])
    ap.add_argument("--golden", action="store_true")
    ap.add_argument("--none", action="store_true")
    ap.add_argument("--from-results")
    ap.add_argument("--out")
    ap.add_argument("--designs", nargs="*", default=None, help="with --from-results: restrict designs")
    a = ap.parse_args()
    designs = list(DESIGNS) if a.design == "all" else [a.design]
    if a.from_results:
        return from_results(a.from_results, a.out or os.path.join(a.from_results, "compose_results.jsonl"), a.designs)
    meta = task_meta()
    if a.golden:
        repairs = {m: os.path.join(TASKS_DIR, m, "golden.v") for m in meta}
    elif a.none:
        repairs = {}
    else:
        repairs = dict(kv.split("=", 1) for kv in a.repairs)
    for d in designs:
        rel = {m: p for m, p in repairs.items() if d in designs_for([m])}
        r = compose_blackboxed(d, rel)
        print(json.dumps(r))
        if a.out:
            with open(a.out, "a") as fh:
                fh.write(json.dumps(r) + "\n")


def from_results(results_dir, out, only=None):
    """Group final candidates by (model, condition, rep) and compose each group into every relevant design."""
    groups = {}
    for mf in glob.glob(os.path.join(results_dir, "**", "metrics.json"), recursive=True):
        m = json.load(open(mf))
        if m.get("track") != "R" or not m.get("final_candidate"):
            continue
        key = (m["model"], m["condition"], m["rep"])
        groups.setdefault(key, {})[m["task"]] = (m["final_candidate"], m)
    with open(out, "w") as fh:
        for (model, cond, rep), items in sorted(groups.items()):
            for d in (only or list(DESIGNS)):
                rel = {t: c for t, (c, mm) in items.items() if d in designs_for([t])}
                if not rel:
                    continue
                # policy: a leaf enters the composition only if it compiled; otherwise the reference stays
                rel = {t: c for t, c in rel.items() if items[t][1].get("final_compile_ok")}
                r = compose_blackboxed(d, rel)
                r.update({"model": model, "condition": cond, "rep": rep,
                          "leaf_clean": {t: items[t][1].get("clean_pass") for t in rel}})
                fh.write(json.dumps(r) + "\n"); fh.flush()
                print(model, cond, rep, d, r["top_level_synthesis_pass"], r.get("latch_cells_excl_crashed"))


if __name__ == "__main__":
    main()
