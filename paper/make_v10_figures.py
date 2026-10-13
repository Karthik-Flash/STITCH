"""Figures for paper v10 (paper/overleaf/main.tex and supplement.tex), all in the shared style of figstyle.py.
  python -B paper/make_v10_figures.py          (the Set 4b heat map comes from phase2/frontier/make_numbers_set4.py)
Each panel is drawn at its final printed width and written to paper/overleaf/figures/<name>.pdf. Every value is read
from a generated evidence file, never typed by hand:
  PHASE3 = phase3/evidence/phase3_final/PHASE3_FINAL.md (pooled and stratum tables, cumulative-by-call, composition)
  PAPERN = phase3/evidence/phase3_final/PAPER_NUMBERS.md (latch-bearing tasks; per-model rows)
  Set 1  = phase2/set1_analysis/tier_pass_rates.csv, cost_by_tier.csv, cost_summary.csv
  Ladder = phase2/set3_analysis builders (Twin, Set 1, Set 3 master logs) and set4_analysis.json (API pass rates)
  Twin   = phase2/twin_analysis_SET2/_data.py (Twin master log, module tiers)
  API P3 = phase2/frontier/evidence/p3_ladder_signoff.json (table12)
"""
import csv
import importlib.util
import json
import os
import re
import sys

sys.dont_write_bytecode = True
HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HERE)
sys.path.insert(0, HERE)
import figstyle as fs  # noqa: E402
import numpy as np  # noqa: E402
from matplotlib.patches import Patch  # noqa: E402
from statsmodels.stats.proportion import confint_proportions_2indep, proportion_confint  # noqa: E402

OUT = os.path.join(HERE, "overleaf", "figures")
P2 = os.path.join(REPO, "phase2")
P3 = os.path.join(REPO, "phase3", "evidence", "phase3_final")
API = [("gpt-4.1-mini-2025-04-14", "GPT-4.1 mini"), ("gemini-2.5-flash", "Gemini 2.5 Flash"),
       ("claude-haiku-4-5-20251001", "Claude Haiku 4.5")]


def _load(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    sys.path.insert(0, os.path.dirname(path))
    spec.loader.exec_module(mod)
    return mod


def _md_table(text, heading):
    """Rows of the first markdown table after the line equal to `heading`."""
    lines = text.splitlines()
    i = next(k for k, l in enumerate(lines) if l.strip() == heading)
    rows, hdr = [], None
    for l in lines[i + 1:]:
        if l.startswith("|"):
            cells = [c.strip() for c in l.strip("|").split("|")]
            if hdr is None:
                hdr = cells
            elif not set(l) <= set("|-: "):
                rows.append(dict(zip(hdr, cells)))
        elif rows:
            break
    return rows


def _count(cell):
    k, n = re.match(r"(\d+)/(\d+)", cell).groups()
    return int(k), int(n)


def _wilson(k, n):
    lo, hi = proportion_confint(k, n, method="wilson")
    return 100 * k / n, 100 * lo, 100 * hi


def _err(r):
    """Error-bar lengths from (value, lo, hi) triples, clipped at 0 against rounding at 0% and 100%."""
    return [[max(0, v - lo) for v, lo, _ in r], [max(0, hi - v) for v, _, hi in r]]


PHASE3 = open(os.path.join(P3, "PHASE3_FINAL.md"), encoding="utf-8").read()
PAPERN = open(os.path.join(P3, "PAPER_NUMBERS.md"), encoding="utf-8").read()


def labelled_hbars(ax, conds, ks, n, xmax=100):
    """One bar per condition, the condition name above its bar, the value at its end, Wilson 95% CI."""
    y = np.arange(len(conds))[::-1].astype(float)
    r = [_wilson(k, n) for k in ks]
    ax.barh(y, [v for v, _, _ in r], 0.42, color=[fs.COND[c] for c in conds], edgecolor="none", zorder=2,
            xerr=_err(r), error_kw=fs.ERR)
    for yy, c, (v, _, hi) in zip(y, conds, r):
        ax.text(0, yy + 0.26, fs.LABEL[c], va="bottom", ha="left", fontsize=7)
        ax.text(hi + 2, yy, f"{v:.0f}%", va="center", ha="left", fontsize=7.5, fontweight="bold" if c == "baseline" else None)
    ax.set_ylim(-0.45, len(conds) - 0.2)
    ax.set_yticks([])
    ax.set_xlim(0, xmax)
    ax.set_xticks([0, 25, 50, 75, 100])
    ax.spines["left"].set_visible(False)
    fs.style(ax, "x")


# ---------------------------------------------------------------- F1 teaser
def teaser():
    pooled = {r["condition"]: r for r in _md_table(PHASE3, "## Pooled, six original models (headline; qwen2.5-coder:32b reported separately below)")}
    fig, ax = fs.figure(fs.THIRD, 1.95)
    labelled_hbars(ax, fs.P3_ORDER, [_count(pooled[c]["signed_off_defective"])[0] for c in fs.P3_ORDER], 198)
    ax.set_xlabel("signed off defective (% of 198 runs)")
    fs.save(fig, os.path.join(OUT, "fig_teaser_a"))

    line = next(l for l in PAPERN.splitlines() if "latch-bearing tasks, runs ending latch-free" in l)
    latch = {c: _count(v) for c, v in re.findall(r"(\w+) (\d+/\d+)", line.split(":", 1)[1])}
    fig, ax = fs.figure(fs.THIRD, 1.95)
    labelled_hbars(ax, fs.P3_ORDER, [latch[c][0] for c in fs.P3_ORDER], latch["baseline"][1])
    ax.set_xlabel(f"latch-free, synthesises (% of {latch['baseline'][1]} runs)")
    fs.save(fig, os.path.join(OUT, "fig_teaser_b"))

    comp = {r[next(iter(r))]: r for r in _md_table(PHASE3, "### Composition (top-level synthesis pass)")}
    designs = [("mesh2x2", "2×2 mesh"), ("mesh3x3", "3×3 mesh"), ("mpsoc", "MPSoC")]
    conds = ["baseline", "sem_adv_v3", "sem_esc_restart_v3"]
    fig, ax = fs.figure(fs.THIRD, 1.95)
    w = 0.26
    for j, c in enumerate(conds):
        ks = [_count(comp[d][c])[0] for d, _ in designs]
        xs = np.arange(len(designs)) + (j - 1) * w
        ax.bar(xs, ks, w * 0.92, color=fs.COND[c], zorder=2, label=fs.LABEL[c])
        for x, k in zip(xs, ks):
            if k:
                ax.text(x, k + 0.4, str(k), ha="center", va="bottom", fontsize=7)
            else:
                ax.text(x, 0.5, "aborts", rotation=90, ha="center", va="bottom", fontsize=6.8, color=fs.MUTED)
    ax.set_xticks(range(len(designs)))
    ax.set_xticklabels([d for _, d in designs])
    ax.set_ylim(0, 24.5)
    ax.set_yticks([0, 6, 12, 18])
    ax.set_ylabel("top-level synthesis passes (of 18)")
    ax.legend(loc="upper left", ncol=1, fontsize=7, bbox_to_anchor=(0.0, 1.04), borderaxespad=0, handleheight=0.8,
              labelspacing=0.25)
    fs.style(ax)
    fs.save(fig, os.path.join(OUT, "fig_teaser_c"))


# ---------------------------------------------------------------- F5 + F9: the latch defect at scale, composition
def compose():
    res = open(os.path.join(REPO, "phase3", "evidence", "phase3_run", "PHASE3_RESULTS.md"), encoding="utf-8").read()
    bounds = {r["design"]: r for r in _md_table(res, "### T7. Composition against the bounds (Q6)")}
    designs = [("mesh2x2", "2×2 mesh\n4 routers"), ("mesh3x3", "3×3 mesh\n9 routers"), ("mpsoc", "MPSoC\ntop")]
    cells = lambda s: int(re.search(r"(\d+) cells", s).group(1))  # noqa: E731
    fig, ax = fs.figure(fs.HALF, 2.15)
    w = 0.36
    for j, (col, lab, colour) in enumerate((("unrepaired reference", "as written (synthesis aborts)", "#4d4c48"),
                                            ("all golden repairs", "task leaves repaired", "#c9c8c3"))):
        v = [cells(bounds[d][col]) for d, _ in designs]
        xs = np.arange(3) + (j - 0.5) * w
        ax.bar(xs, v, w * 0.92, color=colour, label=lab, zorder=2)
        for x, y in zip(xs, v):
            ax.text(x, y + 90, f"{y:,}", ha="center", va="bottom", fontsize=7)
    ax.set_xticks(range(3))
    ax.set_xticklabels([d for _, d in designs])
    ax.set_ylim(0, 7300)
    ax.set_ylabel("latch cells after synthesis")
    ax.legend(loc="lower center", bbox_to_anchor=(0.5, 1.0), ncol=1, borderaxespad=0.2, labelspacing=0.2)
    fs.style(ax)
    fs.save(fig, os.path.join(OUT, "fig_latch_scale"))

    comp = {r[next(iter(r))]: r for r in _md_table(PHASE3, "### Composition (top-level synthesis pass)")}
    fig, ax = fs.figure(fs.HALF, 2.15)
    w = 0.135
    for j, c in enumerate(fs.P3_ORDER):
        ks = [_count(comp[d][c])[0] for d, _ in designs]
        xs = np.arange(3) + (j - 2.5) * w
        ax.bar(xs, ks, w * 0.9, color=fs.COND[c], label=fs.LABEL[c], zorder=2)
        for x, k in zip(xs, ks):
            if not k:
                ax.text(x, 0.3, "0", ha="center", va="bottom", fontsize=7)
    ax.set_xticks(range(3))
    ax.set_xticklabels([d.replace("\n", " ") if d.startswith("MPSoC") else d.split("\n")[0] for _, d in designs])
    ax.set_ylim(0, 18.5)
    ax.set_yticks([0, 6, 12, 18])
    ax.set_ylabel("top-level synthesis passes (of 18)")
    ax.legend(loc="lower center", bbox_to_anchor=(0.5, 1.0), ncol=3, fontsize=7, borderaxespad=0.2, labelspacing=0.2,
              columnspacing=0.7)
    fs.style(ax)
    fs.save(fig, os.path.join(OUT, "fig_compose"))


# ---------------------------------------------------------------- F4 Phase 3
def p3():
    sil = {r["condition"]: _count(r["**signoff_clean**"]) for r in _md_table(PHASE3, "### sim-silent tasks")}
    vis = {r["condition"]: _count(r["**signoff_clean**"]) for r in _md_table(PHASE3, "### sim-visible tasks")}
    fig, ax = fs.figure(fs.HALF, 2.35)
    order = fs.P3_ORDER
    y = np.arange(len(order))[::-1].astype(float)
    for j, (d, hatch) in enumerate(((sil, None), (vis, "/////"))):
        r = [_wilson(*d[c]) for c in order]
        yy = y + (0.19 if j == 0 else -0.19)
        ax.barh(yy, [v for v, _, _ in r], 0.36, color=[fs.COND[c] for c in order], hatch=hatch, edgecolor="#ffffff",
                linewidth=0, zorder=2, xerr=_err(r), error_kw=fs.ERR)
        for k, (v, _, hi) in zip(yy, r):
            ax.text(hi + 1.5, k, f"{v:.0f}", va="center", fontsize=6.8)
    ax.set_yticks(y)
    ax.set_yticklabels([fs.LABEL[c] for c in order])
    ax.set_xlim(0, 105)
    ax.set_xticks([0, 25, 50, 75, 100])
    ax.set_xlabel("sign-off clean (%), Wilson 95% CI")
    ax.legend(handles=[Patch(facecolor=fs.MUTED, label=f"sim-silent (n={sil['baseline'][1]})"),
                       Patch(facecolor=fs.MUTED, hatch="/////", edgecolor="#ffffff", label=f"sim-visible (n={vis['baseline'][1]})")],
              loc="lower center", bbox_to_anchor=(0.4, 1.0), ncol=2, borderaxespad=0.2)
    fs.style(ax, "x")
    fs.save(fig, os.path.join(OUT, "fig_p3_stratum"))

    cum = {r["condition"]: [100 * _count(r[f"by call {i}"])[0] / _count(r[f"by call {i}"])[1] for i in range(7)]
           for r in _md_table(PHASE3, "### Cumulative signoff_clean by LLM call (six models)")}
    fig, ax = fs.figure(fs.HALF, 2.35)
    for c in order:
        ax.plot(range(7), cum[c], color=fs.COND[c], linewidth=1.5, marker="o", markersize=2.5, label=fs.LABEL[c],
                zorder=3 if c == "sem_esc_restart_v3" else 2)
    ends, placed = sorted((cum[c][-1], c) for c in order), []
    for v, c in ends:                                   # end labels, nudged apart (min 6 points)
        placed.append(max(v, placed[-1] + 6) if placed else v)
    for (v, c), yy in zip(ends, placed):
        ax.text(6.18, yy, f"{v:.0f}", va="center", fontsize=6.8)
    ax.set_xlim(0, 6.6)
    ax.set_ylim(0, 80)
    ax.set_xticks(range(7))
    ax.set_xlabel("model calls used")
    ax.set_ylabel("sign-off clean so far (%)")
    ax.legend(loc="lower center", bbox_to_anchor=(0.45, 1.0), ncol=2, fontsize=7, borderaxespad=0.2, labelspacing=0.2)
    fs.style(ax)
    fs.save(fig, os.path.join(OUT, "fig_p3_bycall"))


# ---------------------------------------------------------------- F6 Set 1
def set1():
    tiers, conds = ["ceiling", "recoverable", "floor"], ["baseline", "sem_adv", "sem_escalate", "sem_escalate_restart"]
    pr = {(r["tier"], r["condition"]): r for r in csv.DictReader(open(os.path.join(P2, "set1_analysis", "tier_pass_rates.csv")))}
    co = {(r["tier"], r["condition"]): r for r in csv.DictReader(open(os.path.join(P2, "set1_analysis", "cost_by_tier.csv")))}
    fig, ax = fs.figure(fs.HALF, 2.15)
    w = 0.2
    for j, c in enumerate(conds):
        xs = np.arange(3) + (j - 1.5) * w
        r = [100 * float(pr[(t, c)]["pass_rate"]) for t in tiers]
        lo = [r[i] - 100 * float(pr[(t, c)]["wilson_ci_lo"]) for i, t in enumerate(tiers)]
        hi = [100 * float(pr[(t, c)]["wilson_ci_hi"]) - r[i] for i, t in enumerate(tiers)]
        ax.bar(xs, r, w * 0.92, color=fs.COND[c], label=fs.LABEL[c], zorder=2, yerr=[lo, hi], error_kw=fs.ERR)
    ax.set_xticks(range(3))
    ax.set_xticklabels([f"{t}\n({pr[(t, 'baseline')]['n_modules']} modules)" for t in tiers])
    ax.set_ylabel("pass rate (%), Wilson 95% CI")
    ax.set_ylim(0, 100)
    ax.legend(loc="lower center", bbox_to_anchor=(0.5, 1.0), ncol=2, borderaxespad=0.2, labelspacing=0.2)
    fs.style(ax)
    fs.save(fig, os.path.join(OUT, "fig_set1_tiers"))

    fig, ax = fs.figure(fs.HALF, 2.15)
    w = 0.26
    for j, c in enumerate(conds[1:]):
        xs = np.arange(3) + (j - 1) * w
        ax.bar(xs, [float(co[(t, c)]["mean_tool_calls_per_run"]) for t in tiers], w * 0.92, color=fs.COND[c],
               label=fs.LABEL[c], zorder=2)
    for i, t in enumerate(tiers):
        adv, esc = (float(co[(t, c)]["mean_tool_calls_per_run"]) for c in ("sem_adv", "sem_escalate"))
        ax.text(i, max(adv, esc) + 0.3, f"−{100 * (adv - esc) / adv:.1f}%", ha="center", fontsize=7)
    ax.set_xticks(range(3))
    ax.set_xticklabels(tiers)
    ax.set_ylabel("Verilator + Yosys calls per run")
    ax.set_ylim(0, 9)
    ax.legend(loc="lower center", bbox_to_anchor=(0.5, 1.0), ncol=3, borderaxespad=0.2)
    fs.style(ax)
    fs.save(fig, os.path.join(OUT, "fig_set1_calls"))


# ---------------------------------------------------------------- F7 ladder and deficit
def ladder():
    s3 = os.path.join(P2, "set3_analysis")
    lad = _load(os.path.join(s3, "fig_capability_ladder_full.py"), "ladder_full").build()
    har = _load(os.path.join(s3, "harmful_regime_by_capability.py"), "harm").build()
    a4 = json.load(open(os.path.join(P2, "results", "set4_api", "analysis", "set4_analysis.json"), encoding="utf-8"))
    rows = [dict(r) for r in lad]
    for mid, name in API:
        p = a4["pass_rates"][f"{mid}|baseline"]
        rows.append({"label": name, "run": "api", "rate": p["rate"], "ci_lo": p["lo"], "ci_hi": p["hi"]})
    rows.sort(key=lambda r: r["rate"])
    shade = {"twin": "#c9c8c3", "set3": fs.COND["baseline"], "api": "#4d4c48"}
    fig, ax = fs.figure(fs.HALF, 2.75)
    y = np.arange(len(rows))
    ax.barh(y, [100 * r["rate"] for r in rows], 0.68, color=[shade[r["run"]] for r in rows], zorder=2,
            hatch=["////" if r["run"] == "twin" else None for r in rows], edgecolor="#ffffff", linewidth=0,
            xerr=[[100 * (r["rate"] - r["ci_lo"]) for r in rows], [100 * (r["ci_hi"] - r["rate"]) for r in rows]],
            error_kw=fs.ERR)
    ax.set_yticks(y)
    ax.set_yticklabels([r["label"] for r in rows])
    ax.set_xlim(0, 100)
    ax.set_xlabel("baseline pass rate (%), Wilson 95% CI")
    ax.legend(handles=[Patch(facecolor=shade["twin"], hatch="////", edgecolor="#ffffff", label="Twin, T=0.5"),
                       Patch(facecolor=shade["set3"], label="Set 3, T=0.1"),
                       Patch(facecolor=shade["api"], label="API, T=0.1")],
              loc="lower center", bbox_to_anchor=(0.3, 1.0), ncol=3, borderaxespad=0.2, fontsize=7)
    fs.style(ax, "x")
    fs.save(fig, os.path.join(OUT, "fig_ladder"))

    drows = [dict(r) for r in har]
    for mid, name in API:
        bp, ap = a4["pass_rates"][f"{mid}|baseline"], a4["pass_rates"][f"{mid}|sem_adv"]
        lo, hi = confint_proportions_2indep(ap["k"], ap["n"], bp["k"], bp["n"], method="newcomb", compare="diff")
        drows.append({"model": name, "run": "api", "baseline_rate": bp["rate"],
                      "delta_pp": 100 * (ap["rate"] - bp["rate"]), "delta_ci_lo_pp": 100 * lo, "delta_ci_hi_pp": 100 * hi})
    drows.sort(key=lambda r: r["baseline_rate"])
    tag = {"set1": "Set 1", "set3": "Set 3", "api": "API"}
    fig, ax = fs.figure(fs.HALF, 2.75)
    y = np.arange(len(drows))
    ax.axvline(0, color=fs.INK, linewidth=0.7, zorder=3)
    ax.barh(y, [r["delta_pp"] for r in drows], 0.62, color=fs.COND["sem_adv"], zorder=2,
            xerr=[[r["delta_pp"] - r["delta_ci_lo_pp"] for r in drows], [r["delta_ci_hi_pp"] - r["delta_pp"] for r in drows]],
            error_kw=fs.ERR)
    for i, r in enumerate(drows):
        ax.text(1.0, i, f"{r['delta_pp']:+.1f}".replace("-", "−"), va="center", ha="left", fontsize=7,
                transform=ax.get_yaxis_transform())
    ax.set_yticks(y)
    ax.set_yticklabels([f"{r['model']} ({tag[r['run']]})" for r in drows])
    ax.set_xlim(-30, 30)
    ax.set_xticks([-30, -15, 0, 15, 30])
    ax.set_xlabel("sem_adv − baseline (points), 95% CI")
    fs.style(ax, "x")
    fs.save(fig, os.path.join(OUT, "fig_deficit"))


# ---------------------------------------------------------------- supplement figures
def supp_twin():
    tw = _load(os.path.join(P2, "twin_analysis_SET2", "_data.py"), "twin_data")
    counts, cats = tw.pivot_pass_counts(tw.load_master_log()), tw.load_categories()
    mods = sorted((m for m, i in cats.items() if i["difficulty_tier"] == "recoverable"),
                  key=lambda m: (cats[m]["functional_class"], m))
    pairs = [("twin_a", ("rtlcoder-deepseek-v1.1", "shared"), ("deepseek-coder:6.7b", "shared"),
              "RTLCoder, shared prompt", "deepseek-coder, shared prompt"),
             ("twin_b", ("rtlcoder-deepseek-v1.1", "native"), ("rtlcoder-deepseek-v1.1", "shared"),
              "RTLCoder, native prompt", "RTLCoder, shared prompt")]
    for name, ca, cb, la, lb in pairs:
        fig, ax = fs.figure(fs.HALF, 3.3)
        y = np.arange(len(mods))[::-1]
        for j, (c, lab, col) in enumerate(((ca, la, "#4d4c48"), (cb, lb, "#c9c8c3"))):
            ax.barh(y + (0.19 if j == 0 else -0.19), [counts.get((m,) + c, 0) for m in mods], 0.36, color=col,
                    label=lab, zorder=2)
        ax.set_yticks(y)
        ax.set_yticklabels(mods, fontsize=7)
        ax.set_xticks([0, 1, 2, 3])
        ax.set_xlim(0, 3.1)
        ax.set_xlabel("passes (of 3)")
        ax.legend(loc="lower center", bbox_to_anchor=(0.3, 1.0), ncol=1, borderaxespad=0.2)
        fs.style(ax, "x")
        fs.save(fig, os.path.join(OUT, f"fig_s_{name}"))


def supp_set1_cost():
    rows = {r["condition"]: r for r in csv.DictReader(open(os.path.join(P2, "set1_analysis", "cost_summary.csv")))}
    conds = ["baseline", "sem_adv", "sem_escalate", "sem_escalate_restart"]
    for name, key, lab, scale in (("fig_s_set1_calls", "mean_tool_calls_per_run", "Verilator + Yosys calls per run", 1),
                                  ("fig_s_set1_pass", "pass_rate", "pass rate, all 42 modules (%)", 100)):
        fig, ax = fs.figure(fs.HALF, 1.9)
        v = [scale * float(rows[c][key]) for c in conds]
        ax.bar(range(4), v, 0.6, color=[fs.COND[c] for c in conds], zorder=2)
        for i, x in enumerate(v):
            ax.text(i, x + max(v) * 0.02, f"{x:.2f}" if scale == 1 else f"{x:.1f}", ha="center", va="bottom", fontsize=7)
        ax.set_xticks(range(4))
        ax.set_xticklabels([fs.LABEL[c] for c in conds], fontsize=7)
        ax.set_ylabel(lab)
        ax.set_ylim(0, max(v) * 1.18)
        fs.style(ax)
        fs.save(fig, os.path.join(OUT, name))


def supp_p3_models():
    names = [("llama3.2:3b", "llama3.2:3b"), ("gemma3:4b", "gemma3:4b"), ("deepseek-coder:6.7b", "deepseek-coder:6.7b"),
             ("qwen2.5-coder:7b", "qwen2.5-coder:7b"), ("llama3.1:latest", "llama3.1:8b"), ("qwen2.5-coder:14b", "qwen2.5-coder:14b")]
    conds = ["baseline_gate", "raw_adv", "sem_adv_v3", "sem_esc_restart_v3"]
    per = {}
    for l in PAPERN.splitlines():
        m = re.match(r"- per model (\S+): signoff_clean of 33: (.*?); sim-visible", l)
        if m:
            per[m.group(1)] = {c: int(k) for c, k in re.findall(r"(\w+) (\d+)", m.group(2))}
    fig, ax = fs.figure(fs.FULL, 2.1)
    w = 0.2
    for j, c in enumerate(conds):
        r = [_wilson(per[k][c], 33) for k, _ in names]
        xs = np.arange(len(names)) + (j - 1.5) * w
        ax.bar(xs, [v for v, _, _ in r], w * 0.92, color=fs.COND[c], label=fs.LABEL[c], zorder=2,
               yerr=_err(r), error_kw=fs.ERR)
    ax.set_xticks(range(len(names)))
    ax.set_xticklabels([n for _, n in names])
    ax.set_ylim(0, 105)
    ax.set_ylabel("sign-off clean (%), of 33")
    ax.legend(loc="lower center", bbox_to_anchor=(0.5, 1.0), ncol=4, borderaxespad=0.2)
    fs.style(ax)
    fs.save(fig, os.path.join(OUT, "fig_s_p3_models"))


def supp_p3_api():
    t12 = json.load(open(os.path.join(P2, "frontier", "evidence", "p3_ladder_signoff.json"), encoding="utf-8"))["table12"]
    fig, ax = fs.figure(fs.FULL, 2.0)
    w = 0.13
    for j, c in enumerate(fs.P3_ORDER):
        ks = [t12[f"{mid}|{c}"][0] for mid, _ in API]
        xs = np.arange(3) + (j - 2.5) * w
        ax.bar(xs, ks, w * 0.92, color=fs.COND[c], label=fs.LABEL[c], zorder=2)
        for x, k in zip(xs, ks):
            ax.text(x, k + 0.4, str(k), ha="center", va="bottom", fontsize=6.5)
    ax.set_xticks(range(3))
    ax.set_xticklabels([n for _, n in API])
    ax.set_ylim(0, 38)
    ax.set_yticks([0, 11, 22, 33])
    ax.set_ylabel("sign-off clean (of 33)")
    ax.legend(loc="lower center", bbox_to_anchor=(0.5, 1.0), ncol=6, borderaxespad=0.2)
    fs.style(ax)
    fs.save(fig, os.path.join(OUT, "fig_s_p3_api"))


if __name__ == "__main__":
    teaser()
    compose()
    p3()
    set1()
    ladder()
    supp_twin()
    supp_set1_cost()
    supp_p3_models()
    supp_p3_api()
