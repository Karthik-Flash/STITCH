#!/usr/bin/env python3
"""Pre-flight Step 1: acceptance checks for the spec-complete mem_wb_mux testbench (mem_wb_mux_tb_full.v).
Re-simulates golden, the defective input, two golden mutants and the final candidate of all 90 mem_wb_mux runs
against the current tb.v and the full testbench. Needs iverilog on PATH (run under WSL from the repo root):
    python3 phase3/evidence/preflight_final/step1_mem_wb_mux.py"""
import glob, hashlib, json, os, shutil, sys, tempfile
sys.path.insert(0, "phase3/runner")
from p3_eval import simulate  # noqa: E402
from posthoc_checks import RESULTS  # noqa: E402  (phase3/results/phase3_run)

T = "phase3/tasks/mem_wb_mux"
OLD, NEW = T + "/tb.v", os.path.join(os.path.dirname(os.path.abspath(__file__)), "mem_wb_mux_tb_full.v")
# the 16 runs POSTHOC_CHECKS.md flags as "not proven equivalent" on mem_wb_mux
FLAGGED = {("sem_adv_v2", "deepseek-coder:6.7b", 2), ("sem_adv_v2", "deepseek-coder:6.7b", 3),
           ("sem_adv_v3", "deepseek-coder:6.7b", 2), ("raw_adv", "gemma3:4b", 1), ("raw_adv", "gemma3:4b", 2),
           ("raw_adv", "gemma3:4b", 3), ("sem_esc_restart_v3", "gemma3:4b", 1), ("sem_esc_restart_v3", "gemma3:4b", 2),
           ("raw_adv", "llama3.1:latest", 1), ("raw_adv", "llama3.1:latest", 2), ("raw_adv", "llama3.1:latest", 3),
           ("sem_adv_v3", "llama3.1:latest", 1), ("sem_esc_restart_v3", "llama3.1:latest", 1),
           ("sem_esc_restart_v3", "llama3.1:latest", 2), ("sem_esc_restart_v3", "llama3.1:latest", 3),
           ("sem_adv_v2", "qwen2.5-coder:7b", 2)}


def sim(v, tb):
    with tempfile.TemporaryDirectory() as d:
        shutil.copy(v, os.path.join(d, "dut.v")); shutil.copy(tb, os.path.join(d, "tb.v"))
        return simulate(["dut.v"], "tb.v", d)["outcome"]


h = lambda p: hashlib.sha256(open(p, "rb").read().replace(b"\r\n", b"\n")).hexdigest()
print("old tb sha256", h(OLD)); print("new tb sha256", h(NEW))
g = open(T + "/golden.v").read()
d = tempfile.mkdtemp()
mut = {"mutant: write_data2 = 0 in the 'every other case' branch":
       g.replace("write_data2 = ex_mem_output_data_2;", "write_data2 = 32'd0;"),
       "mutant: write_data2 = 0 only when memwrite==0 or FWD==2'b11 (the uncovered cases)":
       g.replace("      write_data2 = result;\n",
                 "      write_data2 = result;\n    if (!ex_mem_memwrite || ex_mem_FWD_RS2 == 2'b11) write_data2 = 32'd0;\n")}
files = [("golden", T + "/golden.v"), ("DEFECTIVE INPUT", T + "/input.v")]
for i, (k, v) in enumerate(mut.items()):
    assert v != g
    open(os.path.join(d, f"m{i}.v"), "w").write(v); files.append((k, os.path.join(d, f"m{i}.v")))
for name, v in files:
    print(f"{name}: old tb {sim(v, OLD)}, full tb {sim(v, NEW)}")

rows = []
for m in sorted(glob.glob(os.path.join(RESULTS, "*", "*", "mem_wb_mux", "rep*", "metrics.json"))):
    r = json.load(open(m))
    cand = os.path.join(os.path.dirname(m), f"iter{r['llm_calls']}", "dut.v")
    rows.append(dict(c=r["condition"], m=r["model"], rep=r["rep"], func=r["func_pass"], clean=r["clean_pass"],
                     old=sim(cand, OLD) == "PASS", new=sim(cand, NEW) == "PASS"))
key = lambda r: (r["c"], r["m"], r["rep"])
print(f"\nruns {len(rows)}; old-tb re-sim disagrees with logged func_pass: {[key(r) for r in rows if r['old'] != r['func']]}")
f = [r for r in rows if key(r) in FLAGGED]
print(f"(b) flagged runs failing the full tb: {sum(not r['new'] for r in f)}/{len(f)}")
oth = [r for r in rows if key(r) not in FLAGGED and r["clean"]]
print(f"(c) other clean runs: {len(oth)}; flipping to FAIL: {[key(r) for r in oth if not r['new']]}")
print("\n| condition | func_pass old tb | func_pass full tb | clean_pass old tb | clean_pass full tb |\n|---|---|---|---|---|")
for c in ("baseline", "raw_adv", "sem_adv_v2", "sem_adv_v3", "sem_esc_restart_v3"):
    R = [r for r in rows if r["c"] == c]
    print(f"| {c} | {sum(r['old'] for r in R)}/{len(R)} | {sum(r['new'] for r in R)}/{len(R)} | "
          f"{sum(r['clean'] for r in R)}/{len(R)} | {sum(r['clean'] and r['new'] for r in R)}/{len(R)} |")
