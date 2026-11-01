#!/usr/bin/env python3
"""Job preflight, run by gen_job.slurm after the gate and after `ollama serve` is up, before any generation.

  0. GPU (nvidia-smi name, memory.total): fails below 40 GiB, so the 32b model and its 32k KV cache stay on the GPU;
     GEN_TASKS (comma-separated task names, empty = all): fails on an unknown name
  1. python3 imports the runner needs (stitch_runner_p3, p3_eval, stitch_interpreter_v3 through p3_bridge)
  2. tool versions (yosys, verilator, iverilog, python, ollama server)
  3. model digest from /api/tags == the digest Phase 3 recorded for the model; fails otherwise
  4. the Ollama request options of run_arms.py and oneshot_gen.py, captured from gen_job.slurm's own command lines;
     fails if they differ
  5. writes runs/RUN_MANIFEST.json: git commit, hostname, job id, GPU, GEN_TASKS, tool versions, Ollama version,
     model digest, generation options
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
MIN_GPU_MIB = 40 * 1024


def gpus() -> tuple[str, list[dict]]:
    try:
        raw = subprocess.run(["nvidia-smi", "--query-gpu=name,memory.total", "--format=csv"], capture_output=True,
                             text=True, timeout=60).stdout.strip()
    except (OSError, subprocess.TimeoutExpired) as e:
        return f"nvidia-smi failed ({e.__class__.__name__})", []
    rows = [l.rsplit(",", 1) for l in raw.splitlines()[1:] if "," in l]
    return raw, [{"name": n.strip(), "memory_total_mib": int(m.split()[0])} for n, m in rows]


def gen_tasks(study: str) -> tuple[list[str], list[str]]:
    names = [t.strip() for t in os.environ.get("GEN_TASKS", "").split(",") if t.strip()]
    return names, [t for t in names if not os.path.isdir(os.path.join(study, "tasks", t))]


def get(url: str):
    with urllib.request.urlopen(url, timeout=30) as r:
        return json.loads(r.read())


def git_commit(study: str) -> str:
    # written by deploy_gen.ps1 in the study root (no .git on the cluster); mesh3x3/ and ni/ read the same file
    f = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "DEPLOYED_COMMIT.txt")
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
    raw, gpu = gpus()
    good = bool(gpu) and all(g["memory_total_mib"] >= MIN_GPU_MIB for g in gpu)
    ok &= good
    print(f"[gpu] {'ok ' if good else 'BAD'} {gpu or raw} (need >= {MIN_GPU_MIB} MiB each)")
    tasks, unknown = gen_tasks(B.STUDY)
    ok &= not unknown
    print(f"[tasks] {'BAD unknown: ' + ','.join(unknown) if unknown else 'ok '} GEN_TASKS="
          f"{','.join(tasks) if tasks else '(empty = all)'}")

    R = B.runner()
    print(f"[imports] ok: stitch_runner_p3 ({R.__file__}), p3_eval ({B.E.__file__}), "
          f"stitch_interpreter_v3 {R.IV3.V3_VERSION} ({R.IV3.__file__})")

    tools = {"yosys": R._version([B.E.YOSYS, "-V"]), "verilator": R._version([B.E.VERILATOR, "--version"]),
             "iverilog": R._version([B.E.IVERILOG, "-V"])}
    lat = os.environ.get("LLAMA_ARG_THREADS")
    good = lat is not None and int(lat) == B.THREADS == int(os.environ.get("LLAMA_ARG_THREADS_BATCH") or -1)
    if os.environ.get("SLURM_JOB_ID"):                  # on the cluster both mechanisms must agree
        ok &= good
    print(f"[threads] {'ok ' if good else 'BAD'} LLAMA_ARG_THREADS={lat} LLAMA_ARG_THREADS_BATCH="
          f"{os.environ.get('LLAMA_ARG_THREADS_BATCH')} options.num_thread={B.THREADS} "
          f"(SLURM_CPUS_PER_TASK={os.environ.get('SLURM_CPUS_PER_TASK')})")
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
    same = bodies["runner via run_arms"] == bodies["oneshot_gen"] and \
        bodies["oneshot_gen"]["options"].get("num_thread") == B.THREADS and \
        bodies["oneshot_gen"]["client_http_timeout_s"] == B.CLIENT_TIMEOUT_S
    ok &= same
    for k, v in bodies.items():
        print(f"[options] {k}: {json.dumps(v, sort_keys=True)}")
    print(f"[options] {'ok ' if same else 'BAD'} run_arms and oneshot_gen send the same request options "
          f"(num_thread {B.THREADS}, client timeout {B.CLIENT_TIMEOUT_S} s)")

    manifest = {"timestamp": dt.datetime.now().isoformat(timespec="seconds"), "git_commit": git_commit(B.STUDY),
                "hostname": socket.gethostname(), "slurm_job_id": os.environ.get("SLURM_JOB_ID"),
                "gpu": gpu, "gpu_query": raw, "gen_tasks": tasks or "all",
                "cpu_threads": {"SLURM_CPUS_PER_TASK": os.environ.get("SLURM_CPUS_PER_TASK"),
                                "LLAMA_ARG_THREADS": os.environ.get("LLAMA_ARG_THREADS"),
                                "LLAMA_ARG_THREADS_BATCH": os.environ.get("LLAMA_ARG_THREADS_BATCH"),
                                "options.num_thread (p3_bridge)": B.THREADS},
                "client_timeout_s": B.CLIENT_TIMEOUT_S,
                "first_call_checks": {"exit_below_tok_s": B.MIN_TOK_S, "warn_below_tok_s": B.WARN_TOK_S,
                                      "n_threads_must_equal": B.THREADS},
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
