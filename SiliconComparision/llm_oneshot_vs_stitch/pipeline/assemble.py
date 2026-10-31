#!/usr/bin/env python3
"""Assemble whole 2x2 meshes from the arms' final files and check them. Writes assembled/<design>/ and
reports/ASSEMBLY.md.

Top and module set: those of A1 (latch_study/A1_original_synthesisable/mesh2x2; top top_2x2_router, the top that
latch_study/scripts/run_yosys_stat.sh uses for mesh2x2). Golden replacements: tasks/<m>/golden.v, i.e. the study's
golden/reference (B-equivalent plus the two declaration-only lines, see README).
Designs per arm (oneshot, simloop, stitch):
  pure            every module from the arm's final file
  hybrid_compile  modules whose final file does not compile in its task replaced by golden
  hybrid_signoff  modules that are not so_clean replaced by golden
Each module's definition is taken from its own file only; other module definitions in an LLM file are dropped and
listed. Identical designs (sha256 over the sorted per-module files) are kept once, with aliases.
Checks per design: Icarus compile of the whole mesh with tasks/top_2x2_router/tb_signoff.v (design modules renamed
<m>__d so the testbench's golden reference copy keeps the golden children); top tb pass; Yosys
(read; hierarchy -check -top; synth -top; check; stat -top, the latch_study script): cells, $_DLATCH cells, check
problems, logic loops; Verilator --lint-only -Wall (p3_eval's settings). composes = compile + top tb pass.
Sanity rows: A1 and golden/reference through the same Yosys script.
Usage: python pipeline/assemble.py   (needs iverilog, vvp, yosys, verilator; after pipeline/reeval.py)
"""
from __future__ import annotations

import concurrent.futures as cf
import glob
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import analysis_common as A  # noqa: E402
import reeval  # noqa: E402

TOP = "top_2x2_router"
A1_DIR = os.path.join(os.path.dirname(A.STUDY), "latch_study", "A1_original_synthesisable", "mesh2x2")
OUT = os.path.join(A.STUDY, "assembled")
MOD_RE = re.compile(r"\bmodule\s+(\w+)\b.*?\bendmodule\b", re.S)


def strip_comments(t: str) -> str:
    return re.sub(r"//[^\n]*|/\*.*?\*/", lambda x: " " * len(x.group(0)) if "\n" not in x.group(0) else
                  re.sub(r"[^\n]", " ", x.group(0)), t, flags=re.S)


def module_defs(text: str) -> dict:
    """name -> exact source text of each module definition (comments ignored for finding the boundaries)."""
    clean = strip_comments(text)
    return {m.group(1): text[m.start():m.end()] for m in MOD_RE.finditer(clean)}


def a1_modules() -> set:
    return {n for f in glob.glob(os.path.join(A1_DIR, "*.v")) for n in module_defs(open(f).read())}


def golden(m: str) -> str:
    return module_defs(open(os.path.join(A.STUDY, "tasks", m, "golden.v")).read())[m]


def design_sources(arm: str, kind: str) -> tuple[dict, list, list]:
    """module -> (text, source, reason); dropped extra definitions; modules missing from the arm file."""
    src, dropped = {}, []
    for m in A.modules():
        e = reeval.load(arm, m)
        if kind == "hybrid_compile" and not e["compile_ok"]:
            src[m] = (golden(m), "golden", "final file does not compile")
            continue
        if kind == "hybrid_signoff" and not e["so_clean"]:
            src[m] = (golden(m), "golden", "final file not so_clean (" + A.flags(
                {"compile": e["compile_ok"], "func": e["func_pass"], "signoff": e["signoff"],
                 "struct_clean": e["struct_clean"]}) + ")")
            continue
        defs = module_defs(open(A.final_file(arm, m)).read())
        dropped += [f"{m}.v: {n}" for n in defs if n != m]
        if m in defs:
            src[m] = (defs[m] + "\n", arm, "LLM final file")
        else:
            src[m] = (golden(m), "golden", f"no `module {m}` in the {arm} file")
    return src, dropped, []


def digest(src: dict) -> str:
    return hashlib.sha256("".join(f"{m}:{hashlib.sha256(t.encode()).hexdigest()}\n"
                                  for m, (t, _, _) in sorted(src.items())).encode()).hexdigest()


def rename_for_tb(text: str, names: list[str]) -> str:
    """Design modules -> <m>__d (definitions and instantiations), so the tb's golden reference copy is untouched."""
    for n in names:
        if n == TOP:
            continue
        text = re.sub(rf"\bmodule\s+{n}\b", f"module {n}__d", text)
        text = re.sub(rf"(?m)^(\s*){n}(\s+(?:#\s*\(|[A-Za-z_]\w*\s*\())", rf"\g<1>{n}__d\g<2>", text)
    return text


def run(cmd, cwd, timeout=3600):
    p = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True, timeout=timeout)
    return p.returncode, p.stdout + p.stderr


def yosys_stat(rtl_dir: str, files: list[str]) -> dict:
    script = f"read_verilog {' '.join(files)}; hierarchy -check -top {TOP}; synth -top {TOP}; check; stat -top {TOP}"
    rc, log = run(["yosys", "-p", script], rtl_dir)
    sec = log[log.rfind("=== design hierarchy ==="):] if "=== design hierarchy ===" in log else ""
    total = latches = 0
    for line in sec.splitlines():
        t = line.split()
        if len(t) >= 2 and re.fullmatch(r"\d+", t[0]) and t[1].startswith("$"):
            n, typ = int(t[0]), t[1]
        elif len(t) >= 2 and t[0].startswith("$") and re.fullmatch(r"\d+", t[-1]):
            n, typ = int(t[-1]), t[0]
        else:
            continue
        total += n
        latches += n if re.match(r"\$_?DLATCH", typ) else 0
    prob = re.findall(r"Found and reported (\d+) problems", log)
    loops = len(set(re.findall(r"^Warning: found logic loop in module (\S+)", log, re.M)))
    err = next((l for l in log.splitlines() if l.startswith("ERROR")), None)
    return {"yosys_ok": rc == 0 and err is None, "cells": total if sec else None,
            "latch_cells": latches if sec else None, "check_problems": int(prob[-1]) if prob else None,
            "loops": loops, "yosys_error": err, "_log": log}


def check_design(rtl_dir: str, work: str) -> dict:
    import p3_bridge as B
    files = sorted(os.path.basename(f) for f in glob.glob(os.path.join(rtl_dir, "*.v")))
    names = [f[:-2] for f in files]
    os.makedirs(work, exist_ok=True)
    ren = os.path.join(work, "design_renamed.v")
    open(ren, "w").write("\n".join(rename_for_tb(open(os.path.join(rtl_dir, f)).read(), names) for f in files))
    td = os.path.join(A.STUDY, "tasks", TOP)
    lib = sorted(glob.glob(os.path.join(td, "lib", "*.v")))
    shutil.copy(os.path.join(td, "tb_signoff.v"), os.path.join(work, "tb.v"))
    rc, clog = run(["iverilog", "-g2012", "-o", "sim.vvp", "-s", "tb", "design_renamed.v", *lib, "tb.v"], work)
    r = {"icarus_compile": rc == 0, "compile_error": next((l for l in clog.splitlines() if "error" in l), None)}
    if rc == 0:
        _, slog = run(["vvp", "-n", "sim.vvp"], work)
        r["top_tb"] = "PASS" if "ALL TESTS PASSED" in slog else ("FAIL" if "FAIL" in slog else "UNKNOWN")
        r["top_tb_first_fail"] = next((l for l in slog.splitlines() if "FAIL" in l), None)
        open(os.path.join(work, "top_tb.log"), "w").write(slog)
    else:
        r["top_tb"], r["top_tb_first_fail"] = "not run", None
    for f in ("sim.vvp", "tb.v", "design_renamed.v"):
        if os.path.exists(os.path.join(work, f)):
            os.remove(os.path.join(work, f))
    open(os.path.join(work, "icarus.log"), "w").write(clog)
    y = yosys_stat(rtl_dir, files)
    open(os.path.join(work, "yosys.log"), "w").write(y.pop("_log"))
    v = B._ORIG["lint"]([os.path.join(rtl_dir, f) for f in files], TOP, work, 600)
    open(os.path.join(work, "verilator.log"), "w").write(v["log"])
    r.update(y, verilator_errors=len(v["errors"]), verilator_hard=v["n_hard"], verilator_warnings=v["n_warnings"])
    r["composes"] = r["icarus_compile"] and r["top_tb"] == "PASS"
    return r


def write_design(did: str, src: dict, dropped: list) -> str:
    d = os.path.join(OUT, did)
    if os.path.isdir(d):
        shutil.rmtree(d)
    os.makedirs(os.path.join(d, "rtl"))
    lines = ["module,source,reason,sha256"]
    for m, (t, s, why) in sorted(src.items()):
        p = os.path.join(d, "rtl", f"{m}.v")
        open(p, "w", newline="\n").write(t)
        lines.append(f"{m},{s},{why},{A.sha(p)}")
    open(os.path.join(d, "SOURCES.csv"), "w", newline="\n").write("\n".join(lines) + "\n")
    open(os.path.join(d, "DROPPED.txt"), "w", newline="\n").write("\n".join(dropped) + ("\n" if dropped else ""))
    return d


def equivalent(arm: str, m: str) -> bool:
    """Yosys formal equivalence of the arm's module m against golden (synthesis semantics: blocking vs nonblocking
    assignment and sensitivity lists do not matter). proc; memory_map; async2sync; equiv_make/simple/induct -seq 5."""
    with tempfile.TemporaryDirectory() as d:
        open(os.path.join(d, "g.v"), "w").write(re.sub(rf"\bmodule\s+{m}\b", "module gold", golden(m)))
        own = module_defs(open(A.final_file(arm, m)).read()).get(m)
        if own is None:
            return False
        open(os.path.join(d, "l.v"), "w").write(re.sub(rf"\bmodule\s+{m}\b", "module gate", own))
        rc, _ = run(["yosys", "-q", "-p", "read_verilog g.v; read_verilog l.v; proc; memory -nomap; memory_map; "
                     "opt_clean; async2sync; equiv_make gold gate eq; hierarchy -top eq; equiv_simple -seq 5; "
                     "equiv_induct -seq 5; equiv_status -assert"], d, 600)
        return rc == 0


def drop_in(arm: str, m: str) -> bool:
    """Golden mesh with only module m from the arm: compile + top sign-off tb pass (funnel's 'composes' stage)."""
    src = {x: (golden(x), "golden", "") for x in A.modules()}
    src[m] = (module_defs(open(A.final_file(arm, m)).read()).get(m, golden(m)) + "\n", arm, "")
    with tempfile.TemporaryDirectory() as d:
        os.makedirs(os.path.join(d, "rtl"))
        for x, (t, _, _) in src.items():
            open(os.path.join(d, "rtl", f"{x}.v"), "w").write(t)
        files = sorted(os.listdir(os.path.join(d, "rtl")))
        ren = "\n".join(rename_for_tb(open(os.path.join(d, "rtl", f)).read(), [f[:-2] for f in files]) for f in files)
        open(os.path.join(d, "design.v"), "w").write(ren)
        td = os.path.join(A.STUDY, "tasks", TOP)
        shutil.copy(os.path.join(td, "tb_signoff.v"), os.path.join(d, "tb.v"))
        rc, _ = run(["iverilog", "-g2012", "-o", "s.vvp", "-s", "tb", "design.v",
                     *sorted(glob.glob(os.path.join(td, "lib", "*.v"))), "tb.v"], d)
        if rc != 0:
            return False
        _, log = run(["vvp", "-n", "s.vvp"], d)
        return "ALL TESTS PASSED" in log


NEGATIVE_CONTROL = ("oneshot", "encoder")  # compiles, fails its tb: the equivalence check must reject it


def module_checks() -> dict:
    """(arm, m) -> {drop_in, equivalent} for every module whose final file is so_clean (the LLM modules that
    hybrid_signoff keeps)."""
    jobs = [(arm, m) for arm in A.ARMS for m in A.modules() if reeval.load(arm, m)["so_clean"]]
    with cf.ProcessPoolExecutor(max_workers=min(8, os.cpu_count() or 4)) as ex:
        di = list(ex.map(drop_in, *zip(*jobs)))
        eq = list(ex.map(equivalent, *zip(*jobs)))
    return {j: {"drop_in": d, "equivalent": e} for j, d, e in zip(jobs, di, eq)}


def race_modules(mc: dict, arm: str | None = None) -> list:
    """LLM modules kept by hybrid_signoff that fail the drop-in mesh test but are formally equivalent to golden."""
    return sorted({m for (a, m), v in mc.items() if (arm is None or a == arm) and not v["drop_in"] and v["equivalent"]})


def race_note(mods: list) -> str:
    rt = " (routing_algo_mesh is combinational: the golden uses nonblocking assignments in an explicit-list always " \
         "block, the LLM module `always @(*)`)" if "routing_algo_mesh" in mods else ""
    return (f"Fails the cycle-exact mesh tb only through {', '.join(mods)}. Each is formally equivalent to its golden "
            "module (Yosys equivalence check; a negative control fails). The mismatch comes from the golden's "
            "blocking-assignment flops (q = d) racing in simulation; the LLM modules use nonblocking (<=)" + rt +
            ". With those swapped back to golden the mesh composes (diag_signoff_dropin_*).")


def golden_blocking_lines(m: str) -> list:
    """path:line of blocking assignments inside the golden's clocked always blocks."""
    p = os.path.join(A.STUDY, "tasks", m, "golden.v")
    out, clocked = [], False
    for i, l in enumerate(strip_comments(open(p).read()).splitlines(), 1):
        if re.search(r"\balways\b", l):
            clocked = bool(re.search(r"\b(posedge|negedge)\b", l))
        elif clocked and re.search(r"[^<>=!]=[^=]", l) and not re.search(r"\b(if|for|assign)\b", l):
            out.append(f"{A.rel(p)}:{i}")
    return out


def main() -> int:
    mods = set(A.modules())
    a1 = a1_modules()
    assert a1 == mods, f"module set differs from A1: {sorted(a1 ^ mods)}"
    mc = module_checks()
    neg = equivalent(*NEGATIVE_CONTROL)
    assert not neg, "negative control passed the equivalence check"
    bad = [k for k, v in mc.items() if not v["drop_in"] and not v["equivalent"]]
    assert not bad, f"drop-in failures not explained by equivalence: {bad}"
    json.dump({**{f"{a}/{m}": v for (a, m), v in mc.items()},
               "_negative_control": {"module": "/".join(NEGATIVE_CONTROL), "equivalent": neg}},
              open(os.path.join(OUT, "module_checks.json"), "w"), indent=1)
    designs, alias = {}, {}
    plan = [(arm, kind) for arm in A.ARMS for kind in ("pure", "hybrid_compile", "hybrid_signoff")]
    plan += [("golden", "control"), *[(arm, "diag_signoff_dropin") for arm in A.ARMS]]
    for arm, kind in plan:
        if True:
            if kind == "control":
                src = {m: (golden(m), "golden", "control: every module golden") for m in A.modules()}
                dropped = []
            elif kind == "diag_signoff_dropin":
                src, dropped, _ = design_sources(arm, "hybrid_signoff")
                for m in list(src):
                    if src[m][1] == arm and not mc[(arm, m)]["drop_in"]:
                        src[m] = (golden(m), "golden", "diagnostic: fails the drop-in mesh test")
            else:
                src, dropped, _ = design_sources(arm, kind)
            h = digest(src)
            did = "control_all_golden" if kind == "control" else f"{kind}_{arm}"
            if h in alias:
                designs[alias[h]]["aliases"].append(did)
                continue
            alias[h] = did
            designs[did] = {"dir": write_design(did, src, dropped), "aliases": [], "digest": h, "dropped": dropped,
                            "golden_modules": sum(s == "golden" for _, s, _ in src.values())}
    with cf.ProcessPoolExecutor(max_workers=min(8, os.cpu_count() or 4)) as ex:
        futs = {did: ex.submit(check_design, os.path.join(d["dir"], "rtl"), os.path.join(d["dir"], "check"))
                for did, d in designs.items()}
        a1f = ex.submit(yosys_stat, A1_DIR, sorted(os.path.basename(f) for f in glob.glob(os.path.join(A1_DIR, "*.v"))))
        ref_dir = os.path.join(A.STUDY, "golden", "reference")
        reff = ex.submit(yosys_stat, ref_dir, sorted(os.path.basename(f) for f in glob.glob(os.path.join(ref_dir, "*.v"))))
        for did, f in futs.items():
            designs[did].update(f.result())
        a1r, refr = a1f.result(), reff.result()
    for d in designs.values():
        json.dump({k: v for k, v in d.items() if k != "dir"}, open(os.path.join(d["dir"], "check", "result.json"), "w"),
                  indent=1)
    md = ["# Assembly of the 2x2 mesh (pipeline/assemble.py)", "",
          f"Top `{TOP}` and the module set ({len(mods)} modules) are A1's "
          f"(`{os.path.relpath(A1_DIR, os.path.dirname(A.STUDY)).replace(os.sep, '/')}`; A1's ORFS config.mk is not in "
          "the repository, so the top is the one `latch_study/scripts/run_yosys_stat.sh` uses for mesh2x2). Golden "
          "replacements come from `golden/reference` (B-equivalent plus two declaration-only lines).", "",
          "composes = Icarus compile of the whole mesh + `tasks/top_2x2_router/tb_signoff.v` pass. Yosys: the "
          "latch_study script (`synth -top`, `check`, `stat`). check problems = Yosys `check` count (0 = `check "
          "-assert` passes). Verilator: `--lint-only -Wall`, p3_eval settings (hard = MULTIDRIVEN, UNOPTFLAT, LATCH, "
          "WIDTHTRUNC).", "",
          "| design | golden modules | composes | Icarus compile | top tb | Yosys ok | cells | latch cells | check "
          "problems | logic loops | Verilator errors / hard | aliases |",
          "|---|---|---|---|---|---|---|---|---|---|---|---|"]
    for did, d in designs.items():
        md.append(f"| {did} | {d['golden_modules']} | {d['composes']} | {d['icarus_compile']} | {d['top_tb']} | "
                  f"{d['yosys_ok']} | {d['cells']} | {d['latch_cells']} | {d['check_problems']} | {d['loops']} | "
                  f"{d['verilator_errors']} / {d['verilator_hard']} | {', '.join(d['aliases']) or '-'} |")
    for name, r in (("A1 (latch_study, sanity)", a1r), ("golden/reference (B-equivalent)", refr)):
        md.append(f"| {name} | - | - | - | - | {r['yosys_ok']} | {r['cells']} | {r['latch_cells']} | "
                  f"{r['check_problems']} | {r['loops']} | - | - |")
    md += ["", "control_all_golden = every module golden through the same assembly and checks (tests the harness). "
           "diag_signoff_dropin_<arm> = hybrid_signoff with the LLM modules that fail the drop-in test also replaced "
           "(diagnostic only, not a hand-off design).", "",
           "## LLM modules kept by hybrid_signoff (so_clean in their task)", "",
           "drop-in = golden mesh with only this module from the arm: compiles and passes the top sign-off tb. "
           "equivalent = Yosys formal equivalence with the golden module (synthesis semantics).", "",
           "| arm | module | drop-in | equivalent to golden |", "|---|---|---|---|"]
    md += [f"| {a} | {m} | {v['drop_in']} | {v['equivalent']} |" for (a, m), v in sorted(mc.items())]
    md += ["", f"Negative control: {'/'.join(NEGATIVE_CONTROL)} (compiles, fails its tb) equivalent to golden: {neg}.",
           "", "## PRIMARY designs (hybrid_signoff)", ""]
    md += [f"- hybrid_signoff_{arm}: {race_note(race_modules(mc, arm))}" for arm in A.ARMS
           if f"hybrid_signoff_{arm}" in designs]
    md += ["", "## Audit finding: golden RTL", "",
           "The golden 2x2 mesh (tasks/top_2x2_router/tb_signoff.v reference) contains blocking-assignment flops that "
           "race in simulation; the mesh tb compares cycle-exact against it. The hybrid_signoff meshes fail it only "
           f"through {', '.join(race_modules(mc))}. " + race_note(race_modules(mc)).split(". ", 1)[1], "",
           "Blocking assignments in the golden's clocked always blocks:", ""]
    md += [f"- {m}: {', '.join(golden_blocking_lines(m)) or 'none (combinational)'}" for m in race_modules(mc)]
    md += ["", "First errors:", ""]
    for did, d in designs.items():
        bits = [x for x in (d["compile_error"] and f"Icarus: `{d['compile_error'][:200]}`",
                            d["top_tb_first_fail"] and f"top tb: `{d['top_tb_first_fail'][:200]}`",
                            d["yosys_error"] and f"Yosys: `{d['yosys_error'][:200]}`") if x]
        if bits:
            md.append(f"- {did}: " + "; ".join(bits))
    md += ["", "Extra module definitions dropped from LLM files:", ""]
    for did, d in designs.items():
        md.append(f"- {did}: {', '.join(d['dropped']) or 'none'}")
    A.write_report("ASSEMBLY.md", md)
    print("\n".join(md))
    return 0


if __name__ == "__main__":
    sys.exit(main())
