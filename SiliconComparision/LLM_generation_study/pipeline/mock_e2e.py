#!/usr/bin/env python3
"""End-to-end test of generate.py with mock LLMs on all 7 tasks, 2 reps, in a scratch folder (no GPU, no model).

One-shot mock plan: route_compute and output_port return broken syntax (the golden without its last 'endmodule'),
flit_mux returns a version that passes its testbench but infers a latch, the rest return the golden. The arms use the
Phase 3 mock fix_on_2 (first call echoes the current RTL, later calls return golden.v).
Checks the outcome every arm must have on each case, including the case STITCH exists for: simloop stops on the
latched flit_mux (it passes the testbench) and STITCH does not (it is not struct_clean), fires, and ends clean.
Then reruns generate.py to check that everything finished is skipped. Exit 0 only if every check holds.
Usage: python3 pipeline/mock_e2e.py [--work DIR]
"""
import argparse
import glob
import json
import os
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
PLAN = {"route_compute": "broken", "output_port": "broken", "flit_mux": "latch"}
REPS = 2


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--work", default=None)
    a = ap.parse_args()
    work = os.path.abspath(a.work or tempfile.mkdtemp(prefix="llmgen_e2e_"))
    env = {**os.environ, "GEN_WORK": work, "PYTHONDONTWRITEBYTECODE": "1"}
    cmd = [sys.executable, os.path.join(HERE, "generate.py"), "--backend", "mock", "--model", "mock",
           "--reps", str(REPS), "--mock-plan", *[f"{m}={p}" for m, p in PLAN.items()]]
    first = subprocess.run(cmd, env=env, capture_output=True, text=True)
    print(first.stdout[-3000:], first.stderr[-2000:], sep="\n")
    second = subprocess.run(cmd, env=env, capture_output=True, text=True)

    sys.path.insert(0, HERE)
    import generate as G
    B = G.B

    def run(arm, m, r=1):
        cond = {v: k for k, v in G.ARMS.items()}[arm]
        return json.load(open(os.path.join(work, "arms", f"rep{r}", "results", "mock", cond, m, "rep1", "metrics.json")))

    def oneshot_eval(m, r=1):
        return B.evaluate(os.path.join(work, "outputs", "oneshot", f"rep{r}", f"{m}.v"), os.path.join(G.TASKS, m), m)

    n = {arm: len(glob.glob(os.path.join(work, "outputs", arm, "rep*", "*.v"))) for arm in ("oneshot", "simloop", "stitch")}
    fm = {arm: run(arm, "flit_mux") for arm in ("simloop", "stitch")}
    checks = {
        "first run exit 0": first.returncode == 0,
        f"every arm wrote {7 * REPS} outputs": all(v == 7 * REPS for v in n.values()),
        "oneshot golden fifo: clean_pass": oneshot_eval("fifo")["clean_pass"],
        "oneshot broken route_compute: compile error": not oneshot_eval("route_compute")["compile_ok"],
        "oneshot latched flit_mux: testbench pass, not struct_clean": (lambda e: e["func_pass"] and not e["struct_clean"])(
            oneshot_eval("flit_mux")),
        "simloop fixes broken route_compute": run("simloop", "route_compute")["func_pass"],
        "stitch fixes broken output_port, clean": run("stitch", "output_port")["clean_pass"],
        "simloop stops on latched flit_mux with 0 calls, not clean": fm["simloop"]["llm_calls"] == 0
                                                                    and not fm["simloop"]["clean_pass"],
        "stitch on latched flit_mux: fired, ends clean": fm["stitch"]["semantic_fired"] and fm["stitch"]["clean_pass"],
        "golden router through both arms: clean, 0 calls": all(run(arm, "router_5port")["clean_pass"] and
                                                              run(arm, "router_5port")["llm_calls"] == 0
                                                              for arm in ("simloop", "stitch")),
        "rep 2 paired with one-shot rep 2": open(os.path.join(work, "arms", "rep2", "tasks", "flit_mux", "input.v")).read()
                                            == open(os.path.join(work, "outputs", "oneshot", "rep2", "flit_mux.v")).read(),
        "rerun skips everything, exit 0": second.returncode == 0 and "llm_calls" not in second.stdout
                                          and second.stdout.count("skip oneshot") == 7 * REPS
                                          and "== arms rep1: runner" not in second.stdout,
    }
    for k, v in checks.items():
        print(f"  {'ok ' if v else 'BAD'} {k}")
    print("MOCK E2E:", "PASS" if all(checks.values()) else "FAIL", "| work dir:", work)
    return 0 if all(checks.values()) else 1


if __name__ == "__main__":
    sys.exit(main())
