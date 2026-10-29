"""Bridge to the frozen Phase 3 code (phase3/runner, src/interpreter), used by import only, never edited.

p3_eval.evaluate() compiles, lints and synthesises dut.v alone. A parent module needs its children, so for a task
with a lib/ folder (tasks/<m>/lib/*.v = golden/reference children, tasks/<m>/stubs/*.v = port-only stubs) the
three tool calls are wrapped:
  simulate : dut.v + lib/*.v + tb.v              (children behave exactly as the reference)
  lint     : dut.v + stubs/*.v                   (only the parent's own warnings are counted)
  synth    : dut.v, stubs read with -lib         (children are black boxes: only the parent's own latches count)
A task without lib/ (every leaf, and the three Phase 3 registers) runs through p3_eval unchanged.
The lib/ and stubs/ files live inside the task folder, so the runner's strip_paths() removes their paths from
any feedback text.
"""
from __future__ import annotations

import glob
import os
import sys

STUDY = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REPO = os.path.dirname(os.path.dirname(STUDY))
# Where outputs/, prompts/, runs/ and reports/SUMMARY.md go. Default: the study folder. The local mock test sets
# GEN_WORK to a scratch folder so it never writes into the real outputs.
WORK = os.path.abspath(os.environ.get("GEN_WORK") or STUDY)
RUNNER = os.path.join(REPO, "phase3", "runner")
INTERP = os.environ.get("STITCH_INTERPRETER_DIR") or os.path.join(REPO, "src", "interpreter")
os.environ.setdefault("STITCH_INTERPRETER_DIR", INTERP)
for p in (RUNNER, INTERP):
    if p not in sys.path:
        sys.path.insert(0, p)

import p3_eval as E  # noqa: E402

_ORIG = {"simulate": E.simulate, "lint": E.lint, "synth": E.synth, "evaluate": E.evaluate}
_CTX = {"lib": [], "stubs": []}


def task_files(task_dir: str) -> tuple[list[str], list[str]]:
    lib = sorted(glob.glob(os.path.join(os.path.abspath(task_dir), "lib", "*.v")))
    stubs = sorted(glob.glob(os.path.join(os.path.abspath(task_dir), "stubs", "*.v")))
    return lib, stubs


def _simulate(design_files, tb_file, cwd, timeout=60):
    return _ORIG["simulate"](list(design_files) + _CTX["lib"], tb_file, cwd, timeout)


def _lint(design_files, top, cwd, timeout=60):
    return _ORIG["lint"](list(design_files) + _CTX["stubs"], top, cwd, timeout)


def _synth(design_files, top, cwd, timeout=600, lib_files=()):
    return _ORIG["synth"](design_files, top, cwd, timeout, tuple(lib_files) + tuple(_CTX["stubs"]))


E.simulate, E.lint, E.synth = _simulate, _lint, _synth


def evaluate(candidate_file, task_dir, top, workdir=None, keep=False):
    """p3_eval.evaluate with the task's children added (no-op for tasks without lib/)."""
    _CTX["lib"], _CTX["stubs"] = task_files(task_dir)
    try:
        return _ORIG["evaluate"](candidate_file, task_dir, top, workdir=workdir, keep=keep)
    finally:
        _CTX["lib"], _CTX["stubs"] = [], []


def simulate_with(candidate_file, tb_file, task_dir, workdir, timeout=600):
    """One simulation of candidate + task children against an arbitrary testbench (sign-off oracle)."""
    import shutil
    os.makedirs(workdir, exist_ok=True)
    shutil.copy(candidate_file, os.path.join(workdir, "dut.v"))
    shutil.copy(tb_file, os.path.join(workdir, "tb.v"))
    lib, _ = task_files(task_dir)
    return _ORIG["simulate"](["dut.v"] + lib, "tb.v", workdir, timeout)


def runner():
    """The Phase 3 runner module with its evaluate() routed through this bridge."""
    import stitch_runner_p3 as R
    R.evaluate = evaluate
    return R
