#!/usr/bin/env python3
"""Build handoff_orfs/ (the ORFS PPA hand-off for the coworker) from assembled/ and zip it.

Designs (assembled/<source> -> handoff_orfs/designs/<ID>/): rtl/*.v, VERILOG_FILES.txt, config.mk.template (only
VERILOG_FILES filled; every other line comes from the coworker's A1 config.mk), SOURCES.csv, PREFLIGHT.md.
PPA_TABLE.md: A1 and B rows from latch_study/PPA_SUMMARY.md (ORFS, SKY130HD, 10 ns); Yosys latch cells and
"functionally correct" prefilled from assembled/<source>/check/result.json and assembled/module_checks.json.
Usage: python pipeline/handoff.py [zip_path]   (after pipeline/assemble.py; default zip %TEMP%/handoff_orfs_2x2.zip)
"""
from __future__ import annotations

import hashlib
import json
import os
import re
import shutil
import sys
import tempfile
import zipfile

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import analysis_common as A  # noqa: E402
import assemble as S  # noqa: E402

HO = os.path.join(A.STUDY, "handoff_orfs")
PPA_SUMMARY = os.path.join(os.path.dirname(A.STUDY), "latch_study", "PPA_SUMMARY.md")
# (ID, assembled design, required, one-line meaning)
DESIGNS = [
    ("C0_control_all_golden", "control_all_golden", True,
     "every module golden, through our assembly: setup check, must reproduce B"),
    ("P1_hybrid_signoff_oneshot", "hybrid_signoff_oneshot", True,
     "PRIMARY: one-shot LLM modules that pass their own sign-off checks, golden for the rest"),
    ("P2_hybrid_signoff_retry", "hybrid_signoff_simloop", True,
     "PRIMARY: same after the retry loops (simulation-only retry and STITCH give byte-identical designs)"),
    ("O1_hybrid_compile_oneshot", "hybrid_compile_oneshot", False,
     "optional: every one-shot module that compiles, golden for the rest; fails the mesh tb, PPA indicative only"),
    ("O2_hybrid_compile_stitch", "hybrid_compile_stitch", False,
     "optional: every STITCH module that compiles, golden for the rest; fails the mesh tb, PPA indicative only"),
]
COLS = ["area um2", "fmax MHz", "total power mW", "check_setup unconstrained endpoints", "flow errors / notes",
        "Yosys latch cells", "functionally correct"]


def ppa_ref(label: str) -> dict:
    """Row 'A1 / 2x2' or 'B / 2x2' of latch_study/PPA_SUMMARY.md (values copied there from the coworker's CSVs)."""
    for l in open(PPA_SUMMARY, encoding="utf-8"):
        c = [x.strip() for x in l.strip().strip("|").split("|")]
        if c[0] == label:
            return {"area": float(c[1]), "fmax": float(c[3]), "power_mw": round(float(c[7]) * 1000, 3)}
    raise KeyError(label)


def result(did: str) -> dict:
    return json.load(open(os.path.join(S.OUT, did, "check", "result.json")))


def checks() -> dict:
    j = json.load(open(os.path.join(S.OUT, "module_checks.json")))
    return {tuple(k.split("/")): v for k, v in j.items() if not k.startswith("_")}


def correct(did: str, r: dict, mc: dict) -> str:
    if r["composes"]:
        return "yes (passes the mesh tb)"
    if did.startswith("hybrid_signoff_"):
        rm = S.race_modules(mc, did.split("_")[-1])
        return f"no: fails the cycle-exact mesh tb only through {len(rm)} formally equivalent modules (PREFLIGHT.md)"
    return "no (fails the mesh tb)"


def config_template(hid: str, files: list) -> str:
    cp = "# copy from your A1 config.mk"
    return "\n".join([
        f"# ORFS config.mk template for {hid}.",
        "# Only VERILOG_FILES is filled in. Every other line: copy it unchanged from your A1 config.mk",
        "# (sky130hd, 10 ns clock). DESIGN_NAME stays top_2x2_router. Give DESIGN_NICKNAME a per-design value if",
        "# your runs would otherwise overwrite each other.",
        f"export PLATFORM        = {cp}",
        f"export DESIGN_NAME     = {cp} (top_2x2_router)",
        f"export DESIGN_NICKNAME = {cp}",
        "export VERILOG_FILES   = " + " \\\n                         ".join(f"$(DESIGN_DIR)/rtl/{f}" for f in files),
        f"export SDC_FILE        = {cp} (use your A1 constraint.sdc unchanged)",
        f"# every other line of your A1 config.mk: {cp[2:]}",
        ""])


def preflight(hid: str, did: str, req: bool, meaning: str, r: dict, mc: dict, n_llm: int) -> str:
    md = [f"# {hid} preflight (pipeline/handoff.py)", "", f"{meaning}. {'Required' if req else 'Optional'}.", "",
          f"Source: `assembled/{did}` (pipeline/assemble.py); identical designs: {', '.join(r['aliases']) or 'none'}.",
          f"Modules: 34 ({n_llm} LLM-generated, {r['golden_modules']} golden; see SOURCES.csv). Top: top_2x2_router.",
          "", "| check | result |", "|---|---|",
          f"| Icarus compile (whole mesh) | {r['icarus_compile']} |",
          f"| mesh tb (tasks/top_2x2_router/tb_signoff.v, cycle-exact against the golden mesh) | {r['top_tb']} |",
          f"| Yosys synth (latch_study script) | {r['yosys_ok']} |",
          f"| Yosys cells | {r['cells']} |", f"| Yosys latch cells | {r['latch_cells']} |",
          f"| Yosys check problems | {r['check_problems']} |", f"| Yosys logic loops | {r['loops']} |",
          f"| Verilator errors / hard warnings | {r['verilator_errors']} / {r['verilator_hard']} |"]
    if r.get("top_tb_first_fail"):
        md += ["", f"First mesh tb failure: `{r['top_tb_first_fail'][:200]}`"]
    if did.startswith("hybrid_signoff_"):
        md += ["", "## Note", "", S.race_note(S.race_modules(mc, did.split("_")[-1]))]
    elif not r["composes"]:
        md += ["", "## Note", "", "Functionally incorrect: fails the mesh tb. PPA is indicative only."]
    return "\n".join(md) + "\n"


def readme(refs: dict) -> str:
    b = refs["B"]
    return "\n".join([
        "# 2x2 mesh ORFS hand-off: LLM-generated modules", "",
        "These are 2x2 mesh routers (top `top_2x2_router`) in which some modules were written by an LLM "
        "(qwen2.5-coder:32b) and the rest are golden. We need their PPA, measured the same way as A1 and B.", "",
        "## How to run", "",
        "1. Use your exact A1 ORFS setup: sky130hd, 10 ns clock, the same config.mk settings and constraint.sdc.",
        "2. Per design, take `designs/<ID>/config.mk.template`: copy every line from your A1 config.mk, keep its "
        "VERILOG_FILES (the files in `designs/<ID>/VERILOG_FILES.txt`, under `designs/<ID>/rtl/`). Top stays "
        "`top_2x2_router`. SDC: use your A1 constraint.sdc unchanged.",
        "3. Run C0 first.", "",
        "## Sanity check", "",
        f"C0 is the golden design through our assembly. It must match B within flow noise (B: {b['area']:,.0f} um2, "
        f"{b['fmax']} MHz, {b['power_mw']} mW). If it does not, stop and tell us before running the rest.", "",
        "## What to fill in", "",
        "PPA_TABLE.md, one row per design. Also run `check_setup -verbose` (OpenSTA) and report the number of "
        "unconstrained endpoints.", "",
        "## What each design means", "",
        *[f"- {hid}: {meaning}." for hid, _, _, meaning in DESIGNS], "",
        "## Checklist", "",
        "- [ ] C0  - [ ] P1  - [ ] P2  - [ ] O1 (optional)  - [ ] O2 (optional)",
        "- [ ] PPA_TABLE.md filled",
        "- [ ] ORFS reports/logs dir per design zipped and sent back",
        "- [ ] A1 config.mk + constraint.sdc sent back (we store them in latch_study/orfs_A1/)", "",
        "## Return", "",
        "Send the zip (filled PPA_TABLE.md, the reports/logs per design, your A1 config.mk and constraint.sdc) back "
        "to Soumya.", ""])


def ppa_table(refs: dict, rows: list) -> str:
    md = ["# PPA table (fill in the empty cells)", "",
          "A1 and B: ORFS, SKY130HD, 10 ns clock, from latch_study/PPA_SUMMARY.md. Yosys latch cells and functionally "
          "correct are prefilled by pipeline/handoff.py (Yosys: the latch_study script, reports/ASSEMBLY.md; the B row uses "
          "golden/reference, the B-equivalent RTL; functionally correct = passes the cycle-exact mesh tb).", "",
          "| design | " + " | ".join(COLS) + " |", "|" + "---|" * (len(COLS) + 1)]
    for name, key, lat, fc in (("A1 (primary ref)", "A1", refs["A1_latch"], "reference (original RTL, with latches)"),
                               ("B (like-for-like ref)", "B", refs["B_latch"], "yes (golden)")):
        r = refs[key]
        md.append(f"| {name} | {r['area']:.0f} | {r['fmax']} | {r['power_mw']} | not measured | - | {lat} | {fc} |")
    md += [f"| {hid} |  |  |  |  |  | {lat} | {fc} |" for hid, lat, fc in rows]
    return "\n".join(md) + "\n"


def sanity_latches() -> tuple:
    """A1 and golden/reference (B-equivalent) latch cells, from the sanity rows of reports/ASSEMBLY.md."""
    t = open(os.path.join(A.STUDY, "reports", "ASSEMBLY.md"), encoding="utf-8").read()
    a1 = re.search(r"\| A1 \(latch_study, sanity\) \|(?:[^|]*\|){6}\s*(\d+)", t).group(1)
    ref = re.search(r"\| golden/reference \(B-equivalent\) \|(?:[^|]*\|){6}\s*(\d+)", t).group(1)
    return int(a1), int(ref)


def main() -> int:
    zp = sys.argv[1] if len(sys.argv) > 1 else os.path.join(tempfile.gettempdir(), "handoff_orfs_2x2.zip")
    mc = checks()
    refs = {"A1": ppa_ref("A1 / 2x2"), "B": ppa_ref("B / 2x2")}
    refs["A1_latch"], refs["B_latch"] = sanity_latches()
    if os.path.isdir(HO):
        shutil.rmtree(HO)
    rows = []
    for hid, did, req, meaning in DESIGNS:
        r = result(did)
        assert r["yosys_ok"], f"{did} does not synthesise"
        d = os.path.join(HO, "designs", hid)
        shutil.copytree(os.path.join(S.OUT, did, "rtl"), os.path.join(d, "rtl"))
        files = sorted(os.listdir(os.path.join(d, "rtl")))
        open(os.path.join(d, "VERILOG_FILES.txt"), "w", newline="\n").write("\n".join(f"rtl/{f}" for f in files) + "\n")
        open(os.path.join(d, "config.mk.template"), "w", newline="\n").write(config_template(hid, files))
        shutil.copy(os.path.join(S.OUT, did, "SOURCES.csv"), os.path.join(d, "SOURCES.csv"))
        n_llm = sum(1 for l in open(os.path.join(d, "SOURCES.csv")).read().splitlines()[1:] if l.split(",")[1] != "golden")
        open(os.path.join(d, "PREFLIGHT.md"), "w", newline="\n").write(preflight(hid, did, req, meaning, r, mc, n_llm))
        rows.append((hid, r["latch_cells"], correct(did, r, mc)))
    assert "hybrid_signoff_stitch" in result("hybrid_signoff_simloop")["aliases"], "P2 alias changed"
    open(os.path.join(HO, "README.md"), "w", newline="\n").write(readme(refs))
    open(os.path.join(HO, "PPA_TABLE.md"), "w", newline="\n").write(ppa_table(refs, rows))
    with zipfile.ZipFile(zp, "w", zipfile.ZIP_DEFLATED) as z:
        for root, _, fs in sorted(os.walk(HO)):
            for f in sorted(fs):
                p = os.path.join(root, f)
                z.write(p, os.path.relpath(p, os.path.dirname(HO)))
    print(f"wrote {A.rel(HO)}; zip {zp} sha256 {hashlib.sha256(open(zp, 'rb').read()).hexdigest()}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
