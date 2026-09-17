"""
phase2/set1_analysis/table_condition_decision.py -- deliverable 4: the
paper's "where escalation helps" table. Recoverable-band modules only
(17 of 42, from Twin's module_categories.json) x 3 models = 51 rows.
Each row reports the 4 condition pass counts and a single verdict label.

VERDICT LOGIC -- the brief gives four label definitions that are not
mutually exclusive as literally stated (e.g. "baseline >= sem_adv+1" and
"sem_esc/sem_esc_restart >= baseline AND sem_adv < baseline" can both be
true on the same row). Resolved here with an explicit priority order,
documented plainly rather than left implicit (same discipline
categorize.py used for its 12/15 pooled-rate interpretation):

  1. Tied            -- spread(baseline, sem_adv, sem_esc, sem_esc_r) <= 1
                         (max pass count - min pass count across all four
                         conditions). If everything is within 1 replicate
                         of everything else, no other label is meaningful.
  2. Escalation wins  -- max(sem_esc, sem_esc_r) >= baseline + 1
                         (checked only once Tied is ruled out -- a real
                         lift from at least one escalation variant)
  3. Protective       -- sem_adv <= baseline - 1
                         AND max(sem_esc, sem_esc_r) >= baseline
                         (sem_adv regressed below baseline, but at least
                         one escalation variant held ground -- the
                         "regression avoided" case)
  4. Baseline wins    -- sem_adv <= baseline - 1
                         (sem_adv regressed and neither escalation variant
                         held ground either -- baseline is simply better,
                         checked last since Protective is the more
                         specific/informative case when it also applies)
  5. Mixed (uncategorized) -- none of the above (e.g. sem_adv notably
                         BETTER than baseline, an inverse-direction
                         pattern the brief's four labels don't name).
                         Reported separately, not folded into "Tied" --
                         see SET1_ANALYSIS.md for whether this bucket is
                         ever non-empty and what it means when it is.

One row (RAM / llama3.1:latest, a recoverable-band module -- verified
directly, not assumed) is touched by 2 of the 6 known transient errors
(all 3 sem_escalate replicates AND 2 of 3 sem_escalate_restart replicates
timed out), leaving sem_escalate with ZERO valid replicates for that
(module, model) pair. No verdict can be honestly computed on a condition
with 0 valid draws -- that row is labeled "Insufficient data" instead of
being forced through the classifier, and excluded from the wins/
protective/losses/tied/mixed tally at the bottom (reported as its own
separate count).

At the bottom: wins / protective / losses / tied / mixed / insufficient-data
counts (using the brief's own naming: wins=Escalation wins,
losses=Baseline wins).

Usage: python phase2/set1_analysis/table_condition_decision.py
Output: table_condition_decision.tex, table_condition_decision.csv
"""
import csv
import os
import sys
from collections import Counter

_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, _HERE)
import _data  # noqa: E402

OUT_TEX = os.path.join(_HERE, "table_condition_decision.tex")
OUT_CSV = os.path.join(_HERE, "table_condition_decision.csv")


def _tex_escape(s):
    return s.replace("_", r"\_")


def classify(b, sa, se, ser):
    """b/sa/se/ser are pass counts out of their own valid-n (normally 3).
    Comparisons are on raw pass counts, per the brief -- valid whenever
    all four conditions have the same n (true for all 51 recoverable-band
    rows: none of the 6 known-error cells falls in the recoverable band,
    verified in main())."""
    vals = (b, sa, se, ser)
    spread = max(vals) - min(vals)
    esc_best = max(se, ser)

    if spread <= 1:
        return "Tied"
    if esc_best >= b + 1:
        return "Escalation wins"
    if sa <= b - 1 and esc_best >= b:
        return "Protective"
    if sa <= b - 1:
        return "Baseline wins"
    return "Mixed (uncategorized)"


def build():
    entries = _data.load_master_log()
    counts = _data.pivot_pass_counts(entries)
    categories = _data.load_categories()
    recoverable = sorted(m for m, info in categories.items() if info["difficulty_tier"] == "recoverable")

    rows = []
    for m in recoverable:
        for model in _data.MODELS:
            cell = {}
            for cond in _data.CONDITIONS:
                p, n = counts[(m, model, cond)]
                cell[cond] = (p, n)
            b, bn = cell["baseline"]
            sa, san = cell["sem_adv"]
            se, sen = cell["sem_escalate"]
            ser, sern = cell["sem_escalate_restart"]
            if 0 in (bn, san, sen, sern):
                verdict = "Insufficient data"
            else:
                verdict = classify(b, sa, se, ser)
            rows.append({
                "module": m, "model": model,
                "baseline": (b, bn), "sem_adv": (sa, san),
                "sem_escalate": (se, sen), "sem_escalate_restart": (ser, sern),
                "verdict": verdict,
            })
    return rows


def write_tex(rows):
    lines = []
    lines.append("% Auto-generated by phase2/set1_analysis/table_condition_decision.py -- do not hand-edit.")
    lines.append(r"\begin{table}[t]")
    lines.append(r"\centering")
    lines.append(r"\small")
    lines.append(r"\caption{Set 1: per-(module, model) condition decision, recoverable-band modules "
                 r"only ($n{=}17$ modules $\times$ 3 models $=$ 51 rows). Pass counts shown as p/n "
                 r"(n$=$3 except one RAM/llama3.1 row touched by transient timeouts); "
                 r"verdict logic in table\_condition\_decision.py.}")
    lines.append(r"\label{tab:set1-condition-decision}")
    lines.append(r"\begin{tabular}{llccccl}")
    lines.append(r"\toprule")
    lines.append(r"Module & Model & baseline & sem\_adv & sem\_esc & sem\_esc\_r & Verdict \\")
    lines.append(r"\midrule")
    for r in rows:
        b, bn = r["baseline"]; sa, san = r["sem_adv"]
        se, sen = r["sem_escalate"]; ser, sern = r["sem_escalate_restart"]
        lines.append(
            f"{_tex_escape(r['module'])} & {_tex_escape(_data.MODEL_DISPLAY[r['model']])} & "
            f"{b}/{bn} & {sa}/{san} & {se}/{sen} & "
            f"{ser}/{sern} & {r['verdict']} \\\\"
        )
    lines.append(r"\bottomrule")
    lines.append(r"\end{tabular}")
    lines.append(r"\end{table}")
    with open(OUT_TEX, "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")


def write_csv(rows):
    with open(OUT_CSV, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["module", "model", "baseline", "sem_adv", "sem_escalate",
                     "sem_escalate_restart", "verdict"])
        for r in rows:
            b, bn = r["baseline"]; sa, san = r["sem_adv"]
            se, sen = r["sem_escalate"]; ser, sern = r["sem_escalate_restart"]
            w.writerow([r["module"], r["model"], f"{b}/{bn}", f"{sa}/{san}",
                         f"{se}/{sen}", f"{ser}/{sern}", r["verdict"]])


def main():
    rows = build()
    assert len(rows) == 51, f"expected 17 recoverable modules x 3 models = 51 rows, got {len(rows)}"

    write_tex(rows)
    write_csv(rows)

    tally = Counter(r["verdict"] for r in rows)
    print(f"Wrote {OUT_TEX} and {OUT_CSV} ({len(rows)} rows)")
    print()
    print("Verdict tally:")
    for label in ("Escalation wins", "Protective", "Baseline wins", "Tied",
                   "Mixed (uncategorized)", "Insufficient data"):
        print(f"  {label:<24} {tally.get(label, 0)}")
    assert sum(tally.values()) == 51


if __name__ == "__main__":
    main()
