#!/usr/bin/env python3
"""2x2 regression after the multi-study changes (laptop; needs iverilog, yosys, verilator and the local runs/).

  1. make_tasks.py --check: the 34 tasks/ folders regenerate byte-identical
  2. funnel.py, taxonomy.py and summarize.py rewrite reports/FUNNEL.md, TAXONOMY.md, SUMMARY.md and summary.json;
     each must be byte-identical to the committed file (git HEAD). summarize.py is run with the cluster paths in
     runs/arms metrics.json (final_candidate) mapped to the local study, as analysis_common does.
Exit 0 only if all hold. Usage: python pipeline/regress_2x2.py
"""
from __future__ import annotations

import hashlib
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
STUDY = os.path.dirname(HERE)
REPORTS = ("reports/FUNNEL.md", "reports/TAXONOMY.md", "reports/SUMMARY.md", "reports/summary.json")
SUMMARIZE = ("import sys; sys.path.insert(0, sys.argv[1]); import analysis_common as A, summarize as S; "
             "real = S.score; S.score = lambda c, m: real(c.replace(A.HPC_STUDY, A.STUDY + '/'), m); "
             "sys.argv = ['summarize.py', '--model', 'qwen2.5-coder:32b']; S.main()")


def main() -> int:
    env = {**os.environ, "STITCH_STUDY": "2x2"}
    py = sys.executable
    ok = subprocess.run([py, os.path.join(HERE, "make_tasks.py"), "--check"], env=env).returncode == 0
    for cmd in ([py, os.path.join(HERE, "funnel.py")], [py, os.path.join(HERE, "taxonomy.py")],
                [py, "-c", SUMMARIZE, HERE]):
        ok &= subprocess.run(cmd, env=env, stdout=subprocess.DEVNULL).returncode == 0
    for f in REPORTS:
        head = subprocess.run(["git", "show", f"HEAD:./{f}"], cwd=STUDY, capture_output=True).stdout
        same = hashlib.sha256(head).hexdigest() == hashlib.sha256(open(os.path.join(STUDY, f), "rb").read()).hexdigest()
        ok &= same
        print(f"{'ok ' if same else 'BAD'} {f} {'byte-identical to git HEAD' if same else 'DIFFERS from git HEAD'}")
    print("2x2 REGRESSION:", "PASS" if ok else "FAIL")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
