"""Figures after the Gemini completion run (SET4_PREREG Amendment 3), written as NEW files:
  phase2/results/set4_api/analysis_4b/fig_set4b_q1_baseline.{png,pdf}  Set 4b Q1: baseline passes /3, module x model
  phase2/results/p3_api/analysis/fig_p3_api_ladder_signoff.{png,pdf}   Phase 3 ladder rows: sign-off clean of 33
Reads only the JSON written by analysis_set4b.py and p3_api/p3_signoff_ladder.py. Run after both.
The Set 4 figures (analysis/fig5_capability_ladder_api, fig_set4_inr_per_pass) use Set 4 data only and are unchanged.
"""
import json
import os
import textwrap

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
from matplotlib.patches import Patch  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
RES = os.path.join(os.path.dirname(HERE), "results")
SURFACE, INK, MUTED, GRID = "#fcfcfb", "#0b0b0b", "#52514e", "#e4e3df"
SERIES = ["#2a78d6", "#eb6834", "#1baf7a"]                       # categorical slots 1-3 (validated, light)
RAMP = {0: "#cde2fb", 1: "#86b6ef", 2: "#2a78d6", 3: "#104281"}   # blue ramp steps 100/250/450/650
SHORT = {"gpt-4.1-mini-2025-04-14": "GPT-4.1 mini", "gemini-2.5-flash": "Gemini 2.5 Flash",
         "claude-haiku-4-5-20251001": "Claude Haiku 4.5"}
plt.rcParams.update({"font.size": 9, "axes.edgecolor": MUTED, "axes.labelcolor": INK, "xtick.color": MUTED,
                     "ytick.color": MUTED, "figure.facecolor": SURFACE, "axes.facecolor": SURFACE})


def save(fig, path):
    for ext in ("png", "pdf"):
        fig.savefig(f"{path}.{ext}", dpi=300, facecolor=SURFACE)
    plt.close(fig)
    print("wrote", path + ".{png,pdf}")


def fig_q1():
    res = json.load(open(os.path.join(RES, "set4_api", "analysis_4b", "set4b_analysis.json"), encoding="utf-8"))
    models, q1 = res["models"], res["Q1"]
    mods = sorted(q1, key=lambda m: (-sum(q1[m][x]["k"] for x in models), m.lower()))
    fig, ax = plt.subplots(figsize=(5.2, 7.2))
    for i, mod in enumerate(mods):
        for j, m in enumerate(models):
            c = q1[mod][m]
            pending = c["n"] == 0
            ax.add_patch(plt.Rectangle((j, i), 1, 1, facecolor=SURFACE if pending else RAMP[c["k"]],
                                       edgecolor=SURFACE, linewidth=2, hatch="///" if pending else None))
            if pending:
                ax.add_patch(plt.Rectangle((j + 0.04, i + 0.08), 0.92, 0.84, fill=False, edgecolor=GRID, linewidth=0,
                                           hatch="///"))
            ax.text(j + 0.5, i + 0.5, "pending" if pending else f"{c['k']}/{c['n']}", ha="center", va="center",
                    fontsize=8, color=MUTED if pending else ("white" if c["k"] >= 2 else INK))
    ax.set_xlim(0, len(models))
    ax.set_ylim(len(mods), 0)
    ax.set_xticks([j + 0.5 for j in range(len(models))])
    ax.set_xticklabels([SHORT[m] for m in models])
    ax.xaxis.tick_top()
    ax.set_yticks([i + 0.5 for i in range(len(mods))])
    ax.set_yticklabels(mods)
    ax.tick_params(length=0)
    for s in ax.spines.values():
        s.set_visible(False)
    cov = res["coverage"]
    ax.set_title("Set 4b floor tier: baseline passes out of 3\n" + textwrap.fill(
        "valid runs of 228: " + ", ".join(f"{SHORT[m]} {cov[m]['valid']}" for m in models), 58),
        fontsize=9, color=INK, pad=28)
    ax.legend(handles=[Patch(facecolor=RAMP[k], edgecolor=SURFACE, label=f"{k}/3") for k in range(4)]
              + [Patch(facecolor=SURFACE, edgecolor=MUTED, hatch="///", label="pending (not run)")],
              loc="upper center", bbox_to_anchor=(0.5, -0.01), ncol=5, frameon=False, fontsize=7.5,
              handlelength=1.2, columnspacing=0.8)
    fig.tight_layout()
    save(fig, os.path.join(RES, "set4_api", "analysis_4b", "fig_set4b_q1_baseline"))


def fig_ladder():
    res = json.load(open(os.path.join(RES, "p3_api", "analysis", "p3_ladder_signoff.json"), encoding="utf-8"))
    conds = ["baseline", "baseline_gate", "raw_adv", "sem_adv_v2", "sem_adv_v3", "sem_esc_restart_v3"]
    models = [m for m in SHORT if any(k.startswith(m + "|") for k in res["table12"])]
    fig, ax = plt.subplots(figsize=(7.2, 3.4))
    w = 0.26
    for j, m in enumerate(models):
        xs = [i + (j - (len(models) - 1) / 2) * w for i in range(len(conds))]
        vals = [res["table12"][f"{m}|{c}"][0] for c in conds]
        ax.bar(xs, vals, w, color=SERIES[j], edgecolor=SURFACE, linewidth=1.5, label=SHORT[m], zorder=2)
        for x, v in zip(xs, vals):
            ax.text(x, v + 0.5, str(v), ha="center", va="bottom", fontsize=7, color=INK)
    ax.set_xticks(range(len(conds)))
    ax.set_xticklabels(conds, fontsize=8)
    ax.set_ylim(0, 36)
    ax.set_yticks([0, 11, 22, 33])
    ax.set_ylabel("sign-off clean (of 33 runs)")
    ax.grid(axis="y", color=GRID, linewidth=0.6, zorder=0)
    for s in ("top", "right"):
        ax.spines[s].set_visible(False)
    ax.set_title("Phase 3 MPSoC ladder rows, API models (N=3, descriptive, not pooled)", fontsize=9, color=INK)
    ax.legend(frameon=False, fontsize=8, ncol=len(models), loc="upper center", bbox_to_anchor=(0.5, -0.12))
    fig.tight_layout()
    save(fig, os.path.join(RES, "p3_api", "analysis", "fig_p3_api_ladder_signoff"))


if __name__ == "__main__":
    fig_q1()
    fig_ladder()
