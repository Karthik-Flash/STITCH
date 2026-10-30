#!/usr/bin/env python3
"""Score the three arms per module and write reports/SUMMARY.md and reports/summary.json.

Arms: oneshot (outputs/oneshot/<m>.v, evaluated here), simloop and stitch (final candidates of the Phase 3 runner,
read from <arms>/results/<model>/<condition>/<m>/rep1/metrics.json). Every final candidate is also simulated
against tasks/<m>/tb_signoff.v (never seen by the loop).
  func     tb.v passes                         clean    func AND struct_clean (p3_eval)
  signoff  tb_signoff.v passes                 so_clean signoff AND struct_clean   <- headline per module
Bonus row: outputs/oneshot/top_module_full.v (the whole router from one prompt). Its modules other than top_module
are renamed <name>__cand so they cannot collide with the reference children the testbench's reference copy uses.

Usage: python pipeline/summarize.py --model qwen2.5-coder:32b [--arms runs/arms]
"""
from __future__ import annotations

import argparse
import glob
import json
import os
import re
import sys
import tempfile

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import p3_bridge as B  # noqa: E402

STUDY = B.STUDY
TASKS = os.path.join(STUDY, "tasks")
ARMS = {"simloop": "baseline", "stitch": "sem_esc_restart_v3"}


def safe(model: str) -> str:
    return re.sub(r"[^A-Za-z0-9_.-]", "_", model)


def score(cand: str, m: str) -> dict:
    td = os.path.join(TASKS, m)
    top = json.load(open(os.path.join(td, "meta.json")))["top"]
    ev = B.evaluate(cand, td, top)
    with tempfile.TemporaryDirectory() as wd:
        so = B.simulate_with(cand, os.path.join(td, "tb_signoff.v"), td, wd)
    return {"compile": ev["compile_ok"], "func": ev["func_pass"], "struct_clean": ev["struct_clean"],
            "clean": ev["clean_pass"], "latch_events": ev["latch_events"], "signoff": so["outcome"] == "PASS",
            "so_clean": so["outcome"] == "PASS" and ev["struct_clean"]}


def call_meta(paths: list[str]) -> dict:
    """done_reason and output tokens of each LLM call (oneshot record.json / arms iter*/llm_meta.json), in order."""
    metas = [json.load(open(p)) for p in paths]
    metas = [m.get("llm_meta", m) for m in metas]
    return {"done_reasons": [m.get("done_reason") for m in metas], "tokens_out": [m.get("eval_count") for m in metas]}


def iter_metas(run_dir: str) -> list[str]:
    ps = glob.glob(os.path.join(run_dir, "iter*", "llm_meta.json"))
    return sorted(ps, key=lambda p: int(re.search(r"iter(\d+)", p).group(1)))


def score_full_router(cand: str) -> dict:
    """Whole-router candidate: rename its non-top modules, compile with the reference lib + top_module tests."""
    td = os.path.join(TASKS, "top_module")
    text = open(cand).read()
    names = [n for n in re.findall(r"\bmodule\s+(\w+)", text) if n != "top_module"]
    for n in names:
        text = re.sub(rf"\b{n}\b", f"{n}__cand", text)
    with tempfile.TemporaryDirectory() as wd:
        ren = os.path.join(wd, "cand.v")
        open(ren, "w").write(text)
        lib, _ = B.task_files(td)
        out = {"modules_defined": len(names) + ("top_module" in text)}
        for tb in ("tb.v", "tb_signoff.v"):
            d = os.path.join(wd, tb[:-2])
            os.makedirs(d)
            import shutil
            shutil.copy(ren, os.path.join(d, "dut.v"))
            shutil.copy(os.path.join(td, tb), os.path.join(d, "tb.v"))
            out[tb] = B._ORIG["simulate"](["dut.v"] + lib, "tb.v", d, 600)["outcome"]
        v = B._ORIG["lint"]([ren], "top_module", wd)
        y = B._ORIG["synth"]([ren], "top_module", wd)
        out.update({"func": out["tb.v"] == "PASS", "signoff": out["tb_signoff.v"] == "PASS",
                    "yosys_ok": y["ok"], "latch_events": y["latch_events"], "verilator_hard": v["n_hard"],
                    "struct_clean": bool(y["ok"] and y["latch_events"] == 0 and y["loops"] == 0 and v["n_hard"] == 0)})
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--model", default="qwen2.5-coder:32b")
    ap.add_argument("--arms", default=os.path.join(B.WORK, "runs", "arms"))
    ap.add_argument("--modules", nargs="*", default=None)
    a = ap.parse_args()
    modules = a.modules or sorted(m for m in os.listdir(TASKS) if os.path.isdir(os.path.join(TASKS, m)))
    rows = []
    for m in modules:
        row = {"module": m}
        one = os.path.join(B.WORK, "outputs", "oneshot", f"{m}.v")
        rec = os.path.join(B.WORK, "runs", "oneshot", m, "record.json")
        status = json.load(open(rec)).get("status", "ok") if os.path.exists(rec) else None
        row["oneshot"] = score(one, m) if os.path.exists(one) and status == "ok" else None
        row["status"] = {"oneshot": "INFRA" if status == "infra_error" else None}
        if row["oneshot"]:
            row["oneshot"].update(call_meta([rec]))
        for arm, cond in ARMS.items():
            mp = os.path.join(a.arms, "results", safe(a.model), cond, m, "rep1", "metrics.json")
            if not os.path.exists(mp):
                row[arm] = None
                err = os.path.join(os.path.dirname(mp), "error.json")
                if os.path.exists(err):
                    msg = json.load(open(err)).get("error", "")
                    row["status"][arm] = "INFRA" if re.search(r"timed? ?out|Timeout|URLError|Connection|ollama failed",
                                                              msg, re.I) else "ERROR"
                continue
            met = json.load(open(mp))
            s = score(met["final_candidate"], m)
            s.update({"iterations": met["iterations"], "stop": met["stop_reason"],
                      "semantic_fired": met["semantic_fired"], "classes": met["classes_fired"],
                      "runner_func": met["func_pass"], "runner_clean": met["clean_pass"],
                      **call_meta(iter_metas(os.path.dirname(mp)))})
            row[arm] = s
        rows.append(row)
        print(m, {k: (row[k]["so_clean"] if row[k] else row["status"].get(k)) for k in ("oneshot", *ARMS)},
              flush=True)
    full = os.path.join(B.WORK, "outputs", "oneshot", "top_module_full.v")
    bonus = score_full_router(full) if os.path.exists(full) else None

    def cell(s, status=None):
        if s is None:
            return status or "--"
        flags = "".join(c if s[k] else "." for c, k in (("C", "compile"), ("F", "func"), ("S", "signoff"),
                                                         ("K", "struct_clean")))
        extra = f" it={s['iterations']} sf={int(s['semantic_fired'])}" if "iterations" in s else ""
        return f"{flags}{' **so_clean**' if s['so_clean'] else ''}{extra}"

    md = ["# One-shot vs simulation loop vs STITCH", "", f"Model: `{a.model}`. Generated by `pipeline/summarize.py`.",
          "", "Flags: C compile, F tb.v pass, S tb_signoff.v pass, K struct_clean (Yosys 0 latches/loops, Verilator 0 "
          "hard warnings); `.` = no. so_clean = S and K. it = LLM calls, sf = STITCH semantic feedback fired. "
          "INFRA = not finished: timeout or connection error (resubmit retries it); ERROR = runner error; "
          "-- = not run. Totals count finished modules only.", "",
          "| module | oneshot | simloop (baseline) | stitch (sem_esc_restart_v3) |", "|---|---|---|---|"]
    for r in rows:
        md.append(f"| {r['module']} | " + " | ".join(cell(r[k], r["status"].get(k)) for k in ("oneshot", *ARMS)) + " |")
    tot = {arm: sum(1 for r in rows if r.get(arm) and r[arm]["so_clean"]) for arm in ("oneshot", "simloop", "stitch")}
    n = {arm: sum(1 for r in rows if r.get(arm)) for arm in ("oneshot", "simloop", "stitch")}
    md += ["", "so_clean totals: " + ", ".join(f"{arm} {tot[arm]}/{n[arm]}" for arm in tot)]
    length = {arm: [f"{r['module']}#{i}" for r in rows if r.get(arm)
                    for i, d in enumerate(r[arm].get("done_reasons", []), 1) if d == "length"] for arm in tot}
    md += ["", "LLM calls that ended with done_reason=length (module#call): "
           + "; ".join(f"{arm} {len(v)} ({', '.join(v) or '-'})" for arm, v in length.items())]
    if bonus:
        md += ["", "Bonus, whole router in one prompt (`top_module_full`): " + json.dumps(bonus)]
    else:
        bud = os.path.join(STUDY, "reports", "PREDEPLOY_BUDGET.md")
        hit = re.search(r"\| top_module_full \| (\d+) \|", open(bud).read()) if os.path.exists(bud) else None
        ctx = re.search(r"\| options\.num_ctx \| \d+ \| \d+ \| (\d+) \|", open(bud).read()) if hit else None
        md += ["", "Bonus, whole router in one prompt (`top_module_full`): not attempted"
               + (f": prompt alone {int(hit.group(1)):,} of {int(ctx.group(1)):,} tokens (budget.py)" if ctx else "")]
    os.makedirs(os.path.join(B.WORK, "reports"), exist_ok=True)
    open(os.path.join(B.WORK, "reports", "SUMMARY.md"), "w").write("\n".join(md) + "\n")
    json.dump({"model": a.model, "rows": rows, "totals": tot, "n": n, "full_router": bonus},
              open(os.path.join(B.WORK, "reports", "summary.json"), "w"), indent=1)
    print("\n".join(md))
    return 0


if __name__ == "__main__":
    sys.exit(main())
