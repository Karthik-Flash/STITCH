#!/usr/bin/env python3
"""Which modules of a study reuse the 2x2 results. Writes reports/REUSE.md and reports/reuse.json.

Specs: a module that also exists in 2x2 starts from the 2x2 spec (specs/<m>.md copied once, never overwritten;
spec_ports fills the generated blocks from this study's modules.csv). A module is REUSED when
  (a) its golden (golden/reference/<file>) equals the 2x2 golden (tasks/<m>/golden.v) after whitespace normalisation,
      or the two goldens are proven equivalent by Yosys (assemble.equiv_texts with clocks=True: clk2fflogic,
      children flattened from the 2x2 reference; negative control: the 2x2 one-shot encoder against its golden must fail), and
  (b) the prompt the study would send (oneshot_gen.prompt_for) is byte-identical to the 2x2 prompt (prompts/<m>.txt).
Otherwise NEW. Raw and normalised sha256 of both goldens, the equivalence result and both prompt hashes are recorded.
Wrappers (studies.WRAPPERS) are not modules of the study: never generated, never prompted.
Usage: python3 pipeline/reuse.py --study mesh3x3|ni   (needs yosys; after inventory.py and build_reference.py)
"""
from __future__ import annotations

import hashlib
import json
import os
import re
import shutil
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import analysis_common as A  # noqa: E402
import assemble as S  # noqa: E402
import make_tasks as MT  # noqa: E402
import oneshot_gen as OG  # noqa: E402
import spec_ports  # noqa: E402

ROOT = A.studies.ROOT                      # the 2x2 study


def h(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def norm(b: bytes) -> bytes:
    return " ".join(b.decode("utf-8").split()).encode()


def two_by_two_rows() -> dict:
    import csv
    with open(os.path.join(ROOT, "modules.csv"), encoding="utf-8", newline="") as f:
        return {r["module"]: r for r in csv.DictReader(f)}


def mutate(text: str) -> str:
    """One operator changed: the first `&&` becomes `||`, else the first 1'b1 / 1'b 1 becomes 1'b0."""
    out = text.replace("&&", "||", 1) if "&&" in text else re.sub(r"1'b ?1", "1'b0", text, count=1)
    assert out != text
    return out


def lib_2x2(m: str, rows2: dict) -> str:
    out, todo = [], [c.rsplit("x", 1)[0] for c in rows2[m]["children"].split(";") if c]
    while todo:
        c = todo.pop()
        if c not in out:
            out.append(c)
            todo += [x.rsplit("x", 1)[0] for x in rows2[c]["children"].split(";") if x]
    return "\n".join(open(os.path.join(ROOT, "tasks", c, "golden.v")).read() for c in sorted(out))


def main() -> int:
    rows, rows2 = MT.load_rows(), two_by_two_rows()
    os.makedirs(os.path.join(A.STUDY, "specs"), exist_ok=True)
    for m in rows:
        dst = os.path.join(A.STUDY, "specs", f"{m}.md")
        if m in rows2 and not os.path.exists(dst):
            shutil.copyfile(os.path.join(ROOT, "specs", f"{m}.md"), dst)
    spec_ports.main()
    g2 = os.path.join(ROOT, "tasks", "encoder", "golden.v")
    neg = S.equiv_texts(open(g2).read(), S.module_defs(open(os.path.join(ROOT, "outputs", "oneshot", "encoder.v")).read())
                        ["encoder"], "encoder", clocks=True)
    assert not neg, "negative control passed the equivalence check"
    out = {}
    for m in sorted(rows, key=lambda x: int(rows[x]["bottom_up_order"])):
        own = open(os.path.join(A.STUDY, "golden", "reference", rows[m]["file"]), "rb").read()
        spec = os.path.join(A.STUDY, "specs", f"{m}.md")
        p_study = h(OG.prompt_for(m, rows).encode()) if os.path.exists(spec) else None
        r = {"raw_study": h(own), "norm_study": h(norm(own)), "prompt_study": p_study}
        if m in rows2:
            gold = open(os.path.join(ROOT, "tasks", m, "golden.v"), "rb").read()
            r.update(raw_2x2=h(gold), norm_2x2=h(norm(gold)),
                     prompt_2x2=h(open(os.path.join(ROOT, "prompts", f"{m}.txt"), "rb").read().replace(b"\r\n", b"\n")))
            r["same_norm"] = r["norm_2x2"] == r["norm_study"]
            r["equivalent"] = None if r["same_norm"] else S.equiv_texts(
                S.module_defs(gold.decode())[m], S.module_defs(own.decode())[m], m, lib_2x2(m, rows2), clocks=True)
            if r["equivalent"]:   # mutant control: the study golden with one operator changed must be rejected
                mut = mutate(S.module_defs(own.decode())[m])
                r["mutant_rejected"] = not S.equiv_texts(S.module_defs(gold.decode())[m], mut, m, lib_2x2(m, rows2),
                                                         clocks=True)
                assert r["mutant_rejected"], f"{m}: equivalence check accepts a mutant"
            r["same_prompt"] = r["prompt_2x2"] == p_study
            golden_ok = r["same_norm"] or r["equivalent"]
            r["status"] = "REUSED" if golden_ok and r["same_prompt"] else "NEW"
            r["why"] = ("whitespace-identical golden" if r["same_norm"] else
                        "Yosys-equivalent golden" if r["equivalent"] else "golden differs (not equivalent)")
            r["why"] += ", mutant rejected" if r.get("mutant_rejected") else ""
            r["why"] += ", identical prompt" if r["same_prompt"] else ", prompt differs"
        else:
            r.update(status="NEW", why="no 2x2 module of this name")
        r["points_to"] = f"2x2 results of {m} (outputs/<arm>/{m}.v, runs/)" if r["status"] == "REUSED" else None
        out[m] = r
    json.dump(out, open(os.path.join(A.STUDY, "reports", "reuse.json"), "w"), indent=1)
    md = [f"# Reuse of 2x2 results ({A.studies.NAME}; pipeline/reuse.py)", "",
          "REUSED = golden equal to 2x2 after whitespace normalisation, or Yosys-equivalent, AND byte-identical "
          f"prompt. Equivalence negative control (2x2 one-shot encoder vs golden) equivalent: {neg}. Wrappers "
          f"(not golden, never prompted): {', '.join(A.studies.WRAPPERS.get(A.studies.NAME, [])) or 'none'}.", "",
          f"REUSED {sum(r['status'] == 'REUSED' for r in out.values())}, NEW {sum(r['status'] == 'NEW' for r in out.values())}: "
          + ", ".join(m for m, r in out.items() if r["status"] == "NEW"), "",
          "| module | status | why | golden sha256 raw (2x2 / study) | normalised (2x2 / study) | equivalent | "
          "prompt sha256 (2x2 / study) |", "|---|---|---|---|---|---|---|"]
    s = lambda x: x[:12] if x else "-"  # noqa: E731
    for m, r in out.items():
        md.append(f"| {m} | {r['status']} | {r['why']} | {s(r.get('raw_2x2'))} / {s(r['raw_study'])} | "
                  f"{s(r.get('norm_2x2'))} / {s(r['norm_study'])} | "
                  f"{'-' if r.get('equivalent') is None else r['equivalent']} | "
                  f"{s(r.get('prompt_2x2'))} / {s(r['prompt_study'])} |")
    md += ["", "Full hashes: reports/reuse.json."]
    A.write_report("REUSE.md", md)
    print("\n".join(md))
    return 0


if __name__ == "__main__":
    sys.exit(main())
