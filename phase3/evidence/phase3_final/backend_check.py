#!/usr/bin/env python3
"""POST HOC (2026-09-30): job A (baseline_gate) ran with Ollama's Vulkan backend on the H200 (CUDA discovery timed
out, see results/final_batch_logs/ollama_serve_369809.log); job C and, as far as recorded, the 990 runs used CUDA.
On sim-visible tasks the first prompt of baseline_gate and baseline is byte-identical (the input fails simulation, so
both get the simulation result only). Compare the first responses: identity rate gate-vs-baseline against the
baseline-vs-baseline (other replicate) rate, and first-call func_pass. Repo root:  python phase3/evidence/phase3_final/backend_check.py"""
import glob, itertools, json, os
from collections import defaultdict
R = "phase3/results"
meta = {json.load(open(f))["top"]: json.load(open(f)) for f in glob.glob("phase3/tasks/*/meta.json")}


def runs(d, cond):
    out = {}
    for f in glob.glob(f"{R}/{d}/*/{cond}/*/rep*/metrics.json"):
        m = json.load(open(f)); out[(m["model"], m["task"], m["rep"])] = (m, os.path.dirname(f))
    return out


B, G = runs("phase3_run", "baseline"), runs("phase3_gate_ctrl", "baseline_gate")
rd = lambda p: open(p, "rb").read()
same = diff = 0; f1 = {"baseline": 0, "baseline_gate": 0}; n1 = 0
cells = defaultdict(dict)
for k, (m, d) in B.items():
    if meta[k[1]]["sim_silent"] or m["llm_calls"] == 0 or G[k][0]["llm_calls"] == 0:
        continue
    g, gd = G[k]
    same += rd(f"{d}/iter1/prompt.txt") == rd(f"{gd}/iter1/prompt.txt"); diff += rd(f"{d}/iter1/prompt.txt") != rd(f"{gd}/iter1/prompt.txt")
    f1["baseline"] += m["per_iter"][1]["func_pass"]; f1["baseline_gate"] += g["per_iter"][1]["func_pass"]; n1 += 1
    cells[k[:2]][("b", k[2])] = rd(f"{d}/iter1/response.txt"); cells[k[:2]][("g", k[2])] = rd(f"{gd}/iter1/response.txt")
bb, gb = [0, 0], [0, 0]
for c in cells.values():
    for (a, x), (b, y) in itertools.combinations(sorted(c.items()), 2):
        if a[0] == b[0] == "b":
            bb[0] += x == y; bb[1] += 1
        elif a[0] != b[0]:
            gb[0] += x == y; gb[1] += 1
print(f"sim-visible (model, task, rep) with >=1 call in both: {n1}; iter1 prompt byte-identical {same}, different {diff}")
print(f"iter1 response byte-identical: baseline vs baseline (other rep) {bb[0]}/{bb[1]} ({100*bb[0]/bb[1]:.0f}%); "
      f"baseline_gate vs baseline (any rep) {gb[0]}/{gb[1]} ({100*gb[0]/gb[1]:.0f}%)")
print(f"iter1 func_pass on those identical prompts: baseline {f1['baseline']}/{n1}, baseline_gate {f1['baseline_gate']}/{n1}")
