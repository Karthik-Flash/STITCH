#!/usr/bin/env python3
"""Pre-flight Step A2: acceptance checks (a)-(e) for a spec-complete sign-off testbench of one task.
Re-simulates golden, the defective input, a gap-only mutant and the final candidate of every run of the task
against tb.v and the candidate sign-off testbench; 'not proven' runs are read from step2_equiv_output.txt.
Needs iverilog (WSL, repo root):
    python3 phase3/evidence/preflight_final/step2_signoff_tb.py Address_select Address_select_tb_full.v"""
import ast, glob, hashlib, json, os, re, shutil, sys, tempfile
sys.path.insert(0, "phase3/runner")
from p3_eval import simulate  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
task, new = sys.argv[1], os.path.join(HERE, sys.argv[2])
T, RES = f"phase3/tasks/{task}", "phase3/results/phase3_run"
OLD = T + "/tb.v"
# gap-only mutants: golden changed only where tb.v does not look
MUTANT = {"Address_select": ("    J_addr = X + PC;\n",
                             "    J_addr = (!IF_Flush && Instruction_code[6:0] == 7'b1101111) ? X + PC : 32'd0;\n")}


def sim(v, tb):
    with tempfile.TemporaryDirectory() as d:
        shutil.copy(v, os.path.join(d, "dut.v")); shutil.copy(tb, os.path.join(d, "tb.v"))
        return simulate(["dut.v"], "tb.v", d)["outcome"] == "PASS"


h = lambda p: hashlib.sha256(open(p, "rb").read().replace(b"\r\n", b"\n")).hexdigest()
print(f"{task}: tb.v sha256 {h(OLD)}; sign-off tb sha256 {h(new)}")
g = open(T + "/golden.v").read()
a, b = MUTANT[task]
assert a in g
mut = os.path.join(tempfile.mkdtemp(), "m.v"); open(mut, "w").write(g.replace(a, b))
for name, v in (("(a) golden", T + "/golden.v"), ("(d) gap-only mutant", mut), ("(e) DEFECTIVE INPUT", T + "/input.v")):
    print(f"{name}: tb.v {'PASS' if sim(v, OLD) else 'FAIL'}, sign-off tb {'PASS' if sim(v, new) else 'FAIL'}")
flag = set()
for l in open(os.path.join(HERE, "step2_equiv_output.txt")):
    if l.strip().startswith("(") and f"'{task}'" in l:
        c, m, t, rep = ast.literal_eval(l.strip())[:4]
        flag.add((c, m, rep))
rows = []
for f in sorted(glob.glob(f"{RES}/*/*/{task}/rep*/metrics.json")):
    r = json.load(open(f))
    cand = os.path.join(os.path.dirname(f), f"iter{r['llm_calls']}", "dut.v")
    rows.append(((r["condition"], r["model"], r["rep"]), r["func_pass"], r["clean_pass"], sim(cand, new)))
F = [x for x in rows if x[0] in flag]
O = [x for x in rows if x[0] not in flag and x[2]]
print(f"runs {len(rows)}; (b) not-proven clean runs failing the sign-off tb: {sum(not x[3] for x in F)}/{len(F)}; "
      f"passing it: {[x[0] for x in F if x[3]]}")
print(f"(c) other clean runs: {len(O)}; flipping to FAIL: {[x[0] for x in O if not x[3]]}")
print("tb.v-FAIL runs that pass the sign-off tb (must be none):", [x[0] for x in rows if x[3] and not x[1]])
print("\n| condition | clean_pass (tb.v) | clean under sign-off tb |\n|---|---|---|")
for c in ("baseline", "raw_adv", "sem_adv_v2", "sem_adv_v3", "sem_esc_restart_v3"):
    R = [x for x in rows if x[0][0] == c]
    print(f"| {c} | {sum(x[2] for x in R)}/{len(R)} | {sum(x[2] and x[3] for x in R)}/{len(R)} |")
