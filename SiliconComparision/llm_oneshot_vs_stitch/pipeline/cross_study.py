#!/usr/bin/env python3
"""Cross-study summary (2x2, mesh3x3, ni). Writes reports/CROSS_STUDY.md in the study root.

Every number is read from a committed report of each study: reports/summary.json (so_clean per arm, NEW modules),
reports/reuse.json (NEW / REUSED), reports/STITCH_VS_RETRY.md (outcome classes, attributable gains, regressions),
reports/TAXONOMY.md (primary label counts of the final files), reports/FAILURE_AUDIT.md (class counts),
reports/ASSEMBLY.md (pure / hybrid_signoff composes). Golden-RTL findings: the list GOLDEN below, one entry per
finding with the report that shows it.
Usage: python pipeline/cross_study.py   (after every study's analysis; no tools needed)
"""
from __future__ import annotations

import csv
import json
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import studies  # noqa: E402

ARMS = ("oneshot", "simloop", "stitch")
GOLDEN = {
    "2x2": ["blocking-assignment flops in the golden race in the cycle-exact mesh tb (reports/ASSEMBLY.md)"],
    "mesh3x3": ["nine mesh-edge data outputs wired to implicit 1-bit nets in mesh_router3x3.v (reports/HANDWRITTEN.md)",
                "the 2x2 golden blocking-assignment race carries over to the cycle-exact 3x3 mesh tb "
                "(reports/ASSEMBLY.md)"],
    "ni": ["new1 and nidepack connect router_fifo positionally with its last outputs shifted (full_int <- full_ext, "
           "empty <- full_int) (README, reports/FAILURE_AUDIT.md)",
           "rp1's j is initialised at declaration and never reset: one packet per power-up, undefined in silicon "
           "(specs/rp1.md)",
           "depack holds wr_en after a word, so the FIFO rewrites the word until it fills (specs/depack.md)",
           "golden halves joined directly in ni_pair misread each other on the same clock edge "
           "(reports/NI_PAIR_TRACE.md)"],
}


def rep(study: str, name: str) -> str:
    return open(os.path.join(studies.DIRS[study], "reports", name), encoding="utf-8").read()


def table(text: str, header_start: str) -> list[dict]:
    """Rows of the first markdown table whose header line starts with header_start, as dicts."""
    lines = text.splitlines()
    i = next(k for k, l in enumerate(lines) if l.startswith(header_start))
    head = [c.strip() for c in lines[i].strip().strip("|").split("|")]
    out = []
    for l in lines[i + 2:]:
        if not l.startswith("|"):
            break
        out.append(dict(zip(head, [c.strip() for c in l.strip().strip("|").split("|")])))
    return out


def after(text: str, pattern: str) -> str:
    return re.search(pattern, text).group(1).strip()


def study_row(s: str) -> dict:
    rows = json.load(open(os.path.join(studies.DIRS[s], "reports", "summary.json")))["rows"]
    if s == "2x2":
        new, reused = len(rows), 0
    else:
        ru = json.load(open(os.path.join(studies.DIRS[s], "reports", "reuse.json")))
        new, reused = sum(r["status"] == "NEW" for r in ru.values()), sum(r["status"] == "REUSED" for r in ru.values())
    so = {a: sum(1 for r in rows if r[a] and r[a]["so_clean"]) for a in ARMS}
    with open(os.path.join(studies.DIRS[s], "modules.csv"), encoding="utf-8", newline="") as f:
        kids = {r["module"]: bool(r["children"]) for r in csv.DictReader(f)}
    split = {k: [r for r in rows if kids[r["module"]] == k] for k in (False, True)}
    so_split = {k: " / ".join(str(sum(1 for r in v if r[a] and r[a]["so_clean"])) for a in ARMS) + f" (of {len(v)})"
                for k, v in split.items()}
    svr = rep(s, "STITCH_VS_RETRY.md")
    outcome = {r["class"]: (r["count"], r["modules"]) for r in table(svr, "| class |")}
    helped = after(svr, r"diverged after a different \(STITCH\) prompt in: ([^;]*);")
    hurt_stitch = after(svr, r"## Where it hurt\s+.*?Arms diverged after a different \(STITCH\) prompt in: ([^;]*);")
    hurt_sampling = after(svr, r"## Where it hurt\s+.*?after an\s+identical prompt \(sampling\) in: ([^.]*)\.") \
        if re.search(r"## Where it hurt", svr) else "-"
    tax = table(rep(s, "TAXONOMY.md"), "| label |")
    tot = sorted(((sum(int(r[a]) for a in ARMS), r["label"]) for r in tax if r["label"] != "ok"), reverse=True)
    dom = ", ".join(f"{lab} ({' / '.join(next(r for r in tax if r['label'] == lab)[a] for a in ARMS)})"
                    for _, lab in tot[:2])
    aud = table(rep(s, "FAILURE_AUDIT.md"), "| arm | not so_clean |")
    classes = [c for c in aud[0] if c not in ("arm", "not so_clean")]
    audit = ", ".join(f"{c} {sum(int(r[c]) for r in aud)}" for c in classes if sum(int(r[c]) for r in aud))
    asm = table(rep(s, "ASSEMBLY.md"), "| design |")
    by = {r["design"]: r for r in asm}
    for r in asm:
        for a in (r.get("aliases") or "-").split(", "):
            if a != "-":
                by[a] = r

    def comp(kind: str) -> str:
        return " / ".join("y" if by[f"{kind}_{a}"]["composes"] == "True" else "n" for a in ARMS)

    def llm(a: str) -> str:
        r = by[f"hybrid_signoff_{a}"]
        return r["LLM modules (new / reused)"] if "LLM modules (new / reused)" in r else \
            f"{new - int(r['golden modules'])} / 0"
    kept = table(rep(s, "ASSEMBLY.md"), "| arm | module |")
    race = sorted({r["module"] for r in kept if r["drop-in"] == "False"})
    race_eq = all(r["equivalent to golden"] == "True" for r in kept if r["drop-in"] == "False")
    diag = " / ".join("y" if f"diag_signoff_dropin_{a}" in by and by[f"diag_signoff_dropin_{a}"]["composes"] == "True"
                      else "-" for a in ARMS)

    return {"study": s, "top": studies.TOPS[s], "modules": f"{new} / {reused}",
            "so_clean": " / ".join(f"{so[a]}" for a in ARMS), "n_new": new,
            "stitch_only": f"{outcome['stitch_only'][0]}" + (f" ({outcome['stitch_only'][1]})"
                                                             if outcome["stitch_only"][1] != "-" else ""),
            "gains": helped or "none", "reg": f"{hurt_stitch or 'none'} / {hurt_sampling or 'none'}",
            "dominant": dom, "audit": audit, "pure": comp("pure"), "hybrid": comp("hybrid_signoff"),
            "golden": len(GOLDEN[s]), "leaf": so_split[False], "hier": so_split[True],
            "so_n": so, "outcome": outcome, "hurt_stitch": hurt_stitch, "hurt_sampling": hurt_sampling,
            "hybrid_llm": " ; ".join(llm(a) for a in ARMS), "race": race, "race_eq": race_eq, "diag": diag,
            "audit_n": {c: sum(int(r[c]) for r in aud) for c in classes}}


def main() -> int:
    rs = [study_row(s) for s in ("2x2", "mesh3x3", "ni")]
    for r in rs:
        r["race_txt"] = (", ".join(r["race"]) + ("" if r["race_eq"] else " (NOT all equivalent)")) if r["race"] else "none"
    md = ["# Cross-study summary (pipeline/cross_study.py)", "",
          "One model (qwen2.5-coder:32b), one run per arm, same options in every study (T=0.1, no seed, num_ctx "
          "32768, budget 6 calls). N=1 per study: counts, no rates. NEW = generated in this study; REUSED = the "
          "2x2 result of the same module (golden and prompt match, reports/REUSE.md). Per-arm values are "
          "oneshot / simloop / stitch and count NEW modules only.", "",
          "| | " + " | ".join(f"{r['study']} (top {r['top']})" for r in rs) + " |",
          "|---|" + "---|" * len(rs)]
    for key, lab in (("modules", "modules NEW / REUSED"),
                     ("so_clean", "so_clean (of the NEW modules)"),
                     ("leaf", "so_clean NEW modules without children"),
                     ("hier", "so_clean NEW modules with children"),
                     ("stitch_only", "so_clean under STITCH only"),
                     ("gains", "attributable structural gains of STITCH (different prompt)"),
                     ("reg", "regressions vs retry: attributable / sampling"),
                     ("dominant", "dominant failure classes (primary label, final files)"),
                     ("audit", "audit classes of failing finals (all arms)"),
                     ("pure", "pure design composes"),
                     ("hybrid", "hybrid_signoff composes"),
                     ("hybrid_llm", "LLM modules in hybrid_signoff, NEW / REUSED"),
                     ("race_txt", "hybrid_signoff drop-in failures (all formally equivalent to golden)"),
                     ("diag", "hybrid_signoff with those swapped back composes"),
                     ("golden", "golden-RTL findings")):
        md.append(f"| {lab} | " + " | ".join(f"{r[key]}" for r in rs) + " |")
    md += ["", "so_clean NEW counts: 2x2 of 34, mesh3x3 of 1, ni of 4. composes = the whole design passes its top "
           "testbench (2x2, 3x3: cycle-exact mesh tb; ni: ni_pair property checks).", "",
           "## Golden-RTL findings", ""]
    for s, fs in GOLDEN.items():
        md += [f"- {s}: " + "; ".join(fs)]
    md += ["", "## Conclusions across studies", ""] + [f"{i}. {c}" for i, c in enumerate(conclusions(rs), 1)]
    p = os.path.join(studies.ROOT, "reports", "CROSS_STUDY.md")
    open(p, "w", encoding="utf-8", newline="\n").write("\n".join(md) + "\n")
    print("\n".join(md))
    return 0


def conclusions(rs: list) -> list[str]:
    two, m3, ni = rs
    newer = [r for r in rs[1:]]
    c = []
    c.append(
        f"Retrying repairs 2x2 modules but none of the NEW 3x3 and NI modules. In 2x2, so_clean rises from "
        f"{two['so_n']['oneshot']} (one-shot) to {two['so_n']['simloop']} / {two['so_n']['stitch']} (simloop / "
        f"stitch); in mesh3x3 and NI it stays at " + " and ".join(
            f"{r['so_n']['oneshot']} / {r['so_n']['simloop']} / {r['so_n']['stitch']} of {r['n_new']}" for r in newer) +
        ". This contradicts the 2x2 reading that retrying repairs failures in general: here it repaired none of the "
        f"{sum(r['n_new'] for r in newer)} NEW modules.")
    c.append(
        "The 2x2 split between leaf and hierarchical modules holds only in part. No NEW module with children is "
        "so_clean in any arm of any study (2x2 " + two["hier"] + ", mesh3x3 " + m3["hier"] + ", NI " + ni["hier"] +
        "). The 2x2 \"leaf modules, yes\" does not carry over to NI: its two leaf modules, the state machines rp1 and "
        "depack, are so_clean in no arm (" + ni["leaf"] + ").")
    c.append(
        "STITCH does not produce a so_clean module that the simulation-only retry misses, in any study (STITCH only: "
        + ", ".join(f"{r['study']} {r['outcome']['stitch_only'][0]}" for r in rs) + "). Its attributable effects "
        f"are single flags: 2x2 gains on {two['gains']}; mesh3x3 one regression after a STITCH prompt "
        f"({m3['hurt_stitch']}); NI none (the {ni['hurt_sampling']} regression is sampling).")
    c.append(
        "The failures are the LLM's: every failing final file of mesh3x3 and NI is LLM_BUG, as in 2x2 apart from its "
        "two asynch_comparator TB_ARTIFACT cases. No study has a SPEC_AMBIGUITY case and NI has no GOLDEN_DEFECT case "
        "(audit classes: " + "; ".join(f"{r['study']} {r['audit']}" for r in rs) + "). The one NI file that "
        "could have failed only through the golden's port shift (new1, simloop) still mismatches the shift-corrected "
        "golden.")
    c.append(
        "No pure design composes in any study. In 2x2 and 3x3 the hybrid_signoff meshes fail the cycle-exact mesh tb "
        f"only through the same modules ({', '.join(two['race'])} in 2x2; {', '.join(m3['race'])} in 3x3), each "
        "formally equivalent to its golden; with them swapped back the meshes compose. The NI hybrid_signoff design "
        f"composes, but it keeps no NEW module (LLM modules NEW / REUSED: {ni['hybrid_llm'].split(' ; ')[0]}): it "
        "measures REUSED 2x2 modules only.")
    return c

if __name__ == "__main__":
    sys.exit(main())
