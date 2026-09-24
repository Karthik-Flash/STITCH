#!/usr/bin/env python3
"""
audit_existing_runs.py -- Phase 3 E0 (CPU only, zero LLM calls).

Question: of the Phase 1/2 runs recorded as PASS, how many final RTL files are structurally dirty
(latch / Yosys crash / loop / MULTIDRIVEN / WIDTHTRUNC)? Baseline never ran Yosys, so this has never
been measured. The answer is the "silent structural pass" rate of the published conditions.

Layout is repo-specific, so everything is a parameter. Claude Code: confirm the glob and the two
field names against one real metrics.json before launching (see phase3/HANDOFF_PHASE3_CLAUDE_CODE.md, task T6).

Usage:
  python phase3/runner/audit_existing_runs.py --metrics-glob "phase2/results/**/metrics.json" \
      --pass-field passed --condition-field condition --model-field model --module-field module \
      --out phase3/results/e0_audit.jsonl
"""
import argparse
import glob
import json
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from p3_eval import lint, synth  # noqa: E402


def final_rtl(run_dir):
    """Heuristic: the .v in the highest-numbered iteration directory (not a testbench).

    Adapted for the real Phase 2 layout (phase2/results/set{1,3}_run/<module>/<model>/<cond>/rep<N>/iter_<k>/):
    every iter_<k>/ holds the candidate <module>.v AND a copy of the testbench named <module>_tb.v. The original
    filter only excluded names STARTING with tb/test/testbench, so <module>_tb.v slipped through and the mtime
    tie-break picked the testbench in 278 of 576 passing runs. Testbench names are now matched at the start of the
    file name or after an underscore. Paths are matched with '/' separators so this behaves the same on Windows."""
    tb = re.compile(r"(^|[/_])(tb|test|testbench)(_[^/]*)?\.v$", re.I)
    cands = [p for p in glob.glob(os.path.join(run_dir, "**", "*.v"), recursive=True)
             if not tb.search(p.replace(os.sep, "/"))]
    if not cands:
        return None

    def key(p):
        nums = [int(x) for x in re.findall(r"iter(?:ation)?_?(\d+)", p)]
        return (max(nums) if nums else -1, os.path.getmtime(p))
    return max(cands, key=key)


def top_of(path):
    m = re.search(r"^\s*module\s+([A-Za-z_]\w*)", open(path, errors="ignore").read(), re.M)
    return m.group(1) if m else None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--metrics-glob", required=True)
    ap.add_argument("--pass-field", default="passed")
    ap.add_argument("--condition-field", default="condition")
    ap.add_argument("--model-field", default="model")
    ap.add_argument("--module-field", default="module")
    ap.add_argument("--only-passes", type=int, default=1)
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    files = glob.glob(a.metrics_glob, recursive=True)
    print(f"{len(files)} metrics files")
    os.makedirs(os.path.dirname(os.path.abspath(a.out)), exist_ok=True)
    agg = {}
    with open(a.out, "w") as fh:
        for mf in files:
            try:
                m = json.load(open(mf))
            except Exception:
                continue
            passed = bool(m.get(a.pass_field))
            if a.only_passes and not passed:
                continue
            rtl = final_rtl(os.path.dirname(mf))
            if not rtl or not top_of(rtl):
                continue
            wd = os.path.dirname(rtl)
            y = synth([os.path.basename(rtl)], top_of(rtl), wd, timeout=300)
            v = lint([os.path.basename(rtl)], top_of(rtl), wd)
            dirty = not (y["ok"] and y["latch_events"] == 0 and y["loops"] == 0 and v["n_hard"] == 0)
            rec = {"metrics": mf, "rtl": rtl, "model": m.get(a.model_field), "condition": m.get(a.condition_field),
                   "module": m.get(a.module_field), "passed": passed, "yosys_ok": y["ok"], "yosys_error": y["error"],
                   "latch_events": y["latch_events"], "latch_cells": y["latch_cells"], "loops": y["loops"],
                   "verilator_codes": v["codes"], "structurally_dirty": dirty}
            fh.write(json.dumps(rec) + "\n")
            k = rec["condition"]
            agg.setdefault(k, [0, 0]); agg[k][0] += 1; agg[k][1] += int(dirty)
    print("\ncondition            passes  structurally_dirty")
    for k, (n, d) in sorted(agg.items(), key=lambda kv: str(kv[0])):
        print(f"{str(k):<20} {n:>6}  {d:>6} ({100*d/max(n,1):.1f}%)")


if __name__ == "__main__":
    main()
