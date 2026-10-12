"""Step 2: toolchain parity. Re-evaluate saved Set 3 candidates (run on HPC
oss-cad-suite) with the laptop's WSL tools through the SAME engine functions,
and compare with what Set 3 recorded.

  (a) detect_outcome verdict (sim_outcome) on every sampled iteration;
  (b) where Set 3 ran the tools on that iteration: semantic_fired, and for
      sem_adv the directive class (interpreter codes + Yosys latch/loop).
      Escalation run logs store only interpreter_invoked, so (b) there is
      the fired flag.

Sample (deterministic): for every module x condition, the first PASS
iteration, the first FAIL iteration, and the first semantic-fired iteration
found (sorted order), each counted once. Run in WSL:
  PYTHONPATH=/mnt/c/Users/karth/stitch_set4_pylib python3 phase2/frontier/parity_check.py
Writes phase2/results/set4_api/parity_check.json.
"""
import glob
import json
import os
import shutil
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
PHASE2 = os.path.dirname(HERE)
if os.environ.get("STITCH_SET4_OSSCAD"):
    os.environ["PATH"] = os.path.join(os.environ["STITCH_SET4_OSSCAD"], "bin") + os.pathsep + os.environ["PATH"]
sys.path.insert(0, PHASE2)
import stitch_runner_hpc as sr  # noqa: E402

S3 = os.path.join(PHASE2, "results", "set3_run")
OUT = os.path.join(PHASE2, "results", "set4_api",
                   "parity_check_osscad.json" if os.environ.get("STITCH_SET4_OSSCAD") else "parity_check.json")
SKIP = {"llm_response.txt", "feedback.txt", "sim_log.txt", "sim.vvp"}


def saved_iterations():
    """Yield dicts: module, condition, run_dir, iter, sim_outcome, tools_ran, fired, cls."""
    for p in sorted(glob.glob(os.path.join(S3, "*", "*", "*", "rep*", "*.json"))):
        name = os.path.basename(p)
        parts = p.split(os.sep)
        module, cond = parts[-5], parts[-3]
        run_dir = os.path.dirname(p)
        d = json.load(open(p, encoding="utf-8"))
        if name == "metrics.json":
            for it in d["per_iter_detail"]:
                tools = cond == "sem_adv"
                yield dict(module=module, condition=cond, run_dir=run_dir, iter=it["iter"],
                           sim_outcome=it["sim_outcome"], tools_ran=tools,
                           fired=bool(it["semantic_fired"]),
                           cls=(sorted(it["interp_codes"]), it["yosys_latch"], it["yosys_loop"]) if tools else None)
        elif name == "run_log.json":
            for it in d["iterations"]:
                tools = it["escalation_state"] == "escalated"
                yield dict(module=module, condition=cond, run_dir=run_dir, iter=it["iteration"],
                           sim_outcome=it["sim_outcome"], tools_ran=tools,
                           fired=bool(it["interpreter_invoked"]), cls=None)


def sample():
    picked, seen = [], set()
    for it in saved_iterations():
        k = (it["module"], it["condition"])
        for role in ("PASS" if it["sim_outcome"] == "PASS" else "FAIL",
                     "FIRED" if it["fired"] else None):
            if role and (k, role) not in seen:
                seen.add((k, role))
                it = dict(it, role=role)
                if not any(p["run_dir"] == it["run_dir"] and p["iter"] == it["iter"] for p in picked):
                    picked.append(it)
    return picked


def reevaluate(it):
    src = os.path.join(it["run_dir"], f"iter_{it['iter']}")
    with tempfile.TemporaryDirectory() as tmp:
        for f in os.listdir(src):
            if f not in SKIP:
                shutil.copy(os.path.join(src, f), tmp)
        v_path = os.path.join(tmp, f"{it['module']}.v")
        _, fb, outcome = sr.run_iverilog_sim(tmp, it["module"], benchmark="rtllm")
        res = {"sim_outcome": outcome}
        if it["tools_ran"]:
            vout, vflag = sr.run_verilator_lint(v_path)
            text, codes = sr.interpret_verilator(vout, v_path) if vflag else ("", [])
            latch = loop = False
            if "COMPILATION ERROR" not in fb:
                _, latch, _, _, loop, _ = sr.run_yosys_check(v_path, it["module"])
            res["fired"] = bool(text) or latch or loop
            res["cls"] = (sorted(codes), latch, loop)
    return res


def main():
    picked = sample()
    rows, a_ok, b_n, b_ok = [], 0, 0, 0
    for n, it in enumerate(picked, 1):
        r = reevaluate(it)
        a = r["sim_outcome"] == it["sim_outcome"]
        a_ok += a
        row = {k: it[k] for k in ("module", "condition", "iter", "role", "sim_outcome", "fired")}
        row["run"] = os.path.relpath(it["run_dir"], S3)
        row.update(local_outcome=r["sim_outcome"], a_match=a)
        if it["tools_ran"]:
            b_n += 1
            b = r["fired"] == it["fired"] and (it["cls"] is None or list(r["cls"]) == list(it["cls"]))
            b_ok += b
            row.update(local_fired=r["fired"], saved_cls=it["cls"], local_cls=r["cls"], b_match=b)
        rows.append(row)
        flag = "" if a and row.get("b_match", True) else "   <-- MISMATCH"
        print(f"[{n}/{len(picked)}] {row['run']} iter {it['iter']} {it['role']}: "
              f"saved {it['sim_outcome']} local {r['sim_outcome']}"
              + (f" | fired saved {it['fired']} local {r['fired']}" if it["tools_ran"] else "") + flag)
    summary = {
        "candidates": len(rows),
        "modules": len({r["module"] for r in rows}), "conditions": len({r["condition"] for r in rows}),
        "passes": sum(r["sim_outcome"] == "PASS" for r in rows),
        "fails": sum(r["sim_outcome"] != "PASS" for r in rows),
        "a_agree": a_ok, "b_checked": b_n, "b_agree": b_ok,
        "b_fired_in_sample": sum(1 for r in rows if r.get("fired") and "b_match" in r),
    }
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    json.dump({"summary": summary, "rows": rows}, open(OUT, "w", encoding="utf-8"), indent=2)
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
