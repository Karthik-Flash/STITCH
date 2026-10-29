#!/usr/bin/env python3
"""Job preflight, run by gen_job.slurm after the gate and after `ollama serve` is up, before any generation.

  1. python3 imports the runner needs (stitch_runner_p3, p3_eval, stitch_interpreter_v3 through p3_bridge)
  2. tool versions (yosys, verilator, iverilog, python, ollama server)
  3. model digest from /api/tags == the digest Phase 3 recorded for the model; fails otherwise
  4. the Ollama request options of run_arms.py and oneshot_gen.py, captured from gen_job.slurm's own command lines;
     fails if they differ
  5. writes runs/RUN_MANIFEST.json: git commit, hostname, job id, tool versions, Ollama version, model digest,
     generation options
Exit 0 only if every check passes. Usage: python3 pipeline/preflight.py --model qwen2.5-coder:32b --host http://...
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import os
import platform
import socket
import subprocess
import sys
import urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

# Phase 3 recorded digest: provenance.model_digest of all 198 phase3/results/phase3_32b runs (checked by budget.py).
PHASE3_DIGEST = {"qwen2.5-coder:32b": "b92d6a0bd47ee79114298de0177bf920c05a706d12633950b3936778492bef41"}


def get(url: str):
    with urllib.request.urlopen(url, timeout=30) as r:
        return json.loads(r.read())


def git_commit(study: str) -> str:
    f = os.path.join(study, "DEPLOYED_COMMIT.txt")             # written by deploy_gen.ps1 (no .git on the cluster)
    if os.path.exists(f):
        return open(f).read().strip()
    p = subprocess.run(["git", "rev-parse", "HEAD"], cwd=study, capture_output=True, text=True)
    return p.stdout.strip() or "UNKNOWN"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--model", default="qwen2.5-coder:32b")
    ap.add_argument("--host", default="http://" + os.environ.get("OLLAMA_HOST", "127.0.0.1:11434"))
    a = ap.parse_args()
    ok = True

    import p3_bridge as B
    R = B.runner()
    print(f"[imports] ok: stitch_runner_p3 ({R.__file__}), p3_eval ({B.E.__file__}), "
          f"stitch_interpreter_v3 {R.IV3.V3_VERSION} ({R.IV3.__file__})")

    tools = {"yosys": R._version([B.E.YOSYS, "-V"]), "verilator": R._version([B.E.VERILATOR, "--version"]),
             "iverilog": R._version([B.E.IVERILOG, "-V"])}
    tools["python"] = f"{platform.python_version()} ({sys.executable})"
    ollama_version = get(a.host + "/api/version").get("version", "?")
    tools["ollama"] = ollama_version
    for k, v in tools.items():
        print(f"[tools] {k}: {v}")

    tags = {t["name"]: t["digest"] for t in get(a.host + "/api/tags")["models"]}
    digest, want = tags.get(a.model, "NOT_LISTED"), PHASE3_DIGEST.get(a.model)
    good = want is not None and digest == want
    ok &= good
    print(f"[digest] {'ok ' if good else 'BAD'} {a.model}: {digest} (Phase 3: {want or 'none recorded'})")

    import budget
    bodies = budget.study_bodies(a.model)
    argv = bodies.pop("_argv")
    same = bodies["runner via run_arms"] == bodies["oneshot_gen"]
    ok &= same
    for k, v in bodies.items():
        print(f"[options] {k}: {json.dumps(v, sort_keys=True)}")
    print(f"[options] {'ok ' if same else 'BAD'} run_arms and oneshot_gen send the same request options")

    manifest = {"timestamp": dt.datetime.now().isoformat(timespec="seconds"), "git_commit": git_commit(B.STUDY),
                "hostname": socket.gethostname(), "slurm_job_id": os.environ.get("SLURM_JOB_ID"),
                "tool_versions": tools, "ollama_version": ollama_version, "model": a.model, "model_digest": digest,
                "phase3_digest": want, "generation_options": bodies["oneshot_gen"],
                "generation_options_run_arms": bodies["runner via run_arms"], "job_argv": argv,
                "preflight_ok": bool(ok)}
    os.makedirs(os.path.join(B.WORK, "runs"), exist_ok=True)
    path = os.path.join(B.WORK, "runs", "RUN_MANIFEST.json")
    for p in (path, os.path.join(B.WORK, "runs", f"RUN_MANIFEST_{manifest['slurm_job_id'] or 'local'}.json")):
        json.dump(manifest, open(p, "w"), indent=1)                      # latest + one per (re)submitted job
    print(f"[manifest] {path}")
    print("PREFLIGHT: " + ("ALL PASSED" if ok else "FAIL"))
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
