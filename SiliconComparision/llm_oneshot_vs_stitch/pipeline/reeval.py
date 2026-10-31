#!/usr/bin/env python3
"""Re-evaluate every final file locally (same toolchain versions as the gate) and keep the logs for the analysis.

For each arm (oneshot, simloop, stitch) and module: p3_bridge.evaluate on tasks/<m> (tb.v, Verilator lint, Yosys
synth) and the sign-off simulation against tasks/<m>/tb_signoff.v. Logs and the flags go to
runs/analysis/<arm>/<m>/{sim.log, verilator.log, yosys.log, signoff.log, eval.json} (no .vvp). Cached: an existing
eval.json for the same file sha256 is reused. Also compares the local flags with reports/summary.json (cluster).
Usage: python pipeline/reeval.py [--force]
"""
from __future__ import annotations

import argparse
import concurrent.futures as cf
import json
import os
import shutil
import sys
import tempfile

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import analysis_common as A  # noqa: E402


def out_dir(arm: str, m: str) -> str:
    return os.path.join(A.STUDY, "runs", "analysis", arm, m)


def load(arm: str, m: str) -> dict:
    return json.load(open(os.path.join(out_dir(arm, m), "eval.json")))


def one(arm: str, m: str, force: bool = False) -> dict:
    import p3_bridge as B
    f, od = A.final_file(arm, m), out_dir(arm, m)
    ej = os.path.join(od, "eval.json")
    h = A.sha(f)
    if not force and os.path.exists(ej) and json.load(open(ej)).get("sha256") == h:
        return json.load(open(ej))
    os.makedirs(od, exist_ok=True)
    td = os.path.join(A.STUDY, "tasks", m)
    top = json.load(open(os.path.join(td, "meta.json")))["top"]
    with tempfile.TemporaryDirectory() as wd:
        ev = B.evaluate(f, td, top, workdir=wd, keep=True)
        so = B.simulate_with(f, os.path.join(td, "tb_signoff.v"), td, os.path.join(wd, "so"))
    for k in ("sim", "verilator", "yosys"):
        open(os.path.join(od, f"{k}.log"), "w").write(ev["_logs"][k])
    open(os.path.join(od, "signoff.log"), "w").write(so["log"])
    r = {k: v for k, v in ev.items() if k != "_logs"}
    r.update(sha256=h, file=A.rel(f), signoff_outcome=so["outcome"], signoff=so["outcome"] == "PASS",
             so_clean=so["outcome"] == "PASS" and ev["struct_clean"])
    json.dump(r, open(ej, "w"), indent=1)
    return r


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--force", action="store_true")
    a = ap.parse_args()
    jobs = [(arm, m) for arm in A.ARMS for m in A.modules()]
    with cf.ProcessPoolExecutor(max_workers=os.cpu_count() or 4) as ex:
        res = dict(zip(jobs, ex.map(one, *zip(*jobs), [a.force] * len(jobs))))
    rows, diff = A.summary_rows(), []
    for (arm, m), r in res.items():
        s = rows[m][arm]
        loc = {"compile": r["compile_ok"], "func": r["func_pass"], "signoff": r["signoff"],
               "struct_clean": r["struct_clean"]}
        if s is None or any(loc[k] != s[k] for k in loc):
            diff.append(f"{arm} {m}: local {A.flags(loc)} vs cluster {A.flags(s)}")
    print(f"re-evaluated {len(res)} final files; flags differing from reports/summary.json: {len(diff)}")
    for d in diff:
        print("  " + d)
    return 0


if __name__ == "__main__":
    sys.exit(main())
