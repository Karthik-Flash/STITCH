"""
phase3_figures.py -- paper figures for Phase 3, drawn from the same numbers as PHASE3_RESULTS.md.
Called by analyze_phase3.py (make(R, runs, outdir)); not meant to be run on its own.

Palette: reference categorical slots 1-5 (validated: adjacent CVD dE >= 9.1, normal-vision dE >= 19.6).
Three slots sit below 3:1 contrast on white, so every bar carries a direct value label (relief rule).
"""
import os

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

SLOTS = ["#2a78d6", "#eb6834", "#1baf7a", "#eda100", "#e87ba4"]
INK, INK2, GRID = "#0b0b0b", "#52514e", "#e6e5e0"
CONDS = ["baseline", "raw_adv", "sem_adv_v2", "sem_adv_v3", "sem_esc_restart_v3"]
LABEL = {"baseline": "baseline (sim only)", "raw_adv": "raw_adv", "sem_adv_v2": "sem_adv (v2)",
         "sem_adv_v3": "sem_adv (v3)", "sem_esc_restart_v3": "sem_esc_restart (v3)"}
MODELS = ["llama3.2:3b", "gemma3:4b", "deepseek-coder:6.7b", "qwen2.5-coder:7b", "llama3.1:latest", "qwen2.5-coder:14b"]


def _style(ax, ylabel, title):
    ax.set_title(title, color=INK, fontsize=10)
    ax.set_ylabel(ylabel, color=INK2)
    ax.set_ylim(0, 115)
    ax.set_yticks(range(0, 101, 20))
    ax.grid(axis="y", color=GRID, linewidth=0.8)
    ax.set_axisbelow(True)
    for s in ("top", "right"):
        ax.spines[s].set_visible(False)
    for s in ("left", "bottom"):
        ax.spines[s].set_color(INK2)
    ax.tick_params(colors=INK2)


def _bars(ax, groups, series, get, colors, labels, width):
    """Grouped bars, Wilson CI whiskers, a value label on every bar. get(group, series) -> rate dict."""
    n = len(series)
    for j, s in enumerate(series):
        xs = [i + (j - (n - 1) / 2) * width for i in range(len(groups))]
        rs = [get(g, s) for g in groups]
        ys = [r["pct"] for r in rs]
        err = [[max(0, y - r["lo"]) for y, r in zip(ys, rs)], [max(0, r["hi"] - y) for y, r in zip(ys, rs)]]
        ax.bar(xs, ys, width * 0.92, color=colors[j], label=labels[j], zorder=2)
        ax.errorbar(xs, ys, yerr=err, fmt="none", ecolor=INK2, elinewidth=1, capsize=2, zorder=3)
        for x, r in zip(xs, rs):
            ax.text(x, r["hi"] + 1.5, f"{r['pct']:.0f}", ha="center", va="bottom", fontsize=7, color=INK)
    ax.set_xticks(range(len(groups)))


def _save(fig, outdir, name):
    fig.tight_layout()
    fig.savefig(os.path.join(outdir, name), dpi=200)
    plt.close(fig)
    print("wrote", os.path.join(outdir, name))


def make(R, runs, outdir, rate):
    os.makedirs(outdir, exist_ok=True)
    plt.rcParams.update({"font.size": 9})
    wrap = {c: LABEL[c].replace(" (", "\n(") for c in CONDS}

    # 1. clean_pass by condition, sim-silent vs sim-visible
    fig, ax = plt.subplots(figsize=(8, 3.4))
    _bars(ax, CONDS, ["silent", "visible"], lambda c, s: R["strat"][s][c]["clean"], SLOTS[:2],
          ["sim-silent defects (6 tasks, n=108)", "sim-visible defects (5 tasks, n=90)"], 0.38)
    ax.set_xticklabels([wrap[c] for c in CONDS])
    ax.legend(frameon=False, loc="upper left", fontsize=8)
    _style(ax, "clean_pass (%)", "clean_pass by condition (990 runs, Wilson 95% CI)")
    _save(fig, outdir, "fig_p3_clean_by_condition.png")

    # 2. composition: top-level synthesis pass per design and condition
    designs = ["mesh2x2", "mesh3x3", "mpsoc"]
    fig, ax = plt.subplots(figsize=(8, 3.4))
    _bars(ax, designs, CONDS, lambda d, c: R["comp"][d][c]["pass"], SLOTS, [LABEL[c] for c in CONDS], 0.16)
    ax.set_xticklabels(["2x2 mesh (4 routers)", "3x3 mesh (9 routers)", "MPSoC top"])
    ax.legend(frameon=False, ncol=5, loc="upper center", fontsize=7)
    _style(ax, "top-level synthesis pass (%)", "Repaired leaves spliced into the real designs (18 groups per bar)")
    _save(fig, outdir, "fig_p3_composition.png")

    # 3. cumulative clean_pass by LLM call
    fig, ax = plt.subplots(figsize=(6.5, 3.4))
    for j, c in enumerate(CONDS):
        ys = [R["cum"][c][k]["pct"] for k in range(7)]
        ax.plot(range(7), ys, color=SLOTS[j], linewidth=2, marker="o", markersize=4, label=LABEL[c])
        ax.text(6.15, ys[-1], f"{ys[-1]:.0f}", va="center", fontsize=7.5, color=INK)
    ax.set_xticks(range(7))
    ax.set_xlabel("LLM calls used", color=INK2)
    ax.legend(frameon=False, fontsize=7.5, loc="upper left")
    _style(ax, "runs clean so far (%)", "Cumulative clean_pass by number of model calls (198 runs per line)")
    _save(fig, outdir, "fig_p3_clean_by_call.png")

    # 4. interpreted vs raw tool text, per model
    def per_model(m, c):
        rs = [r for r in runs if r["model"] == m and r["condition"] == c]
        return rate(sum(r["clean_pass"] for r in rs), len(rs))
    fig, ax = plt.subplots(figsize=(8, 3.4))
    _bars(ax, MODELS, ["raw_adv", "sem_adv_v3"], per_model, [SLOTS[1], SLOTS[0]],
          ["raw tool text (raw_adv)", "interpreted (sem_adv v3)"], 0.38)
    ax.set_xticklabels([m.replace(":latest", ":8b").replace(":", "\n") for m in MODELS])
    ax.legend(frameon=False, loc="upper left", fontsize=8)
    _style(ax, "clean_pass (%)", "Interpreted vs raw tool feedback, by model (33 runs per bar)")
    _save(fig, outdir, "fig_p3_v3_vs_raw_by_model.png")


# ----------------------------------------------------------------------------- final batch (v2 figures)
# Additive: new files fig_p3_v2_*.png on the sign-off metric, six models, with the baseline_gate control arm.
# Slot 6 (#008300) extends the validated palette (validate_palette.js, 6 slots, light: all checks pass; three slots
# sub-3:1 on white, so every bar keeps its value label). Colour follows the condition; the x order follows how much
# the model is told (nothing, the alarm, raw text, interpreted text, escalation).
COLOR6 = dict(zip(CONDS + ["baseline_gate"], SLOTS + ["#008300"]))
ORDER6 = ["baseline", "baseline_gate", "raw_adv", "sem_adv_v2", "sem_adv_v3", "sem_esc_restart_v3"]
LABEL6 = {**LABEL, "baseline_gate": "baseline_gate (alarm only)"}


def make_v2(runs, comp, outdir, rate):
    """runs: six-model runs with signoff_clean / first_so_clean (analyze_phase3.apply_signoff); comp: compose rows."""
    os.makedirs(outdir, exist_ok=True)
    plt.rcParams.update({"font.size": 9})
    conds = [c for c in ORDER6 if any(r["condition"] == c for r in runs)]
    wrap = {c: LABEL6[c].replace(" (", "\n(") for c in conds}

    def st(c, s):
        rs = [r for r in runs if r["condition"] == c and r["silent"] == (s == "silent")]
        return rate(sum(bool(r["signoff_clean"]) for r in rs), len(rs))
    fig, ax = plt.subplots(figsize=(8.6, 3.4))
    _bars(ax, conds, ["silent", "visible"], st, SLOTS[:2],
          ["sim-silent defects (6 tasks, n=108)", "sim-visible defects (5 tasks, n=90)"], 0.38)
    ax.set_xticklabels([wrap[c] for c in conds], fontsize=8)
    ax.legend(frameon=False, loc="upper left", fontsize=8)
    _style(ax, "sign-off clean (%)", "Sign-off clean by condition (six models, Wilson 95% CI)")
    _save(fig, outdir, "fig_p3_v2_clean_by_condition.png")

    fig, ax = plt.subplots(figsize=(6.8, 3.4))
    ends = []
    for c in conds:
        rs = [r for r in runs if r["condition"] == c]
        ys = [100 * sum(r["first_so_clean"] is not None and r["first_so_clean"] <= k for r in rs) / len(rs) for k in range(7)]
        ax.plot(range(7), ys, color=COLOR6[c], linewidth=2, marker="o", markersize=4, label=LABEL6[c])
        ends.append(ys[-1])
    placed = []                                        # end labels at least 4 points apart, lowest kept in place
    for y in sorted(ends):
        placed.append(max(y, placed[-1] + 4) if placed else y)
    for y, p in zip(sorted(ends), placed):
        ax.text(6.15, p, f"{y:.0f}", va="center", fontsize=7.5, color=INK)
    ax.set_xticks(range(7))
    ax.set_xlabel("LLM calls used", color=INK2)
    ax.legend(frameon=False, fontsize=7.5, loc="upper left")
    _style(ax, "runs sign-off clean so far (%)", "Cumulative sign-off clean by number of model calls (198 runs per line)")
    _save(fig, outdir, "fig_p3_v2_clean_by_call.png")

    designs = ["mesh2x2", "mesh3x3", "mpsoc"]
    cc = [c for c in conds if any(x["condition"] == c for x in comp)]

    def cp(d, c):
        X = [x for x in comp if x["design"] == d and x["condition"] == c]
        return rate(sum(bool(x["top_level_synthesis_pass"]) for x in X), len(X))
    fig, ax = plt.subplots(figsize=(8.6, 3.4))
    _bars(ax, designs, cc, cp, [COLOR6[c] for c in cc], [LABEL6[c] for c in cc], 0.14)
    ax.set_xticklabels(["2x2 mesh (4 routers)", "3x3 mesh (9 routers)", "MPSoC top"])
    ax.legend(frameon=False, ncol=3, loc="upper center", fontsize=7)
    _style(ax, "top-level synthesis pass (%)", "Repaired leaves spliced into the real designs (18 groups per bar)")
    ax.set_ylim(0, 135)
    _save(fig, outdir, "fig_p3_v2_composition.png")

    def pm(m, c):
        rs = [r for r in runs if r["model"] == m and r["condition"] == c]
        return rate(sum(bool(r["signoff_clean"]) for r in rs), len(rs))
    series = [c for c in ("baseline_gate", "raw_adv", "sem_adv_v3", "sem_esc_restart_v3") if c in conds]
    fig, ax = plt.subplots(figsize=(8.6, 3.4))
    _bars(ax, MODELS, series, pm, [COLOR6[c] for c in series], [LABEL6[c] for c in series], 0.2)
    ax.set_xticklabels([m.replace(":latest", ":8b").replace(":", "\n") for m in MODELS])
    ax.legend(frameon=False, loc="upper left", fontsize=7.5, ncol=2)
    _style(ax, "sign-off clean (%)", "Alarm, raw text, interpreted and escalated feedback, by model (33 runs per bar)")
    ax.set_ylim(0, 125)
    _save(fig, outdir, "fig_p3_v2_by_model.png")
