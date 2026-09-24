"""
p3_eval.py -- one evaluation function for every Phase 3 artefact (task inputs, goldens, LLM candidates,
re-integrated compositions). Pure subprocess + parsing; no LLM.

Pass definitions (reported separately, never merged):
  func_pass   : Icarus compiles and the task testbench prints ALL TESTS PASSED (and no FAIL token)
  struct_clean: Yosys synth succeeds AND 0 'Latch inferred' AND 0 Yosys logic loops AND
                Verilator reports 0 of {MULTIDRIVEN, UNOPTFLAT, LATCH, WIDTHTRUNC}
  clean_pass  : func_pass AND struct_clean          <- the Phase 3 primary metric
Baseline (AutoChip) stops at func_pass, so (func_pass AND NOT struct_clean) = "silent structural pass".
"""
from __future__ import annotations

import os
import re
import shutil
import subprocess
import tempfile
from collections import Counter

IVERILOG = os.environ.get("STITCH_IVERILOG", "iverilog")
VVP = os.environ.get("STITCH_VVP", "vvp")
VERILATOR = os.environ.get("STITCH_VERILATOR", "verilator")
YOSYS = os.environ.get("STITCH_YOSYS", "yosys")
PASS_TOKEN, FAIL_TOKEN = "ALL TESTS PASSED", "FAIL"
HARD_V = ("MULTIDRIVEN", "UNOPTFLAT", "LATCH", "WIDTHTRUNC")
IGNORED_V = ("DECLFILENAME", "EOFNEWLINE", "TIMESCALEMOD")


def _run(cmd, cwd, timeout):
    try:
        p = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True, timeout=timeout)
        return p.returncode, (p.stdout or "") + (p.stderr or ""), False
    except subprocess.TimeoutExpired as e:
        out = e.stdout.decode(errors="ignore") if isinstance(e.stdout, bytes) else (e.stdout or "")
        return -9, out + "\n[TIMEOUT]", True


def simulate(design_files, tb_file, cwd, timeout=60):
    exe = os.path.join(cwd, "sim.vvp")
    rc, out, _ = _run([IVERILOG, "-g2012", "-o", exe, "-s", "tb"] + list(design_files) + [tb_file], cwd, timeout)
    if rc != 0:
        return {"compile_ok": False, "outcome": "COMPILE_ERROR", "log": out}
    rc, log, to = _run([VVP, "-n", exe], cwd, timeout)       # cwd set: fixes the $readmemh class of bug
    if to:
        oc = "TIMEOUT"
    elif FAIL_TOKEN in log:
        oc = "FAIL"
    elif PASS_TOKEN in log:
        oc = "PASS"
    else:
        oc = "UNKNOWN"                                        # never treated as PASS
    return {"compile_ok": True, "outcome": oc, "log": (out + "\n" + log).strip()}


def lint(design_files, top, cwd, timeout=60):
    rc, log, _ = _run([VERILATOR, "--lint-only", "-Wall"] + [f"-Wno-{c}" for c in IGNORED_V] +
                      ["--top-module", top] + list(design_files), cwd, timeout)
    codes = Counter(re.findall(r"%Warning-([A-Z_0-9]+):", log))
    errors = [l for l in log.splitlines() if l.startswith("%Error") and "Exiting due to" not in l]
    return {"log": log, "codes": dict(codes), "n_warnings": sum(codes.values()), "errors": errors,
            "n_hard": sum(codes.get(c, 0) for c in HARD_V)}


def synth(design_files, top, cwd, timeout=600, lib_files=()):
    lib = "".join(f"read_verilog -lib {f}; " for f in lib_files)
    script = (f"{lib}read_verilog {' '.join(design_files)}; hierarchy -check -top {top}; "
              f"synth -top {top}; check; stat -top {top}")
    rc, log, to = _run([YOSYS, "-p", script], cwd, timeout)
    ok = rc == 0 and not to and "ERROR:" not in log
    events = [l for l in log.splitlines() if re.search(r"\bLatch inferred for signal", l) and "No latch" not in l]
    loops = len(set(re.findall(r"^Warning: found logic loop in module (\S+)", log, re.M)))
    i = log.rfind("=== design hierarchy ===")
    sec = log[i:] if i >= 0 else log[log.rfind("=== "):] if "=== " in log else ""
    cells = sum(int(n) for n in re.findall(r"\$_DLATCH\w*\s+(\d+)", sec))
    err = next((l for l in log.splitlines() if l.startswith("ERROR")), None)
    return {"log": log, "ok": ok, "error": err, "latch_events": len(events), "latch_cells": cells,
            "loops": loops, "timeout": to}


def evaluate(candidate_file, task_dir, top, workdir=None, keep=False):
    """Evaluate one candidate .v for one task. Returns a flat metrics dict (+ raw logs under '_logs')."""
    own = workdir is None
    wd = workdir or tempfile.mkdtemp(prefix="p3_")
    try:
        dut = os.path.join(wd, "dut.v")
        if os.path.abspath(candidate_file) != os.path.abspath(dut):
            shutil.copy(candidate_file, dut)
        tb = os.path.join(wd, "tb.v")
        shutil.copy(os.path.join(task_dir, "tb.v"), tb)
        s = simulate(["dut.v"], "tb.v", wd)
        v = lint(["dut.v"], top, wd)
        y = synth(["dut.v"], top, wd) if s["compile_ok"] else {"ok": False, "error": "not run (compile error)",
                                                               "latch_events": None, "latch_cells": None,
                                                               "loops": None, "log": ""}
        func = s["outcome"] == "PASS"
        clean = bool(y["ok"] and y["latch_events"] == 0 and y["loops"] == 0 and v["n_hard"] == 0)
        return {"compile_ok": s["compile_ok"], "sim_outcome": s["outcome"], "func_pass": func,
                "yosys_ok": y["ok"], "yosys_error": y.get("error"), "latch_events": y["latch_events"],
                "latch_cells": y["latch_cells"], "yosys_loops": y["loops"],
                "verilator_codes": v["codes"], "verilator_warnings_count": v["n_warnings"],
                "verilator_hard": v["n_hard"], "struct_clean": clean, "clean_pass": func and clean,
                "silent_structural_pass": func and not clean,
                "_logs": {"sim": s["log"], "verilator": v["log"], "yosys": y["log"]}}
    finally:
        if own and not keep:
            shutil.rmtree(wd, ignore_errors=True)
