#!/usr/bin/env python3
"""Run the two feedback arms on the one-shot outputs through the unmodified Phase 3 runner.

  simloop = Phase 3 `baseline` (simulation feedback only, stops at func_pass)
  stitch  = Phase 3 `sem_esc_restart_v3`
Budget 6 LLM calls, N = 1, T = 0.1, system prompt phase3/runner/system_prompt.txt.

For each module a per-run copy of tasks/<m> is made under <out>/tasks/<m> with input.v = outputs/oneshot/<m>.v
(the committed tasks/ stay untouched). The runner is imported, its TASKS_DIR is pointed at that copy and its
evaluate() is routed through p3_bridge (children from lib/); stitch_runner_p3.py itself is not edited.
Final candidates are copied to outputs/simloop/<m>.v and outputs/stitch/<m>.v. Provenance (model digest, tool
versions, interpreter/runner hashes, every task file hash) goes to <out>/provenance.json; each run's metrics.json
also carries the runner's own provenance block. Resumable: runs with a metrics.json are skipped.

Usage: python pipeline/run_arms.py --model qwen2.5-coder:32b [--host ...] [--modules a b] [--out runs/arms]
       python pipeline/run_arms.py --backend mock --mock-mode fix_on_2 --model mock ...
"""
from __future__ import annotations

import argparse
import datetime as dt
import glob
import hashlib
import json
import os
import re
import shutil
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import p3_bridge as B  # noqa: E402

STUDY = B.STUDY
ARMS = {"baseline": "simloop", "sem_esc_restart_v3": "stitch"}
SYSTEM_PROMPT_FILE = os.path.join(B.REPO, "phase3", "runner", "system_prompt.txt")


def sha256_lf(path: str) -> str:
    return hashlib.sha256(open(path, "rb").read().replace(b"\r\n", b"\n")).hexdigest()


def safe(model: str) -> str:
    return re.sub(r"[^A-Za-z0-9_.-]", "_", model)


def prepare_tasks(modules: list[str], out: str) -> str:
    tdir = os.path.join(out, "tasks")
    for m in modules:
        src, dst = os.path.join(STUDY, "tasks", m), os.path.join(tdir, m)
        oneshot = os.path.join(B.WORK, "outputs", "oneshot", f"{m}.v")
        if not os.path.exists(oneshot):
            raise SystemExit(f"missing one-shot output {oneshot}: run oneshot_gen.py first")
        if os.path.isdir(dst):
            if sha256_lf(os.path.join(dst, "input.v")) != sha256_lf(oneshot):
                raise SystemExit(f"{dst}/input.v differs from {oneshot}: use a new --out for a new generation")
            continue
        shutil.copytree(src, dst)
        shutil.copyfile(oneshot, os.path.join(dst, "input.v"))
    return tdir


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--model", default="qwen2.5-coder:32b")
    ap.add_argument("--backend", choices=["ollama", "mock"], default="ollama")
    ap.add_argument("--mock-mode", choices=["golden", "echo", "fix_on_2"], default="fix_on_2")
    ap.add_argument("--host", default=os.environ.get("OLLAMA_HOST", "http://127.0.0.1:11434"))
    ap.add_argument("--modules", nargs="*", default=None)
    ap.add_argument("--max-iters", type=int, default=6)
    ap.add_argument("--reps", type=int, default=1)
    ap.add_argument("--temperature", type=float, default=0.1)
    ap.add_argument("--num-ctx", type=int, default=32768)
    ap.add_argument("--out", default=os.path.join(B.WORK, "runs", "arms"))
    a = ap.parse_args()
    if not a.host.startswith("http"):
        a.host = "http://" + a.host

    modules = a.modules or sorted(os.listdir(os.path.join(STUDY, "tasks")))
    modules = [m for m in modules if os.path.isdir(os.path.join(STUDY, "tasks", m))]
    out = os.path.abspath(a.out)
    os.makedirs(out, exist_ok=True)
    R = B.runner()
    R.TASKS_DIR = prepare_tasks(modules, out)
    argv = ["stitch_runner_p3.py", "--model", a.model, "--backend", a.backend, "--mock-mode", a.mock_mode,
            "--host", a.host, "--conditions", *ARMS, "--tasks", *modules, "--reps", str(a.reps),
            "--temperature", str(a.temperature), "--max-iters", str(a.max_iters), "--num-ctx", str(a.num_ctx),
            "--system-prompt-file", SYSTEM_PROMPT_FILE, "--out", os.path.join(out, "results")]
    print("runner argv:", " ".join(argv[1:]), flush=True)
    sys.argv = argv
    R.main()

    # Final candidates -> outputs/simloop, outputs/stitch
    for cond, arm in ARMS.items():
        os.makedirs(os.path.join(B.WORK, "outputs", arm), exist_ok=True)
        for m in modules:
            mp = os.path.join(out, "results", safe(a.model), cond, m, "rep1", "metrics.json")
            if os.path.exists(mp):
                final = json.load(open(mp))["final_candidate"]
                shutil.copyfile(final, os.path.join(B.WORK, "outputs", arm, f"{m}.v"))
            else:
                print(f"no metrics for {cond} {m} (see error.json)")

    prov = {"timestamp": dt.datetime.now().isoformat(timespec="seconds"), "model": a.model, "backend": a.backend,
            "mock_mode": a.mock_mode if a.backend == "mock" else None, "conditions": ARMS,
            "max_iters": a.max_iters, "reps": a.reps, "temperature": a.temperature, "num_ctx": a.num_ctx,
            "runner_static": R._STATIC, "model_digest": R._DIGEST.get(a.model),
            "pipeline_sha256_lf": {os.path.basename(p): sha256_lf(p)
                                   for p in sorted(glob.glob(os.path.join(STUDY, "pipeline", "*.py")))},
            "task_files_sha256_lf": {os.path.relpath(p, R.TASKS_DIR).replace(os.sep, "/"): sha256_lf(p)
                                     for p in sorted(glob.glob(os.path.join(R.TASKS_DIR, "**", "*.*"),
                                                               recursive=True)) if os.path.isfile(p)}}
    json.dump(prov, open(os.path.join(out, "provenance.json"), "w"), indent=1)
    print(f"provenance: {os.path.join(out, 'provenance.json')}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
