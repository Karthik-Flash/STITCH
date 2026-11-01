#!/usr/bin/env python3
"""Assemble whole designs for the mesh3x3 and ni studies and check them. Writes assembled/<design>/ and
reports/ASSEMBLY.md. (The 2x2 study uses pipeline/assemble.py; this script reuses its helpers.)

Module set: this study's NEW modules (tasks/, generated in this study) plus its REUSED modules (reports/reuse.json),
which take the 2x2 results: the 2x2 final file of the same arm (outputs/<arm>/<m>.v in the study root) and the 2x2
local re-evaluation (runs/analysis/<arm>/<m>/eval.json) for the hybrid choices. Golden replacements: tasks/<m>/golden.v
for NEW modules, this study's golden/reference for REUSED ones. Top: studies.TOPS (top_3x3_router; ni_pair, the
wrapper wrapper/ni_pair.v, which is never generated and is part of every NI design).
Designs per arm (oneshot, simloop, stitch): pure, hybrid_compile, hybrid_signoff (as in assemble.py), plus
control_all_golden (every module golden) and A1_style_<study> (golden/A1: the hand-written RTL with only the
Yosys-aborting modules fixed, as in latch_study). Byte-identical designs are kept once, with aliases.
Checks per design: as assemble.py, with the top testbench of tasks/<top>/ or wrapper/<top>/ (tb_signoff.v + lib/).
Per LLM module kept by a hybrid_signoff design: drop-in (golden design with only this module from the arm passes the
top testbench) and Yosys equivalence with its golden (assemble.equiv_texts, clocks=True, golden children flattened);
controls: the 2x2 one-shot encoder must be rejected, and each module found equivalent must be rejected once mutated
(reuse.mutate, else an inverted assignment).
Usage: python3 pipeline/assemble_study.py --study mesh3x3|ni   (needs iverilog, vvp, yosys, verilator; after reeval.py)
"""
from __future__ import annotations

import concurrent.futures as cf
import functools
import glob
import json
import os
import re
import shutil
import sys
import tempfile

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import analysis_common as A  # noqa: E402
import assemble as S  # noqa: E402
import make_tasks as MT  # noqa: E402
import reeval  # noqa: E402
import reuse  # noqa: E402

assert A.NAME != "2x2", "2x2 uses pipeline/assemble.py"
TOP = A.studies.TOP
NEW, REUSED = A.modules(), A.reused()
WRAP = A.studies.WRAPPERS.get(A.NAME, [])
TOP_DIR = os.path.join(A.STUDY, "wrapper" if TOP in WRAP else "tasks", TOP)
OUT = os.path.join(A.STUDY, "assembled")
A1_ID = {"mesh3x3": "A1_style_3x3", "ni": "A1_style_ni"}[A.NAME]
S.OUT = OUT                                           # assemble.write_design writes under assemble.OUT


@functools.lru_cache(None)
def defs_in(d: str) -> dict:
    out = {}
    for f in sorted(glob.glob(os.path.join(d, "*.v"))):
        for n, t in S.module_defs(open(f).read()).items():
            assert n not in out, f"{n} defined twice in {d}"
            out[n] = t
    return out


def golden(m: str) -> str:
    return S.golden(m) if m in NEW else defs_in(os.path.join(A.STUDY, "golden", "reference"))[m]


def wrapper_src() -> dict:
    return {w: (S.module_defs(open(os.path.join(A.STUDY, "wrapper", f"{w}.v")).read())[w] + "\n", "wrapper",
                "wrapper (not golden, never generated)") for w in WRAP}


def ev(arm: str, m: str) -> dict:
    return reeval.load(arm, m) if m in NEW else json.load(open(os.path.join(A.ROOT, "runs", "analysis", arm, m,
                                                                            "eval.json")))


def final(arm: str, m: str) -> str:
    return A.final_file(arm, m) if m in NEW else os.path.join(A.ROOT, "outputs", arm, f"{m}.v")


def label(arm: str, m: str) -> str:
    return arm if m in NEW else f"{arm} (2x2, reused)"


def own(arm: str, m: str) -> str | None:
    return S.module_defs(open(final(arm, m)).read()).get(m)


def design_sources(arm: str, kind: str) -> tuple[dict, list]:
    src, dropped = wrapper_src(), []
    for m in NEW + REUSED:
        e = ev(arm, m)
        if kind == "hybrid_compile" and not e["compile_ok"]:
            src[m] = (golden(m), "golden", "final file does not compile")
            continue
        if kind == "hybrid_signoff" and not e["so_clean"]:
            src[m] = (golden(m), "golden", "final file not so_clean (" + A.flags(
                {"compile": e["compile_ok"], "func": e["func_pass"], "signoff": e["signoff"],
                 "struct_clean": e["struct_clean"]}) + ")")
            continue
        defs = S.module_defs(open(final(arm, m)).read())
        dropped += [f"{m}.v: {n}" for n in defs if n != m]
        src[m] = (defs[m] + "\n", label(arm, m), "LLM final file") if m in defs else \
            (golden(m), "golden", f"no `module {m}` in the {arm} file")
    return src, dropped


def control() -> dict:
    return {**wrapper_src(), **{m: (golden(m), "golden", "control: every module golden") for m in NEW + REUSED}}


def a1_style() -> dict:
    d = defs_in(os.path.join(A.STUDY, "golden", "A1"))
    assert set(d) == set(NEW + REUSED), f"golden/A1 module set differs: {sorted(set(d) ^ set(NEW + REUSED))}"
    return {**wrapper_src(), **{m: (t, "A1", "hand-written RTL, only Yosys-aborting modules fixed (golden/A1)")
                                for m, t in d.items()}}


def tb_run(rtl: dict, work: str) -> dict:
    """Icarus compile of the design (modules renamed <m>__d) with the top testbench, then the simulation."""
    names = sorted(rtl)
    open(os.path.join(work, "design_renamed.v"), "w").write("\n".join(S.rename_for_tb(rtl[n], names) for n in names))
    shutil.copy(os.path.join(TOP_DIR, "tb_signoff.v"), os.path.join(work, "tb.v"))
    lib = sorted(glob.glob(os.path.join(TOP_DIR, "lib", "*.v")))
    rc, clog = S.run(["iverilog", "-g2012", "-o", "sim.vvp", "-s", "tb", "design_renamed.v", *lib, "tb.v"], work)
    r = {"icarus_compile": rc == 0, "compile_error": next((l for l in clog.splitlines() if "error" in l), None),
         "top_tb": "not run", "top_tb_first_fail": None, "_clog": clog, "_slog": ""}
    if rc == 0:
        _, slog = S.run(["vvp", "-n", "sim.vvp"], work)
        r["top_tb"] = "PASS" if "ALL TESTS PASSED" in slog else ("FAIL" if "FAIL" in slog else "UNKNOWN")
        r["top_tb_first_fail"] = next((l for l in slog.splitlines() if "FAIL" in l), None)
        r["_slog"] = slog
    for f in ("sim.vvp", "tb.v", "design_renamed.v"):
        if os.path.exists(os.path.join(work, f)):
            os.remove(os.path.join(work, f))
    return r


def check_design(rtl_dir: str, work: str) -> dict:
    import p3_bridge as B
    files = sorted(os.path.basename(f) for f in glob.glob(os.path.join(rtl_dir, "*.v")))
    os.makedirs(work, exist_ok=True)
    r = tb_run({f[:-2]: open(os.path.join(rtl_dir, f)).read() for f in files}, work)
    open(os.path.join(work, "icarus.log"), "w").write(r.pop("_clog"))
    open(os.path.join(work, "top_tb.log"), "w").write(r.pop("_slog"))
    y = S.yosys_stat(rtl_dir, files, TOP)
    open(os.path.join(work, "yosys.log"), "w").write(y.pop("_log"))
    v = B._ORIG["lint"]([os.path.join(rtl_dir, f) for f in files], TOP, work, 1800)
    open(os.path.join(work, "verilator.log"), "w").write(v["log"])
    r.update(y, verilator_errors=len(v["errors"]), verilator_hard=v["n_hard"], verilator_warnings=v["n_warnings"])
    r["composes"] = r["icarus_compile"] and r["top_tb"] == "PASS"
    return r


def drop_in(arm: str, m: str) -> bool:
    src = {n: t for n, (t, _, _) in control().items()}
    src[m] = own(arm, m) + "\n"
    with tempfile.TemporaryDirectory() as d:
        return tb_run(src, d)["top_tb"] == "PASS"


@functools.lru_cache(None)
def lib_of(m: str) -> str:
    rows, out, todo = MT.load_rows(), [], list(MT.load_rows()[m]["child_list"])
    while todo:
        c = todo.pop()
        if c not in out:
            out.append(c)
            todo += rows[c]["child_list"]
    return "\n".join(golden(c) for c in sorted(out))


def mutate(text: str) -> str:
    """reuse.mutate (first && -> ||, else first 1'b1 -> 1'b0); otherwise the first nonblocking or continuous
    assignment gets its right-hand side inverted."""
    try:
        return reuse.mutate(text)
    except AssertionError:
        out = re.sub(r"(<=|\bassign\s+[^=;]+=)\s*([^;]+);", r"\1 ~(\2);", text, count=1)
        assert out != text, "no mutation point"
        return out


def equivalent(arm: str, m: str) -> dict:
    """clocks=True equivalence with the golden; a module found equivalent must be rejected once mutated."""
    o = own(arm, m)
    eq = S.equiv_texts(golden(m), o, m, lib_of(m), clocks=True)
    r = {"equivalent": eq}
    if eq:
        r["mutant_rejected"] = not S.equiv_texts(golden(m), mutate(o), m, lib_of(m), clocks=True)
    return r


def encoder_control() -> bool:
    """The 2x2 one-shot encoder (compiles, fails its tb) against its golden: must not be equivalent."""
    return S.equiv_texts(open(os.path.join(A.ROOT, "tasks", "encoder", "golden.v")).read(),
                         S.module_defs(open(os.path.join(A.ROOT, "outputs", "oneshot", "encoder.v")).read())["encoder"],
                         "encoder", clocks=True)


def module_checks() -> dict:
    """(arm, m) -> {drop_in, equivalent, mutant_rejected} for every LLM module that a hybrid_signoff design keeps.
    Byte-identical module texts are checked once."""
    jobs = [(arm, m) for arm in A.ARMS for m in NEW + REUSED if ev(arm, m)["so_clean"] and own(arm, m)]
    first = {}
    for j in jobs:
        first.setdefault((j[1], own(*j)), j)
    uniq = list(dict.fromkeys(first.values()))
    with cf.ProcessPoolExecutor(max_workers=min(8, os.cpu_count() or 4)) as ex:
        di = dict(zip(uniq, ex.map(drop_in, *zip(*uniq)))) if uniq else {}
        eq = dict(zip(uniq, ex.map(equivalent, *zip(*uniq)))) if uniq else {}
    out = {}
    for j in jobs:
        u = first[(j[1], own(*j))]
        out[j] = {"where": "new" if j[1] in NEW else "reused (2x2)", "drop_in": di[u], **eq[u]}
    return out


def main() -> int:
    mc = module_checks()
    neg = encoder_control()
    assert not neg, "negative control (2x2 one-shot encoder) passed the equivalence check"
    bad = [k for k, v in mc.items() if v.get("mutant_rejected") is False]
    assert not bad, f"equivalence check accepts a mutant: {bad}"
    if os.path.isdir(OUT):    # no stale design from an earlier run
        shutil.rmtree(OUT)
    os.makedirs(OUT)
    json.dump({**{f"{a}/{m}": v for (a, m), v in mc.items()},
               "_negative_control": {"module": "2x2 oneshot/encoder", "equivalent": neg}},
              open(os.path.join(OUT, "module_checks.json"), "w"), indent=1)
    plan = [(arm, kind) for arm in A.ARMS for kind in ("pure", "hybrid_compile", "hybrid_signoff")]
    plan += [("golden", "control"), ("A1", "a1"), *[(arm, "diag_signoff_dropin") for arm in A.ARMS]]
    designs, alias = {}, {}
    for arm, kind in plan:
        if kind == "control":
            src, dropped, did = control(), [], "control_all_golden"
        elif kind == "a1":
            src, dropped, did = a1_style(), [], A1_ID
        elif kind == "diag_signoff_dropin":
            src, dropped = design_sources(arm, "hybrid_signoff")
            fails = [m for m, (_, s, _) in src.items() if s.startswith(arm) and not mc[(arm, m)]["drop_in"]]
            if not fails:
                continue
            for m in fails:
                src[m] = (golden(m), "golden", "diagnostic: fails the drop-in test")
            did = f"{kind}_{arm}"
        else:
            src, dropped = design_sources(arm, kind)
            did = f"{kind}_{arm}"
        h = S.digest(src)
        if h in alias:
            designs[alias[h]]["aliases"].append(did)
            continue
        alias[h] = did
        designs[did] = {"dir": S.write_design(did, src, dropped), "aliases": [], "digest": h, "dropped": dropped,
                        "golden_modules": sum(s == "golden" for _, s, _ in src.values()),
                        "llm_new": sum(1 for m, (_, s, _) in src.items() if m in NEW and s in A.ARMS),
                        "llm_reused": sum(1 for m, (_, s, _) in src.items() if m in REUSED and s.endswith("reused)"))}
    with cf.ProcessPoolExecutor(max_workers=min(8, os.cpu_count() or 4)) as ex:
        futs = {did: ex.submit(check_design, os.path.join(d["dir"], "rtl"), os.path.join(d["dir"], "check"))
                for did, d in designs.items()}
        ref_dir = os.path.join(A.STUDY, "golden", "reference")    # sanity row (mesh3x3; ni's top is the wrapper)
        reff = None if TOP in WRAP else ex.submit(S.yosys_stat, ref_dir, sorted(
            os.path.basename(f) for f in glob.glob(os.path.join(ref_dir, "*.v"))), TOP)
        for did, f in futs.items():
            designs[did].update(f.result())
        refr = reff and reff.result()
    for d in designs.values():
        json.dump({k: v for k, v in d.items() if k != "dir"}, open(os.path.join(d["dir"], "check", "result.json"), "w"),
                  indent=1)
    n_mod = len(NEW) + len(REUSED)
    md = [f"# Assembly of the {A.NAME} designs (pipeline/assemble_study.py)", "",
          f"Top `{TOP}`" + (" (wrapper `wrapper/ni_pair.v`, not golden, never generated; part of every design)"
                            if TOP in WRAP else "") +
          f". {n_mod} modules: {len(NEW)} NEW (generated in this study: {', '.join(NEW)}) and {len(REUSED)} REUSED "
          "(the 2x2 final file of the same arm, reports/REUSE.md). Golden replacements: tasks/<m>/golden.v (NEW), "
          "golden/reference (REUSED).", "",
          f"composes = Icarus compile of the whole design + `{A.rel(os.path.join(TOP_DIR, 'tb_signoff.v'))}` pass"
          + (" (cycle-exact against the golden design)." if TOP not in WRAP else
             " (property checks: the primary verdict for ni_pair, CP1).") +
          " Yosys: the latch_study script (`synth -top`, `check`, `stat`). Verilator: `--lint-only -Wall`, p3_eval "
          "settings (hard = MULTIDRIVEN, UNOPTFLAT, LATCH, WIDTHTRUNC).", "",
          "| design | golden modules | LLM modules (new / reused) | composes | Icarus compile | top tb | Yosys ok | "
          "cells | latch cells | check problems | logic loops | Verilator errors / hard | aliases |",
          "|---|---|---|---|---|---|---|---|---|---|---|---|---|"]
    for did, d in designs.items():
        md.append(f"| {did} | {d['golden_modules']} | {d['llm_new']} / {d['llm_reused']} | {d['composes']} | "
                  f"{d['icarus_compile']} | {d['top_tb']} | {d['yosys_ok']} | {d['cells']} | {d['latch_cells']} | "
                  f"{d['check_problems']} | {d['loops']} | {d['verilator_errors']} / {d['verilator_hard']} | "
                  f"{', '.join(d['aliases']) or '-'} |")
    if refr:
        md.append(f"| golden/reference (sanity) | - | - | - | - | - | {refr['yosys_ok']} | {refr['cells']} | "
                  f"{refr['latch_cells']} | {refr['check_problems']} | {refr['loops']} | - | - |")
    md += ["", f"control_all_golden = every module golden. {A1_ID} = golden/A1 (reports/HANDWRITTEN.md). "
           "diag_signoff_dropin_<arm> = hybrid_signoff with the LLM modules that fail the drop-in test also replaced "
           "(diagnostic only).", "",
           "## LLM modules kept by hybrid_signoff (so_clean in their task)", "",
           "drop-in = golden design with only this module from the arm passes the top testbench. equivalent = Yosys "
           "formal equivalence with the golden module (clocks=True: clk2fflogic; golden children flattened). mutant "
           "rejected = the LLM module with one operator changed is not equivalent (control).", "",
           "| arm | module | new / reused | drop-in | equivalent to golden | mutant rejected |", "|---|---|---|---|---|---|"]
    md += [f"| {a} | {m} | {v['where']} | {v['drop_in']} | {v['equivalent']} | {v.get('mutant_rejected', '-')} |"
           for (a, m), v in sorted(mc.items())]
    md += ["", f"Negative control: the 2x2 one-shot encoder (compiles, fails its tb) equivalent to golden: {neg}.", "",
           "First errors:", ""]
    for did, d in designs.items():
        bits = [x for x in (d["compile_error"] and f"Icarus: `{d['compile_error'][:200]}`",
                            d["top_tb_first_fail"] and f"top tb: `{d['top_tb_first_fail'][:200]}`",
                            d["yosys_error"] and f"Yosys: `{d['yosys_error'][:200]}`") if x]
        if bits:
            md.append(f"- {did}: " + "; ".join(bits))
    md += ["", "Extra module definitions dropped from LLM files:", ""]
    md += [f"- {did}: {', '.join(d['dropped']) or 'none'}" for did, d in designs.items()]
    A.write_report("ASSEMBLY.md", md)
    print("\n".join(md))
    return 0


if __name__ == "__main__":
    sys.exit(main())
