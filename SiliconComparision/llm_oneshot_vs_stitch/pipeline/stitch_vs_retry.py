#!/usr/bin/env python3
"""STITCH (sem_esc_restart_v3) vs the simulation-only retry loop (baseline), per module. Writes
reports/STITCH_VS_RETRY.md.

Per module: one-shot / simloop final / stitch final flags (C compile, F tb.v, S tb_signoff.v, K struct_clean), calls,
sf, the interpreter directive codes fed back per iteration (metrics.json per_iter feedback_classes), and an outcome:
already_clean (one-shot so_clean), both_fixed, stitch_only, retry_only, neither.
Prompt equivalence: for runs where STITCH never fired (sf=0), are the stitch prompts byte-identical to the simloop
prompts, iteration by iteration?
Gains (a flag stitch has and simloop lacks) and regressions (the reverse): the stitch iteration where the flag was
gained or lost and the feedback that preceded it. Failed sf=1 modules: their class from reports/FAILURE_AUDIT.md.
Usage: python pipeline/stitch_vs_retry.py   (after reeval.py and audit.py)
"""
from __future__ import annotations

import collections
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import analysis_common as A  # noqa: E402
import reeval  # noqa: E402

FLAG = {"C": "compile_ok", "K": "struct_clean"}


def fl(e: dict) -> dict:
    return {"C": e["compile_ok"], "F": e["func_pass"], "S": e["signoff"], "K": e["struct_clean"]}


def fs(f: dict) -> str:
    return "".join(k if f[k] else "." for k in "CFSK")


def audit_classes() -> dict:
    out = {}
    for l in open(os.path.join(A.STUDY, "reports", "FAILURE_AUDIT.md"), encoding="utf-8"):
        c = [x.strip() for x in l.split("|")]
        if len(c) > 5 and c[2] in A.ARMS and c[4] in ("LLM_BUG", "SPEC_AMBIGUITY", "TB_ARTIFACT", "GOLDEN_DEFECT"):
            out[(c[1], c[2])] = c[4]
    return out


def feedback_before(met: dict, k: int) -> str:
    """What the stitch prompt of iteration k carried: directives fed after iteration k-1, escalation, restart."""
    prev = met["per_iter"][k - 1]
    bits = []
    if prev.get("feedback_classes"):
        bits.append("directives " + ", ".join(prev["feedback_classes"]))
    if met.get("escalated_at") is not None and k - 1 >= met["escalated_at"]:
        bits.append("escalated (tool text)" if not prev.get("feedback_semantic_fired") else "escalated")
    if prev.get("restart"):
        bits.append("restart from the one-shot file")
    return "; ".join(bits) or "simulation feedback only"


def prompts_identical(m: str) -> tuple[bool, str]:
    a, b = A.iter_dirs("simloop", m)[1:], A.iter_dirs("stitch", m)[1:]
    for i, (da, db) in enumerate(zip(a, b), 1):
        if open(os.path.join(da, "prompt.txt"), "rb").read() != open(os.path.join(db, "prompt.txt"), "rb").read():
            return False, f"first differing prompt: iteration {i}"
    if len(a) != len(b):
        return False, f"identical while both ran; calls differ ({len(a)} vs {len(b)})"
    return True, f"{len(a)} prompt(s) byte-identical"


def divergence(m: str, mt: dict) -> tuple[int | None, str]:
    """First iteration where the two arms' RTL differs, and why: different prompt (the stitch feedback) or the same
    prompt sampled differently (T=0.1, no seed)."""
    a, b = A.iter_dirs("simloop", m), A.iter_dirs("stitch", m)
    for i in range(1, min(len(a), len(b))):
        if open(os.path.join(a[i], "dut.v"), "rb").read() != open(os.path.join(b[i], "dut.v"), "rb").read():
            same = open(os.path.join(a[i], "prompt.txt"), "rb").read() == open(os.path.join(b[i], "prompt.txt"),
                                                                              "rb").read()
            return i, ("identical prompt, different sample (not attributable to STITCH)" if same else
                       f"different prompt; stitch carried: {feedback_before(mt, i)}")
    return None, f"RTL identical while both ran; simloop stopped after {len(a) - 1} call(s), stitch made {len(b) - 1}"


def first_iter_sampling() -> tuple[int, list]:
    n, diff = 0, []
    for m in A.modules():
        a, b = A.iter_dirs("simloop", m), A.iter_dirs("stitch", m)
        if len(a) > 1 and len(b) > 1 and open(os.path.join(a[1], "prompt.txt"), "rb").read() == open(
                os.path.join(b[1], "prompt.txt"), "rb").read():
            n += 1
            if open(os.path.join(a[1], "dut.v"), "rb").read() != open(os.path.join(b[1], "dut.v"), "rb").read():
                diff.append(m)
    return n, diff


def main() -> int:
    ac = audit_classes()
    rows, outcome, gains, regress, failed_sf, equiv = [], collections.defaultdict(list), [], [], [], []
    sampling = set()
    for m in A.modules():
        o, s, t = (reeval.load(a, m) for a in A.ARMS)
        fo, fsim, fst = fl(o), fl(s), fl(t)
        ms, mt = A.metrics("simloop", m), A.metrics("stitch", m)
        if o["so_clean"]:
            oc = "already_clean"
        elif s["so_clean"] and t["so_clean"]:
            oc = "both_fixed"
        elif t["so_clean"]:
            oc = "stitch_only"
        elif s["so_clean"]:
            oc = "retry_only"
        else:
            oc = "neither"
        outcome[oc].append(m)
        codes = " / ".join(f"{it['iter']}:{','.join(it['feedback_classes'])}" for it in mt["per_iter"]
                           if it.get("feedback_classes")) or "-"
        rows.append(f"| {m} | {fs(fo)} | {fs(fsim)} it={ms['llm_calls']} | {fs(fst)} it={mt['llm_calls']} "
                    f"sf={int(mt['semantic_fired'])} | {codes} | {oc} |")
        if not mt["semantic_fired"] and mt["llm_calls"] and ms["llm_calls"]:
            same, why = prompts_identical(m)
            equiv.append((m, same, why))
        for k in "CK":
            if fst[k] != fsim[k]:
                seq = {arm: "".join(k if x[FLAG[k]] else "." for x in met["per_iter"])
                       for arm, met in (("simloop", ms), ("stitch", mt))}
                dv, cause = divergence(m, mt)
                line = (f"{m}: {'compile' if k == 'C' else 'struct_clean (K)'} per iteration (0 = one-shot): simloop "
                        f"`{seq['simloop']}`, stitch `{seq['stitch']}`; arms first produce different RTL at iteration "
                        f"{dv}: {cause}")
                (gains if fst[k] else regress).append(line)
                if dv is not None and "identical prompt" in cause:
                    sampling.add(m)
        if mt["semantic_fired"] and not t["so_clean"]:
            failed_sf.append((m, ac.get((m, "stitch"), "?")))
    did_not = [m for m, _ in failed_sf]
    helped = sorted({g.split(":")[0] for g in gains} | set(outcome["stitch_only"]))
    hurt = sorted({r.split(":")[0] for r in regress} | set(outcome["retry_only"]))
    dom = collections.Counter(c for _, c in failed_sf)
    md = ["# STITCH vs simulation-only retry (pipeline/stitch_vs_retry.py)", "",
          "Flags: C compile, F tb.v, S tb_signoff.v, K struct_clean (local re-evaluation of the final files). "
          "it = LLM calls, sf = STITCH semantic feedback fired. Directive codes: `iteration:codes` fed back after that "
          "iteration (stitch arm).", "",
          "## Outcome classes", "", "| class | count | modules |", "|---|---|---|"]
    md += [f"| {c} | {len(outcome[c])} | {', '.join(outcome[c]) or '-'} |"
           for c in ("already_clean", "both_fixed", "stitch_only", "retry_only", "neither")]
    n_same = sum(1 for _, s_, _ in equiv if s_)
    md += ["", "## Prompt equivalence (stitch runs with sf=0 and at least one call in both arms)", "",
           f"{n_same} of {len(equiv)} such modules got byte-identical prompts in both arms: "
           f"{', '.join(m for m, s_, _ in equiv if s_) or '-'}. These modules cannot distinguish the arms.", ""]
    md += [f"- {m}: {why}" for m, s_, why in equiv if not s_]
    n1, d1 = first_iter_sampling()
    md += ["", "## Sampling", "",
           f"The first LLM call of the two arms gets the same prompt (feedback-first protocol). In {n1} modules both "
           f"arms made that call with a byte-identical prompt; in {len(d1)} of them the two answers differ "
           f"({', '.join(d1)}). Generation used temperature 0.1 with no seed, so a difference between the arms can "
           "come from sampling alone. Below, each gain or regression names the first iteration where the arms' RTL "
           "differs and whether the prompts differed there."]
    md += ["", "## Gains (stitch has the flag, simloop does not)", ""] + [f"- {g}" for g in gains]
    md += ["", "## Regressions (simloop has the flag, stitch does not)", ""] + [f"- {r}" for r in regress]
    md += ["", f"## STITCH fired (sf=1) and the final still fails: {len(failed_sf)} modules", "",
           "Audit class (reports/FAILURE_AUDIT.md): " + ", ".join(f"{c} {n}" for c, n in dom.most_common()), "",
           ", ".join(f"{m} ({c})" for m, c in failed_sf), "",
           "## Where STITCH helped", "",
           f"Final flag better than the simulation-only loop: {', '.join(helped) or 'none'}. Of these, the arms "
           f"diverged after a different (STITCH) prompt in: {', '.join(h for h in helped if h not in sampling) or 'none'}; "
           f"after an identical prompt (sampling) in: {', '.join(h for h in helped if h in sampling) or 'none'}. "
           f"No module reached so_clean under STITCH only ({len(outcome['stitch_only'])}).",
           "", "## Where it did not", "",
           f"STITCH fired but the final still fails ({len(did_not)}): {', '.join(did_not)}. "
           f"Never fired and failed in both arms: {', '.join(m for m in outcome['neither'] if m not in did_not) or '-'}.",
           "", "## Where it hurt", "",
           f"Final flag worse than the simulation-only loop: {', '.join(hurt) or 'none'}. Arms diverged after a "
           f"different (STITCH) prompt in: {', '.join(h for h in hurt if h not in sampling) or 'none'}; after an "
           f"identical prompt (sampling) in: {', '.join(h for h in hurt if h in sampling) or 'none'}.",
           "", "## Per module", "", "| module | one-shot | simloop final | stitch final | stitch directive codes per "
           "iteration | outcome |", "|---|---|---|---|---|---|", *rows]
    A.write_report("STITCH_VS_RETRY.md", md)
    print("\n".join(md[:60]))
    return 0


if __name__ == "__main__":
    sys.exit(main())
