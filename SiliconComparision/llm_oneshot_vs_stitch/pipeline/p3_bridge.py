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
The runner's urllib is wrapped too, without changing the request: each /api/chat response's done_reason and token
counts are kept and written to <iter dir>/llm_meta.json by the next evaluate() (one-shot reads them with
pop_chat_meta()). After the first call of a process, the GPU layer-offload line of $OLLAMA_SERVE_LOG is printed.
"""
from __future__ import annotations

import glob
import io
import json
import os
import re
import sys
import types
import urllib.request

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


CHAT_META = ("done_reason", "prompt_eval_count", "eval_count", "total_duration", "load_duration", "eval_duration")
_CHAT = {"last": None, "calls": 0}


def gpu_offload_line() -> str:
    log = os.environ.get("OLLAMA_SERVE_LOG", "")
    if not os.path.exists(log):
        return f"no server log ({log or 'OLLAMA_SERVE_LOG unset'})"
    hits = re.findall(r"offloaded \d+/\d+ layers to GPU", open(log, errors="replace").read())
    return hits[-1] if hits else "no layer-offload line in the server log"


def _urlopen(req, timeout=None):
    """urllib.request.urlopen (looked up at call time) that keeps /api/chat response metadata; request unchanged."""
    r = urllib.request.urlopen(req, timeout=timeout)
    if not getattr(req, "full_url", "").endswith("/api/chat"):
        return r
    with r:
        data = r.read()
    j = json.loads(data)
    _CHAT["last"] = {k: j.get(k) for k in CHAT_META}
    _CHAT["calls"] += 1
    if _CHAT["calls"] == 1:
        line = gpu_offload_line()
        m = re.match(r"offloaded (\d+)/(\d+)", line)
        partial = " WARNING: partial offload" if m and m.group(1) != m.group(2) else ""
        print(f"[gpu offload] {line}{partial}", flush=True)
        _CHAT["last"]["gpu_offload"] = line
    return io.BytesIO(data)


def pop_chat_meta() -> dict:
    meta, _CHAT["last"] = _CHAT["last"], None
    return meta or {}


def evaluate(candidate_file, task_dir, top, workdir=None, keep=False):
    """p3_eval.evaluate with the task's children added (no-op for tasks without lib/). Writes the metadata of the LLM
    call that produced this candidate to <workdir>/llm_meta.json."""
    meta = pop_chat_meta()
    if meta and workdir:
        json.dump(meta, open(os.path.join(workdir, "llm_meta.json"), "w"), indent=1)
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
    R.urllib = types.SimpleNamespace(request=types.SimpleNamespace(urlopen=_urlopen, Request=urllib.request.Request))
    return R
