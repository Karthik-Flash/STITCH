"""Phase 3 API point: phase3/runner/stitch_runner_p3.py, unmodified, with ONLY the model transport swapped
(its Ollama class -> the backends.py API adapter). Loop, resume, feedback, evaluation, prompts, provenance
and output layout are the Phase 3 runner's own. Nothing under phase3/ is written (bytecode disabled).

Run in WSL (matched 0.69 suite):
  STITCH_SET4_OSSCAD=... python3 p3_api_runner.py --api openai --model gpt-4.1-mini-2025-04-14 --tag p3_pilot \
      --out /mnt/d/.../phase2/results/p3_api/pilot --provider-cap-usd 1.5 -- --tasks mux3 ni_flit_pack --reps 1
Everything after `--` goes to stitch_runner_p3.main() (it gets --model/--out/--backend ollama/--temperature 0.1/
--max-iters 6/--system-prompt-file phase3/runner/system_prompt.txt added here, as in phase3_run.slurm).
Writes <out>/PROGRESS.json after every run.
"""
import argparse
import datetime
import glob
import json
import os
import sys

sys.dont_write_bytecode = True
HERE = os.path.dirname(os.path.abspath(__file__))
FRONTIER = os.path.dirname(HERE)
REPO = os.path.dirname(os.path.dirname(FRONTIER))
P3R = os.path.join(REPO, "phase3", "runner")
if os.environ.get("STITCH_SET4_OSSCAD"):
    os.environ["PATH"] = os.path.join(os.environ["STITCH_SET4_OSSCAD"], "bin") + os.pathsep + os.environ["PATH"]
sys.path.insert(0, P3R)
sys.path.insert(0, FRONTIER)
import stitch_runner_p3 as R  # noqa: E402
import backends as B          # noqa: E402

LEDGERS = os.path.join(REPO, "phase2", "results", "p3_api", "ledgers")
STATE = {"last_error": None}


class APIChat:
    """Drop-in for stitch_runner_p3.Ollama: chat(system, user) -> (text, tokens_in, tokens_out)."""
    def __init__(self, backend):
        self.b, self.host = backend, "api"

    def chat(self, system, user):
        try:
            return self.b(self.b.model, [{"role": "system", "content": system}, {"role": "user", "content": user}])
        except B.CallFailed as e:          # exhausted retries: let the Phase 3 loop record this run as errored
            raise RuntimeError(f"CallFailed: {e}") from None


def progress(out, backend, planned, **extra):
    done = len(glob.glob(os.path.join(out, "*", "*", "*", "rep*", "metrics.json")))
    errored = sum(1 for e in glob.glob(os.path.join(out, "*", "*", "*", "rep*", "error.json"))
                  if not os.path.exists(os.path.join(os.path.dirname(e), "metrics.json")))
    mine, total = backend.spent()
    rec = {"done": done, "planned": planned, "errored_pending": errored, "spend_usd_provider": round(mine, 4),
           "spend_usd_all_providers": round(total, 4), "last_error": STATE["last_error"],
           "timestamp_utc": datetime.datetime.now(datetime.timezone.utc).isoformat(timespec="seconds"), **extra}
    tmp = os.path.join(out, "PROGRESS.json.tmp")
    json.dump(rec, open(tmp, "w"), indent=1)
    os.replace(tmp, os.path.join(out, "PROGRESS.json"))


def main():
    argv = sys.argv[1:]
    passthrough = argv[argv.index("--") + 1:] if "--" in argv else []
    ours = argv[:argv.index("--")] if "--" in argv else argv
    ap = argparse.ArgumentParser()
    ap.add_argument("--api", required=True, choices=["openai", "anthropic", "gemini"])
    ap.add_argument("--model", required=True)
    ap.add_argument("--tag", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--provider-cap-usd", type=float, required=True)
    ap.add_argument("--budget-usd", type=float, default=15.0)
    ap.add_argument("--max-tokens", type=int, default=8192)
    ap.add_argument("--ledger-dir", default=LEDGERS)
    a = ap.parse_args(ours)

    backend = B.Backend(a.api, a.model, max_tokens=a.max_tokens, ledger_dir=a.ledger_dir,
                        budget_usd=a.budget_usd, provider_cap_usd=a.provider_cap_usd, temperature=0.1)
    os.makedirs(a.out, exist_ok=True)

    R.Ollama = lambda model, host, temperature, num_ctx, timeout: APIChat(backend)   # the transport swap
    R.model_digest = lambda llm, model: f"api:{model}"   # no Ollama digest; returned model IDs are in the ledger

    tasks_arg = passthrough[passthrough.index("--tasks") + 1:] if "--tasks" in passthrough else []
    tasks_arg = [t for t in tasks_arg[:next((i for i, t in enumerate(tasks_arg) if t.startswith("--")), len(tasks_arg))]]
    n_tasks = len(tasks_arg) or len([d for d in os.listdir(R.TASKS_DIR) if os.path.isdir(os.path.join(R.TASKS_DIR, d))])
    reps = int(passthrough[passthrough.index("--reps") + 1]) if "--reps" in passthrough else 3
    planned = n_tasks * len(R.CONDITIONS) * reps

    orig = R.run_one

    def run_one(llm, model, cond, task, rep, args, run_dir, gate_cache):
        B.CONTEXT.clear()
        B.CONTEXT.update(module=task, condition=cond, replicate=rep, tag=a.tag)
        try:
            m = orig(llm, model, cond, task, rep, args, run_dir, gate_cache)
            STATE["last_error"] = None
            return m
        except Exception as e:
            STATE["last_error"] = f"{task}/{cond}/rep{rep}: {B.redact(repr(e))[:300]}"
            raise
        finally:
            progress(a.out, backend, planned)
    R.run_one = run_one

    sys.argv = ["stitch_runner_p3.py", "--backend", "ollama", "--model", a.model, "--out", a.out,
                "--temperature", "0.1", "--max-iters", "6",
                "--system-prompt-file", os.path.join(P3R, "system_prompt.txt")] + passthrough
    try:
        R.main()
    except (B.BudgetExceeded, B.ReasoningDetected, B.ProviderStop) as e:
        STATE["last_error"] = f"STOPPED {type(e).__name__}: {e}"
        progress(a.out, backend, planned, stopped=True)
        print(f"STOPPED CLEANLY: {type(e).__name__}: {e}", flush=True)
        sys.exit(3)
    progress(a.out, backend, planned, finished=True)


if __name__ == "__main__":
    main()
