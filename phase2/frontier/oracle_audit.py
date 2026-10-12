"""Set 4b oracle audit (no paid calls). For each module given: run the RTLLM reference design
(verified_<m>.v, renamed exactly as rtllm_task_a_screen.py does) through the Set 3 harness
(stitch_runner_hpc.run_iverilog_sim, detect_outcome(benchmark="rtllm")) on the Set 4 toolchain,
and tally the failure types of every Set 4b run of that module. Every result is a CANDIDATE
that needs manual confirmation. Run in WSL:
  STITCH_SET4_OSSCAD=... PYTHONPATH=... RTLLM_ROOT=/mnt/d/Projects/RTLLM python3 oracle_audit.py m1 m2 ...
"""
import collections
import glob
import json
import os
import re
import shutil
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
PHASE2 = os.path.dirname(HERE)
if os.environ.get("STITCH_SET4_OSSCAD"):
    os.environ["PATH"] = os.path.join(os.environ["STITCH_SET4_OSSCAD"], "bin") + os.pathsep + os.environ["PATH"]
sys.path.insert(0, PHASE2)
import set3_runner as s3  # noqa: E402
import stitch_runner_hpc as sr  # noqa: E402

ROOT = os.path.join(PHASE2, "results", "set4_api", "floor_full")
OUT = os.path.join(PHASE2, "results", "set4_api", "analysis_4b", "oracle_audit.json")


def resolve(name):
    for cat in s3.CATEGORIES:
        for p in glob.glob(os.path.join(s3.RTLLM_ROOT, cat, "*", name)):
            return p
    raise FileNotFoundError(name)


def reference_passes(mod):
    src = resolve(mod)
    with tempfile.TemporaryDirectory() as tmp:
        for f in os.listdir(src):
            if f in ("makefile", "design_description.txt") or f.startswith("verified_"):
                continue
            shutil.copy(os.path.join(src, f), os.path.join(tmp, f"{mod}_tb.v" if f == "testbench.v" else f))
        golden = open(os.path.join(src, f"verified_{mod}.v"), encoding="utf-8").read()
        open(os.path.join(tmp, f"{mod}.v"), "w").write(golden.replace(f"verified_{mod}", mod))
        ok, fb, outcome = sr.run_iverilog_sim(tmp, mod, benchmark="rtllm")
        log = open(os.path.join(tmp, "sim_log.txt"), encoding="utf-8", errors="replace").read()
    return outcome, log.strip().splitlines()[-3:]


def run_tallies(mod):
    types, lines = collections.Counter(), collections.Counter()
    for d in glob.glob(os.path.join(ROOT, "*", mod, "*", "*", "rep*")):
        for it in sorted(glob.glob(os.path.join(d, "iter_*"))):
            log = open(os.path.join(it, "sim_log.txt"), encoding="utf-8", errors="replace").read()
            if "COMPILATION ERROR" in log or re.search(r"\berror\b", log.split("--- SIMULATION ---")[0], re.I):
                types["compile"] += 1
                key = next((l for l in log.splitlines() if "error" in l.lower()), "")
                lines[re.sub(r"^\S+:\d+:\s*", "", key)[:90]] += 1
            else:
                types["sim"] += 1
                key = next((l.strip() for l in log.splitlines()
                            if any(w in l.lower() for w in ("fail", "error", "mismatch", "timeout"))), "(no verdict line)")
                lines[re.sub(r"\d+", "N", key)[:90]] += 1
    return types, lines.most_common(3)


def main():
    out = {}
    for mod in sys.argv[1:]:
        outcome, tail = reference_passes(mod)
        types, top = run_tallies(mod)
        out[mod] = {"reference_outcome": outcome, "reference_log_tail": tail,
                    "iteration_failure_types": dict(types), "top_failure_lines": top,
                    "status": "candidate, needs manual confirmation"}
        print(f"{mod}: reference {outcome} | failures {dict(types)} | top {top}")
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    json.dump(out, open(OUT, "w"), indent=2)


if __name__ == "__main__":
    main()
