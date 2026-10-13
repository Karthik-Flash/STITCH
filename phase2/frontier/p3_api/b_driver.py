"""Part B driver for one provider (run in WSL after that provider's Part A finishes):
  python3 b_driver.py <provider> <cap_usd>
Whole modules in b_plan.json priority order. Before each module: if its projected cost exceeds the budget left
under the provider cap (shared ledger phase2/results/p3_api/ledgers), it is not started and is listed as
"not run (cap)". Each module is a separate set4_runner call (tag floor_full, resumes, never re-runs completed
runs). A clean stop (exit 3: cap, reasoning, model-ID/auth) ends the provider. Then one --retry-errored pass.
Status: phase2/results/p3_api/b_status_<provider>.json.
"""
import datetime
import json
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(os.path.dirname(os.path.dirname(HERE)))
P3A = os.path.join(REPO, "phase2", "results", "p3_api")
LEDGERS = os.path.join(P3A, "ledgers")
RUN = os.path.join(REPO, "phase2", "frontier", "run_set4.sh")


def now():
    return datetime.datetime.now(datetime.timezone.utc).isoformat(timespec="seconds")


def spent(provider):
    p = os.path.join(LEDGERS, f"{provider}_ledger.jsonl")
    return sum(json.loads(l)["cost_usd"] for l in open(p) if l.strip()) if os.path.exists(p) else 0.0


def main():
    provider, cap = sys.argv[1], float(sys.argv[2])
    plan = json.load(open(os.path.join(P3A, "b_plan.json")))["plan"][provider]
    status = {"provider": provider, "cap_usd": cap, "started": now(), "modules": []}
    path = os.path.join(P3A, f"b_status_{provider}.json")
    planned = 228
    base = ["bash", RUN, "--backend", provider, "--model", plan["model"], "--tag", "floor_full",
            "--budget-usd", "15", "--provider-cap-usd", str(cap), "--ledger-dir", LEDGERS, "--planned", str(planned)]
    log = open(os.path.join(P3A, f"b_{provider}.log"), "a")
    stopped = None
    for row in plan["modules"]:
        left = cap - spent(provider)
        rec = {"module": row["module"], "projected_usd": row["projected_usd"], "budget_left_usd": round(left, 4)}
        if stopped:
            rec["result"] = f"not run ({stopped})"
        elif row["projected_usd"] > left:
            rec["result"] = "not run (cap: projection exceeds budget left)"
        else:
            rc = subprocess.run(base + ["--modules", row["module"]], stdout=log, stderr=subprocess.STDOUT).returncode
            rec.update(result="completed" if rc == 0 else f"stopped (exit {rc})", end=now(),
                       spent_after_usd=round(spent(provider), 4))
            if rc != 0:
                stopped = f"provider stopped at {row['module']} (exit {rc})"
        status["modules"].append(rec)
        json.dump(status, open(path, "w"), indent=1)
    if not stopped:
        mods = ",".join(r["module"] for r in status["modules"] if r["result"] == "completed")
        if mods:
            status["retry_pass_exit"] = subprocess.run(base + ["--modules", mods, "--retry-errored"],
                                                       stdout=log, stderr=subprocess.STDOUT).returncode
    status.update(finished=now(), stopped=stopped, spent_usd=round(spent(provider), 4))
    json.dump(status, open(path, "w"), indent=1)


if __name__ == "__main__":
    main()
