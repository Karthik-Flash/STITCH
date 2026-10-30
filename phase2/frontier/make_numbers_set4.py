"""Every Set 4 / Set 4b number the paper quotes, as LaTeX macros, from the analysis JSON files, plus the Haiku
projection (paper v10, Part E) and the Set 4b floor heat map.
The v10 paper files now live in paper/archive/v10/overleaf/ (local only). Paper v11 (paper/main.tex) quotes these
values as plain numbers and has no heat map; run this script to read the values (it prints every macro) or to
rebuild v10.
  python -B phase2/frontier/make_numbers_set4.py                  (projects Haiku's missing cells, marked)
  python -B phase2/frontier/make_numbers_set4.py --no-projection  (measured runs only; missing cells "not run")
Writes (rewriting only the marked blocks of the two .tex files):
  paper/archive/v10/overleaf/main.tex        between "% BEGIN GENERATED NUMBERS" and "% END GENERATED NUMBERS"
  paper/archive/v10/overleaf/supplement.tex  the same NUMBERS block, and the S6 tables between "% BEGIN GENERATED TABLES" and
                                 "% END GENERATED TABLES"
  paper/archive/v10/overleaf/figures/fig_floor_heatmap.pdf
  phase2/frontier/evidence/set4b_haiku_projection.json (projection inputs, method and outputs)
If Haiku's pending Set 4b runs are completed, re-run analysis_set4b.py and then this script: the projected cells
disappear, every \\proj{} value becomes the measured one and the projection notes become empty.
Sources: phase2/results/set4_api/analysis/set4_analysis.json (analysis_set4.py),
         phase2/results/set4_api/analysis_4b/set4b_analysis.json (analysis_set4b.py),
         phase2/results/set4_api/parity_check_osscad.json (parity_check.py),
         phase2/results/set4_api/floor_full/<provider>/master_log.json (per-cell counts for the projection).
"""
import json
import math
import os
import sys
from collections import defaultdict

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(os.path.dirname(HERE))
SET4 = os.path.join(REPO, "phase2", "results", "set4_api")
OVERLEAF = os.path.join(REPO, "paper", "archive", "v10", "overleaf")
EVIDENCE = os.path.join(HERE, "evidence", "set4b_haiku_projection.json")
GPT, GEM, HAI = "gpt-4.1-mini-2025-04-14", "gemini-2.5-flash", "claude-haiku-4-5-20251001"
MODELS = [GPT, GEM, HAI]
CONDS = ["baseline", "sem_adv", "sem_escalate", "sem_escalate_restart"]
SHORT = {GPT: "GPT-4.1 mini", GEM: "Gemini 2.5 Flash", HAI: "Claude Haiku 4.5"}
CTEX = {"baseline": r"\cond{baseline}", "sem_adv": r"\cond{sem\_adv}", "sem_escalate": r"\cond{sem\_escalate}",
        "sem_escalate_restart": r"\cond{sem\_esc\_restart}"}


def esc(name):
    return name.replace("_", r"\_")


def tex_list(mods):
    m = [r"\texttt{" + esc(x) + "}" for x in mods]
    return m[0] if len(m) == 1 else ", ".join(m[:-1]) + " and " + m[-1]


def tier(rate):
    return "floor" if rate < 0.2 else ("recoverable" if rate < 0.8 else "ceiling")


# ---------------------------------------------------------------- Haiku projection (Part E)
def cell_counts():
    """{(model, module, condition): [passes, valid runs]} over the Set 4b master logs."""
    c = defaultdict(lambda: [0, 0])
    for p in ("openai", "gemini", "anthropic"):
        for r in json.load(open(os.path.join(SET4, "floor_full", p, "master_log.json"), encoding="utf-8")):
            if not r.get("error"):
                k = c[(r["model"], r["module"], r["condition"])]
                k[0] += bool(r["pass"])
                k[1] += 1
    return c


def elogit(k, n):
    """Empirical logit (add one half), finite at 0/n and n/n."""
    return math.log((k + 0.5) / (n - k + 0.5))


def project(modules):
    """Haiku projection for each (module, condition) cell with fewer than 3 valid Haiku runs.
    Start: the mean pass rate of GPT-4.1 mini and Gemini 2.5 Flash on that cell. Shift: Haiku's mean empirical-logit
    difference from those two models over the cells all three measured in full (3 runs each), applied on the logit
    scale (a mean rate of exactly 0 or 1 stays there). Range: the lower to the higher of the two models' rates."""
    c = cell_counts()
    for m in modules:
        for x in CONDS:
            assert c[(GPT, m, x)][1] == 3 and c[(GEM, m, x)][1] == 3, (m, x)
    full = [(m, x) for m in modules for x in CONDS if c[(HAI, m, x)][1] == 3]
    diffs = [elogit(*c[(HAI, m, x)]) - (elogit(*c[(GPT, m, x)]) + elogit(*c[(GEM, m, x)])) / 2 for m, x in full]
    d = sum(diffs) / len(diffs)
    cells = []
    for m in modules:
        for x in CONDS:
            h, g, f = c[(HAI, m, x)], c[(GPT, m, x)], c[(GEM, m, x)]
            if h[1] == 3:
                continue
            rg, rf = g[0] / 3, f[0] / 3
            ref = (rg + rf) / 2
            p = ref if ref in (0, 1) else 1 / (1 + math.exp(-(math.log(ref / (1 - ref)) + d)))
            cells.append({"module": m, "condition": x, "haiku_observed": h, "gpt": g, "gemini": f,
                          "projected_rate": round(p, 4), "projected_passes_of_3": round(3 * p, 2),
                          "range_passes_of_3": [3 * min(rg, rf), 3 * max(rg, rf)]})
    out = {"method": project.__doc__.split("\n", 1)[1].strip().replace("\n   ", ""),
           "offset_logit": round(d, 4), "offset_cells": len(full), "projected_cells": cells,
           "counts": {f"{mo}|{m}|{x}": c[(mo, m, x)] for mo in MODELS for m in modules for x in CONDS}}
    json.dump(out, open(EVIDENCE, "w", encoding="utf-8", newline="\n"), indent=1)
    print(f"wrote {os.path.relpath(EVIDENCE, REPO)}: offset {d:+.3f} logit over {len(full)} cells, "
          f"{len(cells)} projected cells")
    return out


# ---------------------------------------------------------------- macros
def macros(a, b, par, pj):
    m = {}   # macro name -> (value, source)

    # ---- Set 4: recoverable band, 3 models x 17 modules x 4 conditions x N=3
    m["SetFourRuns"] = (a["runs_total"], "set4_analysis.json runs_total")
    m["SetFourErrored"] = (a["runs_errored"], "set4_analysis.json runs_errored")
    for c, tag in zip(CONDS, ("Base", "Adv", "Esc", "Restart")):
        p = a["pass_rates"][f"pooled|{c}"]
        m[f"SetFourPooled{tag}"] = (f"{100 * p['rate']:.1f}", f"pass_rates pooled|{c}")
        m[f"SetFourPooled{tag}K"] = (f"{p['k']}/{p['n']}", f"pass_rates pooled|{c}")
    for mo, tag in ((GPT, "GPT"), (GEM, "Gemini"), (HAI, "Haiku")):
        p = a["pass_rates"][f"{mo}|baseline"]
        m[f"SetFour{tag}BaseK"] = (f"{p['k']}/{p['n']}", f"pass_rates {mo}|baseline")
        m[f"SetFour{tag}ToolRed"] = (f"{a['tools'][mo]['reduction_pct']:.1f}", f"tools {mo} reduction_pct")
    for c, tag in zip(CONDS[1:], ("Adv", "Esc", "Restart")):
        g = a["contrasts"][f"{GPT}|{c}"]
        m[f"SetFourGPTDelta{tag}"] = (f"{g['mean_pts']:+.1f}".replace("-", "$-$"), f"contrasts {GPT}|{c}")
    ps = [v["p"] for k, v in a["contrasts"].items()]
    m["SetFourMinP"] = (f"{min(ps):.3f}", "contrasts, min sign-flip p over all scopes and conditions")
    t = a["tools"]["pooled"]
    m["SetFourToolRed"] = (f"{t['reduction_pct']:.1f}", "tools pooled reduction_pct")
    m["SetFourToolAdv"] = (f"{t['sem_adv']:.2f}", "tools pooled sem_adv")
    m["SetFourToolEsc"] = (f"{t['sem_escalate']:.2f}", "tools pooled sem_escalate")
    inr = [v["inr_per_pass"] for v in a["cost"].values() if v.get("inr_per_pass")]
    m["SetFourInrPassMin"] = (f"{min(inr):.2f}", "cost, min inr_per_pass over model x condition")
    m["SetFourInrPassMax"] = (f"{max(inr):.2f}", "cost, max inr_per_pass over model x condition")
    fp = sorted(a["fingerprint_counts"].items(), key=lambda kv: -kv[1])
    m["SetFourFingerprintMain"] = (fp[0][1], f"fingerprint_counts {fp[0][0]}")
    m["SetFourFingerprintOther"] = (fp[1][1], f"fingerprint_counts {fp[1][0]}")
    m["SetFourParitySim"] = (f"{par['a_agree']}/{par['candidates']}", "parity_check_osscad.json a_agree/candidates")
    m["SetFourParityInterp"] = (f"{par['b_agree']}/{par['b_checked']}", "parity_check_osscad.json b_agree/b_checked")

    # ---- Set 4b: floor tier, 19 modules x 4 conditions x N=3 = 228 per model
    planned = 19 * len(CONDS) * 3
    m["SetFourBPlanned"] = (planned, "19 modules x 4 conditions x N=3")
    for mo, tag in ((GPT, "GPT"), (GEM, "Gemini"), (HAI, "Haiku")):
        m[f"SetFourB{tag}Valid"] = (b["coverage"][mo]["valid"], f"set4b_analysis.json coverage {mo} valid")
        m[f"SetFourB{tag}Errored"] = (b["coverage"][mo]["errored"], f"coverage {mo} errored")
    m["SetFourBHaikuPending"] = (planned - b["coverage"][HAI]["valid"], "planned - Haiku valid")
    m["SetFourBValidTotal"] = (sum(v["valid"] for v in b["coverage"].values()), "coverage, sum of valid runs")
    m["SetFourAllValid"] = (a["runs_total"] - a["runs_errored"] + m["SetFourBValidTotal"][0],
                            "Set 4 valid runs + Set 4b valid runs")
    models, q1 = b["models"], b["Q1"]
    leave = [mod for mod in q1 if any(q1[mod][x]["n"] and q1[mod][x]["tier"] != "floor" for x in models)]
    ceil_all = [mod for mod in q1 if all(q1[mod][x]["n"] and q1[mod][x]["tier"] == "ceiling" for x in models)]
    still = [mod for mod in q1 if all(q1[mod][x]["tier"] == "floor" for x in models if q1[mod][x]["n"])]
    m["SetFourBFloorModules"] = (len(q1), "Q1 modules")
    m["SetFourBLeaveFloor"] = (len(leave), "Q1: modules with a non-floor baseline tier for at least one model")
    m["SetFourBCeilingAll"] = (len(ceil_all), "Q1: modules at ceiling for all three models (all three measured)")
    m["SetFourBStillFloor"] = (tex_list(sorted(still, key=str.lower)), "Q1: floor for every model that ran them")
    q2 = b["Q2"]
    tool = CONDS[1:]
    fails = sum(q2[c]["fails"] for c in tool)
    fsf = sum(q2[c]["fails_with_sf"] for c in tool)
    m["SetFourBToolFails"] = (fails, "Q2: fails in the three tool conditions")
    m["SetFourBToolFailsSF"] = (fsf, "Q2: of those, with semantic_fired")
    m["SetFourBToolFailsSFPct"] = (round(100 * fsf / fails), "Q2: percentage")
    m["SetFourBDBPZeroCells"] = (sum(len(q2[c]["passes_sf_before_pass_where_baseline_0of3"]) for c in tool),
                                 "Q2: passes with a directive before the pass in baseline-0/3 cells (all traced, none attributable)")
    m["SetFourBMinP"] = (f"{min(v['p'] for v in b['Q3'].values()):.3f}", "Q3: min sign-flip p")
    m["SetFourBQThreeContrasts"] = (len(b["Q3"]), "Q3: number of contrasts")
    allthree = [mod for mod, row in b["Q4_table"].items() if all(row[x][1] for x in models)]
    m["SetFourBAllThreeModules"] = (len(allthree), "Q4: modules every model ran")
    m["SetFourBQFour"] = (tex_list(b["Q4"]) if b["Q4"] else "none", "Q4 strict list")
    m["SetFourBQFourRuns"] = (sum(b["Q4_table"][b["Q4"][0]][x][1] for x in models) if b["Q4"] else 0,
                              "Q4: valid runs on the strict module")
    alu = b["Q4_table"]["alu"]
    m["SetFourBAluGemini"] = (f"{alu[GEM][0]}/{alu[GEM][1]}", "Q4_table alu gemini")

    # ---- Haiku projection: only the floor heat map and the Q1 ceiling count use it
    cells = pj["projected_cells"]
    base_proj = {x["module"]: x["projected_rate"] for x in cells if x["condition"] == "baseline"}
    measured = sum(1 for mod in q1 if q1[mod][HAI]["n"])
    haiku_tier = {mod: q1[mod][HAI]["tier"] if q1[mod][HAI]["n"] else tier(base_proj[mod]) for mod in q1} \
        if base_proj else {}
    ceil_full = sum(1 for mod in q1 if q1[mod][GPT]["tier"] == q1[mod][GEM]["tier"] == haiku_tier.get(mod) == "ceiling")
    m["SetFourBHaikuModules"] = (measured, "Q1: modules with Haiku baseline runs")
    m["SetFourBProjCells"] = (len(cells), "set4b_haiku_projection.json projected_cells")
    m["SetFourBProjOffset"] = (f"{pj['offset_logit']:+.2f}".replace("-", "$-$"), "set4b_haiku_projection.json offset_logit")
    m["SetFourBProjOffsetCells"] = (pj["offset_cells"], "set4b_haiku_projection.json offset_cells")
    m["SetFourBCeilingAllClause"] = ((rf", and \proj{{{ceil_full}}} of all {len(q1)} once Haiku's missing modules "
                                      r"are projected") if base_proj else "",
                                     "Q1 ceiling for all three over all modules, Haiku projected where not run")
    note = (rf"Haiku: {measured} of {len(q1)} modules measured; values marked~\textsuperscript{{\dag}} (hatched in "
            r"the heat map) are projections, to be replaced.\projcheck{}") if cells else (
        rf"Haiku: {measured} of {len(q1)} modules measured; heat-map cells marked -- were not run."
        if measured < len(q1) else "")
    m["SetFourBProjNote"] = (note, "empty once no projected cell remains")
    return m


# ---------------------------------------------------------------- S6 tables
def _pts(x):
    return f"{x:+.1f}".replace("-", "$-$")


def tables(a, b, pj):
    out = []

    def tab(label, caption, spec, header, rows, extra=""):
        out.extend([r"\begin{table}[!htbp]", r"\centering", r"\footnotesize", rf"\caption{{{caption}}}",
                    rf"\label{{{label}}}", extra + rf"\begin{{tabular}}{{{spec}}}", r"\toprule", header + r" \\",
                    r"\midrule"] + [r + r" \\" for r in rows] + [r"\bottomrule", r"\end{tabular}", r"\end{table}", ""])

    hdr4 = " & ".join(CTEX[c] for c in CONDS)
    # Set 4: passes per condition per model; Wilson CI on the pooled row
    rows = [SHORT[mo] + " & " + " & ".join(f"{a['pass_rates'][f'{mo}|{c}']['k']}/{a['pass_rates'][f'{mo}|{c}']['n']}"
                                           for c in CONDS) for mo in MODELS]
    rows.append(r"\midrule Pooled & " + " & ".join(
        f"{a['pass_rates'][f'pooled|{c}']['k']}/{a['pass_rates'][f'pooled|{c}']['n']}" for c in CONDS))
    rows.append(r"Pooled, \% [CI] & " + " & ".join(
        "{:.1f} [{:.1f}, {:.1f}]".format(*(100 * a["pass_rates"][f"pooled|{c}"][k] for k in ("rate", "lo", "hi")))
        for c in CONDS))
    tab("tab:s-set4-pass", r"Set~4, recoverable band ($17$ modules, $N{=}3$): passes per condition, with the pooled "
        r"rate and its Wilson $95\%$ CI. All three models are at or near ceiling.",
        "@{}l rrrr@{}", "Model & " + hdr4, rows)
    # Set 4: contrasts (cell bootstrap, sign-flip)
    rows = []
    for mo in ["pooled"] + MODELS:
        cells = []
        for c in CONDS[1:]:
            k = a["contrasts"].get(f"{mo}|{c}")
            cells += [f"{_pts(k['mean_pts'])} [{_pts(k['lo'])}, {_pts(k['hi'])}]", f"{k['p']:.3f}"] if k else ["--", "--"]
        rows.append((SHORT.get(mo) or f"Pooled ({a['contrasts']['pooled|sem_adv']['cells']} cells)") + " & " + " & ".join(cells))
    tab("tab:s-set4-contrast", r"Set~4: condition minus baseline (points), (model, module) cell bootstrap $95\%$ CI and "
        r"sign-flip $p$. No contrast differs from baseline.",
        "@{}l rr rr rr@{}", r" & \multicolumn{2}{c}{" + CTEX["sem_adv"] + r"} & \multicolumn{2}{c}{" + CTEX["sem_escalate"]
        + r"} & \multicolumn{2}{c}{" + CTEX["sem_escalate_restart"] + r"} \\ \cmidrule(lr){2-3}\cmidrule(lr){4-5}"
        r"\cmidrule(l){6-7} Scope & $\Delta$ [CI] & $p$ & $\Delta$ [CI] & $p$ & $\Delta$ [CI] & $p$", rows)
    # Set 4: mechanism trace and tool calls
    rows = []
    for mo in MODELS + ["pooled"]:
        t = a["trace"][f"{mo}|sem_adv"]
        e, r_ = a["trace"][f"{mo}|sem_escalate"], a["trace"][f"{mo}|sem_escalate_restart"]
        tl = a["tools"][mo]
        rows.append(("\\midrule " if mo == "pooled" else "") + f"{SHORT.get(mo, 'Pooled')} & {t['sf_runs']} & "
                    f"{t['passes_with_sf']} ({t['passes_sf_before_pass']}) & {e['escalated']} ({e['escalated_passes']}) & "
                    f"{r_['escalated']} ({r_['escalated_passes']}) & {tl['sem_adv']:.2f} & {tl['sem_escalate']:.2f} & "
                    f"{tl['reduction_pct']:.1f}")
    tab("tab:s-set4-trace", r"Set~4 mechanism trace. \cond{sem\_adv}: runs where the interpreter fired, and passes with "
        r"it firing (in brackets: fired on an iteration before the passing one). Escalation conditions: escalated runs "
        r"(of which passed). Last three columns: Verilator and Yosys calls per run and the cut of \cond{sem\_escalate} "
        r"against \cond{sem\_adv}.",
        "@{}l rrrr rrr@{}", r"Model & \makecell{fired\\runs} & \makecell{passes\\fired} & \makecell{\cond{sem\_esc.}\\escalated}"
        r" & \makecell{\cond{sem\_esc\_rst.}\\escalated} & \makecell{calls\\\cond{sem\_adv}} & "
        r"\makecell{calls\\\cond{sem\_esc.}} & \makecell{cut\\\%}", rows)
    # Set 4: cost
    rows = [SHORT[mo] + " & " + " & ".join(f"{a['cost'][f'{mo}|{c}']['inr_per_run']:.3f} & "
                                           f"{a['cost'][f'{mo}|{c}']['inr_per_pass']:.3f}" for c in CONDS) for mo in MODELS]
    tab("tab:s-set4-cost", r"Set~4 cost in INR per run and per passing run (USD $\times 96 \times 1.18$, list prices).",
        "@{}l rr rr rr rr@{}", " & " + " & ".join(rf"\multicolumn{{2}}{{c}}{{{CTEX[c]}}}" for c in CONDS)
        + r" \\ \cmidrule(lr){2-3}\cmidrule(lr){4-5}\cmidrule(lr){6-7}\cmidrule(l){8-9} Model"
        + " & run & pass" * 4, rows)

    # Set 4b: coverage
    planned = 19 * len(CONDS) * 3
    rows = [f"{SHORT[mo]} & {b['coverage'][mo]['valid']} & {b['coverage'][mo]['errored']} & "
            f"{planned - b['coverage'][mo]['valid'] - b['coverage'][mo]['errored']}" for mo in MODELS]
    tab("tab:s-set4b-cov", rf"Set~4b coverage, of ${planned}$ planned runs per model. Errored runs failed on an "
        r"exhausted account credit, cost nothing, and are excluded (pending).",
        "@{}l rrr@{}", r"Model & valid & \makecell{errored\\(pending)} & not run", rows)
    # Set 4b: Q1 and Q4 per module
    q1, q4 = b["Q1"], b["Q4_table"]
    ab = {"ceiling": "C", "recoverable": "R", "floor": "F"}
    rows = []
    for mod in sorted(q1, key=str.lower):
        cells = []
        for mo in MODELS:
            c, t = q1[mod][mo], q4[mod][mo]
            cells += ["--", "--"] if not c["n"] else [f"{c['k']}/{c['n']} {ab[c['tier']]}", f"{t[0]}/{t[1]}"]
        rows.append(r"\texttt{" + esc(mod) + "} & " + " & ".join(cells))
    tab("tab:s-set4b-q1", r"Set~4b per floor module: baseline passes of $3$ with the tier this model puts the module in "
        r"(Q1; C ceiling, R recoverable, F floor), and passes over all valid runs of all four conditions (Q4). "
        r"--: not run" + (r" (measured values only; projections: \cref{tab:s-proj})." if pj["projected_cells"] else "."),
        "@{}l rr rr rr@{}", r" & \multicolumn{2}{c}{GPT-4.1 mini} & \multicolumn{2}{c}{Gemini 2.5 Flash} & "
        r"\multicolumn{2}{c}{Claude Haiku 4.5} \\ \cmidrule(lr){2-3}\cmidrule(lr){4-5}\cmidrule(l){6-7} "
        r"Module & Q1 & Q4 & Q1 & Q4 & Q1 & Q4", rows)
    # Set 4b: Q2
    rows = []
    for c in CONDS:
        q = b["Q2"][c]
        rows.append(f"{CTEX[c]} & {q['runs']} & {q['fails']} & {q['fails_with_sf']} & {q['passes']} & "
                    f"{q['passes_sf_before_pass']} & {len(q['passes_sf_before_pass_where_baseline_0of3'])} & "
                    f"{q['escalated'] if 'escalated' in q else '--'}")
    tab("tab:s-set4b-q2", r"Set~4b, Q2: the interpreter on floor failures. Passes with a directive delivered before the "
        r"passing iteration, and those in cells whose baseline was $0/3$ (each traced; none attributable to the "
        r"directive).",
        "@{}l rrrrrrr@{}", r"Condition & runs & fails & \makecell{fails\\fired} & passes & \makecell{directive\\before pass}"
        r" & \makecell{of which\\baseline $0/3$} & escalated", rows)
    # Set 4b: Q3
    rows = []
    for scope in ["pooled"] + MODELS:
        cells, n = [], ""
        for c in CONDS[1:]:
            k = b["Q3"].get(f"{scope}|{c}")
            cells += [f"{_pts(k['mean_pts'])} [{_pts(k['lo'])}, {_pts(k['hi'])}]", f"{k['p']:.3f}"] if k else ["--", "--"]
            n = n or (k and k["cells"])
        rows.append(f"{SHORT.get(scope, 'Pooled')} & {n} & " + " & ".join(cells))
    tab("tab:s-set4b-q3", r"Set~4b, Q3: condition minus baseline on cells whose baseline was below $3/3$ (points, cell "
        r"bootstrap $95\%$ CI, sign-flip $p$). No contrast is significant.",
        "@{}l r rr rr rr@{}", r" & & \multicolumn{2}{c}{" + CTEX["sem_adv"] + r"} & \multicolumn{2}{c}{"
        + CTEX["sem_escalate"] + r"} & \multicolumn{2}{c}{" + CTEX["sem_escalate_restart"] + r"} \\ "
        r"\cmidrule(lr){3-4}\cmidrule(lr){5-6}\cmidrule(l){7-8} Scope & cells & $\Delta$ [CI] & $p$ & $\Delta$ [CI] & $p$ "
        r"& $\Delta$ [CI] & $p$", rows)

    # Haiku projection (Part E): method and the projected cells
    cells = pj["projected_cells"]
    measured = sum(1 for x in q1 if q1[x][HAI]["n"])
    if not cells:
        out.append(r"\subsection*{Haiku coverage}")
        out += [r"Claude Haiku~4.5 is complete on the floor tier; no value in the paper is projected." if measured == len(q1)
                else rf"Claude Haiku~4.5 is measured on {measured} of {len(q1)} floor modules; its missing cells are "
                     r"reported as not run, and no value in the paper is projected.", ""]
        return "\n".join(out) + "\n"
    out.append(r"\subsection*{Haiku projection (to be replaced by measured runs)}")
    out += [rf"Claude Haiku~4.5 is measured on {sum(1 for x in q1 if q1[x][HAI]['n'])} of {len(q1)} floor modules. "
            r"Only two places in the paper need a complete Haiku column, the floor heat map and the count of modules "
            r"at ceiling for all three models; there, each missing (module, condition) cell is projected and marked "
            r"with a dagger. Each projection starts from the mean pass rate of GPT-4.1 mini and Gemini 2.5 Flash on "
            r"that cell and shifts it on the logit scale by Haiku's mean logit difference from those two models over "
            rf"the {pj['offset_cells']} cells all three measured in full (empirical logits with one half added to "
            rf"each count, so that $0/3$ and $3/3$ stay finite): "
            rf"${pj['offset_logit']:+.2f}$ logits, Haiku being the stronger. A mean rate of exactly $0$ or $1$ stays "
            r"there. The range is the lower to the higher of the two other models' rates. Every observed conclusion "
            r"in the paper uses measured runs only, and \texttt{make\_numbers\_set4.py} replaces each projection once "
            r"the runs are completed. Inputs, method and outputs: "
            r"\texttt{phase2/frontier/evidence/set4b\_haiku\_projection.json}.", ""]
    by = defaultdict(dict)
    for x in cells:
        by[x["module"]][x["condition"]] = x
    rows = []
    for mod in sorted(by, key=str.lower):
        cl = []
        for c in CONDS:
            x = by[mod].get(c)
            cl.append("--" if not x else "{:.1f} [{:g}, {:g}]".format(x["projected_passes_of_3"], *x["range_passes_of_3"]))
        rows.append(r"\texttt{" + esc(mod) + "} & " + " & ".join(cl))
    tab("tab:s-proj", r"Projected Claude Haiku~4.5 passes of $3$ per missing cell, with the range spanned by GPT-4.1 "
        r"mini and Gemini 2.5 Flash in brackets. --: measured (\texttt{float\_multi} lacks one \cond{sem\_esc\_restart} "
        r"run; its value is the projected expectation for a full cell).",
        "@{}l rrrr@{}", "Module & " + hdr4, rows)
    return "\n".join(out) + "\n"


# ---------------------------------------------------------------- floor heat map (main paper)
def heatmap(b, pj):
    sys.path.insert(0, os.path.join(REPO, "paper"))
    import figstyle as fs
    import numpy as np
    from matplotlib.colors import LinearSegmentedColormap
    from matplotlib.patches import Patch, Rectangle

    q1 = b["Q1"]
    proj = {x["module"]: x for x in pj["projected_cells"] if x["condition"] == "baseline"}
    order = sorted(q1, key=lambda mod: (-(q1[mod][GPT]["k"] + q1[mod][GEM]["k"]), mod.lower()))
    val = np.array([[q1[mod][mo]["k"] if q1[mod][mo]["n"] else proj.get(mod, {}).get("projected_passes_of_3", np.nan)
                     for mod in order] for mo in MODELS], dtype=float)
    cmap = LinearSegmentedColormap.from_list("grey", ["#f4f3f0", "#3f3e3b"])
    fig, ax = fs.figure(fs.FULL, 1.7)
    ax.imshow(val, cmap=cmap, vmin=0, vmax=3, aspect="auto")
    for i, mo in enumerate(MODELS):
        for j, mod in enumerate(order):
            v, projected = val[i, j], not q1[mod][mo]["n"]
            ink = "#ffffff" if v >= 1.9 else fs.INK
            if np.isnan(v):                    # projections disabled: a cell Haiku did not run stays empty
                ax.text(j, i, "–", ha="center", va="center", fontsize=7.5, color=fs.MUTED)
            elif projected:                    # hatch the cell, keep the value legible on a solid patch
                ax.add_patch(Rectangle((j - 0.5, i - 0.5), 1, 1, fill=False, hatch="////",
                                       edgecolor=(1, 1, 1, 0.55), linewidth=0))
                ax.text(j, i, f"{v:.1f}†", ha="center", va="center", fontsize=7, style="italic", color=ink,
                        bbox={"boxstyle": "square,pad=0.12", "facecolor": cmap(v / 3), "edgecolor": "none"})
            else:
                ax.text(j, i, f"{v:.0f}", ha="center", va="center", fontsize=7.5, color=ink)
    if proj:
        ax.legend(handles=[Patch(facecolor="#7a7975", hatch="////", edgecolor=(1, 1, 1, 0.55),
                                 label="proj.: Haiku not run, projected (italic, †)")],
                  loc="lower right", bbox_to_anchor=(1.0, 1.0), borderaxespad=0.2, fontsize=7)
    ax.set_xticks(range(len(order)))
    ax.set_xticklabels(order, rotation=40, ha="right", rotation_mode="anchor", fontsize=7)
    ax.set_yticks(range(len(MODELS)))
    ax.set_yticklabels([SHORT[mo] for mo in MODELS])
    ax.set_xticks(np.arange(-0.5, len(order)), minor=True)
    ax.set_yticks(np.arange(-0.5, len(MODELS)), minor=True)
    ax.grid(which="minor", color="#ffffff", linewidth=1.5)
    ax.tick_params(which="both", length=0)
    for s in ax.spines.values():
        s.set_visible(False)
    fs.save(fig, os.path.join(OVERLEAF, "figures", "fig_floor_heatmap"))


def splice(path, tag, body):
    """Replace the lines between '% BEGIN GENERATED <tag>' and '% END GENERATED <tag>' in path."""
    text = open(path, encoding="utf-8").read()
    start, end = f"% BEGIN GENERATED {tag}\n", f"% END GENERATED {tag}"
    i, j = text.index(start) + len(start), text.index(end)
    open(path, "w", encoding="utf-8", newline="\n").write(text[:i] + body + text[j:])
    print(f"rewrote the {tag} block of {os.path.relpath(path, REPO)}")


def main():
    a = json.load(open(os.path.join(SET4, "analysis", "set4_analysis.json"), encoding="utf-8"))
    b = json.load(open(os.path.join(SET4, "analysis_4b", "set4b_analysis.json"), encoding="utf-8"))
    par = json.load(open(os.path.join(SET4, "parity_check_osscad.json"), encoding="utf-8"))["summary"]
    pj = project(sorted(b["Q1"], key=str.lower))
    if "--no-projection" in sys.argv:          # keep measured runs only; missing Haiku cells read "not run"
        pj = dict(pj, projected_cells=[])
    m = macros(a, b, par, pj)
    block = ["% GENERATED by phase2/frontier/make_numbers_set4.py -- do not edit by hand."]
    fmt = lambda v: f"{v:,}".replace(",", "{,}") if isinstance(v, int) else v   # noqa: E731  1{,}211 in math mode
    block += [f"\\newcommand{{\\{k}}}{{{fmt(v)}}}  % {src}" for k, (v, src) in m.items()]
    block = "\n".join(block) + "\n"
    for f in ("main.tex", "supplement.tex"):
        splice(os.path.join(OVERLEAF, f), "NUMBERS", block)
    splice(os.path.join(OVERLEAF, "supplement.tex"), "TABLES", tables(a, b, pj))
    heatmap(b, pj)
    for k, (v, _) in m.items():
        print(f"  \\{k} = {v}")


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    main()
