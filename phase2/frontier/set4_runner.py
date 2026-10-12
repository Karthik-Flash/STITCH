"""Set 4: Set 3's exact protocol on commercial non-reasoning API models.

Reuses phase2/set3_runner.py unchanged (module pool, staging, per-cell
runners, master_log checkpoint/resume) and only swaps the LLM call: the same
runtime rebinding of stitch_runner_hpc.call_llm / escalation_runner_hpc.call_llm
that set3_runner.py itself uses for Ollama. No existing file is edited, so the
Ollama path is untouched (see ollama_parity_mock.py).

Runs in WSL (the Set 3 engine calls iverilog/verilator/yosys natively):
  PYTHONPATH=/mnt/c/Users/karth/stitch_set4_pylib RTLLM_ROOT=/mnt/d/Projects/RTLLM \\
  python3 phase2/frontier/set4_runner.py --backend gemini --model gemini-2.5-flash --tag pilot ...

Layout: phase2/results/set4_api/<tag>/<backend>/ (master_log.json + per-run dirs,
same shape as Set 3); spend ledgers are shared across tags in
phase2/results/set4_api/ledgers/ so every call ever made counts against the caps.
One process per provider, sequential calls: concurrency limit = 1 per provider.
"""
import argparse
import datetime
import json
import os
import shutil
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
PHASE2 = os.path.dirname(HERE)
# Set-4-only toolchain (prereg amendment A3): prepend a dated oss-cad-suite to PATH
if os.environ.get("STITCH_SET4_OSSCAD"):
    os.environ["PATH"] = os.path.join(os.environ["STITCH_SET4_OSSCAD"], "bin") + os.pathsep + os.environ["PATH"]
sys.path.insert(0, PHASE2)
sys.path.insert(0, HERE)

import set3_runner as s3                  # noqa: E402
import stitch_runner_hpc as sr            # noqa: E402
import escalation_runner_hpc as erh       # noqa: E402
import backends as B                      # noqa: E402

SET4_ROOT = os.path.join(PHASE2, "results", "set4_api")
LEDGER_DIR = os.path.join(SET4_ROOT, "ledgers")


def _resolve_any(names):
    """(design, category, rel) for arbitrary RTLLM designs, e.g. a ceiling
    module for the smoke test. Same directory walk as set3_runner."""
    found = []
    for cat in s3.CATEGORIES:
        cat_dir = os.path.join(s3.RTLLM_ROOT, cat)
        for sub in sorted(os.listdir(cat_dir)) if os.path.isdir(cat_dir) else []:
            for design in sorted(os.listdir(os.path.join(cat_dir, sub))):
                if design in names:
                    found.append((design, cat, f"{cat}/{sub}/{design}"))
    missing = set(names) - {f[0] for f in found}
    if missing:
        sys.exit(f"FATAL: not found under {s3.RTLLM_ROOT}: {sorted(missing)}")
    return found


def _tool_versions():
    out = {}
    for name, cmd in {"iverilog": ["iverilog", "-V"], "verilator": ["verilator", "--version"],
                      "yosys": ["yosys", "-V"]}.items():
        try:
            r = subprocess.run(cmd, capture_output=True, text=True, timeout=20)
            out[name] = (r.stdout + r.stderr).strip().splitlines()[0]
        except Exception as e:  # recorded, not fatal
            out[name] = f"unavailable: {type(e).__name__}"
    return out


def _wrap(fn, raw_root_attr, classic):
    def run(design, category, model, condition, spec, tb, deps, replicate):
        safe = model.replace(":", "_").replace(".", "")
        raw = os.path.join(getattr(s3, raw_root_attr), safe, condition, design)
        if not classic:
            raw = os.path.join(raw, f"replicate_{replicate}")
        shutil.rmtree(raw, ignore_errors=True)  # no stale iter_* dirs from an errored attempt
        if ARGS.run_worst_usd:   # Set 4c: stop between runs, never start one whose worst case could cross a cap
            mine, total = PROGRESS["backend"].spent()
            if mine + ARGS.run_worst_usd > ARGS.provider_cap_usd or total + ARGS.run_worst_usd > ARGS.budget_usd:
                raise B.BudgetExceeded(f"not starting {design}/{condition}/rep{replicate}: its worst case "
                                       f"${ARGS.run_worst_usd} could exceed a cap (provider ${mine:.4f}/{ARGS.provider_cap_usd}, "
                                       f"global ${total:.4f}/{ARGS.budget_usd})")
        B.CONTEXT.clear()
        B.CONTEXT.update(module=design, condition=condition, replicate=replicate, tag=ARGS.tag)
        write_progress(running=f"{design}/{condition}/rep{replicate}")
        try:
            return fn(design, category, model, condition, spec, tb, deps, replicate)
        except B.CallFailed as e:
            PROGRESS["last_error"] = f"{design}/{condition}/rep{replicate}: CallFailed: {B.redact(str(e))[:200]}"
            raise RuntimeError(f"CallFailed: {e}") from None  # run_all records it as errored
        except Exception as e:
            PROGRESS["last_error"] = f"{design}/{condition}/rep{replicate}: {B.redact(repr(e))[:200]}"
            raise
    return run


PROGRESS = {"last_error": None}


def write_progress(**extra):
    """<results root>/PROGRESS.json: done / planned, spend, last error, timestamp (written before each run and at exit)."""
    root, backend = PROGRESS.get("root"), PROGRESS.get("backend")
    if not root:
        return
    entries = s3._load_master_log() if os.path.exists(s3.MASTER_LOG) else []
    mine, total = backend.spent()
    rec = {"done": len(entries), "errored": sum(1 for e in entries if e.get("error")),
           "planned": PROGRESS.get("planned"), "spend_usd_provider": round(mine, 4),
           "spend_usd_all_providers": round(total, 4), "last_error": PROGRESS["last_error"],
           "timestamp_utc": datetime.datetime.now(datetime.timezone.utc).isoformat(timespec="seconds"), **extra}
    tmp = os.path.join(root, "PROGRESS.json.tmp")
    with open(tmp, "w") as f:
        json.dump(rec, f, indent=1)
    os.replace(tmp, os.path.join(root, "PROGRESS.json"))


def smoke_call(backend):
    msgs = [{"role": "system", "content": sr.SYSTEM_PROMPT},
            {"role": "user", "content": "Write a Verilog-2001 module named buf1 with input a and output y, y = a."}]
    B.CONTEXT.update(module="smoke_call", condition="none", replicate=0, tag=ARGS.tag)
    text, pt, ct = backend(backend.model, msgs)
    with open(backend.ledger, encoding="utf-8") as f:
        last = json.loads(f.readlines()[-1])
    keep = ("status", "model_version", "response_id", "request_id", "system_fingerprint", "input_tokens",
            "cached_tokens", "output_tokens", "reasoning_tokens", "finish_reason", "latency_s", "cost_usd")
    print(json.dumps({k: last.get(k) for k in keep}, indent=2))
    print("contains 'module buf1':", "module buf1" in text)


def main():
    global ARGS
    ap = argparse.ArgumentParser()
    ap.add_argument("--backend", required=True, choices=["openai", "anthropic", "moonshot", "gemini"])
    ap.add_argument("--model", required=True)
    ap.add_argument("--tag", required=True, help="smoke | pilot | full")
    ap.add_argument("--max-tokens", type=int, default=8192)
    ap.add_argument("--budget-usd", type=float, default=25.0)
    ap.add_argument("--provider-cap-usd", type=float, default=7.0)
    ap.add_argument("--modules", default="", help="comma list; default = the 17 recoverable-band modules")
    ap.add_argument("--conditions", default=",".join(s3.CONDITIONS))
    ap.add_argument("--n", type=int, default=3)
    ap.add_argument("--smoke-call", action="store_true", help="one minimal call, then exit")
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--retry-errored", action="store_true",
                    help="drop errored entries from master_log first so they run once more (amendment A5)")
    ap.add_argument("--ledger-dir", default=LEDGER_DIR, help="Set 4b uses its own (ledgers_4b)")
    ap.add_argument("--planned", type=int, default=0, help="planned total for PROGRESS.json (default: this call's runs)")
    ap.add_argument("--thinking-budget", type=int, default=None, help="Set 4c only: Gemini thinkingBudget (reasoning)")
    ap.add_argument("--run-worst-usd", type=float, default=0.0,
                    help="Set 4c only: worst-case cost of one run; a run is not started if it could cross a cap")
    ARGS = ap.parse_args()

    backend = B.Backend(ARGS.backend, ARGS.model, max_tokens=ARGS.max_tokens, ledger_dir=ARGS.ledger_dir,
                        budget_usd=ARGS.budget_usd, provider_cap_usd=ARGS.provider_cap_usd,
                        thinking_budget=ARGS.thinking_budget)

    if ARGS.smoke_call:
        smoke_call(backend)
        return

    if ARGS.modules:
        names = ARGS.modules.split(",")
        pool = sorted(_resolve_any(names), key=lambda t: names.index(t[0]))  # run in the order given
    else:
        pool = s3._load_module_pool(s3.RTLLM_ROOT, s3.TASK_A_SCREEN_JSON, s3.MODULE_CATEGORIES_JSON)

    root = os.path.join(SET4_ROOT, ARGS.tag, ARGS.backend)
    s3.MODELS = [ARGS.model]
    s3.CONDITIONS = ARGS.conditions.split(",")
    s3.N_REPLICATES = ARGS.n
    s3.TEMPERATURE = backend.temperature
    s3.RESULTS_ROOT = root
    s3.RAW_CLASSIC_ROOT = os.path.join(root, "_raw_classic")
    s3.RAW_ESCALATION_ROOT = os.path.join(root, "_raw_escalation")
    s3.MASTER_LOG = os.path.join(root, "master_log.json")
    s3.INCIDENTS_LOG = os.path.join(root, "incidents.log")
    s3.STAGED_ROOT = os.path.join(root, "_staged")
    s3.RETRY_ATTEMPTS = 1  # retries happen per call (max 3) inside the backend; a failed run is not re-run
    s3._run_classic = _wrap(s3._run_classic, "RAW_CLASSIC_ROOT", classic=True)
    s3._run_escalation = _wrap(s3._run_escalation, "RAW_ESCALATION_ROOT", classic=False)
    sr.call_llm = backend
    erh.call_llm = backend

    total = len(pool) * len(s3.CONDITIONS) * ARGS.n
    print(f"Set 4 | {ARGS.backend}/{ARGS.model} | tag={ARGS.tag} | T={backend.temperature} | "
          f"max_tokens={ARGS.max_tokens} | modules={[p[0] for p in pool]} | "
          f"conditions={s3.CONDITIONS} | N={ARGS.n} | runs={total}")
    mine, glob_ = backend.spent()
    print(f"spent so far: provider ${mine:.4f} / cap {ARGS.provider_cap_usd}, "
          f"global ${glob_:.4f} / cap {ARGS.budget_usd}")
    if ARGS.dry_run:
        return

    os.makedirs(root, exist_ok=True)
    manifest = {
        "started_utc": datetime.datetime.now(datetime.timezone.utc).isoformat(timespec="seconds"),
        "provider": ARGS.backend, "model": ARGS.model, "temperature": backend.temperature,
        "max_tokens": ARGS.max_tokens, "price_usd_per_M": B.PRICES[ARGS.model],
        "price_source": B.PRICE_SOURCES.get(ARGS.model, B.PRICE_SOURCES[ARGS.backend]),
        "caps_usd": [ARGS.provider_cap_usd, ARGS.budget_usd],
        "thinking_budget": ARGS.thinking_budget, "run_worst_usd": ARGS.run_worst_usd,
        "modules": [p[0] for p in pool], "conditions": s3.CONDITIONS, "n": ARGS.n,
        "iteration_caps": {"classic": sr.MAX_RETRIES, "escalation": 8},
        "tools": _tool_versions(),
        "git_head": subprocess.run(["git", "-C", PHASE2, "rev-parse", "HEAD"],
                                   capture_output=True, text=True).stdout.strip(),
    }
    with open(os.path.join(root, f"manifest_{manifest['started_utc'].replace(':', '')}.json"), "w") as f:
        json.dump(manifest, f, indent=2)

    if ARGS.retry_errored and os.path.exists(s3.MASTER_LOG):
        entries = s3._load_master_log()
        kept = [e for e in entries if not e.get("error")]
        with open(os.path.join(root, "errored_before_retry.json"), "w") as f:
            json.dump([e for e in entries if e.get("error")], f, indent=2)
        s3._save_master_log(kept)
        print(f"retry-errored: {len(entries) - len(kept)} errored entries queued for one more attempt")

    PROGRESS.update(root=root, backend=backend, planned=ARGS.planned or total)
    try:
        s3.run_all(pool)
    except (B.BudgetExceeded, B.ReasoningDetected, B.ProviderStop) as e:
        PROGRESS["last_error"] = f"STOPPED {type(e).__name__}: {e}"
        write_progress(stopped=True)
        print(f"\nSTOPPED CLEANLY: {type(e).__name__}: {e}")
        print("Completed runs are in master_log.json; rerun the same command to resume.")
        sys.exit(3)
    write_progress(finished=True)
    mine, glob_ = backend.spent()
    print(f"spent: provider ${mine:.4f}, global ${glob_:.4f}")


if __name__ == "__main__":
    main()
