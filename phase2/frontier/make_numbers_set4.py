"""Write paper/numbers_set4.tex: every Set 4 / Set 4b number the paper quotes, as LaTeX macros, from the analysis
JSON files. If Haiku's 85 pending Set 4b runs are completed later, re-run analysis_set4b.py and then this script;
the paper text needs no edit.
  python phase2/frontier/make_numbers_set4.py
Sources: phase2/results/set4_api/analysis/set4_analysis.json (analysis_set4.py),
         phase2/results/set4_api/analysis_4b/set4b_analysis.json (analysis_set4b.py),
         phase2/results/set4_api/parity_check_osscad.json (parity_check.py).
"""
import json
import os

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(os.path.dirname(HERE))
SET4 = os.path.join(REPO, "phase2", "results", "set4_api")
OUT = os.path.join(REPO, "paper", "numbers_set4.tex")
GPT, GEM, HAI = "gpt-4.1-mini-2025-04-14", "gemini-2.5-flash", "claude-haiku-4-5-20251001"
CONDS = ["baseline", "sem_adv", "sem_escalate", "sem_escalate_restart"]
TEX = {"adder_pipe_64bit": r"adder\_pipe\_64bit", "freq_divbyfrac": r"freq\_divbyfrac"}


def tex_list(mods):
    m = [r"\texttt{" + TEX.get(x, x.replace("_", r"\_")) + "}" for x in mods]
    return m[0] if len(m) == 1 else ", ".join(m[:-1]) + " and " + m[-1]


def main():
    a = json.load(open(os.path.join(SET4, "analysis", "set4_analysis.json"), encoding="utf-8"))
    b = json.load(open(os.path.join(SET4, "analysis_4b", "set4b_analysis.json"), encoding="utf-8"))
    par = json.load(open(os.path.join(SET4, "parity_check_osscad.json"), encoding="utf-8"))["summary"]
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
    m["SetFourBCeilingAll"] = (len(ceil_all), "Q1: modules at ceiling for all three models")
    m["SetFourBStillFloor"] = (tex_list(sorted(still, key=str.lower)), "Q1: floor for every model that ran them")
    q2 = b["Q2"]
    tool = [c for c in CONDS[1:]]
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

    lines = ["% GENERATED by phase2/frontier/make_numbers_set4.py -- do not edit by hand.",
             "% Re-run analysis_set4.py / analysis_set4b.py, then this script, to refresh."]
    for k, (v, src) in m.items():
        lines.append(f"\\newcommand{{\\{k}}}{{{v}}}  % {src}")
    open(OUT, "w", encoding="utf-8", newline="\n").write("\n".join(lines) + "\n")
    print(f"wrote {OUT}: {len(m)} macros")
    for k, (v, _) in m.items():
        print(f"  \\{k} = {v}")
    tables(a, b)


SHORT = {GPT: "GPT-4.1 mini", GEM: "Gemini 2.5 Flash", HAI: "Claude Haiku 4.5"}
CTEX = {"baseline": r"\texttt{baseline}", "sem_adv": r"\texttt{sem\_adv}", "sem_escalate": r"\texttt{sem\_escalate}",
        "sem_escalate_restart": r"\texttt{sem\_esc\_restart}"}


def _pts(x):
    return f"${x:+.1f}$"


def tables(a, b):
    """paper/tables_set4.tex: the Set 4 / 4b tables of Supplementary Material S6 (same sources as the macros)."""
    out = ["% GENERATED by phase2/frontier/make_numbers_set4.py -- do not edit by hand.",
           r"\providecommand{\fitbox}[1]{\resizebox{\ifdim\width>\linewidth\linewidth\else\width\fi}{!}{#1}}"]
    models = [GPT, GEM, HAI]

    def tab(label, caption, spec, header, rows):
        out.extend([r"\begin{table}[htbp]", r"\centering", rf"\caption{{{caption}}}", rf"\label{{{label}}}",
                    r"\footnotesize", r"\setlength{\tabcolsep}{4pt}",
                    r"\fitbox{" + rf"\begin{{tabular}}{{{spec}}}", r"\toprule", header + r" \\", r"\midrule"]
                   + [r + r" \\" for r in rows] + [r"\bottomrule", r"\end{tabular}}", r"\end{table}", ""])

    # Set 4: pass rate per condition per model, Wilson CI on the pooled row
    rows = []
    for mo in models + ["pooled"]:
        cells = []
        for c in CONDS:
            p = a["pass_rates"][f"{mo}|{c}"]
            ci = f" ({100 * p['lo']:.1f} to {100 * p['hi']:.1f})" if mo == "pooled" else ""
            cells.append(f"${p['k']}/{p['n']}$ (${100 * p['rate']:.1f}\\%$){ci}")
        rows.append((SHORT.get(mo, "Pooled") + " & " + " & ".join(cells)))
    tab("tab:s-set4-pass", r"Set~4, recoverable band ($17$ modules, $N{=}3$): passes per condition; Wilson $95\%$ CI on the pooled row.",
        "@{}l cccc@{}", "Model & " + " & ".join(CTEX[c] for c in CONDS), rows)
    # Set 4: contrasts (cell bootstrap, sign-flip)
    rows = []
    for mo in ["pooled"] + models:
        cells = []
        for c in CONDS[1:]:
            k = a["contrasts"].get(f"{mo}|{c}")
            cells.append(f"{_pts(k['mean_pts'])} [{_pts(k['lo'])}, {_pts(k['hi'])}], $p{{=}}{k['p']:.3f}$" if k else "--")
        rows.append(SHORT.get(mo, f"Pooled ({a['contrasts']['pooled|sem_adv']['cells']} cells)") + " & " + " & ".join(cells))
    tab("tab:s-set4-contrast", r"Set~4: condition minus baseline, points, (model, module) cell bootstrap $95\%$ CI and sign-flip $p$.",
        "@{}l ccc@{}", "Scope & " + " & ".join(CTEX[c] for c in CONDS[1:]), rows)
    # Set 4: mechanism trace and tool calls
    rows = []
    for mo in models + ["pooled"]:
        t = a["trace"][f"{mo}|sem_adv"]
        e, r_ = a["trace"][f"{mo}|sem_escalate"], a["trace"][f"{mo}|sem_escalate_restart"]
        tl = a["tools"][mo]
        rows.append(f"{SHORT.get(mo, 'Pooled')} & ${t['sf_runs']}$ & ${t['passes_with_sf']}$ (${t['passes_sf_before_pass']}$) & "
                    f"${e['escalated']}$ (${e['escalated_passes']}$) & ${r_['escalated']}$ (${r_['escalated_passes']}$) & "
                    f"${tl['sem_adv']:.2f}\\rightarrow{tl['sem_escalate']:.2f}$ (${tl['reduction_pct']:.1f}\\%$)")
    tab("tab:s-set4-trace", r"Set~4 mechanism trace. \texttt{sem\_adv}: runs where the interpreter fired, and passes with it firing (in brackets: fired on an iteration before the passing one). Escalation conditions: escalated runs (passed). Last column: Verilator+Yosys calls per run, \texttt{sem\_adv} to \texttt{sem\_escalate}.",
        "@{}l c c c c c@{}", r"Model & sf runs & passes w/ sf & \texttt{sem\_escalate} & \texttt{sem\_esc\_restart} & tool calls/run", rows)
    # Set 4: cost
    rows = []
    for mo in models:
        cells = []
        for c in CONDS:
            x = a["cost"][f"{mo}|{c}"]
            cells.append(f"${x['inr_per_run']:.3f}$ / ${x['inr_per_pass']:.3f}$")
        rows.append(SHORT[mo] + " & " + " & ".join(cells))
    tab("tab:s-set4-cost", r"Set~4 cost, INR per run / per passing run (USD $\times 96 \times 1.18$, list prices).",
        "@{}l cccc@{}", "Model & " + " & ".join(CTEX[c] for c in CONDS), rows)

    # Set 4b: coverage
    planned = 19 * len(CONDS) * 3
    rows = [f"{SHORT[mo]} & ${b['coverage'][mo]['valid']}$ & ${b['coverage'][mo]['errored']}$ & "
            f"${planned - b['coverage'][mo]['valid'] - b['coverage'][mo]['errored']}$" for mo in models]
    tab("tab:s-set4b-cov", rf"Set~4b coverage, of ${planned}$ planned runs per model. Errored runs failed on an exhausted account credit, cost nothing, and are excluded (pending).",
        "@{}l ccc@{}", "Model & valid & errored (pending) & not run", rows)
    # Set 4b: Q1 and Q4 per module
    q1, q4 = b["Q1"], b["Q4_table"]
    rows = []
    for mod in sorted(q1, key=str.lower):
        cells = []
        for mo in models:
            c, t = q1[mod][mo], q4[mod][mo]
            cells.append("--" if not c["n"] else f"${c['k']}/{c['n']}$ {c['tier']}")
            cells.append("--" if not t[1] else f"${t[0]}/{t[1]}$")
        rows.append(r"\texttt{" + mod.replace("_", r"\_") + "} & " + " & ".join(cells))
    tab("tab:s-set4b-q1", r"Set~4b per floor module: baseline passes of $3$ with the tier at this model (Q1), and passes over all valid runs, all conditions (Q4). --: not run.",
        "@{}l cc cc cc@{}", r" & \multicolumn{2}{c}{GPT-4.1 mini} & \multicolumn{2}{c}{Gemini 2.5 Flash} & \multicolumn{2}{c}{Claude Haiku 4.5} \\ Module & Q1 & Q4 & Q1 & Q4 & Q1 & Q4", rows)
    # Set 4b: Q2
    rows = []
    for c in CONDS:
        q = b["Q2"][c]
        rows.append(f"{CTEX[c]} & ${q['runs']}$ & ${q['fails']}$ & ${q['fails_with_sf']}$ & ${q['passes']}$ & "
                    f"${q['passes_sf_before_pass']}$ & ${len(q['passes_sf_before_pass_where_baseline_0of3'])}$ & "
                    f"{('$' + str(q['escalated']) + '$') if 'escalated' in q else '--'}")
    tab("tab:s-set4b-q2", r"Set~4b, Q2: the interpreter on floor failures. Passes with a directive delivered before the passing iteration, and those in cells whose baseline was $0/3$ (each traced; none attributable to the directive).",
        "@{}l ccccccc@{}", "Condition & runs & fails & fails w/ sf & passes & directive before pass & ...baseline 0/3 & escalated", rows)
    # Set 4b: Q3
    rows = []
    for scope in ["pooled"] + models:
        cells = []
        for c in CONDS[1:]:
            k = b["Q3"].get(f"{scope}|{c}")
            cells.append(f"{_pts(k['mean_pts'])} [{_pts(k['lo'])}, {_pts(k['hi'])}], ${k['cells']}$, $p{{=}}{k['p']:.3f}$" if k else "--")
        rows.append(SHORT.get(scope, "Pooled") + " & " + " & ".join(cells))
    tab("tab:s-set4b-q3", r"Set~4b, Q3: condition minus baseline on cells whose baseline was below $3/3$: points, cell bootstrap $95\%$ CI, cells, sign-flip $p$.",
        "@{}l ccc@{}", "Scope & " + " & ".join(CTEX[c] for c in CONDS[1:]), rows)
    path = os.path.join(REPO, "paper", "tables_set4.tex")
    open(path, "w", encoding="utf-8", newline="\n").write("\n".join(out) + "\n")
    print(f"wrote {path}")


if __name__ == "__main__":
    main()
