"""Shared helpers for the Part 5 analysis scripts (integrity, audit, funnel, taxonomy, stitch_vs_retry, assemble).

Reads the HPC results as extracted into the study folder: outputs/{oneshot,simloop,stitch}/<m>.v, runs/oneshot/<m>/,
runs/arms/results/qwen2.5-coder_32b/<condition>/<m>/rep1/, runs/RUN_MANIFEST_<job>.json, reports/summary.json.
Paths recorded on the cluster (/scratch/soumyaj/STITCH_GEN/...) are mapped to the local study folder.
"""
from __future__ import annotations

import glob
import hashlib
import json
import os
import re

HERE = os.path.dirname(os.path.abspath(__file__))
STUDY = os.path.dirname(HERE)
MODEL_DIR = "qwen2.5-coder_32b"
RES = os.path.join(STUDY, "runs", "arms", "results", MODEL_DIR)
CONDITION = {"simloop": "baseline", "stitch": "sem_esc_restart_v3"}
ARMS = ("oneshot", "simloop", "stitch")
HPC_STUDY = "/scratch/soumyaj/STITCH_GEN/SiliconComparision/llm_oneshot_vs_stitch/"
LOGS = os.path.join(STUDY, "hpc_logs")
TIMING = ("rr_arbiter", "irs", "round_robin_req", "falling_edge_pulse_generator", "gray_mod6", "memory", "router_fifo")


def modules() -> list[str]:
    return sorted(m for m in os.listdir(os.path.join(STUDY, "tasks")) if os.path.isdir(os.path.join(STUDY, "tasks", m)))


def rel(p: str) -> str:
    return os.path.relpath(p, STUDY).replace(os.sep, "/")


def local(p: str) -> str:
    return os.path.join(STUDY, p[len(HPC_STUDY):]) if p.startswith(HPC_STUDY) else p


def sha(path: str) -> str:
    return hashlib.sha256(open(path, "rb").read()).hexdigest()


def run_dir(arm: str, m: str) -> str:
    return os.path.join(RES, CONDITION[arm], m, "rep1")


def metrics(arm: str, m: str) -> dict | None:
    p = os.path.join(run_dir(arm, m), "metrics.json")
    return json.load(open(p)) if os.path.exists(p) else None


def final_file(arm: str, m: str) -> str:
    return os.path.join(STUDY, "outputs", arm, f"{m}.v")


def iter_dirs(arm: str, m: str) -> list[str]:
    ds = glob.glob(os.path.join(run_dir(arm, m), "iter*"))
    return sorted((d for d in ds if os.path.isdir(d)), key=lambda d: int(re.search(r"iter(\d+)$", d).group(1)))


def summary_rows() -> dict:
    return {r["module"]: r for r in json.load(open(os.path.join(STUDY, "reports", "summary.json")))["rows"]}


def flags(s: dict | None) -> str:
    if not s:
        return "--"
    return "".join(c if s[k] else "." for c, k in (("C", "compile"), ("F", "func"), ("S", "signoff"),
                                                    ("K", "struct_clean")))


def manifests() -> dict:
    out = {}
    for p in glob.glob(os.path.join(STUDY, "runs", "RUN_MANIFEST_*.json")):
        j = re.search(r"RUN_MANIFEST_(\d+)\.json", p)
        if j:
            out[j.group(1)] = json.load(open(p))
    return out


def node_job() -> dict:
    """short node name -> (job id, GPU name, deployed commit) from the run manifests."""
    return {d["hostname"].split(".")[0]: (j, d["gpu"][0]["name"], d["git_commit"]) for j, d in manifests().items()}


def first_line(text: str, pattern: str) -> tuple[int, str] | None:
    for i, l in enumerate(text.splitlines(), 1):
        if re.search(pattern, l):
            return i, l.strip()
    return None


def spec(m: str) -> list[str]:
    return open(os.path.join(STUDY, "tasks", m, "spec.md"), encoding="utf-8").read().splitlines()


def write_report(name: str, lines: list[str]) -> str:
    p = os.path.join(STUDY, "reports", name)
    open(p, "w", encoding="utf-8", newline="\n").write("\n".join(lines).rstrip() + "\n")
    print(f"wrote {rel(p)}")
    return p
