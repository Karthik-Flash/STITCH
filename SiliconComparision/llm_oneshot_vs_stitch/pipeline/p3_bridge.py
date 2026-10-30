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
The runner's urllib is wrapped too (one-shot uses the same runner client, so both paths go through it):
  - every /api/chat body gets options.num_thread = THREADS (CPU threads, not a sampling option; Phase 3 sent none and
    llama-server ran 64 threads on 8 CPUs, about 5 tokens/s); the timeout is CLIENT_TIMEOUT_S for both paths
  - a request body that already timed out once in this process fails at once, so the runner's 3 retries do not
    repeat an hour-long call
  - each response's done_reason and token counts are kept and written to <iter dir>/llm_meta.json by the next
    evaluate() (one-shot reads them with pop_chat_meta())
  - after the first call: print the GPU layer-offload line and llama-server's n_threads from $OLLAMA_SERVE_LOG and
    the generation speed; exit 3 if n_threads != THREADS or speed < MIN_TOK_S, warn below WARN_TOK_S
"""
from __future__ import annotations

import glob
import hashlib
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
THREADS = int(os.environ.get("SLURM_CPUS_PER_TASK") or 4)     # = LLAMA_ARG_THREADS in hpc_env.sh
CLIENT_TIMEOUT_S = 3600                                         # both paths; Phase 3 used 900
MIN_TOK_S, WARN_TOK_S = 8.0, 15.0
_CHAT = {"last": None, "calls": 0, "timed_out": set()}


def _serve_log() -> str | None:
    log = os.environ.get("OLLAMA_SERVE_LOG", "")
    return open(log, errors="replace").read() if log and os.path.exists(log) else None


def gpu_offload_line() -> str:
    text = _serve_log()
    if text is None:
        return f"no server log ({os.environ.get('OLLAMA_SERVE_LOG') or 'OLLAMA_SERVE_LOG unset'})"
    hits = re.findall(r"offloaded \d+/\d+ layers to GPU", text)
    return hits[-1] if hits else "no layer-offload line in the server log"


def first_call_checks(meta: dict) -> None:
    """Print offload, n_threads and speed of the first call; SystemExit(3) on wrong threads or speed < MIN_TOK_S."""
    line = gpu_offload_line()
    m = re.match(r"offloaded (\d+)/(\d+)", line)
    print(f"[gpu offload] {line}{' WARNING: partial offload' if m and m.group(1) != m.group(2) else ''}", flush=True)
    meta["gpu_offload"] = line
    fail = []
    text = _serve_log()
    if text is not None:
        nt = re.findall(r"n_threads = (\d+) \(n_threads_batch = (\d+)\) / (\d+)", text)
        meta["llama_n_threads"] = "n_threads = %s (n_threads_batch = %s) / %s" % nt[-1] if nt else None
        ok = bool(nt) and int(nt[-1][0]) == THREADS and int(nt[-1][1]) == THREADS
        print(f"[threads] {'ok ' if ok else 'BAD'} llama-server {meta['llama_n_threads']} (configured {THREADS})",
              flush=True)
        if not ok:
            fail.append("n_threads")
    else:
        print("[threads] no server log: n_threads not checked", flush=True)
    rate = meta["eval_count"] / (meta["eval_duration"] / 1e9) if meta.get("eval_count") and meta.get("eval_duration") \
        else None
    meta["tok_s"] = round(rate, 2) if rate else None
    tag = "BAD" if rate is not None and rate < MIN_TOK_S else ("WARNING" if rate is not None and rate < WARN_TOK_S
                                                               else "ok ")
    print(f"[speed] {tag} {meta['tok_s']} tok/s generation (eval_count/eval_duration, model load excluded; "
          f"exit below {MIN_TOK_S}, warn below {WARN_TOK_S})", flush=True)
    if tag == "BAD":
        fail.append("speed")
    if fail:
        print(f"FIRST-CALL CHECK FAILED: {', '.join(fail)}", flush=True)
        raise SystemExit(3)


def _is_timeout(e: BaseException) -> bool:
    return isinstance(e, TimeoutError) or isinstance(getattr(e, "reason", None), TimeoutError)


def _urlopen(req, timeout=None):
    """urllib.request.urlopen (looked up at call time) for the runner client: adds options.num_thread to /api/chat,
    fails fast on a body that already timed out, keeps the response metadata."""
    if not getattr(req, "full_url", "").endswith("/api/chat"):
        return urllib.request.urlopen(req, timeout=timeout)
    key = hashlib.sha256(req.data).hexdigest()
    if key in _CHAT["timed_out"]:
        raise TimeoutError("identical /api/chat request already timed out in this process (fast fail)")
    body = json.loads(req.data)
    body.setdefault("options", {})["num_thread"] = THREADS
    req = urllib.request.Request(req.full_url, data=json.dumps(body).encode(), headers=dict(req.header_items()))
    try:
        r = urllib.request.urlopen(req, timeout=timeout)
        with r:
            data = r.read()
    except Exception as e:
        if _is_timeout(e):
            _CHAT["timed_out"].add(key)
        raise
    j = json.loads(data)
    _CHAT["last"] = {k: j.get(k) for k in CHAT_META}
    _CHAT["calls"] += 1
    if _CHAT["calls"] == 1:
        first_call_checks(_CHAT["last"])
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
