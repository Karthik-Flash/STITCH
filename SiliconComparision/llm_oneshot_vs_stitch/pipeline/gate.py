#!/usr/bin/env python3
"""Drift gate, run before any LLM work (no GPU needed).

  G1 tool versions: Yosys 0.69, Verilator 5.053, Icarus 14 (the versions the tasks were validated on)
  G2 check_tasks.py on all tasks: reference passes tb.v and tb_signoff.v, mutants fail, and interpreter v3 fires the
     Phase 3 classes on the three hand-written registers (ASYNC_RESET, MISSING_CLOCK, MISSING_CLOCK)
  G3 prove_prompt_format.py: the wrapped runner's prompts are byte-identical to the plain Phase 3 runner's
  G4 e2e_mock.py: the whole pipeline end to end with mock LLMs on 3 modules
  G5 test_failures.py: resume, infra-error handling, num_thread injection, timeout fast-fail, first-call checks
G2 runs on the selected study (--study, default 2x2). G3-G5 test the pipeline itself on 2x2 modules in scratch
folders, so they always run with STITCH_STUDY=2x2 (they write nothing into any study).
Output of G2-G5 is prefixed "[selftest] ". Exit 0 only if every gate passes.
Usage: python pipeline/gate.py [--study 2x2|mesh3x3|ni]
"""
from __future__ import annotations

import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import p3_bridge as B  # noqa: E402

EXPECT = {"yosys": ([B.E.YOSYS, "-V"], "Yosys 0.69"), "verilator": ([B.E.VERILATOR, "--version"], "Verilator 5.053"),
          "iverilog": ([B.E.IVERILOG, "-V"], "Icarus Verilog version 14")}


def main() -> int:
    ok = True
    for name, (cmd, want) in EXPECT.items():
        rc, out, _ = B.E._run(cmd, ".", 30)
        line = out.strip().splitlines()[0] if out.strip() else f"MISSING (rc={rc})"
        good = line.startswith(want)
        ok &= good
        print(f"[G1] {'ok ' if good else 'BAD'} {name}: {line}  (want {want})")
    if not ok:
        print("GATE: FAIL (toolchain drift)")
        return 1
    for tag, script in (("G2", "check_tasks.py"), ("G3", "prove_prompt_format.py"), ("G4", "e2e_mock.py"),
                        ("G5", "test_failures.py")):
        print(f"[{tag}] {script}", flush=True)
        # Every self-test line gets "[selftest] ": the mock runs print fake [threads]/[speed]/[gpu offload] results
        # that must never be read as the job's real first-call checks.
        env = {**os.environ, "STITCH_STUDY": B.studies.NAME if tag == "G2" else "2x2"}
        p = subprocess.Popen([sys.executable, os.path.join(HERE, script)], stdout=subprocess.PIPE,
                             stderr=subprocess.STDOUT, text=True, errors="replace", env=env)
        for line in p.stdout:
            print("[selftest] " + line, end="", flush=True)
        rc = p.wait()
        print(f"[{tag}] {'ok' if rc == 0 else 'FAIL'}", flush=True)
        if rc != 0:
            print("GATE: FAIL")
            return 1
    print(f"GATE: ALL PASSED ({B.studies.NAME})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
