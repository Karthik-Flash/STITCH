#!/usr/bin/env python3
"""Stage funnel per module x arm. Writes reports/FUNNEL.md.

Stages, in order: compiles (iverilog, task context) -> loop tb (tb.v) -> sign-off tb (tb_signoff.v) -> synthesises
(Yosys ok) -> latch/loop-free (Yosys: 0 latch events, 0 logic loops) -> composes (golden 2x2 mesh with only this
module from the arm compiles and passes tasks/top_2x2_router/tb_signoff.v: the drop-in test of pipeline/assemble.py).
The first failing stage is marked; later stages are not evaluated. Also: LLM calls and sf (STITCH semantic feedback
fired) from reports/summary.json, and the Yosys formal-equivalence result for modules that fail only at composes.
Usage: python pipeline/funnel.py   (after reeval.py and assemble.py)
"""
from __future__ import annotations

import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import analysis_common as A  # noqa: E402
import assemble as S  # noqa: E402
import reeval  # noqa: E402

STAGES = ("compiles", "loop tb", "sign-off tb", "synthesises", "latch/loop-free", "composes")


def stages(arm: str, m: str, mc: dict) -> tuple[list[bool], dict]:
    e = reeval.load(arm, m)
    done = [e["compile_ok"], e["func_pass"], e["signoff"], bool(e["yosys_ok"]),
            bool(e["yosys_ok"]) and e["latch_events"] == 0 and e["yosys_loops"] == 0]
    extra = {}
    if all(done):
        key = f"{arm}/{m}"
        c = mc.get(key) or {"drop_in": S.drop_in(arm, m), "equivalent": S.equivalent(arm, m)}
        done.append(c["drop_in"])
        extra = c
    return done, extra


def main() -> int:
    mcp = os.path.join(S.OUT, "module_checks.json")
    mc = json.load(open(mcp)) if os.path.exists(mcp) else {}
    rows, summ = [], A.summary_rows()
    reached = {arm: [0] * len(STAGES) for arm in A.ARMS}
    first_fail = {arm: {s: 0 for s in STAGES + ("passes all",)} for arm in A.ARMS}
    notes = []
    for m in A.modules():
        cells = []
        for arm in A.ARMS:
            done, extra = stages(arm, m, mc)
            for i, ok in enumerate(done):
                if not ok:
                    break
                reached[arm][i] += 1
            ff = next((STAGES[i] for i, ok in enumerate(done) if not ok), "passes all")
            first_fail[arm][ff] += 1
            s = summ[m][arm] or {}
            calls = f" it={s['iterations']} sf={int(s['semantic_fired'])}" if "iterations" in s else ""
            cells.append(("ok" if ff == "passes all" else f"**{ff}**") + calls)
            if ff == "composes":
                notes.append(f"{m} ({arm}): passes every module stage but fails in the mesh; Yosys formal "
                             f"equivalence with golden: {extra.get('equivalent')}")
        rows.append(f"| {m} | " + " | ".join(cells) + " |")
    md = ["# Stage funnel (pipeline/funnel.py)", "",
          "Per module and arm: the first failing stage (bold), or ok. Stages: " + " -> ".join(STAGES) + ". "
          "composes = golden 2x2 mesh with only this module from the arm passes the top-level sign-off tb (drop-in). "
          "it = LLM calls, sf = STITCH semantic feedback fired.", "",
          "## Totals: modules reaching each stage (counts of 34)", "",
          "| stage | " + " | ".join(A.ARMS) + " |", "|---|---|---|---|"]
    md += [f"| {st} | " + " | ".join(str(reached[a][i]) for a in A.ARMS) + " |" for i, st in enumerate(STAGES)]
    md += ["", "## Totals: first failing stage", "", "| first failing stage | " + " | ".join(A.ARMS) + " |",
           "|---|---|---|---|"]
    md += [f"| {st} | " + " | ".join(str(first_fail[a][st]) for a in A.ARMS) + " |" for st in STAGES + ("passes all",)]
    md += ["", "Bonus whole-router row: not attempted: prompt alone 32,290 of 32,768 tokens (budget.py).", "",
           "## Modules that fail only at composes", ""] + [f"- {n}" for n in notes]
    md += ["", "## Per module", "", "| module | " + " | ".join(A.ARMS) + " |", "|---|---|---|---|", *rows]
    A.write_report("FUNNEL.md", md)
    print("\n".join(md[:30 + len(notes)]))
    return 0


if __name__ == "__main__":
    sys.exit(main())
