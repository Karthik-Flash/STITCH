"""Shared figure style for the paper (v11). Every figure script imports this module.

- One colour per condition across the paper (validated with the dataviz palette checker, all pairs, light mode):
  baseline grey, the alarm-only arm light amber, raw tool text vermillion, interpretation a blue family (v2 light,
  v3 dark), escalation a green family (plain escalation light, escalation with restart the strongest).
- Text at 7.5 to 8 pt at the final printed size: figures are drawn at their final width (FULL, HALF, THIRD inches)
  and included at natural size, so nothing is scaled.
- Vector PDF with TrueType fonts embedded (pdf.fonttype 42); light gridlines; no chart junk.
"""
import os

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

FULL, HALF, THIRD = 6.5, 3.15, 2.08          # inches: \linewidth, a 0.485 subfigure, a 0.32 subfigure
INK, MUTED, GRID, SURF = "#1a1a19", "#5c5b57", "#e6e5e1", "#ffffff"

COND = {
    "baseline": "#8f8e89",
    "baseline_gate": "#e3a835",
    "raw_adv": "#d9622b",
    "sem_adv": "#6fa8e6",                     # RTLLM sem_adv is the production interpreter, v2
    "sem_adv_v2": "#6fa8e6",
    "sem_adv_v3": "#1d5aa6",
    "sem_escalate": "#63bf95",
    "sem_escalate_restart": "#006e4b",
    "sem_esc_restart_v3": "#006e4b",
}
LABEL = {                                     # the paper's condition names (code name -> name in print)
    "baseline": "Baseline",
    "baseline_gate": "Alarm",
    "raw_adv": "Raw",
    "sem_adv": "Interpret",
    "sem_adv_v2": "Interpret v2",
    "sem_adv_v3": "Interpret v3",
    "sem_escalate": "Escalate",
    "sem_escalate_restart": "Escalate-R",
    "sem_esc_restart_v3": "Escalate-R",
}
MODEL = {                                     # Ollama tags and run labels -> model names in print
    "llama3.2:3b": "Llama 3.2 3B", "gemma3:4b": "Gemma 3 4B", "deepseek-coder:6.7b": "DeepSeek-Coder 6.7B",
    "deepseek-coder": "DeepSeek-Coder 6.7B", "qwen2.5-coder:7b": "Qwen2.5-Coder 7B", "llama3.1:8b": "Llama 3.1 8B",
    "llama3.1": "Llama 3.1 8B", "llama3.1:latest": "Llama 3.1 8B", "qwen2.5-coder:14b": "Qwen2.5-Coder 14B",
    "gemma3:27b": "Gemma 3 27B", "qwen2.5-coder:32b": "Qwen2.5-Coder 32B", "RTLCoder": "RTLCoder 6.7B",
}
P3_ORDER = ["baseline", "baseline_gate", "raw_adv", "sem_adv_v2", "sem_adv_v3", "sem_esc_restart_v3"]

plt.rcParams.update({
    "font.family": "sans-serif",
    "font.sans-serif": ["Arial", "Helvetica", "Liberation Sans", "DejaVu Sans"],
    "font.size": 8, "axes.titlesize": 8, "axes.labelsize": 8, "legend.fontsize": 7.5,
    "xtick.labelsize": 7.5, "ytick.labelsize": 7.5,
    "axes.edgecolor": MUTED, "axes.linewidth": 0.6, "xtick.color": MUTED, "ytick.color": MUTED,
    "xtick.major.width": 0.6, "ytick.major.width": 0.6, "xtick.major.size": 2.5, "ytick.major.size": 2.5,
    "axes.labelcolor": INK, "text.color": INK, "axes.titlelocation": "left", "axes.titlepad": 3,
    "legend.frameon": False, "legend.handlelength": 1.0, "legend.handletextpad": 0.4, "legend.columnspacing": 0.9,
    "hatch.linewidth": 0.6, "pdf.fonttype": 42, "ps.fonttype": 42, "savefig.dpi": 300,
    "figure.facecolor": SURF, "axes.facecolor": SURF,
})
ERR = {"elinewidth": 0.6, "capsize": 1.5, "capthick": 0.6, "ecolor": MUTED}


def style(ax, grid="y"):
    for s in ("top", "right"):
        ax.spines[s].set_visible(False)
    if grid:
        ax.grid(axis=grid, color=GRID, linewidth=0.5, zorder=0)
    ax.set_axisbelow(True)


def figure(width, height, **kw):
    """A figure at its final printed size; layout is fitted inside it, so the saved PDF keeps this size."""
    return plt.subplots(figsize=(width, height), layout="constrained", **kw)


def save(fig, path, png=None):
    """Write <path>.pdf (if path) and <png>.png (if png) at the figure's exact size (no tight bounding box)."""
    fig.get_layout_engine().set(w_pad=0.02, h_pad=0.02, wspace=0.04, hspace=0.04)
    for base, ext in ((path, ".pdf"), (png, ".png")):
        if base:
            os.makedirs(os.path.dirname(base), exist_ok=True)
            fig.savefig(base + ext)
            print("wrote", os.path.relpath(base + ext))
    plt.close(fig)
