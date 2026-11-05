#!/usr/bin/env python3
"""Job preflight, run by hpc/gen_job.slurm after `ollama serve` is up and before any generation. Exit 0 only if every
check passes.

  [freeze]  every frozen file equals FREEZE.sha256 (pipeline/freeze.py)
  [gpu]     at least 40 GiB on each visible GPU
  [tools]   Yosys 0.69, Verilator 5.053, Icarus 14: the cluster versions the golden was checked on (smoke job 434111)
  [golden]  each task's golden.v through the pipeline's own evaluation (p3_bridge.evaluate: tb.v with the golden
            children, lint and synthesis with stubs) gives clean_pass, and it passes every sign-off testbench
  [digest]  the model's digest from /api/tags equals the one recorded for this study (hpc_logs/MODELS.txt)
  writes <work>/RUN_MANIFEST.json: deployed commit, host, job id, GPU, tools, Ollama version, model digest, settings
Usage: python3 pipeline/preflight.py --model qwen2.5-coder:32b --host http://127.0.0.1:11500
"""
import argparse
import datetime as dt
import json
import os
import socket
import subprocess
import sys
import tempfile
import urllib.request

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import freeze  # noqa: E402
import generate as G  # noqa: E402

B = G.B
# Digests from step 2 (hpc_logs/MODELS.txt, 2026-11-05) and the 198 Phase 3 runs (qwen).
DIGESTS = {"qwen2.5-coder:32b": "b92d6a0bd47ee79114298de0177bf920c05a706d12633950b3936778492bef41",
           "gemma4:31b-it-q4_K_M": "17ba34c06c801ba22f6047bab21ced9429c6d43e0e42ecf339b0f3e5a61e8d97"}
TOOLS = {"yosys": ([B.E.YOSYS, "-V"], "Yosys 0.69"), "verilator": ([B.E.VERILATOR, "--version"], "Verilator 5.053"),
         "iverilog": ([B.E.IVERILOG, "-V"], "Icarus Verilog version 14")}
MIN_GPU_MIB = 40 * 1024


def get(url):
    with urllib.request.urlopen(url, timeout=30) as r:
        return json.loads(r.read())


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--model", required=True, choices=sorted(DIGESTS))
    ap.add_argument("--host", required=True)
    a = ap.parse_args()
    bad = []

    n, frozen_bad = freeze.check()
    print(f"[freeze] {'ok ' if not frozen_bad else 'BAD'} {n} files" + (f": {', '.join(frozen_bad)}" if frozen_bad else ""))
    bad += ["freeze"] if frozen_bad else []

    raw = subprocess.run(["nvidia-smi", "--query-gpu=name,memory.total", "--format=csv,noheader,nounits"],
                         capture_output=True, text=True).stdout.strip()
    gpus = [l.rsplit(",", 1) for l in raw.splitlines() if "," in l]
    good = bool(gpus) and all(int(mib) >= MIN_GPU_MIB for _, mib in gpus)
    print(f"[gpu] {'ok ' if good else 'BAD'} {raw or 'nvidia-smi gave nothing'} (need >= {MIN_GPU_MIB} MiB)")
    bad += [] if good else ["gpu"]

    tools = {}
    for name, (cmd, want) in TOOLS.items():
        rc, out, _ = B.E._run(cmd, ".", 30)
        tools[name] = out.strip().splitlines()[0] if out.strip() else f"MISSING (rc={rc})"
        good = tools[name].startswith(want)
        print(f"[tools] {'ok ' if good else 'BAD'} {tools[name]} (want {want})")
        bad += [] if good else [name]

    for m in G.MODULES:
        td = os.path.join(G.TASKS, m)
        meta = json.load(open(os.path.join(td, "meta.json")))
        ev = B.evaluate(os.path.join(td, "golden.v"), td, m)
        so = {tb: B.simulate_with(os.path.join(td, "golden.v"), os.path.join(td, tb), td, tempfile.mkdtemp(prefix="pf_"))
              ["outcome"] for tb in meta["signoff_tbs"]}
        good = ev["clean_pass"] and all(v == "PASS" for v in so.values())
        print(f"[golden] {'ok ' if good else 'BAD'} {m}: tb.v {ev['sim_outcome']}, struct_clean {ev['struct_clean']}, "
              + ", ".join(f"{k} {v}" for k, v in so.items()))
        bad += [] if good else [f"golden {m}"]

    version = get(a.host + "/api/version").get("version")
    digest = {t["name"]: t["digest"] for t in get(a.host + "/api/tags")["models"]}.get(a.model, "NOT_LISTED")
    good = digest == DIGESTS[a.model]
    print(f"[digest] {'ok ' if good else 'BAD'} {a.model}: {digest} (recorded {DIGESTS[a.model]}), ollama {version}")
    bad += [] if good else ["digest"]

    work = os.path.abspath(os.environ.get("GEN_WORK") or os.path.join(G.STUDY, "results", G.safe(a.model)))
    os.makedirs(work, exist_ok=True)
    commit_file = os.path.join(G.STUDY, "DEPLOYED_COMMIT.txt")
    manifest = {"timestamp": dt.datetime.now().isoformat(timespec="seconds"), "host": socket.gethostname(),
                "slurm_job_id": os.environ.get("SLURM_JOB_ID"), "partition": os.environ.get("SLURM_JOB_PARTITION"),
                "deployed_commit": open(commit_file).read().strip() if os.path.exists(commit_file) else None,
                "gpu": raw, "tools": tools, "python": sys.version.split()[0], "ollama_version": version,
                "model": a.model, "model_digest": digest, "num_thread": B.THREADS,
                "settings": {"reps": 5, "temperature": 0.1, "num_ctx": 32768, "max_iters": 6,
                             "arms": {"oneshot": "one call", **{v: k for k, v in G.ARMS.items()}}},
                "frozen_files": n, "preflight_failures": bad}
    json.dump(manifest, open(os.path.join(work, "RUN_MANIFEST.json"), "w"), indent=1)
    print(f"manifest: {os.path.join(work, 'RUN_MANIFEST.json')}")
    print("PREFLIGHT: ALL PASSED" if not bad else f"PREFLIGHT: FAILED: {', '.join(bad)}")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
