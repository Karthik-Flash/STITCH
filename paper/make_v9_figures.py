"""Figures for STITCH_EXT_v9.tex (new files in paper/figures/; nothing else is written).
  python -B paper/make_v9_figures.py
Each panel reads a generated evidence file, never a hand-typed number:
  fig_v9_set1_tiers.pdf      phase2/set1_analysis/tier_pass_rates.csv, cost_by_tier.csv
  fig_v9_ladder_deficit.pdf  phase2/set3_analysis builders (Twin, Set 1, Set 3 master logs) and
                             phase2/results/set4_api/analysis/set4_analysis.json (API pass rates)
  fig_v9_p3.pdf              phase3/evidence/phase3_final/PHASE3_FINAL.md (stratum tables, cumulative-by-call table)
Colours: the validated categorical palette (dataviz reference instance), light mode, assigned in fixed order.
"""
import csv
import importlib.util
import json
import os
import re
import sys

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
from statsmodels.stats.proportion import confint_proportions_2indep, proportion_confint  # noqa: E402

sys.dont_write_bytecode = True
HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HERE)
OUT = os.path.join(HERE, "figures")
P2 = os.path.join(REPO, "phase2")
INK, MUTED, GRID, SURF = "#0b0b0b", "#52514e", "#e4e3df", "#ffffff"
C = ["#2a78d6", "#eb6834", "#1baf7a", "#eda100", "#e87ba4", "#008300"]   # categorical slots 1-6
GREY = "#8f8e89"
plt.rcParams.update({"font.size": 8.5, "axes.titlesize": 9, "axes.labelsize": 8.5, "legend.fontsize": 7.8,
                     "xtick.labelsize": 7.8, "ytick.labelsize": 7.8, "axes.edgecolor": MUTED,
                     "xtick.color": MUTED, "ytick.color": MUTED, "axes.labelcolor": INK, "pdf.fonttype": 42,
                     "font.family": "DejaVu Sans"})


def _load(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    sys.path.insert(0, os.path.dirname(path))
    spec.loader.exec_module(mod)
    return mod


def _style(ax, grid="y"):
    for s in ("top", "right"):
        ax.spines[s].set_visible(False)
    ax.grid(axis=grid, color=GRID, linewidth=0.6, zorder=0)
    ax.set_axisbelow(True)


def save(fig, name):
    for ext in ("pdf", "png"):
        fig.savefig(os.path.join(OUT, f"{name}.{ext}"), dpi=300, bbox_inches="tight", pad_inches=0.02)
    plt.close(fig)
    print("wrote", os.path.join(OUT, name + ".{pdf,png}"))


def fig_set1():
    tiers, conds = ["ceiling", "recoverable", "floor"], ["baseline", "sem_adv", "sem_escalate", "sem_escalate_restart"]
    lab = {"baseline": "baseline", "sem_adv": "sem_adv", "sem_escalate": "sem_escalate",
           "sem_escalate_restart": "sem_esc_restart"}
    pr = {(r["tier"], r["condition"]): r for r in csv.DictReader(open(os.path.join(P2, "set1_analysis", "tier_pass_rates.csv")))}
    co = {(r["tier"], r["condition"]): r for r in csv.DictReader(open(os.path.join(P2, "set1_analysis", "cost_by_tier.csv")))}
    fig, (a, b) = plt.subplots(1, 2, figsize=(6.6, 2.55), gridspec_kw={"width_ratios": [1.25, 1]})
    w = 0.2
    for j, c in enumerate(conds):
        xs = np.arange(3) + (j - 1.5) * w
        r = [float(pr[(t, c)]["pass_rate"]) * 100 for t in tiers]
        lo = [r[i] - float(pr[(t, c)]["wilson_ci_lo"]) * 100 for i, t in enumerate(tiers)]
        hi = [float(pr[(t, c)]["wilson_ci_hi"]) * 100 - r[i] for i, t in enumerate(tiers)]
        a.bar(xs, r, w, color=C[j], edgecolor=SURF, linewidth=0.8, label=lab[c], zorder=2,
              yerr=[lo, hi], error_kw={"elinewidth": 0.7, "capsize": 1.5, "ecolor": MUTED})
    nm = {t: pr[(t, "baseline")]["n_modules"] for t in tiers}
    a.set_xticks(range(3))
    a.set_xticklabels([f"{t}\n({nm[t]} modules)" for t in tiers])
    a.set_ylabel("pass rate (%), Wilson 95% CI")
    a.set_ylim(0, 100)
    a.set_title("(a) Set 1 pass rate by tier and condition", loc="left")
    a.legend(frameon=False, ncol=2, loc="upper right", handlelength=1.0, columnspacing=0.8)
    _style(a)
    for j, c in enumerate(conds[1:], start=1):
        xs = np.arange(3) + (j - 2) * 0.26
        v = [float(co[(t, c)]["mean_tool_calls_per_run"]) for t in tiers]
        b.bar(xs, v, 0.26, color=C[j], edgecolor=SURF, linewidth=0.8, zorder=2)
    for i, t in enumerate(tiers):
        adv, esc = float(co[(t, "sem_adv")]["mean_tool_calls_per_run"]), float(co[(t, "sem_escalate")]["mean_tool_calls_per_run"])
        b.text(i, max(adv, esc) + 0.35, f"$-${100 * (adv - esc) / adv:.1f}%", ha="center", fontsize=7.8, color=INK)
    b.set_xticks(range(3))
    b.set_xticklabels(tiers)
    b.set_ylabel("calls per run")
    b.set_ylim(0, 9)
    b.set_title("(b) Verilator + Yosys calls per run", loc="left")
    _style(b)
    fig.tight_layout(w_pad=1.2)
    save(fig, "fig_v9_set1_tiers")


def fig_ladder_deficit():
    s3 = os.path.join(P2, "set3_analysis")
    lad = _load(os.path.join(s3, "fig_capability_ladder_full.py"), "ladder_full").build()
    har = _load(os.path.join(s3, "harmful_regime_by_capability.py"), "harm").build()
    a4 = json.load(open(os.path.join(P2, "results", "set4_api", "analysis", "set4_analysis.json"), encoding="utf-8"))
    api = [("gpt-4.1-mini-2025-04-14", "GPT-4.1 mini"), ("gemini-2.5-flash", "Gemini 2.5 Flash"),
           ("claude-haiku-4-5-20251001", "Claude Haiku 4.5")]
    rows = [dict(r) for r in lad]
    for mid, name in api:
        p = a4["pass_rates"][f"{mid}|baseline"]
        rows.append({"label": name, "run": "api", "n_pass": p["k"], "n_total": p["n"], "rate": p["rate"],
                     "ci_lo": p["lo"], "ci_hi": p["hi"]})
    rows.sort(key=lambda r: r["rate"])
    col = {"twin": GREY, "set3": C[0], "api": C[2]}
    fig, (a, b) = plt.subplots(1, 2, figsize=(6.6, 3.5))
    y = np.arange(len(rows))
    a.barh(y, [100 * r["rate"] for r in rows], 0.7, color=[col[r["run"]] for r in rows], edgecolor=SURF, zorder=2,
           xerr=[[100 * (r["rate"] - r["ci_lo"]) for r in rows], [100 * (r["ci_hi"] - r["rate"]) for r in rows]],
           error_kw={"elinewidth": 0.7, "capsize": 1.5, "ecolor": MUTED})
    a.set_yticks(y)
    a.set_yticklabels([r["label"] for r in rows])
    a.set_xlim(0, 100)
    a.set_xlabel("baseline pass rate, recoverable band (%)")
    a.set_title("(a) capability ladder", loc="left")
    from matplotlib.patches import Patch
    a.legend(handles=[Patch(color=GREY, label="Twin, T=0.5 (ordinal only)"), Patch(color=C[0], label="Set 3, T=0.1"),
                      Patch(color=C[2], label="API, non-reasoning, T=0.1")], frameon=False, loc="upper center",
             bbox_to_anchor=(0.42, -0.2), ncol=2, columnspacing=0.8, handlelength=1.0)
    _style(a, "x")
    drows = [dict(r) for r in har]
    for mid, name in api:
        bp, ap = a4["pass_rates"][f"{mid}|baseline"], a4["pass_rates"][f"{mid}|sem_adv"]
        lo, hi = confint_proportions_2indep(ap["k"], ap["n"], bp["k"], bp["n"], method="newcomb", compare="diff")
        drows.append({"model": name, "run": "api", "baseline_rate": bp["rate"],
                      "delta_pp": 100 * (ap["rate"] - bp["rate"]), "delta_ci_lo_pp": 100 * lo, "delta_ci_hi_pp": 100 * hi})
    drows.sort(key=lambda r: r["baseline_rate"])
    dcol = {"set1": C[1], "set3": C[0], "api": C[2]}
    y = np.arange(len(drows))
    b.axvline(0, color=INK, linewidth=0.8, zorder=3)
    b.barh(y, [r["delta_pp"] for r in drows], 0.7, color=[dcol[r["run"]] for r in drows], edgecolor=SURF, zorder=2,
           xerr=[[r["delta_pp"] - r["delta_ci_lo_pp"] for r in drows], [r["delta_ci_hi_pp"] - r["delta_pp"] for r in drows]],
           error_kw={"elinewidth": 0.7, "capsize": 1.5, "ecolor": MUTED})
    for i, r in enumerate(drows):
        b.text(1.01, i, f"{r['delta_pp']:+.1f}".replace("-", "−"), va="center", ha="left", fontsize=7.4, color=INK,
               transform=b.get_yaxis_transform())
    b.set_yticks(y)
    b.set_yticklabels([r["model"] for r in drows])
    b.set_xlim(-30, 30)
    b.set_xlabel("sem_adv $-$ baseline (points), Newcombe 95% CI")
    b.set_title("(b) always-on deficit", loc="left")
    b.legend(handles=[Patch(color=C[1], label="Set 1, 4B-8B"), Patch(color=C[0], label="Set 3, 14B-32B"),
                      Patch(color=C[2], label="API, non-reasoning")], frameon=False, loc="upper center",
             bbox_to_anchor=(0.42, -0.2), ncol=2, columnspacing=0.8, handlelength=1.0)
    _style(b, "x")
    fig.tight_layout(w_pad=1.0)
    save(fig, "fig_v9_ladder_deficit")


def _md_table(text, heading):
    """Rows of the first markdown table after a heading line that matches `heading` exactly."""
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


def fig_p3():
    md = open(os.path.join(REPO, "phase3", "evidence", "phase3_final", "PHASE3_FINAL.md"), encoding="utf-8").read()
    order = ["baseline", "baseline_gate", "raw_adv", "sem_adv_v2", "sem_adv_v3", "sem_esc_restart_v3"]
    lab = {"baseline": "baseline (sim only)", "baseline_gate": "baseline_gate (alarm)", "raw_adv": "raw_adv",
           "sem_adv_v2": "sem_adv (v2)", "sem_adv_v3": "sem_adv (v3)", "sem_esc_restart_v3": "sem_esc_restart (v3)"}
    sil = {r["condition"]: _count(r["**signoff_clean**"]) for r in _md_table(md, "### sim-silent tasks")}
    vis = {r["condition"]: _count(r["**signoff_clean**"]) for r in _md_table(md, "### sim-visible tasks")}
    cum = {r["condition"]: [_count(r[f"by call {i}"])[0] / _count(r[f"by call {i}"])[1] * 100 for i in range(7)]
           for r in _md_table(md, "### Cumulative signoff_clean by LLM call (six models)")}
    fig, (a, b) = plt.subplots(1, 2, figsize=(6.6, 3.15), gridspec_kw={"width_ratios": [1.3, 1]})
    x = np.arange(len(order))
    for j, (d, name) in enumerate(((sil, "sim-silent ($n{=}108$)"), (vis, "sim-visible ($n{=}90$)"))):
        ks = [d[c] for c in order]
        r = [100 * k / n for k, n in ks]
        ci = [proportion_confint(k, n, method="wilson") for k, n in ks]
        a.bar(x + (j - 0.5) * 0.38, r, 0.38, color=C[j], edgecolor=SURF, linewidth=0.8, label=name, zorder=2,
              yerr=[[r[i] - 100 * ci[i][0] for i in range(len(r))], [100 * ci[i][1] - r[i] for i in range(len(r))]],
              error_kw={"elinewidth": 0.7, "capsize": 1.5, "ecolor": MUTED})
        for i, v in enumerate(r):
            a.text(x[i] + (j - 0.5) * 0.38, 100 * ci[i][1] + 2, f"{v:.0f}", ha="center", fontsize=6.9, color=INK)
    a.set_xticks(x)
    a.set_xticklabels([lab[c] for c in order], fontsize=7.3, rotation=28, ha="right", rotation_mode="anchor")
    a.set_ylim(0, 118)
    a.set_yticks([0, 20, 40, 60, 80, 100])
    a.set_ylabel("sign-off clean (%)")
    a.set_title("(a) sign-off clean by condition and stratum", loc="left")
    a.legend(frameon=False, loc="upper left", ncol=2, handlelength=1.0, columnspacing=0.8)
    _style(a)
    ends, placed = sorted((cum[c][-1], c) for c in order), []
    for v, c in ends:                                   # nudge end labels apart (min 6.5 points)
        placed.append(max(v, placed[-1] + 6.5) if placed else v)
    for (v, c), yy in zip(ends, placed):
        b.text(6.15, yy, f"{v:.0f}", va="center", fontsize=7.0, color=INK)
    for j, c in enumerate(order):
        b.plot(range(7), cum[c], color=C[j], linewidth=1.4, marker="o", markersize=2.6, label=lab[c])
    b.set_xlim(0, 6.7)
    b.set_ylim(0, 100)
    b.set_xlabel("model calls used")
    b.set_ylabel("sign-off clean so far (%)")
    b.set_title("(b) cumulative by model call", loc="left")
    b.legend(frameon=False, loc="upper center", bbox_to_anchor=(0.45, -0.3), ncol=2, fontsize=7.0, handlelength=1.2,
             columnspacing=0.8)
    _style(b)
    fig.tight_layout(w_pad=1.0)
    save(fig, "fig_v9_p3")


if __name__ == "__main__":
    fig_set1()
    fig_ladder_deficit()
    fig_p3()
