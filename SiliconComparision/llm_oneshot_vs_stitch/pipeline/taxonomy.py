#!/usr/bin/env python3
"""Failure taxonomy. Writes reports/TAXONOMY.md.

Labels (a) every one-shot file, (b) each arm's final file (logs of pipeline/reeval.py: runs/analysis/<arm>/<m>/),
(c) every iteration of every arm run (the runner's own logs: runs/arms/results/.../iter<k>/). The primary label of a
file is its first failure, in evaluation order: truncation (done_reason=length or no endmodule) -> compile error
(first iverilog error line) -> tb.v -> tb_signoff.v (finals only) -> structural (Yosys, then Verilator hard warning).
"all labels" lists every category found in the file's logs by the MAP table. Every label cites path:line.
Usage: python pipeline/taxonomy.py   (after pipeline/reeval.py)
"""
from __future__ import annotations

import collections
import json
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import analysis_common as A  # noqa: E402
import reeval  # noqa: E402

CATEGORIES = ("syntax", "ports", "function", "latch", "multi-driven", "width", "timing", "duplicate child definition",
              "truncation")
# (source, regex, category). Order matters: the first matching row labels a line.
MAP = [
    ("iverilog", r"Module \S+ was already declared|module \S+ already declared", "duplicate child definition"),
    ("iverilog", r"syntax error|Invalid module item|invalid port declaration separator|Invalid port connection", "syntax"),
    ("iverilog", r"not a valid l-value for a procedural assignment", "syntax"),
    ("iverilog", r"Unable to bind wire/reg/memory", "syntax"),
    ("iverilog", r"has already been declared|is not a port of|already bound|Output port expression must support|"
                 r"not valid in assign l-value|Failed to elaborate input port", "ports"),
    ("iverilog", r"out of range", "width"),
    ("iverilog", r"also continuously assigned|cannot be driven by a continuous assignment", "multi-driven"),
    ("tb", r"FAIL property", "function | timing (timing-dependent module)"),
    ("tb", r"^FAIL t=", "function | timing (timing-dependent module)"),
    ("yosys", r"Re-definition of module|Duplicate module", "duplicate child definition"),
    ("yosys", r"Multiple edge sensitive events", "timing"),
    ("yosys", r"does not have a port named|not found in module", "ports"),
    ("yosys", r"Latch inferred for signal", "latch"),
    ("yosys", r"found logic loop", "latch"),
    ("yosys", r"multiple conflicting drivers", "multi-driven"),
    ("verilator", r"%Warning-(WIDTHTRUNC|WIDTHEXPAND|SELRANGE)", "width"),
    ("verilator", r"%Warning-(MULTIDRIVEN|MULTIDRIVENPROC)|%Error-PORTSHORT", "multi-driven"),
    ("verilator", r"%Warning-(LATCH|UNOPTFLAT)", "latch"),
    ("verilator", r"%Error-PROCASSWIRE|%Error-ASSIGNIN", "syntax"),
    ("verilator", r"%Error-PINNOTFOUND|%Warning-PINMISSING", "ports"),
    ("directive", r"PINMISSING|UNUSEDSIGNAL|UNDRIVEN", "ports"),
    ("directive", r"WIDTHTRUNC|WIDTHEXPAND", "width"),
    ("directive", r"COMB_LOOP|LATCH", "latch"),
    ("directive", r"MULTIDRIVEN", "multi-driven"),
    ("directive", r"MISSING_CLOCK|ASYNC_RESET", "timing"),
]
NOT_COUNTED = "Verilator UNUSEDSIGNAL, PINCONNECTEMPTY, UNDRIVEN, IMPLICIT (style warnings; the golden has them too)"
LOGS = (("sim.log", "iverilog"), ("sim.log", "tb"), ("signoff.log", "tb"), ("yosys.log", "yosys"),
        ("verilator.log", "verilator"))


def cat_of(source: str, line: str, m: str) -> str | None:
    for src, pat, cat in MAP:
        if src == source and re.search(pat, line):
            return ("timing" if m in A.TIMING else "function") if cat.startswith("function") else cat
    return None


def scan(d: str, m: str, files=LOGS) -> list[tuple[str, str, str]]:
    """(category, path:line, line) for every mapped line, in log order."""
    out = []
    for f, src in files:
        p = os.path.join(d, f)
        if not os.path.exists(p):
            continue
        for i, l in enumerate(open(p, errors="replace").read().splitlines(), 1):
            if src == "iverilog" and "error" not in l.lower():
                continue
            c = cat_of(src, l, m)
            if c:
                out.append((c, f"{A.rel(p)}:{i}", l.strip()))
    return out


def truncated(meta: dict, text: str) -> bool:
    return meta.get("done_reason") == "length" or "endmodule" not in text


def label(d: str, m: str, ev: dict, meta: dict, text: str, final: bool) -> tuple[str, str, list]:
    hits = scan(d, m, LOGS if final else LOGS[:2] + LOGS[3:])
    if truncated(meta, text):
        return "truncation", "done_reason=" + str(meta.get("done_reason")), hits
    if not ev["compile_ok"]:
        h = next((x for x in hits if x[1].split(":")[0].endswith("sim.log") and "error" in x[2].lower()), None)
        return (h[0], f"{h[1]} `{h[2][:120]}`", hits) if h else ("syntax", "unmapped compile error", hits)
    for f in ("sim.log", "signoff.log") if final else ("sim.log",):
        ok = ev["func_pass"] if f == "sim.log" else ev.get("signoff", True)
        if not ok:
            h = next((x for x in hits if x[1].split(":")[0].endswith(f) and x[2].startswith("FAIL")), None)
            if h:
                return h[0], f"{h[1]} `{h[2][:120]}`", hits
    if not ev["struct_clean"]:
        h = next((x for x in hits if x[1].split(":")[0].endswith(("yosys.log", "verilator.log"))), None)
        if h:
            return h[0], f"{h[1]} `{h[2][:120]}`", hits
        return "latch", "struct_clean False, no mapped line", hits
    return "ok", "-", hits


def all_labels(hits: list) -> str:
    seen = {}
    for c, loc, _ in hits:
        seen.setdefault(c, loc)
    return ", ".join(f"{c} ({loc})" for c, loc in seen.items()) or "-"


def main() -> int:
    final_rows, prim = [], collections.Counter()
    for arm in A.ARMS:
        for m in A.modules():
            d = os.path.join(A.STUDY, "runs", "analysis", arm, m)
            ev = reeval.load(arm, m)
            if arm == "oneshot":
                meta = json.load(open(os.path.join(A.STUDY, "runs", "oneshot", m, "record.json"))).get("llm_meta", {})
            else:
                its = A.iter_dirs(arm, m)
                mp = os.path.join(its[-1], "llm_meta.json") if len(its) > 1 else None
                meta = json.load(open(mp)) if mp and os.path.exists(mp) else {}
            lab, cite, hits = label(d, m, ev, meta, open(A.final_file(arm, m)).read(), True)
            prim[(arm, lab)] += 1
            final_rows.append(f"| {m} | {arm} | {lab} | {cite} | {all_labels(hits)} |")
    seq_rows, seq_detail, changes = [], [], collections.Counter()
    for arm in ("simloop", "stitch"):
        for m in A.modules():
            met = A.metrics(arm, m)
            labs = []
            for it, d in zip(met["per_iter"], A.iter_dirs(arm, m)):
                mp = os.path.join(d, "llm_meta.json")
                meta = json.load(open(mp)) if os.path.exists(mp) else {}
                ev = {"compile_ok": it["compile_ok"], "func_pass": it["func_pass"], "struct_clean": it["struct_clean"]}
                lab, cite, _ = label(d, m, ev, meta, open(os.path.join(d, "dut.v")).read(), False)
                fb = it.get("feedback_classes", [])
                fbc = sorted({c for x in fb for s, p, c in MAP if s == "directive" and re.search(p, x)})
                labs.append(lab + (f" [STITCH: {', '.join(fbc)}]" if fbc else "") + (" [restart]" if it.get("restart")
                                                                                       else ""))
                seq_detail.append(f"| {m} | {arm} | {it['iter']} | {lab} | {cite} | {', '.join(fb) or '-'} |")
            first, last = labs[0].split(" [")[0], labs[-1].split(" [")[0]
            changes[(arm, "same" if first == last else f"{first} -> {last}")] += 1
            seq_rows.append(f"| {m} | {arm} | {' -> '.join(labs)} |")
    md = ["# Failure taxonomy (pipeline/taxonomy.py)", "",
          f"Categories: {', '.join(CATEGORIES)}. For a timing-dependent module ({', '.join(A.TIMING)}) a failing tb "
          "line is labelled timing, otherwise function. Logic loops (Yosys `found logic loop`, Verilator UNOPTFLAT, "
          "directive COMB_LOOP) are labelled latch (combinational feedback storage). Not counted: " + NOT_COUNTED + ".",
          "", "## Mapping table", "", "| source | message / code (regex) | category |", "|---|---|---|"]
    md += [f"| {s} | `{p.replace('|', ' or ')}` | {c} |" for s, p, c in MAP]
    md += ["", "## Primary label counts (final files)", "", "| label | " + " | ".join(A.ARMS) + " |", "|---|---|---|---|"]
    for lab in CATEGORIES + ("ok",):
        if any(prim[(a, lab)] for a in A.ARMS):
            md.append(f"| {lab} | " + " | ".join(str(prim[(a, lab)]) for a in A.ARMS) + " |")
    md += ["", "## What retrying changed: primary label of iteration 0 (one-shot input) -> final iteration", "",
           "| change | simloop | stitch |", "|---|---|---|"]
    keys = sorted({k for _, k in changes})
    md += [f"| {k} | {changes[('simloop', k)]} | {changes[('stitch', k)]} |" for k in keys]
    md += ["", "## (a, b) Final files", "", "| module | arm | primary label | cited line | all labels (first line each) |",
           "|---|---|---|---|---|", *final_rows,
           "", "## (c) Per-iteration sequence (iteration 0 = the one-shot file; [STITCH: ...] = categories of the "
           "directives fed back after that iteration)", "", "| module | arm | sequence |", "|---|---|---|", *seq_rows,
           "", "### Per-iteration citations", "", "| module | arm | iter | label | cited line | directive codes fed back |",
           "|---|---|---|---|---|---|", *seq_detail]
    A.write_report("TAXONOMY.md", md)
    for lab in CATEGORIES + ("ok",):
        if any(prim[(a, lab)] for a in A.ARMS):
            print(lab, {a: prim[(a, lab)] for a in A.ARMS})
    print(dict(changes))
    return 0


if __name__ == "__main__":
    sys.exit(main())
