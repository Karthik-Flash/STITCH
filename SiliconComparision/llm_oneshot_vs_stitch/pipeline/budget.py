#!/usr/bin/env python3
"""Pre-deploy budget checks (laptop only: needs phase3/results and a local Ollama). Writes reports/PREDEPLOY_BUDGET.md.

  [options] Ollama request body sent by (a) the Phase 3 production run (argv of phase3/hpc/phase3_run.slurm),
            (b) the Phase 3 runner as gen_job.slurm calls it through run_arms.py, (c) oneshot_gen.py as gen_job.slurm
            calls it. Each is captured from the real code path: the runner/oneshot argparse builds the real
            stitch_runner_p3.Ollama, whose chat() body is captured instead of sent. Fails if (b) != (c).
  [tokens]  ESTIMATED prompt tokens per task: prompt_eval_count of a local Ollama qwen2.5-coder model (same Qwen2.5
            BPE tokenizer as qwen2.5-coder:32b), chat template and system prompt included, num_predict 1.
  [time]    Phase 3 qwen2.5-coder:32b per-call wall time from its logs x 442 calls (34 one-shot + 68 x 6) x 1.5.

Usage: python pipeline/budget.py [--tokenizer-model qwen2.5-coder:latest] [--host http://127.0.0.1:11434]
"""
from __future__ import annotations

import argparse
import glob
import json
import os
import re
import shlex
import statistics
import sys
import tempfile
import urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import p3_bridge as B  # noqa: E402
import make_tasks as MT  # noqa: E402
import oneshot_gen as OG  # noqa: E402
import run_arms as RA  # noqa: E402

R = OG.R
P3 = os.path.join(B.REPO, "phase3")
P3_32B_RESULTS = os.path.join(P3, "results", "phase3_32b", "qwen2.5-coder_32b")
P3_32B_SERVE_LOG = os.path.join(P3, "results", "final_batch_logs", "ollama_serve_369810.log")   # job C = 32b only
N_CALLS = 34 + 68 * 6                                   # whole-router bonus off (GEN_FULL_ROUTER=0)
P3_NUM_CTX = 8192                                       # Phase 3 production (runner default; serve log n_ctx = 8192)
MARGIN = 1.5


# --------------------------------------------------------------------------- [options]
class _Stop(Exception):
    pass


def capture(entry, argv) -> dict:
    """Run entry() with sys.argv = argv until it builds R.Ollama; return the /api/chat body its chat() would send."""
    real, got = R.Ollama, {}

    class Spy(real):
        def __init__(self, *a, **k):
            super().__init__(*a, **k)
            got["llm"] = self
            raise _Stop

    R.Ollama, sys.argv = Spy, argv
    try:
        entry()
    except _Stop:
        pass
    finally:
        R.Ollama = real
    body = {}

    def fake_urlopen(req, timeout=None):
        body.update(json.loads(req.data), client_http_timeout_s=timeout)          # urllib timeout, not sent
        raise _Stop

    real_open, real_sleep = urllib.request.urlopen, R.time.sleep
    urllib.request.urlopen, R.time.sleep = fake_urlopen, (lambda s: None)
    try:
        got["llm"].chat("S", "U")
    except RuntimeError:
        pass
    finally:
        urllib.request.urlopen, R.time.sleep = real_open, real_sleep
    body.pop("messages")
    return body


def job_args(path: str, script: str, model: str = "qwen2.5-coder:32b") -> list[str]:
    """Flags a Slurm script passes to `script` (shell variables replaced by placeholders)."""
    text = open(path, encoding="utf-8").read().replace("\\\n", " ")
    line = next(l for l in text.splitlines() if script in l and l.strip().startswith("python3"))
    toks = shlex.split(line.split(script, 1)[1].split("||")[0])
    out = []
    for t in toks:
        if t in ("$MODS", "$FULL", "$SP", "${P3_EXTRA_ARGS:-}"):
            continue                                       # module lists / system prompt file: no Ollama options
        out.append({"$MODEL": model, '"$m"': model, "$m": model}.get(t, "http://x" if "OLLAMA_HOST" in t else t))
    return out


def study_bodies(model: str = "qwen2.5-coder:32b") -> dict:
    """Request bodies (without messages) that gen_job.slurm's run_arms.py and oneshot_gen.py lines would send."""
    tmp, gen = tempfile.mkdtemp(), os.path.join(HERE, "gen_job.slurm")
    arms, one = job_args(gen, "run_arms.py", model), job_args(gen, "oneshot_gen.py", model)
    real_prep = RA.prepare_tasks
    RA.prepare_tasks = lambda modules, out: os.path.join(B.STUDY, "tasks")
    try:
        return {"runner via run_arms": capture(RA.main, ["r", *arms, "--modules", "encoder", "--out", tmp]),
                "oneshot_gen": capture(OG.main, ["o", *one]), "_argv": {"run_arms": arms, "oneshot_gen": one}}
    finally:
        RA.prepare_tasks = real_prep


def options() -> tuple[list[str], bool, int]:
    p3 = job_args(os.path.join(P3, "hpc", "phase3_run.slurm"), "stitch_runner_p3.py")
    study = study_bodies()
    argv = study.pop("_argv")
    arms, one = argv["run_arms"], argv["oneshot_gen"]
    cols = {"phase3 production": capture(R.main, ["r", *p3, "--tasks", "register_4bit", "--out", tempfile.mkdtemp()]),
            **study}
    flat = {c: {**{k: v for k, v in b.items() if k != "options"}, **{f"options.{k}": v for k, v in b["options"].items()}}
            for c, b in cols.items()}
    keys = sorted(set().union(*flat.values()))
    for k in ("options.num_predict", "options.seed", "options.top_p", "options.top_k", "options.repeat_penalty"):
        keys.append(k) if k not in keys else None
    names = list(cols)
    lines = ["| field | " + " | ".join(names) + " |", "|---" * (len(names) + 1) + "|"]
    for k in keys:
        lines.append(f"| {k} | " + " | ".join(str(flat[n].get(k, "not sent (Ollama/model default)")) for n in names)
                     + " |")
    same = flat["runner via run_arms"] == flat["oneshot_gen"]
    lines += ["", f"job argv: phase3_run.slurm -> runner {' '.join(p3)}; gen_job.slurm -> run_arms {' '.join(arms)}; "
                  f"oneshot_gen {' '.join(one)}",
              f"runner via run_arms == oneshot_gen: {same}"]
    return lines, same, flat["oneshot_gen"]["options.num_ctx"]


# --------------------------------------------------------------------------- [tokens]
def count(host: str, model: str, system: str, user: str, num_ctx: int) -> int:
    b = json.dumps({"model": model, "stream": False, "messages": [{"role": "system", "content": system},
                                                                  {"role": "user", "content": user}],
                    "options": {"num_predict": 1, "temperature": 0, "num_ctx": num_ctx}}).encode()
    req = urllib.request.Request(host + "/api/chat", data=b, headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=1800) as r:
        return json.loads(r.read())["prompt_eval_count"]


def tokens(host: str, model: str, num_ctx: int) -> tuple[list[str], list[str]]:
    rows = MT.load_rows()
    system = open(OG.SYSTEM_PROMPT_FILE, encoding="utf-8").read()
    probe_ctx = 65536
    base = count(host, model, system, "", probe_ctx)
    order = sorted(rows, key=lambda m: int(rows[m]["bottom_up_order"]))
    lines = [f"Estimate. Tokenizer: Qwen2.5 BPE (pre-tokenizer qwen2, n_vocab 152064), counted as Ollama "
             f"prompt_eval_count with local model `{model}` (same tokenizer family as qwen2.5-coder:32b); chat template "
             f"and the Phase 3 system prompt included. Generation budget: num_predict is not sent, so output shares "
             f"num_ctx = {num_ctx} with the prompt; `golden out` (tokens of the golden module in a ```verilog block) "
             f"stands in for the answer size. `arms prompt` = Phase 3 user_prompt(spec, golden as current RTL, no "
             f"feedback), a lower bound for every feedback iteration.", "",
             "| module | one-shot prompt | golden out | one-shot total | arms prompt | arms total | over num_ctx | over Phase 3 num_ctx 8192 |",
             "|---|---|---|---|---|---|---|---|"]
    over = []
    for m in order + ["top_module_full"]:
        if m == "top_module_full":                         # answer counted file by file (each piece fits the probe)
            p = OG.full_router_prompt(rows)
            to = sum(count(host, model, system, open(os.path.join(B.STUDY, "golden", "reference", rows[c]["file"]))
                           .read(), probe_ctx) - base for c in MT.descendants(rows, "top_module") + ["top_module"])
            arms = None
        else:
            p = OG.prompt_for(m, rows)
            gold = open(os.path.join(B.STUDY, "tasks", m, "golden.v")).read()
            spec = open(os.path.join(B.STUDY, "tasks", m, "spec.md"), encoding="utf-8").read()
            arms = count(host, model, system, R.user_prompt(spec, gold), probe_ctx)
            to = count(host, model, system, "```verilog\n" + gold + "```", probe_ctx) - base
        tp = count(host, model, system, p, probe_ctx)
        need = (("one-shot prompt", tp), ("one-shot total", tp + to), ("arms total", arms + to if arms else 0))
        flags = [n for n, v in need if v > num_ctx]
        p3 = [n for n, v in need if v > P3_NUM_CTX]
        if flags and m != "top_module_full":
            over.append(f"{m}: {', '.join(flags)}")
        lines.append(f"| {m} | {tp} | {to} | {tp + to} | {arms if arms else '-'} | "
                     f"{arms + to if arms else '-'} | {', '.join(flags) or '-'} | {', '.join(p3) or '-'} |")
        print(lines[-1], flush=True)
    lines += ["", "Single-module prompts above num_ctx - expected output (prompt + golden-size answer > num_ctx): "
              + ("; ".join(over) if over else "none")]
    return lines, over


# --------------------------------------------------------------------------- [time]
def dur(s: str) -> float:
    return sum(float(v) * {"h": 3600, "m": 60, "s": 1, "ms": 1e-3, "µs": 1e-6}[u]
               for v, u in re.findall(r"([\d.]+)(h|ms|µs|m|s)", s))


def walltime() -> tuple[list[str], int]:
    gin = [dur(l.split("|")[2]) for l in open(P3_32B_SERVE_LOG, encoding="utf-8", errors="replace")
           if '"/api/chat"' in l and "| 200 |" in l]
    ms = [json.load(open(p)) for p in glob.glob(os.path.join(P3_32B_RESULTS, "*", "*", "rep*", "metrics.json"))]
    calls, wall = sum(m["llm_calls"] for m in ms), sum(m["wall_s"] for m in ms)
    per_run = wall / calls
    q = statistics.quantiles(gin, n=20)
    per_call = max(per_run, statistics.mean(gin))
    secs = per_call * N_CALLS * MARGIN
    hours = int(-(-secs // 3600))
    import preflight
    digests = sorted({m["provenance"]["model_digest"] for m in ms})
    lines = [f"Phase 3 qwen2.5-coder:32b (job 369810, H200 NVL):",
             f"- recorded model digest(s) in metrics.json: {digests}; preflight.PHASE3_DIGEST matches: "
             f"{digests == [preflight.PHASE3_DIGEST['qwen2.5-coder:32b']]}",
             f"- serve log ({os.path.basename(P3_32B_SERVE_LOG)}): {len(gin)} /api/chat calls (HTTP 200), LLM time only: "
             f"mean {statistics.mean(gin):.1f} s, median {statistics.median(gin):.1f} s, p95 {q[18]:.1f} s, "
             f"max {max(gin):.1f} s",
             f"- metrics.json: {len(ms)} runs, {calls} LLM calls, {wall:.0f} s wall (LLM + tool evaluation): "
             f"{per_run:.1f} s per call",
             f"- per-call wall time used = max of the two means = {per_call:.1f} s",
             f"- {per_call:.1f} s x {N_CALLS} calls (34 one-shot + 68 x 6) x {MARGIN} = {secs:.0f} s = "
             f"{secs / 3600:.2f} h -> --time={hours:02d}:00:00"]
    return lines, hours


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--tokenizer-model", default="qwen2.5-coder:latest")
    ap.add_argument("--host", default="http://127.0.0.1:11434")
    a = ap.parse_args()
    opt, same, num_ctx = options()
    print("\n".join(opt), flush=True)
    tim, _ = walltime()
    print("\n".join(tim), flush=True)
    tok, _ = tokens(a.host, a.tokenizer_model, num_ctx)
    out = os.path.join(B.STUDY, "reports", "PREDEPLOY_BUDGET.md")
    open(out, "w", encoding="utf-8", newline="\n").write(
        "# Pre-deploy budget (pipeline/budget.py)\n\n## Ollama options\n\n" + "\n".join(opt)
        + "\n\n## Prompt tokens (estimate)\n\n" + "\n".join(tok) + "\n\n## Wall time\n\n" + "\n".join(tim) + "\n")
    print("\n".join(tok[-1:]))
    print(f"wrote {out}")
    return 0 if same else 1


if __name__ == "__main__":
    sys.exit(main())
