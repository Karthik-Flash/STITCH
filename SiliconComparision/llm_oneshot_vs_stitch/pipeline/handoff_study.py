#!/usr/bin/env python3
"""Build <study>/handoff_orfs/ (the ORFS PPA hand-off for the coworker) for mesh3x3 or ni, from assembled/, and zip it.
(The 2x2 hand-off is pipeline/handoff.py; same layout and README style.)

Designs (assembled/<source> -> handoff_orfs/designs/<ID>/): rtl/*.v, VERILOG_FILES.txt, config.mk.template, SOURCES.csv,
PREFLIGHT.md. Required: the A1-style reference, C0 (control_all_golden) and every hybrid_signoff design that differs
from C0 (PRIMARY). A design byte-identical to another one is shipped once, under the first ID, with the alias named.
Optional: hybrid_compile designs that synthesise and differ from the required ones.
config.mk.template: DESIGN_NAME and VERILOG_FILES filled in; floorplan: the Yosys cell-count ratio against the 2x2
control (reports/ASSEMBLY.md of both studies) for scaling a fixed DIE_AREA/CORE_AREA; everything else from A1.
SDC: mesh3x3 uses A1's constraint.sdc unchanged when the top's clock ports equal top_2x2_router's (modules.csv,
checked here); ni ships constraint.sdc with one 10 ns clock per ni_pair clock port and set_clock_groups -asynchronous.
PPA_TABLE.md: reference rows not measured (blank); mesh3x3 also lists the 2x2 A1 and B rows (latch_study/PPA_SUMMARY.md)
for context.
Usage: python pipeline/handoff_study.py --study mesh3x3|ni [zip]   (after assemble_study.py; default zip
%TEMP%/handoff_orfs_3x3.zip or handoff_orfs_ni.zip)
"""
from __future__ import annotations

import csv
import hashlib
import json
import math
import os
import re
import shutil
import sys
import tempfile
import zipfile

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import analysis_common as A  # noqa: E402
import handoff as H  # noqa: E402

assert A.NAME != "2x2", "2x2 uses pipeline/handoff.py"
H.PPA_SUMMARY = os.path.join(os.path.dirname(A.ROOT), "latch_study", "PPA_SUMMARY.md")
TOP = A.studies.TOP
WRAP = A.studies.WRAPPERS.get(A.NAME, [])
OUT = os.path.join(A.STUDY, "assembled")
HO = os.path.join(A.STUDY, "handoff_orfs")
TAG = {"mesh3x3": "3x3", "ni": "ni"}[A.NAME]
A1_ID = f"A1_style_{TAG}"
TB = os.path.join("wrapper" if TOP in WRAP else "tasks", TOP, "tb_signoff.v").replace(os.sep, "/")
COLS = H.COLS


def result(did: str) -> dict:
    return json.load(open(os.path.join(OUT, did, "check", "result.json")))


def checks() -> dict:
    j = json.load(open(os.path.join(OUT, "module_checks.json")))
    return {tuple(k.split("/")): v for k, v in j.items() if not k.startswith("_")}


def designs() -> tuple[list, list]:
    """(ID, assembled design, required, meaning) to ship, and notes on designs not shipped."""
    have = {d: result(d) for d in os.listdir(OUT) if os.path.isfile(os.path.join(OUT, d, "check", "result.json"))}
    alias_of = {a: d for d, r in have.items() for a in r["aliases"]}
    out, notes = [], []
    if A1_ID in have:
        out.append((A1_ID, A1_ID, False, "optional: the hand-written RTL with only the Yosys-aborting modules fixed; "
                                         "already measured as A1 / 3x3 (latch_study/PPA_SUMMARY.md, PPA_TABLE.md)"))
    c0 = "every module golden, through our assembly: like-for-like reference (B-style RTL)"
    if alias_of.get(A1_ID) == "control_all_golden":
        c0 += f"; byte-identical to {A1_ID} (the hand-written NI RTL synthesises without latches, nothing to fix), " \
              "so it is also the A1-style reference"
    out.append(("C0_control_all_golden", "control_all_golden", True, c0))
    n = 0
    for arm in A.ARMS:
        did = f"hybrid_signoff_{arm}"
        if did in have:
            n += 1
            al = have[did]["aliases"]
            out.append((f"P{n}_{did}", did, True, f"PRIMARY: {arm} LLM modules that pass their own sign-off checks "
                        "(REUSED modules: the 2x2 result of the same arm), golden for the rest" +
                        (f"; byte-identical to {', '.join(al)}" if al else "")))
        elif alias_of.get(did) == "control_all_golden":
            notes.append(f"{did}: byte-identical to control_all_golden: no LLM-generated module to measure")
    k = 0
    for arm in A.ARMS:
        did = f"hybrid_compile_{arm}"
        if did in have and have[did]["yosys_ok"]:
            k += 1
            al = have[did]["aliases"]
            out.append((f"O{k}_{did}", did, False, f"optional: every {arm} module that compiles, golden for the rest" +
                        ("" if have[did]["composes"] else "; fails the top tb, PPA indicative only") +
                        (f"; byte-identical to {', '.join(al)}" if al else "")))
        elif did in have:
            notes.append(f"{did}: does not synthesise (Yosys: `{have[did]['yosys_error']}`)")
    if A.NAME == "ni":   # no NEW NI module signed off: nothing here measures LLM output, so nothing is required
        out = [(h, d, False, m) for h, d, _, m in out]
    return out, notes


def ppa_summary(labels: tuple) -> tuple[list, list]:
    """Header and the rows `labels` of the measurement table in latch_study/PPA_SUMMARY.md, as cell lists."""
    cells_of = lambda l: [c.strip() for c in l.strip().strip("|").split("|")]  # noqa: E731
    lines = open(H.PPA_SUMMARY, encoding="utf-8").read().splitlines()
    head = cells_of(next(l for l in lines if l.startswith("| Variant / design")))
    return head, [cells_of(l) for lab in labels for l in lines if l.startswith(f"| {lab} |")]


def correct(did: str, r: dict, mc: dict) -> str:
    if not r["icarus_compile"]:
        return "not simulated: the design does not compile in Icarus (PREFLIGHT.md)"
    if r["composes"]:
        return "yes (passes the top tb)"
    if did.startswith("hybrid_signoff_"):
        arm = did.split("_")[-1]
        eq = [m for (a, m), v in mc.items() if a == arm and not v["drop_in"]]
        if eq and all(mc[(arm, m)]["equivalent"] for m in eq):
            return f"no: fails the top tb only through {len(eq)} formally equivalent modules (PREFLIGHT.md)"
    return "no (fails the top tb)"


def clock_ports(rows_csv: str, top: str) -> list:
    with open(rows_csv, encoding="utf-8", newline="") as f:
        return sorted(next(r for r in csv.DictReader(f) if r["module"] == top)["clock_ports"].split(";"))


def wrapper_clocks() -> list:
    text = open(os.path.join(A.STUDY, "wrapper", f"{TOP}.v")).read()
    return sorted(re.findall(r"^\s*input\s+(\w*clk\w*)\s*,?\s*$", text, re.M))


def io_bits() -> int:
    """I/O pins of the wrapper top (sum of port widths in wrapper/<top>.v)."""
    text = open(os.path.join(A.STUDY, "wrapper", f"{TOP}.v")).read()
    return sum(int(a) - int(b) + 1 if a else 1 for a, b in
               re.findall(r"^\s*(?:input|output)\s+(?:\[(\d+):(\d+)\]\s*)?\w+\s*,?\s*$", text, re.M))


def cells(study_dir: str, did: str = "control_all_golden") -> int:
    lines = open(os.path.join(study_dir, "reports", "ASSEMBLY.md"), encoding="utf-8").read().splitlines()
    row = lambda l: [c.strip() for c in l.strip().strip("|").split("|")]  # noqa: E731
    head = row(next(l for l in lines if l.startswith("| design |")))
    return int(row(next(l for l in lines if l.startswith(f"| {did} |")))[head.index("cells")])


def sdc_note() -> tuple[str, str | None]:
    """(README text, constraint.sdc text or None)."""
    if A.NAME == "mesh3x3":
        a, b = clock_ports(os.path.join(A.ROOT, "modules.csv"), "top_2x2_router"), \
            clock_ports(os.path.join(A.STUDY, "modules.csv"), TOP)
        assert a == b, f"clock ports differ: top_2x2_router {a}, {TOP} {b}"
        return (f"use your A1 constraint.sdc unchanged: `{TOP}` has the same clock port as `top_2x2_router` "
                f"(`{', '.join(b)}`; modules.csv, checked by pipeline/handoff_study.py)."), None
    clk = wrapper_clocks()
    assert len(clk) == 2, clk
    sdc = "\n".join([
        f"# {TOP}: constraint.sdc for the NI hand-off (pipeline/handoff_study.py).",
        f"# The only change versus A1's constraint.sdc: {TOP} has two clock ports ({', '.join(clk)}) that clock the two",
        "# sides of asynchronous FIFOs, so each gets A1's 10 ns clock and the two clocks are declared asynchronous.",
        *[f"create_clock -name {c} -period 10 [get_ports {c}]" for c in clk],
        "set_clock_groups -asynchronous " + " ".join(f"-group [get_clocks {c}]" for c in clk), ""])
    return (f"use `constraint.sdc` from this folder. It is the only SDC change versus A1: one 10 ns clock on each "
            f"clock port of `{TOP}` (`{'`, `'.join(clk)}`, read from wrapper/{TOP}.v by the script) and "
            "`set_clock_groups -asynchronous` between them (the FIFOs between the two clocks are asynchronous). If "
            "your A1 constraint.sdc has further lines (I/O delays, ...), keep them and point them at these clocks."), sdc


def config_template(hid: str, files: list, ratio: float) -> str:
    cp = "# copy from your A1 config.mk"
    sdc = "$(DESIGN_DIR)/../../constraint.sdc  # shipped in handoff_orfs/" if A.NAME == "ni" else \
        f"{cp} (use your A1 constraint.sdc unchanged)"
    return "\n".join([
        f"# ORFS config.mk template for {hid}.",
        f"# DESIGN_NAME and VERILOG_FILES are filled in. Every other line: copy it unchanged from your A1 config.mk",
        "# (sky130hd, 10 ns clock), including CORE_UTILIZATION and the flow settings. Give DESIGN_NICKNAME a",
        "# per-design value if your runs would otherwise overwrite each other.",
        f"# Floorplan: if your A1 config.mk fixes DIE_AREA / CORE_AREA, scale each side by sqrt({ratio:.3g}) = "
        f"{math.sqrt(ratio):.3g} (Yosys cell count of this study's C0 over the 2x2 C0) and use the same values for "
        "every design of this hand-off (README, flow notes).",
        f"export PLATFORM        = {cp}",
        f"export DESIGN_NAME     = {TOP}",
        f"export DESIGN_NICKNAME = {cp}",
        "export VERILOG_FILES   = " + " \\\n                         ".join(f"$(DESIGN_DIR)/rtl/{f}" for f in files),
        f"export SDC_FILE        = {sdc}",
        f"# every other line of your A1 config.mk: {cp[2:]}",
        ""])


def preflight(hid: str, did: str, req: bool, meaning: str, r: dict, mc: dict, src: list) -> str:
    n_llm = sum(1 for s in src if s not in ("golden", "wrapper", "A1"))
    md = [f"# {hid} preflight (pipeline/handoff_study.py)", "", f"{meaning}. {'Required' if req else 'Optional'}.", "",
          f"Source: `assembled/{did}` (pipeline/assemble_study.py); identical designs: {', '.join(r['aliases']) or 'none'}.",
          f"Modules: {len(src)} ({n_llm} LLM-generated, {sum(s == 'golden' for s in src)} golden, "
          f"{sum(s == 'A1' for s in src)} hand-written A1, {sum(s == 'wrapper' for s in src)} wrapper; see SOURCES.csv). "
          f"Top: {TOP}.", "", "| check | result |", "|---|---|",
          f"| Icarus compile (whole design) | {r['icarus_compile']} |",
          f"| top tb ({TB}{', cycle-exact against the golden design' if TOP not in WRAP else ', property checks'}) "
          f"| {r['top_tb']} |",
          f"| Yosys synth (latch_study script) | {r['yosys_ok']} |",
          f"| Yosys cells | {r['cells']} |", f"| Yosys latch cells | {r['latch_cells']} |",
          f"| Yosys check problems | {r['check_problems']} |", f"| Yosys logic loops | {r['loops']} |",
          f"| Verilator errors / hard warnings | {r['verilator_errors']} / {r['verilator_hard']} |"]
    if r.get("top_tb_first_fail"):
        md += ["", f"First top tb failure: `{r['top_tb_first_fail'][:200]}`"]
    if did.startswith("hybrid_signoff_"):
        arm = did.split("_")[-1]
        rows = [(m, v) for (a, m), v in sorted(mc.items()) if a == arm]
        md += ["", "## LLM modules in this design (pipeline/assemble_study.py)", "",
               "| module | new / reused | drop-in | equivalent to golden (clocks=True) |", "|---|---|---|---|"]
        md += [f"| {m} | {v['where']} | {v['drop_in']} | {v['equivalent']} |" for m, v in rows]
    if not r["composes"]:
        md += ["", "## Note", "", "Fails the top tb. PPA is indicative only unless the failure is explained above."]
    return "\n".join(md) + "\n"


def ppa_table(rows: list) -> str:
    md = ["# PPA table (fill in the empty cells)", "",
          f"{TAG} hand-off. " + ("A1 / 3x3 and B / 3x3: ORFS, SKY130HD, 10 ns clock, from latch_study/PPA_SUMMARY.md "
                                 "(already measured). " if A.NAME == "mesh3x3" else "") +
          "Yosys latch cells and functionally correct are prefilled by pipeline/handoff_study.py (Yosys: the "
          f"latch_study script, reports/ASSEMBLY.md; functionally correct = passes {TB}).", "",
          "| design | " + " | ".join(COLS) + " |", "|" + "---|" * (len(COLS) + 1)]
    if A.NAME == "mesh3x3":
        a1 = next(lat for hid, lat, _ in rows if hid == A1_ID)
        b = result("control_all_golden")["latch_cells"]
        for lab, lat, fc in (("A1 / 3x3", a1, "reference (original RTL, with latches)"),
                             ("B / 3x3", b, "yes (golden)")):
            r = H.ppa_ref(lab)
            md.append(f"| {lab} (reference) | {r['area']:.0f} | {r['fmax']} | {r['power_mw']} | not measured | - | "
                      f"{lat} | {fc} |")
    md += [f"| {hid} |  |  |  |  |  | {lat} | {fc} |" for hid, lat, fc in rows]
    if A.NAME == "mesh3x3":
        head, refs = ppa_summary(("A1 / 3x3", "B / 3x3"))
        md += ["", "Every value latch_study/PPA_SUMMARY.md has for the 3x3 references (copied by the script):", "",
               "| " + " | ".join(head) + " |", "|" + "---|" * len(head)]
        md += ["| " + " | ".join(r) + " |" for r in refs]
        md += ["", "For context only, 2x2 mesh (not this design): ORFS, SKY130HD, 10 ns, latch_study/PPA_SUMMARY.md.", "",
               "| design (2x2 mesh) | area um2 | fmax MHz | total power mW |", "|---|---|---|---|"]
        for lab in ("A1 / 2x2", "B / 2x2"):
            r = H.ppa_ref(lab)
            md.append(f"| {lab} | {r['area']:.0f} | {r['fmax']} | {r['power_mw']} |")
    return "\n".join(md) + "\n"


def readme(ds: list, notes: list, ratio: float, sdc_text: str) -> str:
    what = {"mesh3x3": f"3x3 mesh routers (top `{TOP}`)",
            "ni": f"network-interface pairs (top `{TOP}`: the packetiser new1 driving the depacketiser nidepack "
                  "directly, a wrapper we wrote; every design includes it)"}[A.NAME]
    req = [h for h, _, r, _ in ds if r]
    opt = [h for h, _, r, _ in ds if not r]
    b = H.ppa_ref("B / 3x3") if A.NAME == "mesh3x3" else None
    if req:
        order = f"4. Run in this order: {', '.join(req)}" + (f"; then, optional: {', '.join(opt)}." if opt else ".")
    else:
        order = f"4. Nothing is required. Optional, in this order: {', '.join(opt)}."
    return "\n".join([
        f"# {TAG} ORFS hand-off: LLM-generated modules", "",
        *(["Optional. No newly generated NI module signed off, so no design here measures LLM output; P1 differs from "
           "C0 only by two reused 2x2 leaves.", ""] if A.NAME == "ni" else []),
        f"These are {what} in which some modules were written by an LLM (qwen2.5-coder:32b) and the rest are golden, "
        "plus the reference designs. " + ("If you run them, measure them" if A.NAME == "ni" else "We need their PPA, "
                                           "measured") + " the same way as A1 and B in the 2x2 hand-off.", "",
        "## How to run", "",
        "1. Use your exact A1 ORFS setup: sky130hd, 10 ns clock, the same config.mk settings (keep A1's "
        "CORE_UTILIZATION and flow settings).",
        f"2. Per design, take `designs/<ID>/config.mk.template`: DESIGN_NAME (`{TOP}`) and VERILOG_FILES (the files in "
        "`designs/<ID>/VERILOG_FILES.txt`, under `designs/<ID>/rtl/`) are filled in; copy every other line from your "
        "A1 config.mk.",
        f"3. SDC: {sdc_text}",
        order, "",
        *(["## Sanity check", "",
           f"C0 is the golden design through our assembly. It must reproduce B / 3x3 within flow noise (B: "
           f"{b['area']:,.0f} um2, {b['fmax']} MHz, {b['power_mw']} mW; latch_study/PPA_SUMMARY.md). If it does not, "
           "stop and tell us before running the rest. A1 / 3x3 is already measured, so A1_style_3x3 is optional.", ""]
          if b else []),
        "## Flow notes", "",
        f"- Size: Yosys counts {ratio:.3g}x the cells of the 2x2 mesh for this study's C0 (reports/ASSEMBLY.md of both "
        "studies). With A1's CORE_UTILIZATION the floorplan scales by itself; keep it.",
        f"- If your A1 config.mk fixes DIE_AREA / CORE_AREA instead, scale each side by sqrt({ratio:.3g}) = "
        f"{math.sqrt(ratio):.3g} and use the same DIE_AREA / CORE_AREA for every design of this hand-off. Write the "
        "values you used in PPA_TABLE.md (flow errors / notes).",
        *([f"- `{TOP}` has {io_bits()} I/O pins. If the scaled die cannot place them, use the smallest die that "
           "does, the same for every design of this hand-off, and note it."] if TOP in WRAP else []),
        "- This is the only config change versus A1 besides DESIGN_NAME and VERILOG_FILES." +
        (" The SDC change is in step 3." if A.NAME == "ni" else ""), "",
        "## What to fill in", "",
        "PPA_TABLE.md, one row per design. Also run `check_setup -verbose` (OpenSTA) and report the number of "
        "unconstrained endpoints.", "",
        "## What each design means", "",
        *[f"- {hid}: {meaning}." for hid, _, _, meaning in ds],
        *([""] + [f"- Not shipped: {n}." for n in notes] if notes else []), "",
        "## Checklist", "",
        "- " + "  ".join(f"[ ] {h.split('_')[0] if h[0] in 'CPO' else h}" + (" (optional)" if h in opt else "")
                         for h, _, _, _ in ds),
        "- [ ] PPA_TABLE.md filled",
        "- [ ] ORFS reports/logs dir per design zipped and sent back",
        "- [ ] A1 config.mk + constraint.sdc sent back if not sent with the 2x2 hand-off (we store them in "
        "latch_study/orfs_A1/)", "",
        "## Return", "",
        "Send the zip (filled PPA_TABLE.md, the reports/logs per design) back to Soumya.", ""])


def main() -> int:
    zp = sys.argv[1] if len(sys.argv) > 1 else os.path.join(tempfile.gettempdir(), f"handoff_orfs_{TAG}.zip")
    mc = checks()
    ds, notes = designs()
    ratio = cells(A.STUDY) / cells(A.ROOT)
    sdc_text, sdc = sdc_note()
    if os.path.isdir(HO):
        shutil.rmtree(HO)
    rows = []
    for hid, did, req, meaning in ds:
        r = result(did)
        assert r["yosys_ok"], f"{did} does not synthesise"
        d = os.path.join(HO, "designs", hid)
        shutil.copytree(os.path.join(OUT, did, "rtl"), os.path.join(d, "rtl"))
        files = sorted(os.listdir(os.path.join(d, "rtl")))
        open(os.path.join(d, "VERILOG_FILES.txt"), "w", newline="\n").write("\n".join(f"rtl/{f}" for f in files) + "\n")
        open(os.path.join(d, "config.mk.template"), "w", newline="\n").write(config_template(hid, files, ratio))
        shutil.copy(os.path.join(OUT, did, "SOURCES.csv"), os.path.join(d, "SOURCES.csv"))
        src = [l.split(",")[1] for l in open(os.path.join(d, "SOURCES.csv")).read().splitlines()[1:]]
        open(os.path.join(d, "PREFLIGHT.md"), "w", newline="\n").write(preflight(hid, did, req, meaning, r, mc, src))
        fc = correct(did, r, mc)
        if did == A1_ID:
            fc = f"reference (hand-written RTL, with latches); {fc}"
        rows.append((hid, r["latch_cells"], fc))
    if sdc:
        open(os.path.join(HO, "constraint.sdc"), "w", newline="\n").write(sdc)
    open(os.path.join(HO, "README.md"), "w", newline="\n").write(readme(ds, notes, ratio, sdc_text))
    open(os.path.join(HO, "PPA_TABLE.md"), "w", newline="\n").write(ppa_table(rows))
    with zipfile.ZipFile(zp, "w", zipfile.ZIP_DEFLATED) as z:
        for root, _, fs in sorted(os.walk(HO)):
            for f in sorted(fs):
                p = os.path.join(root, f)
                z.write(p, os.path.relpath(p, os.path.dirname(HO)))
    print(f"wrote {A.rel(HO)}; zip {zp} sha256 {hashlib.sha256(open(zp, 'rb').read()).hexdigest()}")
    for n in notes:
        print(n)
    return 0


if __name__ == "__main__":
    sys.exit(main())
