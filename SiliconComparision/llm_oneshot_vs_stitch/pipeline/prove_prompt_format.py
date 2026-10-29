#!/usr/bin/env python3
"""Prove with the mock backend that run_arms' wrapper sends byte-identical prompts to the Phase 3 runner.

A: phase3/runner/stitch_runner_p3.py run as a plain script (subprocess). It reads tasks from <its folder>/../tasks,
   so the runner folder is copied byte for byte (hash-checked) next to a copy of the task; nothing in phase3/ is
   written. The task is phase3/tasks/<task> when present, else this study's tasks/<task> (on the HPC only
   phase3/runner is shipped).
B: the original runner imported through p3_bridge (as run_arms.py does), TASKS_DIR pointed at the same task copy.
Both: --backend mock --mock-mode fix_on_2, conditions baseline + sem_esc_restart_v3, N=1, budget 6, production system
prompt. Every iter*/prompt.txt and every per-iteration metric must be equal. Exit 0 only if they are.
Usage: python pipeline/prove_prompt_format.py [--task register_32bit]
"""
from __future__ import annotations

import argparse
import glob
import json
import os
import shutil
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import p3_bridge as B  # noqa: E402

COMMON = ["--backend", "mock", "--mock-mode", "fix_on_2", "--model", "proof", "--conditions", "baseline",
          "sem_esc_restart_v3", "--reps", "1", "--max-iters", "6", "--system-prompt-file",
          os.path.join(B.REPO, "phase3", "runner", "system_prompt.txt")]


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--task", default="register_32bit")
    a = ap.parse_args()
    src = os.path.join(B.REPO, "phase3", "tasks", a.task)
    src = src if os.path.isdir(src) else os.path.join(B.STUDY, "tasks", a.task)
    with tempfile.TemporaryDirectory(prefix="prove_") as tmp:
        tasks = os.path.join(tmp, "phase3", "tasks")
        shutil.copytree(src, os.path.join(tasks, a.task))
        runner_copy = os.path.join(tmp, "phase3", "runner")
        shutil.copytree(B.RUNNER, runner_copy, ignore=shutil.ignore_patterns("__pycache__"))
        for f in ("stitch_runner_p3.py", "p3_eval.py"):
            assert open(os.path.join(B.RUNNER, f), "rb").read() == open(os.path.join(runner_copy, f), "rb").read()
        out_a, out_b = os.path.join(tmp, "A"), os.path.join(tmp, "B")
        env = {**os.environ, "PYTHONDONTWRITEBYTECODE": "1", "STITCH_INTERPRETER_DIR": B.INTERP}
        subprocess.run([sys.executable, os.path.join(runner_copy, "stitch_runner_p3.py"), *COMMON, "--tasks", a.task,
                        "--out", out_a], check=True, env=env, stdout=subprocess.DEVNULL)
        code = ("import sys; sys.path.insert(0, sys.argv[1]); import p3_bridge as B; R = B.runner(); "
                "R.TASKS_DIR = sys.argv[2]; sys.argv = ['stitch_runner_p3.py'] + sys.argv[3:]; R.main()")
        subprocess.run([sys.executable, "-c", code, HERE, tasks, *COMMON, "--tasks", a.task, "--out", out_b],
                       check=True, env=env, stdout=subprocess.DEVNULL)
        pa = sorted(os.path.relpath(p, out_a) for p in glob.glob(os.path.join(out_a, "**", "prompt.txt"), recursive=True))
        pb = sorted(os.path.relpath(p, out_b) for p in glob.glob(os.path.join(out_b, "**", "prompt.txt"), recursive=True))
        same = pa == pb and all(open(os.path.join(out_a, p), "rb").read() == open(os.path.join(out_b, p), "rb").read()
                                for p in pa)
        keys = ("iterations", "stop_reason", "func_pass", "clean_pass", "semantic_fired", "classes_fired")
        ma = {os.path.relpath(p, out_a): json.load(open(p)) for p in glob.glob(os.path.join(out_a, "**", "metrics.json"), recursive=True)}
        mb = {os.path.relpath(p, out_b): json.load(open(p)) for p in glob.glob(os.path.join(out_b, "**", "metrics.json"), recursive=True)}
        metrics_same = ma.keys() == mb.keys() and all({k: ma[p][k] for k in keys} == {k: mb[p][k] for k in keys}
                                                      for p in ma)
        sp_same = all(ma[p]["provenance"]["system_prompt_sha256_lf"] == mb[p]["provenance"]["system_prompt_sha256_lf"]
                      for p in ma)
        print(f"task {a.task} (from {os.path.relpath(src, B.REPO)}): {len(pa)} prompts (A) vs {len(pb)} (B); byte-identical: {same}; "
              f"metrics identical: {metrics_same}; system prompt hash identical: {sp_same}")
        for p in ma:
            print(f"  {p}: " + ", ".join(f"{k}={ma[p][k]}" for k in keys))
        ok = same and metrics_same and sp_same and len(pa) > 0
        print("PROMPT FORMAT PROOF:", "PASS" if ok else "FAIL")
        return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
