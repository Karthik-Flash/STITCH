#!/usr/bin/env python3
"""Tool pass over a study's hand-written RTL. Writes reports/HANDWRITTEN.md.

Per root of the study (studies.ROOTS): the latch_study Yosys script (read; hierarchy -check -top; synth; check;
stat) on golden/handwritten (does it abort?) and on golden/A1 (the synthesisable copy: cells, latch cells, check
problems, logic loops); Verilator --lint-only -Wall on golden/handwritten (p3_eval settings; hard = MULTIDRIVEN,
UNOPTFLAT, LATCH, WIDTHTRUNC); the Yosys front-end warnings about implicitly declared nets and resized cell ports.
Per module (modules.csv, from pipeline/inventory.py): sequential style and clocking. A module's clocking is
"system clock" when every storage clock / latch enable it has, directly or through a child, comes from an input
port named like a system clock (make_tasks.SYSCLK), "data-clocked" when one comes from another input port, and
"gated" when one comes from an internal net (runs/inventory/a1_proc.json).
Usage: python3 pipeline/handwritten_check.py --study mesh3x3|ni   (needs yosys and verilator; after inventory.py)
"""
from __future__ import annotations

import csv
import glob
import json
import os
import re
import sys
import tempfile
from collections import Counter

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import analysis_common as A  # noqa: E402
import assemble as S  # noqa: E402
import make_tasks as MT  # noqa: E402
import p3_bridge as B  # noqa: E402

HW = os.path.join(A.STUDY, "golden", "handwritten")
A1 = os.path.join(A.STUDY, "golden", "A1")
CLOCK_PINS = ("CLK", "WR_CLK", "RD_CLK", "EN")


def files(d: str) -> list[str]:
    return sorted(os.path.basename(f) for f in glob.glob(os.path.join(d, "*.v")))


def frontend_warnings(root: str) -> tuple[list[str], list[str]]:
    _, log = S.run(["yosys", "-p", f"read_verilog {' '.join(files(HW))}; hierarchy -check -top {root}"], HW)
    implicit = sorted(set(re.findall(r"^(\S+?):\d+: Warning: Identifier `\\(\S+)' is implicitly declared", log, re.M)))
    resized = sorted(set(re.findall(r"^Warning: Resizing cell port (\S+) from (\d+) bits to (\d+) bits", log, re.M)))
    return [f"{f}: {n}" for f, n in implicit], [f"{c} {a}->{b}" for c, a, b in resized]


def clocking(rows: dict) -> dict:
    """module -> (class, evidence)."""
    proc = json.load(open(os.path.join(A.STUDY, "runs", "inventory", "a1_proc.json")))["modules"]
    out = {}
    for m in sorted(rows, key=lambda x: int(rows[x]["bottom_up_order"])):
        mod = proc[m]
        port_of = {b: p for p, v in mod["ports"].items() for b in v["bits"]}
        drivers = []
        for cell in mod["cells"].values():
            t, pins = cell["type"], cell["connections"]
            if t.startswith("$"):
                if "latch" in t or "dff" in t or t.startswith("$mem"):
                    drivers += [b for pin in CLOCK_PINS if pin in pins for b in pins[pin]
                                if not (pin == "EN" and "latch" not in t)]
            elif t in rows:
                child = set(filter(None, rows[t]["clock_ports"].split(";") + rows[t]["latch_enable_ports"].split(";")))
                drivers += [b for pin in child if pin in pins for b in pins[pin]]
        cls, ev = "none (combinational)" if not drivers else "system clock", set()
        for b in drivers:
            p = port_of.get(b)
            if p is None and not isinstance(b, str):
                cls, ev = "gated", ev | {"internal net"}
            elif p is not None and p not in MT.SYSCLK:
                cls = "data-clocked" if cls != "gated" else cls
                ev.add(p)
            elif p is not None:
                ev.add(p)
        children = [c for c in rows[m]["child_list"] if out.get(c, ("",))[0] in ("gated", "data-clocked")]
        if children and cls == "system clock":
            ev.add("child " + ", ".join(children))
        out[m] = (cls, ", ".join(sorted(ev)) or "-")
    return out


def main() -> int:
    rows = MT.load_rows()
    md = [f"# Hand-written RTL tool pass ({A.studies.NAME}; pipeline/handwritten_check.py)", "",
          f"golden/handwritten = the hand-written RTL as received (sanitised copy); golden/A1 = its synthesisable copy "
          f"(latch_study A1: only Yosys-aborting modules fixed).", "", "## Per root", "",
          "| root | handwritten: Yosys | A1: Yosys cells | A1 latch cells | A1 check problems | A1 logic loops | "
          "Verilator errors / hard (handwritten) | hard codes |", "|---|---|---|---|---|---|---|---|"]
    notes = []
    for root in A.studies.ROOTS[A.studies.NAME]:
        hw = S.yosys_stat(HW, files(HW), root)
        hw.pop("_log")
        a1 = S.yosys_stat(A1, files(A1), root)
        a1.pop("_log")
        with tempfile.TemporaryDirectory() as w:
            v = B._ORIG["lint"]([os.path.join(HW, f) for f in files(HW)], root, w, 600)
        hard = {c: n for c, n in v["codes"].items() if c in ("MULTIDRIVEN", "UNOPTFLAT", "LATCH", "WIDTHTRUNC")}
        md.append(f"| {root} | {'ok' if hw['yosys_ok'] else 'aborts: `' + (hw['yosys_error'] or '?')[:90] + '`'} | "
                  f"{a1['cells']} | {a1['latch_cells']} | {a1['check_problems']} | {a1['loops']} | "
                  f"{len(v['errors'])} / {v['n_hard']} | {', '.join(f'{c} {n}' for c, n in sorted(hard.items())) or '-'} |")
        imp, res = frontend_warnings(root)
        notes += [f"- {root}: {len(imp)} implicitly declared nets" + (f": {'; '.join(imp)}" if imp else ""),
                  f"- {root}: {len(res)} cell ports resized" + (f": {'; '.join(res)}" if res else "")]
    md += ["", "## Yosys front-end warnings (handwritten)", "", *notes]
    clk = clocking(rows)
    md += ["", "## Per module", "", "Latch cells per module: modules.csv own_storage (`$dlatch`), golden/A1 after proc.", "",
           "| module | file | children | kind | own storage | clock ports | reset ports | latch-enable ports | "
           "clocking | clock sources |", "|---|---|---|---|---|---|---|---|---|---|"]
    for m in sorted(rows, key=lambda x: int(rows[x]["bottom_up_order"])):
        r = rows[m]
        md.append(f"| {m} | {r['file']} | {r['children'].replace(';', ', ') or '-'} | {r['kind']} | "
                  f"{r['own_storage'].replace(';', ', ') or '-'} | {r['clock_ports'] or '-'} | {r['reset_ports'] or '-'} | "
                  f"{r['latch_enable_ports'] or '-'} | {clk[m][0]} | {clk[m][1]} |")
    A.write_report("HANDWRITTEN.md", md)
    print("\n".join(md))
    return 0


if __name__ == "__main__":
    sys.exit(main())
