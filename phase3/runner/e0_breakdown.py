#!/usr/bin/env python3
"""
e0_breakdown.py -- tables for the E0 retro-audit (reads the JSONL written by audit_existing_runs.py; no tools, no LLM).

A "structurally dirty pass" is a run recorded as PASS (testbench passed) whose final RTL fails at least one structural
check: Yosys did not synthesise it, or it has a Yosys latch / logic loop, or Verilator reports LATCH, UNOPTFLAT,
MULTIDRIVEN or WIDTHTRUNC (the same definition as p3_eval.struct_clean). Causes overlap, so a run can count under
several of them; "any" counts each run once.

Usage:  python phase3/runner/e0_breakdown.py phase3/results/e0_audit_phase2_all4conditions.jsonl
"""
import collections
import json
import math
import sys

CONDS = ["baseline", "sem_adv", "sem_escalate", "sem_escalate_restart"]
CAUSES = [("latch", "latch (Yosys or Verilator)"), ("yosys_fail", "Yosys did not synthesise"),
          ("loop", "loop (Yosys or Verilator UNOPTFLAT)"), ("multidriven", "MULTIDRIVEN"),
          ("widthtrunc", "WIDTHTRUNC")]


def causes(r):
    c = set(r["verilator_codes"])
    out = set()
    if r["latch_events"] or "LATCH" in c:
        out.add("latch")
    if not r["yosys_ok"]:
        out.add("yosys_fail")
    if r["loops"] or "UNOPTFLAT" in c:
        out.add("loop")
    if "MULTIDRIVEN" in c:
        out.add("multidriven")
    if "WIDTHTRUNC" in c:
        out.add("widthtrunc")
    return out


def wilson(k, n, z=1.96):
    if n == 0:
        return "n/a"
    p = k / n
    d = 1 + z * z / n
    centre = (p + z * z / (2 * n)) / d
    half = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
    return f"{100 * k / n:.1f}% ({100 * (centre - half):.1f}-{100 * (centre + half):.1f})"


def set_of(r):
    return "Set 1 (4B-8B)" if "set1_run" in r["metrics"].replace("\\", "/") else "Set 3 (14B-32B)"


def table(header, rows):
    return "\n".join(["| " + " | ".join(header) + " |", "|" + "---|" * len(header)] +
                     ["| " + " | ".join(str(x) for x in r) + " |" for r in rows])


def build(rows):
    for r in rows:                                           # the cause union must equal the script's own dirty flag
        assert bool(causes(r)) == r["structurally_dirty"], r["metrics"]
    t = {}
    agg = lambda sel: (len(sel), sum(r["structurally_dirty"] for r in sel))
    t["per_condition"] = table(
        ["condition", "passes audited", "structurally dirty", "rate (Wilson 95% CI)"],
        [[c, *agg([r for r in rows if r["condition"] == c])[:1], agg([r for r in rows if r["condition"] == c])[1],
          wilson(agg([r for r in rows if r["condition"] == c])[1], agg([r for r in rows if r["condition"] == c])[0])]
         for c in CONDS] +
        [["all four", len(rows), sum(r["structurally_dirty"] for r in rows),
          wilson(sum(r["structurally_dirty"] for r in rows), len(rows))]])
    body = []
    for s in ("Set 1 (4B-8B)", "Set 3 (14B-32B)"):
        for c in CONDS:
            sel = [r for r in rows if set_of(r) == s and r["condition"] == c]
            n, k = agg(sel)
            body.append([s, c, n, k, wilson(k, n)])
    t["per_set_condition"] = table(["set", "condition", "passes", "dirty", "rate (Wilson 95% CI)"], body)
    body = []
    for key, label in CAUSES:
        row = [label]
        for c in CONDS:
            row.append(sum(1 for r in rows if r["condition"] == c and key in causes(r)))
        row.append(sum(1 for r in rows if key in causes(r)))
        body.append(row)
    body.append(["any (each run once)"] + [sum(r["structurally_dirty"] for r in rows if r["condition"] == c) for c in CONDS]
                + [sum(r["structurally_dirty"] for r in rows)])
    t["cause_by_condition"] = table(["cause (runs can have several)"] + CONDS + ["all four"], body)
    models = sorted({(set_of(r), r["model"]) for r in rows})
    body = []
    for s, m in models:
        sel = [r for r in rows if set_of(r) == s and r["model"] == m]
        n, k = agg(sel)
        body.append([s, m, n, k, wilson(k, n)] + [sum(1 for r in sel if key in causes(r)) for key, _ in CAUSES])
    t["by_model"] = table(["set", "model", "passes", "dirty", "rate (Wilson 95% CI)"] + [k for k, _ in CAUSES], body)
    fails = collections.Counter((r["yosys_error"] or "(error line prefixed by file:line, see note)")[:90]
                                for r in rows if not r["yosys_ok"])
    t["yosys_errors"] = table(["Yosys error text as captured by p3_eval", "runs"], fails.most_common())
    mods = collections.Counter(r["module"] for r in rows if r["structurally_dirty"])
    body = []
    for m, k in mods.most_common():
        sel = [r for r in rows if r["module"] == m]
        cs = collections.Counter(x for r in sel for x in causes(r))
        body.append([m, len(sel), k, ", ".join(f"{a} {b}" for a, b in sorted(cs.items())),
                     ", ".join(sorted({r["model"] for r in sel if r["structurally_dirty"]}))])
    t["by_module"] = table(["module", "passes audited", "dirty", "causes (runs)", "models with a dirty pass"], body)
    t["n_modules_dirty"] = len(mods)
    t["feedback_rounds"] = feedback_table(rows)
    return t


def feedback_table(rows):
    """Dirty vs clean passes split by whether the pass came on the first draft (no feedback round happened, so no
    condition could act on the defect). Reads iterations_to_pass from each run's own metrics.json / run_log.json;
    run from the repo root so the recorded relative paths resolve."""
    def it_of(r):
        m = json.load(open(r["metrics"].replace("\\", "/")))
        return (m["summary"] if isinstance(m.get("summary"), dict) else m)["iterations_to_pass"]
    body = []
    for c in CONDS + ["all four"]:
        sel = [r for r in rows if c == "all four" or r["condition"] == c]
        cell = []
        for dirty in (True, False):
            grp = [r for r in sel if r["structurally_dirty"] == dirty]
            first = sum(1 for r in grp if it_of(r) == 1)
            cell += [len(grp), first, len(grp) - first]
        body.append([c] + cell)
    return table(["condition", "dirty passes", "of which first-draft", "of which after feedback",
                  "clean passes", "of which first-draft", "of which after feedback"], body)


if __name__ == "__main__":
    data = [json.loads(line) for line in open(sys.argv[1])]
    for name, text in build(data).items():
        print(f"\n## {name}\n{text}" if isinstance(text, str) else f"\n{name}: {text}")
