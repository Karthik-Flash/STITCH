#!/usr/bin/env python3
"""
Gate 1 -- run on the SAME toolchain the experiment will use (laptop WSL and again on HPC oss-cad-suite).
Checks, per task, using LIVE tool output (not frozen fixtures):
  golden.v  -> func_pass AND struct_clean
  input.v   -> NOT clean_pass; sim outcome matches meta.sim_silent; defect visible to a tool
  drift     -> interpreter v3 on the live logs fires meta.expected_v3_classes; v2 fires meta.expected_v2_classes.
               A mismatch here means the installed Yosys/Verilator print a different message format than
               the one the interpreter was verified on (Yosys 0.33 / Verilator 5.020) -- STOP and report.
Exit code 0 only if every check passes.
"""
import json, os, re, subprocess, sys
HERE = os.path.dirname(os.path.abspath(__file__))
PHASE3_ROOT = os.path.dirname(HERE)
INTERP_DIR = (os.environ.get("STITCH_INTERPRETER_DIR") or os.environ.get("STITCH_INTERP_DIR")
              or os.path.join(os.path.dirname(PHASE3_ROOT), "src", "interpreter"))
sys.path.insert(0, HERE); sys.path.insert(0, INTERP_DIR)
from p3_eval import evaluate, IVERILOG, VERILATOR, YOSYS   # noqa: E402
import stitch_interpreter_v3 as V                          # noqa: E402

T = os.path.join(PHASE3_ROOT, "tasks")


def version(cmd):
    try:
        p = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
        return ((p.stdout or "") + (p.stderr or "")).strip().splitlines()[0]
    except Exception as e:
        return f"MISSING ({e.__class__.__name__})"


tools = {"yosys": version([YOSYS, "-V"]), "verilator": version([VERILATOR, "--version"]),
         "iverilog": version([IVERILOG, "-V"])}
print("toolchain:", json.dumps(tools))
print("interpreter dir:", INTERP_DIR, "| production sha256(LF):", V.base_fingerprint())
if any(v.startswith("MISSING") for v in tools.values()):
    print("GATE 1: FAIL (tool missing -- put oss-cad-suite/bin on PATH)"); sys.exit(2)

ok_all, rows = True, []
for t in sorted(os.listdir(T)):
    td = os.path.join(T, t)
    m = json.load(open(os.path.join(td, "meta.json")))
    g = evaluate(os.path.join(td, "golden.v"), td, m["top"])
    i = evaluate(os.path.join(td, "input.v"), td, m["top"])
    L = i["_logs"]
    r3 = V.interpret(L["verilator"], L["yosys"], os.path.join(td, "input.v"), version="v3", top=m["top"])
    r2 = V.interpret(L["verilator"], L["yosys"], os.path.join(td, "input.v"), version="v2", top=m["top"])
    checks = {
        "golden_func": g["func_pass"], "golden_clean": g["struct_clean"],
        "input_not_clean": not i["clean_pass"],
        "input_sim_matches_meta": i["func_pass"] == m["sim_silent"],
        "input_defect_visible": (not i["struct_clean"]) or (not i["func_pass"]),
        "drift_v3_classes": sorted(r3["classes_fired"]) == sorted(m["expected_v3_classes"]),
        "drift_v2_classes": sorted(r2["classes_fired"]) == sorted(m["expected_v2_classes"]),
    }
    ok = all(checks.values()); ok_all &= ok
    rows.append({"task": t, "ok": ok, "checks": checks, "v3_classes": r3["classes_fired"], "v2_classes": r2["classes_fired"],
                 "input": {k: v for k, v in i.items() if k != "_logs"}, "golden": {k: v for k, v in g.items() if k != "_logs"}})
    print(f"{'OK ' if ok else 'BAD'} {t:<16} golden(func={g['func_pass']},clean={g['struct_clean']}) "
          f"input(sim={i['sim_outcome']},yosys_ok={i['yosys_ok']},latch_ev={i['latch_events']},vcodes={i['verilator_codes']}) "
          f"v2={r2['classes_fired']} v3={r3['classes_fired']}"
          + ("" if ok else f"   FAILED: {[k for k, v in checks.items() if not v]}"))
out = os.path.join(PHASE3_ROOT, "evidence", "task_validation.json")
try:
    json.dump({"toolchain": tools, "rows": rows}, open(out, "w"), indent=1)
except OSError:
    pass
print("GATE 1:", "PASS" if ok_all else "FAIL"); sys.exit(0 if ok_all else 1)
