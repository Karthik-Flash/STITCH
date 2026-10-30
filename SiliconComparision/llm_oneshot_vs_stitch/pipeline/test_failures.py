#!/usr/bin/env python3
"""Failure handling and first-call checks, with mock LLMs in a scratch GEN_WORK folder (run by gate.py as G5).

  A resume: finished records are skipped (also one without a status field, as written before statuses existed);
    an empty folder (op_core after the A100 job) is generated
  B mock timeout on one module: record status=infra_error, no output, the other modules finish, exit 2;
    run_arms skips that module and exits 2; the summary shows INFRA; an arm folder left without metrics.json is moved
    to rep1.failed_*; a rerun with a working mock finishes everything and exits 0
  C p3_bridge: options.num_thread is added to the request; an identical body that timed out fails at once (one
    server call for the runner's 3 attempts); first call exits 3 on wrong n_threads or speed < 8 tok/s, warns < 15
Usage: python pipeline/test_failures.py
"""
from __future__ import annotations

import glob
import io
import json
import os
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
PY = sys.executable
CHECKS: dict[str, bool] = {}


def run(work: str, script: str, *args: str) -> int:
    env = {**os.environ, "GEN_WORK": work, "PYTHONDONTWRITEBYTECODE": "1"}
    print("==", script, " ".join(args), flush=True)
    return subprocess.run([PY, os.path.join(HERE, script), *args], env=env).returncode


def rec(work: str, m: str) -> dict:
    return json.load(open(os.path.join(work, "runs", "oneshot", m, "record.json")))


def resume_case() -> None:
    work = tempfile.mkdtemp(prefix="gen_fail_a_")
    one = ["--backend", "mock", "--model", "mock"]
    run(work, "oneshot_gen.py", *one, "--modules", "encoder", "mux")
    r = rec(work, "mux")
    r.pop("status")                                   # a record from before statuses existed
    json.dump(r, open(os.path.join(work, "runs", "oneshot", "mux", "record.json"), "w"))
    os.makedirs(os.path.join(work, "runs", "oneshot", "op_core"))
    t_enc = os.path.getmtime(os.path.join(work, "runs", "oneshot", "encoder", "record.json"))
    rc = run(work, "oneshot_gen.py", *one, "--modules", "encoder", "mux", "op_core")
    CHECKS["A: rerun exits 0"] = rc == 0
    CHECKS["A: finished record skipped"] = os.path.getmtime(
        os.path.join(work, "runs", "oneshot", "encoder", "record.json")) == t_enc
    CHECKS["A: record without status counts as finished"] = "status" not in rec(work, "mux")
    CHECKS["A: empty op_core folder generated"] = rec(work, "op_core").get("status") == "ok" and \
        os.path.exists(os.path.join(work, "outputs", "oneshot", "op_core.v"))


def timeout_case() -> None:
    work = tempfile.mkdtemp(prefix="gen_fail_b_")
    mods = ["encoder", "register_4bit", "allot_vc"]
    one = ["--backend", "mock", "--model", "mock", "--modules", *mods]
    arms = ["--backend", "mock", "--mock-mode", "fix_on_2", "--model", "mock", "--modules", *mods]
    rc = run(work, "oneshot_gen.py", *one, "--mock-plan", "register_4bit=timeout")
    CHECKS["B: one-shot exits 2 with an infra error"] = rc == 2
    CHECKS["B: record status infra_error, no output"] = rec(work, "register_4bit")["status"] == "infra_error" and \
        not os.path.exists(os.path.join(work, "outputs", "oneshot", "register_4bit.v"))
    CHECKS["B: other modules finished"] = all(rec(work, m)["status"] == "ok" for m in ("encoder", "allot_vc"))
    stale = os.path.join(work, "runs", "arms", "results", "mock", "baseline", "allot_vc", "rep1", "iter5")
    os.makedirs(stale)
    json.dump({"done_reason": "stale"}, open(os.path.join(stale, "llm_meta.json"), "w"))
    rc = run(work, "run_arms.py", *arms)
    res = os.path.join(work, "runs", "arms", "results", "mock")
    CHECKS["B: run_arms exits 2 and skips the failed module"] = rc == 2 and \
        not os.path.exists(os.path.join(res, "baseline", "register_4bit"))
    CHECKS["B: other arm runs finished"] = all(os.path.exists(os.path.join(res, c, m, "rep1", "metrics.json"))
                                               for c in ("baseline", "sem_esc_restart_v3") for m in ("encoder", "allot_vc"))
    CHECKS["B: folder without metrics moved aside, no stale iteration left"] = \
        bool(glob.glob(os.path.join(res, "baseline", "allot_vc", "rep1.failed_*", "iter5"))) and \
        not os.path.exists(os.path.join(res, "baseline", "allot_vc", "rep1", "iter5"))
    run(work, "summarize.py", "--model", "mock", "--modules", *mods)
    s = json.load(open(os.path.join(work, "reports", "summary.json")))
    row = {r["module"]: r for r in s["rows"]}["register_4bit"]
    CHECKS["B: summary shows INFRA"] = row["oneshot"] is None and row["status"]["oneshot"] == "INFRA" and \
        "| register_4bit | INFRA |" in open(os.path.join(work, "reports", "SUMMARY.md")).read()
    rc1 = run(work, "oneshot_gen.py", *one, "--mock-plan", "register_4bit=handwritten")
    rc2 = run(work, "run_arms.py", *arms)
    CHECKS["B: resubmit retries the infra error and finishes (exit 0, 0)"] = (rc1, rc2) == (0, 0) and \
        rec(work, "register_4bit")["status"] == "ok" and \
        all(os.path.exists(os.path.join(res, c, "register_4bit", "rep1", "metrics.json"))
            for c in ("baseline", "sem_esc_restart_v3"))


def bridge_case() -> None:
    import urllib.request
    sys.path.insert(0, HERE)
    import p3_bridge as B
    R = B.runner()
    R.time.sleep, real_sleep = (lambda s: None), R.time.sleep
    real_open = urllib.request.urlopen
    log = os.path.join(tempfile.mkdtemp(prefix="gen_fail_c_"), "serve.log")
    os.environ["OLLAMA_SERVE_LOG"] = log
    B.THREADS = 4
    sent = []

    def reply(rate, threads):
        open(log, "w").write(f"load_tensors: offloaded 65/65 layers to GPU\nsystem_info: n_threads = {threads} "
                             f"(n_threads_batch = {threads}) / 64 | CPU\n")

        def fake(req, timeout=None):
            sent.append(json.loads(req.data))
            return io.BytesIO(json.dumps({"message": {"content": "x"}, "prompt_eval_count": 10, "eval_count": 100,
                                          "eval_duration": int(100 / rate * 1e9), "done_reason": "stop"}).encode())
        return fake

    def first_call(rate, threads):
        B._CHAT.update(calls=0, last=None)
        urllib.request.urlopen = reply(rate, threads)
        try:
            R.Ollama("m", "http://h", 0.1, 32768, 3600).chat("s", "u")
            return 0
        except SystemExit as e:
            return e.code
        finally:
            urllib.request.urlopen = real_open

    try:
        CHECKS["C: 20 tok/s and 4 threads pass"] = first_call(20, 4) == 0
        CHECKS["C: num_thread added to the request"] = sent[-1]["options"] == {"temperature": 0.1, "num_ctx": 32768,
                                                                               "num_thread": 4}
        CHECKS["C: 10 tok/s passes (warning only)"] = first_call(10, 4) == 0
        CHECKS["C: 5 tok/s exits 3"] = first_call(5, 4) == 3
        CHECKS["C: n_threads 64 exits 3"] = first_call(20, 64) == 3
        calls = []

        def slow(req, timeout=None):
            calls.append(1)
            raise TimeoutError("timed out")
        urllib.request.urlopen = slow
        try:
            R.Ollama("m", "http://h", 0.1, 32768, 3600).chat("s", "slow prompt")
            raised = False
        except RuntimeError:
            raised = True
        CHECKS["C: timeout fails fast (1 server call for 3 attempts)"] = raised and len(calls) == 1
    finally:
        urllib.request.urlopen, R.time.sleep = real_open, real_sleep


def main() -> int:
    resume_case()
    timeout_case()
    bridge_case()
    for k, v in CHECKS.items():
        print(f"  {'ok ' if v else 'BAD'} {k}")
    ok = all(CHECKS.values())
    print("FAILURE HANDLING:", "PASS" if ok else "FAIL")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
