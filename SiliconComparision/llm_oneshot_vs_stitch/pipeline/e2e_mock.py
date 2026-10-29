#!/usr/bin/env python3
"""End-to-end test of the whole pipeline with mock LLMs, on 3 modules, in a scratch GEN_WORK folder.

  encoder        (leaf)     one-shot mock returns the golden
  register_4bit  (register) one-shot mock returns the hand-written latched register
  allot_vc       (parent)   one-shot mock returns broken syntax (golden without its final endmodule)
The arms use the Phase 3 mock fix_on_2 (first call echoes the current input, later calls return golden.v).
Checks: every arm produced an output for every module, the STITCH arm fired on the latch (register_4bit), and the
summary was built. Exit 0 only if all hold.
Usage: python pipeline/e2e_mock.py [--work DIR]
"""
from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
MODULES = {"encoder": "golden", "register_4bit": "handwritten", "allot_vc": "broken"}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--work", default=None)
    a = ap.parse_args()
    work = os.path.abspath(a.work or tempfile.mkdtemp(prefix="gen_e2e_"))
    env = {**os.environ, "GEN_WORK": work, "PYTHONDONTWRITEBYTECODE": "1"}
    py = sys.executable
    plan = [f"{m}={mode}" for m, mode in MODULES.items()]
    steps = [
        [py, os.path.join(HERE, "oneshot_gen.py"), "--backend", "mock", "--model", "mock", "--modules", *MODULES,
         "--mock-plan", *plan],
        [py, os.path.join(HERE, "run_arms.py"), "--backend", "mock", "--mock-mode", "fix_on_2", "--model", "mock",
         "--modules", *MODULES],
        [py, os.path.join(HERE, "summarize.py"), "--model", "mock", "--modules", *MODULES],
    ]
    for cmd in steps:
        print("==", " ".join(os.path.basename(c) if c.endswith(".py") else c for c in cmd[1:]), flush=True)
        subprocess.run(cmd, check=True, env=env)
    s = json.load(open(os.path.join(work, "reports", "summary.json")))
    rows = {r["module"]: r for r in s["rows"]}
    checks = {
        "all arms produced outputs": all(os.path.exists(os.path.join(work, "outputs", arm, f"{m}.v"))
                                         for m in MODULES for arm in ("oneshot", "simloop", "stitch")),
        "every arm scored": all(rows[m][arm] is not None for m in MODULES for arm in ("oneshot", "simloop", "stitch")),
        "oneshot: golden leaf signs off clean": rows["encoder"]["oneshot"]["so_clean"],
        "oneshot: latched register not clean": not rows["register_4bit"]["oneshot"]["so_clean"],
        "oneshot: broken parent does not compile": not rows["allot_vc"]["oneshot"]["compile"],
        "stitch fired on the latch": rows["register_4bit"]["stitch"]["semantic_fired"]
                                     and "MISSING_CLOCK" in rows["register_4bit"]["stitch"]["classes"],
        "stitch final register signs off clean": rows["register_4bit"]["stitch"]["so_clean"],
        "summary built": os.path.exists(os.path.join(work, "reports", "SUMMARY.md")),
        "provenance written": os.path.exists(os.path.join(work, "runs", "arms", "provenance.json")),
    }
    for k, v in checks.items():
        print(f"  {'ok ' if v else 'BAD'} {k}")
    print("E2E MOCK:", "PASS" if all(checks.values()) else "FAIL", "| work dir:", work)
    return 0 if all(checks.values()) else 1


if __name__ == "__main__":
    sys.exit(main())
