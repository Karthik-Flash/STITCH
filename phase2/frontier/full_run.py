"""Set 4 full-run driver (prereg Amendment 1). Runs providers in the given order (cheapest
first). Per provider: full run, then ONE --retry-errored pass (A5), then compare actual
full-run spend (ledger, tag=full) with the pilot projection. Continues to the next provider
only if the runner exited 0 and actual <= 1.3 x projected; otherwise stops and records why.
Status: phase2/results/set4_api/full_run_status.json. Run in WSL:
  python3 phase2/frontier/full_run.py openai:gpt-4.1-mini-2025-04-14:0.51:0.76 gemini:...
(provider:model:projected_usd:cap_usd)
"""
import datetime
import json
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
SET4 = os.path.join(HERE, "..", "results", "set4_api")
STATUS = os.path.join(SET4, "full_run_status.json")
RUN = os.path.join(HERE, "run_set4.sh")
GLOBAL_CAP = "18"


def now():
    return datetime.datetime.now(datetime.timezone.utc).isoformat(timespec="seconds")


TAG, LEDGERS = os.environ.get("SET4_TAG", "full"), os.environ.get("SET4_LEDGERS", "ledgers")
EXTRA = os.environ.get("SET4_EXTRA", "").split()  # e.g. "--modules a,b,c" for Set 4b
if TAG != "full":
    STATUS = os.path.join(SET4, f"{TAG}_status_{os.environ.get('SET4_STATUS_SUFFIX', 'all')}.json")
    GLOBAL_CAP = os.environ.get("SET4_GLOBAL_CAP", GLOBAL_CAP)


def full_spend(provider):
    path = os.path.join(SET4, LEDGERS, f"{provider}_ledger.jsonl")
    with open(path, encoding="utf-8") as f:
        return sum(r["cost_usd"] for r in map(json.loads, filter(str.strip, f)) if r.get("tag") == TAG)


def main():
    status = {"started": now(), "providers": []}
    for spec in sys.argv[1:]:
        provider, model, projected, cap = spec.split(":")
        projected, cap = float(projected), float(cap)
        entry = {"provider": provider, "model": model, "projected_usd": projected, "cap_usd": cap, "start": now()}
        status["providers"].append(entry)
        args = ["bash", RUN, "--backend", provider, "--model", model, "--tag", TAG,
                "--budget-usd", GLOBAL_CAP, "--provider-cap-usd", str(cap),
                "--ledger-dir", os.path.join(SET4, LEDGERS)] + EXTRA
        log = os.path.join(SET4, f"{TAG}_{provider}.log")
        with open(log, "a", encoding="utf-8") as lf:
            entry["exit_run"] = subprocess.run(args, stdout=lf, stderr=subprocess.STDOUT).returncode
            if entry["exit_run"] == 0:
                entry["exit_retry"] = subprocess.run(args + ["--retry-errored"], stdout=lf,
                                                     stderr=subprocess.STDOUT).returncode
        ml = json.load(open(os.path.join(SET4, TAG, provider, "master_log.json"), encoding="utf-8"))
        entry.update(end=now(), runs=len(ml), errored=sum(1 for e in ml if e.get("error")),
                     passes=sum(1 for e in ml if e.get("pass")), actual_usd=full_spend(provider))
        entry["ratio_actual_to_projected"] = entry["actual_usd"] / projected
        ok = entry["exit_run"] == 0 and entry.get("exit_retry") == 0 and entry["ratio_actual_to_projected"] <= 1.3
        entry["continue"] = ok
        json.dump(status, open(STATUS, "w"), indent=2)
        if not ok:
            status["stopped"] = f"{provider}: exit_run={entry['exit_run']} exit_retry={entry.get('exit_retry')} " \
                                f"actual/projected={entry['ratio_actual_to_projected']:.2f} (limit 1.3)"
            break
    status["finished"] = now()
    json.dump(status, open(STATUS, "w"), indent=2)
    print(json.dumps(status, indent=2))


if __name__ == "__main__":
    main()
