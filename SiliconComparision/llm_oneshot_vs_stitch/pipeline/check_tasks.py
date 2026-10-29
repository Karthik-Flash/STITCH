#!/usr/bin/env python3
"""Validate every task on the live toolchain (run where Yosys/Verilator/Icarus are on PATH).

Per task:
  ref_loop     golden.v passes tb.v                         (through p3_eval, children from lib/)
  ref_clean    golden.v is struct_clean (p3_eval definition; informational: the STITCH arm stops on clean_pass)
  ref_signoff  golden.v passes tb_signoff.v
  mutant       golden with bit 0 of one output inverted FAILS tb_signoff.v (must hold for every task)
  registers    the hand-written input.v does not sign off (tb_signoff PASS and struct_clean), as expected
  v3           interpreter v3 classes on the hand-written input (drift check: registers must match Phase 3 meta)
Writes reports/task_validation.json and reports/TASK_VALIDATION.md. Exit 0 only if every expectation holds.
Usage: python pipeline/check_tasks.py [--tasks a b ...] [--jobs N]
"""
from __future__ import annotations

import argparse
import concurrent.futures as cf
import json
import os
import sys
import tempfile

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import p3_bridge as B  # noqa: E402
import make_tasks as MT  # noqa: E402

TASKS = os.path.join(B.STUDY, "tasks")
REPORTS = os.path.join(B.STUDY, "reports")


def check(name: str) -> dict:
    import stitch_interpreter_v3 as IV3
    td = os.path.join(TASKS, name)
    meta = json.load(open(os.path.join(td, "meta.json")))
    top = meta["top"]
    rows = MT.load_rows()
    with tempfile.TemporaryDirectory(prefix=f"chk_{name}_") as wd:
        g = B.evaluate(os.path.join(td, "golden.v"), td, top)
        so = B.simulate_with(os.path.join(td, "golden.v"), os.path.join(td, "tb_signoff.v"), td,
                             os.path.join(wd, "ref_so"))
        mpath = os.path.join(wd, "mutant.v")
        open(mpath, "w").write(MT.mutant(name, rows[name], open(os.path.join(td, "golden.v")).read()))
        mso = B.simulate_with(mpath, os.path.join(td, "tb_signoff.v"), td, os.path.join(wd, "mut_so"))
        info = [l for l in so["log"].splitlines() if l.startswith("INFO")]
        r = {"task": name, "timing": meta.get("timing_dependent", False),
             "ref_loop": g["func_pass"], "ref_clean": g["struct_clean"], "ref_latch_events": g["latch_events"],
             "ref_verilator_hard": g["verilator_hard"], "ref_verilator_codes": g["verilator_codes"],
             "ref_signoff": so["outcome"] == "PASS", "ref_signoff_info": info,
             "mutant_output": MT.MUTANT_OUTPUT.get(name) or meta["checked_outputs"][0],
             "mutant_signoff": mso["outcome"],
             "mutant_first_fail": next((l for l in mso["log"].splitlines() if "FAIL" in l), "")}
        if not r["ref_loop"]:
            r["ref_loop_log"] = [l for l in g["_logs"]["sim"].splitlines() if "FAIL" in l or "rror" in l][:5]
        if not r["ref_signoff"]:
            r["ref_signoff_log"] = [l for l in so["log"].splitlines() if "FAIL" in l or "rror" in l][:5]
        if name in MT.PHASE3_REGISTERS:
            i = B.evaluate(os.path.join(td, "input.v"), td, top)
            iso = B.simulate_with(os.path.join(td, "input.v"), os.path.join(td, "tb_signoff.v"), td,
                                  os.path.join(wd, "in_so"))
            v3 = IV3.interpret(i["_logs"]["verilator"], i["_logs"]["yosys"], os.path.join(td, "input.v"),
                               version="v3", top=top)
            r.update({"input_signoff_sim": iso["outcome"], "input_struct_clean": i["struct_clean"],
                      "input_latch_events": i["latch_events"], "input_yosys_ok": i["yosys_ok"],
                      "input_signs_off": iso["outcome"] == "PASS" and i["struct_clean"],
                      "input_v3_classes": sorted(v3["classes_fired"]),
                      "expected_v3_classes": sorted(meta.get("expected_v3_classes", [])),
                      "v3_drift_ok": sorted(v3["classes_fired"]) == sorted(meta.get("expected_v3_classes", []))})
    r["ok"] = bool(r["ref_loop"] and r["ref_signoff"] and r["mutant_signoff"] != "PASS"
                   and (name not in MT.PHASE3_REGISTERS or (not r["input_signs_off"] and r["v3_drift_ok"])))
    return r


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--tasks", nargs="*")
    ap.add_argument("--jobs", type=int, default=os.cpu_count() or 2)
    a = ap.parse_args()
    names = a.tasks or sorted(os.listdir(TASKS))
    names = [n for n in names if os.path.isdir(os.path.join(TASKS, n))]
    with cf.ProcessPoolExecutor(a.jobs) as ex:
        rows = sorted(ex.map(check, names), key=lambda r: r["task"])
    os.makedirs(REPORTS, exist_ok=True)
    tools = {k: B.E._run([cmd, flag], ".", 30)[1].strip().splitlines()[0]
             for k, cmd, flag in (("yosys", B.E.YOSYS, "-V"), ("verilator", B.E.VERILATOR, "--version"),
                                  ("iverilog", B.E.IVERILOG, "-V"))}
    json.dump({"toolchain": tools, "rows": rows}, open(os.path.join(REPORTS, "task_validation.json"), "w"), indent=1)
    md = ["# Task validation", "", "Generated by `pipeline/check_tasks.py`.", "",
          f"Toolchain: {tools['yosys']}; {tools['verilator']}; {tools['iverilog']}", "",
          "| task | timing | ref tb.v | ref tb_signoff | ref struct_clean | mutant (flipped output) tb_signoff | ok |",
          "|---|---|---|---|---|---|---|"]
    for r in rows:
        md.append(f"| {r['task']} | {'yes' if r['timing'] else ''} | {'PASS' if r['ref_loop'] else 'FAIL'} | "
                  f"{'PASS' if r['ref_signoff'] else 'FAIL'} | {r['ref_clean']} | "
                  f"{r['mutant_signoff']} (`{r['mutant_output']}`) | {'yes' if r['ok'] else 'NO'} |")
    md += ["", "Hand-written Phase 3 registers (expected not to sign off):", "",
           "| task | tb_signoff sim | struct_clean | latch events | signs off | v3 classes | expected v3 |",
           "|---|---|---|---|---|---|---|"]
    for r in rows:
        if "input_signs_off" in r:
            md.append(f"| {r['task']} | {r['input_signoff_sim']} | {r['input_struct_clean']} | {r['input_latch_events']} | "
                      f"{r['input_signs_off']} | {r['input_v3_classes']} | {r['expected_v3_classes']} |")
    open(os.path.join(REPORTS, "TASK_VALIDATION.md"), "w").write("\n".join(md) + "\n")
    bad = [r["task"] for r in rows if not r["ok"]]
    print("\n".join(md))
    print("TASK VALIDATION:", "PASS" if not bad else f"FAIL {bad}")
    return 0 if not bad else 1


if __name__ == "__main__":
    sys.exit(main())
