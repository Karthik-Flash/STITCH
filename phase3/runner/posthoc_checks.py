#!/usr/bin/env python3
"""
posthoc_checks.py -- POST HOC checks requested by the planner (2026-09-28). Not part of the pre-planned analysis.

  keepbest   re-score every Phase 3 run under a keep-best-so-far return policy (rank clean > func_pass > rest,
             ties -> latest candidate; the defective input counts as a candidate). Uses the logged per_iter scores.
  degenerate audit every clean_pass run on the 6 sim-silent tasks: Yosys equivalence vs golden.v and constant-driven
             output bits vs golden. Needs yosys on PATH (run under WSL).
  phase2     Set 1 / Set 3 recoverable-band contrasts vs baseline with the same (model, module)-cell bootstrap and
             sign-flip test Phase 3 uses.
  equiv      (final-batch pre-flight, 2026-09-28) equivalence audit of every clean_pass run on the named tasks,
             baseline included; runs failing a differing tasks/<task>/tb_signoff.v are counted, not audited. WSL.

Usage (repo root):  python phase3/runner/posthoc_checks.py keepbest|degenerate|phase2|equiv <task>...
"""
import glob
import json
import os
import subprocess
import sys
import tempfile
from collections import Counter, defaultdict

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from analyze_phase3 import CONDS, boot_ci, fp, load, rate, sg, signflip_p  # noqa: E402

P3 = os.path.dirname(HERE)
REPO = os.path.dirname(P3)
RESULTS = os.path.join(P3, "results", "phase3_run")


def cell_contrast(pairs, label):
    """pairs: {(model, unit): [(a, b), ...]} -> mean diff (pts), cell bootstrap CI, sign-flip p."""
    d = [100 * sum(a - b for a, b in v) / len(v) for _, v in sorted(pairs.items())]
    lo, hi = boot_ci(d, label)
    return f"{sg(sum(d) / len(d))} [{sg(lo)}, {sg(hi)}], cells={len(d)}, sign-flip p={fp(signflip_p(d, label))}"


# ----------------------------------------------------------------------------- keep-best-so-far
def keepbest():
    runs, _ = load(RESULTS, os.path.join(P3, "tasks"))
    rank = lambda p: 2 if p["clean_pass"] else (1 if p["func_pass"] else 0)
    for r in runs:
        best = max(range(len(r["per_iter"])), key=lambda i: (rank(r["per_iter"][i]), i))
        b = r["per_iter"][best]
        r["kb"] = {"func": b["func_pass"], "clean": b["clean_pass"], "silent": b["func_pass"] and not b["clean_pass"],
                   "is_input": best == 0}
    print("POST HOC: keep-best-so-far return policy (990 runs; as-run values in brackets)\n")
    print("| condition | func_pass | clean_pass | silent structural pass | returns the defective input |")
    print("|---|---|---|---|---|")
    for c in CONDS:
        R = [r for r in runs if r["condition"] == c]
        n = len(R)
        f = lambda k: sum(r["kb"][k] for r in R)
        print(f"| {c} | {rate(f('func'), n)['fmt']} [{sum(r['func_pass'] for r in R)}] | {rate(f('clean'), n)['fmt']} "
              f"[{sum(r['clean_pass'] for r in R)}] | {rate(f('silent'), n)['fmt']} [{sum(r['silent_structural_pass'] for r in R)}] "
              f"| {f('is_input')} |")
    idx = {(r["model"], r["task"], r["rep"], r["condition"]): r for r in runs}
    for a in ("sem_adv_v2", "sem_adv_v3", "sem_esc_restart_v3"):
        for metric in ("clean", "func"):
            pairs = defaultdict(list)
            for (m, t, rep, c), r in idx.items():
                if c == a:
                    pairs[(m, t)].append((int(r["kb"][metric]), int(idx[(m, t, rep, "raw_adv")]["kb"][metric])))
            print(f"{a} - raw_adv, {metric}_pass (keep-best): {cell_contrast(pairs, f'kb:{a}:{metric}')}")


# ----------------------------------------------------------------------------- degenerate-repair audit
YS = """read_verilog {g}; hierarchy -top {t}; proc; async2sync; opt_clean; rename {t} gold; design -stash gold
read_verilog {c}; hierarchy -top {t}; proc; async2sync; opt_clean; rename {t} gate; design -stash gate
design -copy-from gold -as gold gold; design -copy-from gate -as gate gate
equiv_make gold gate equiv; hierarchy -top equiv; equiv_simple -seq 5; equiv_induct -seq 5; equiv_status"""


def const_out_bits(v, top):
    """Output bits driven by a constant after synthesis (tied-off outputs)."""
    with tempfile.TemporaryDirectory() as d:
        j = os.path.join(d, "n.json")
        subprocess.run(["yosys", "-q", "-p", f"read_verilog {v}; synth -top {top}; opt -full; write_json {j}"],
                       capture_output=True, text=True, timeout=120)
        if not os.path.exists(j):
            return None
        mod = json.load(open(j))["modules"][top]
        return sum(1 for p in mod["ports"].values() if p["direction"] == "output" for b in p["bits"] if isinstance(b, str))


# Specs say select code 2'b11 "does not occur in operation" for these two tasks: re-check with it mapped to 2'b00.
LEGAL = {
    "MuxPC": ("module MuxPC(input [31:0] next_address, input [31:0] B_addr, input [31:0] J_addr, input [1:0] PCsrc,"
              " output [31:0] input_to_ifu); core u(.next_address(next_address), .B_addr(B_addr), .J_addr(J_addr),"
              " .PCsrc(PCsrc == 2'b11 ? 2'b00 : PCsrc), .input_to_ifu(input_to_ifu)); endmodule"),
    "mux3": ("module mux3(input [1:0] sel, input [31:0] id_ex_output_data1, input [31:0] ex_forwarding,"
             " input [31:0] mem_forwarding, output [31:0] alu_in); core u(.sel(sel == 2'b11 ? 2'b00 : sel),"
             " .id_ex_output_data1(id_ex_output_data1), .ex_forwarding(ex_forwarding),"
             " .mem_forwarding(mem_forwarding), .alu_in(alu_in)); endmodule"),
    # spec: gnt is one-hot or all-zero; any other grant is mapped to all-zero
    "noc_xbar4": ("module noc_xbar4(input [3:0] gnt, input [31:0] in0, input [31:0] in1, input [31:0] in2,"
                  " input [31:0] in3, output [31:0] out_data, output out_valid);"
                  " core u(.gnt((gnt & (gnt - 4'd1)) == 4'd0 ? gnt : 4'd0), .in0(in0), .in1(in1), .in2(in2),"
                  " .in3(in3), .out_data(out_data), .out_valid(out_valid)); endmodule"),
}


def legal_equivalent(golden, cand, top):
    """Equivalence when the top only ever sees legal select codes (each original module renamed to core)."""
    with tempfile.TemporaryDirectory() as d:
        files = []
        for i, v in enumerate((golden, cand)):
            f = os.path.join(d, f"{i}.v")
            open(f, "w").write(open(v).read().replace(f"module {top}", "module core", 1) + "\n" + LEGAL[top] + "\n")
            files.append(f)
        return equivalent(*files, top, flat=True)


def equivalent(golden, cand, top, flat=False):
    ys = YS.format(g=golden, c=cand, t=top)
    if flat:
        ys = ys.replace("proc;", "proc; flatten;")
    p = subprocess.run(["yosys", "-p", ys], capture_output=True, text=True, timeout=300)
    out = p.stdout + p.stderr
    if "Equivalence successfully proven!" in out:
        return "equivalent"
    if " are unproven." in out:                     # equiv_status summary line, printed only when it ran
        return "not proven equivalent"
    return "equiv check error"


def degenerate():
    runs, meta = load(RESULTS, os.path.join(P3, "tasks"))
    silent = sorted(t for t in meta if meta[t]["sim_silent"])
    gold_const = {t: const_out_bits(os.path.join(P3, "tasks", t, "golden.v"), t) for t in silent}
    print("golden constant-driven output bits:", gold_const)
    gold_equiv = {t: equivalent(os.path.join(P3, "tasks", t, "golden.v"), os.path.join(P3, "tasks", t, "golden.v"), t)
                  for t in silent}
    print("golden vs itself (checks the flow works per task):", gold_equiv)
    tally = defaultdict(Counter)
    flagged = []
    for r in runs:
        if r["task"] not in silent or not r["clean_pass"] or r["condition"] == "baseline":
            continue
        d = os.path.join(RESULTS, r["model"].replace(":", "_"), r["condition"], r["task"], f"rep{r['rep']}")
        cand = os.path.join(d, f"iter{r['llm_calls']}", "dut.v")
        eq = equivalent(os.path.join(P3, "tasks", r["task"], "golden.v"), cand, r["task"])
        cb = const_out_bits(cand, r["task"])
        extra = None if cb is None or gold_const[r["task"]] is None else cb - gold_const[r["task"]]
        if eq != "equivalent" and r["task"] in LEGAL and \
                legal_equivalent(os.path.join(P3, "tasks", r["task"], "golden.v"), cand, r["task"]) == "equivalent":
            eq = "equivalent on legal inputs"
        tally[r["condition"]][eq] += 1
        if extra:
            tally[r["condition"]]["extra constant output bits"] += 1
        if eq not in ("equivalent", "equivalent on legal inputs") or extra:
            flagged.append((r["condition"], r["model"], r["task"], r["rep"], eq, extra))
    cols = ["equivalent", "equivalent on legal inputs", "not proven equivalent", "equiv check error"]
    print("\n| condition | clean sim-silent runs | " + " | ".join(cols) + " | extra constant output bits |")
    print("|---|---|---|---|---|---|---|")
    for c in CONDS[1:]:
        t = tally[c]
        print(f"| {c} | {sum(t[k] for k in cols)} | " + " | ".join(str(t[k]) for k in cols) +
              f" | {t['extra constant output bits']} |")
    print("\nflagged runs (condition, model, task, rep, equivalence, extra constant output bits):")
    for f in flagged:
        print(" ", f)


def equiv(tasks):
    """Equivalence audit of every clean_pass run (all conditions, baseline included) on the given tasks. Where the
    task has a tb_signoff.v that differs from tb.v, a run enters the audit only if its final candidate also passes
    tb_signoff.v; the ones that fail it are counted separately."""
    from p3_eval import simulate
    runs, _ = load(RESULTS, os.path.join(P3, "tasks"))
    tdir = lambda t: os.path.join(P3, "tasks", t)
    rd = lambda b: open(b, "rb").read().replace(b"\r\n", b"\n")

    def signoff_pass(cand, t):
        with tempfile.TemporaryDirectory() as d:
            for src, dst in ((cand, "dut.v"), (os.path.join(tdir(t), "tb_signoff.v"), "tb.v")):
                open(os.path.join(d, dst), "wb").write(open(src, "rb").read())
            return simulate(["dut.v"], "tb.v", d)["outcome"] == "PASS"

    differs = {t for t in tasks if os.path.exists(os.path.join(tdir(t), "tb_signoff.v"))
               and rd(os.path.join(tdir(t), "tb_signoff.v")) != rd(os.path.join(tdir(t), "tb.v"))}
    print("tasks with a tb_signoff.v that differs from tb.v:", sorted(differs))
    for t in tasks:
        g = os.path.join(tdir(t), "golden.v")
        print(f"{t}: golden vs itself = {equivalent(g, g, t)}; golden constant-driven output bits = {const_out_bits(g, t)}")
    tally, flagged = defaultdict(Counter), []
    for r in sorted(runs, key=lambda r: (r["task"], r["condition"], r["model"], r["rep"])):
        if r["task"] not in tasks or not r["clean_pass"]:
            continue
        t = r["task"]
        cand = os.path.join(RESULTS, r["model"].replace(":", "_"), r["condition"], t, f"rep{r['rep']}",
                            f"iter{r['llm_calls']}", "dut.v")
        if t in differs and not signoff_pass(cand, t):
            tally[t]["fails tb_signoff"] += 1
            continue
        g = os.path.join(tdir(t), "golden.v")
        eq = equivalent(g, cand, t)
        if eq != "equivalent" and t in LEGAL and legal_equivalent(g, cand, t) == "equivalent":
            eq = "equivalent on legal inputs"
        cb, gb = const_out_bits(cand, t), const_out_bits(g, t)
        extra = None if cb is None or gb is None else cb - gb
        tally[t][eq] += 1
        if extra:
            tally[t]["extra constant output bits"] += 1
        if eq not in ("equivalent", "equivalent on legal inputs") or extra:
            flagged.append((r["condition"], r["model"], t, r["rep"], eq, extra, cand))
    cols = ["fails tb_signoff", "equivalent", "equivalent on legal inputs", "not proven equivalent", "equiv check error",
            "extra constant output bits"]
    print("\n| task | clean_pass runs | " + " | ".join(cols) + " |\n|---|---|" + "---|" * len(cols))
    for t in tasks:
        print(f"| {t} | {sum(tally[t][k] for k in cols[:5])} | " + " | ".join(str(tally[t][k]) for k in cols) + " |")
    print("\nflagged runs (condition, model, task, rep, equivalence, extra constant output bits, candidate):")
    for f in flagged:
        print(" ", f)


# ----------------------------------------------------------------------------- Phase 2 cell bootstrap
def phase2():
    cats = json.load(open(os.path.join(REPO, "phase2", "twin_analysis_SET2", "module_categories.json")))
    band = {m for m, v in cats.items() if v["difficulty_tier"] == "recoverable"}
    for name in ("set1_run", "set3_run"):
        rows = [e for e in json.load(open(os.path.join(REPO, "phase2", "results", name, "master_log.json")))
                if not e.get("error") and e["module"] in band]
        cell = defaultdict(lambda: defaultdict(list))
        for e in rows:
            cell[(e["model"], e["module"])][e["condition"]].append(int(bool(e["pass"])))
        print(f"\n{name}: recoverable band, {len(band)} modules, {len(cell)} (model, module) cells, {len(rows)} valid runs")
        for a in ("sem_adv", "sem_escalate", "sem_escalate_restart"):
            d = {k: v for k, v in cell.items() if v[a] and v["baseline"]}
            diffs = [100 * (sum(v[a]) / len(v[a]) - sum(v["baseline"]) / len(v["baseline"])) for _, v in sorted(d.items())]
            lo, hi = boot_ci(diffs, f"p2:{name}:{a}")
            ka = sum(sum(v[a]) for v in cell.values()); na = sum(len(v[a]) for v in cell.values())
            kb = sum(sum(v["baseline"]) for v in cell.values()); nb = sum(len(v["baseline"]) for v in cell.values())
            print(f"  {a} - baseline: {ka}/{na} vs {kb}/{nb}; cell mean {sg(sum(diffs) / len(diffs))} pts "
                  f"[{sg(lo)}, {sg(hi)}], cells={len(diffs)}, sign-flip p={fp(signflip_p(diffs, f'p2:{name}:{a}'))}")


if __name__ == "__main__":
    if sys.argv[1] == "equiv":                      # equiv <task> [<task> ...]
        equiv(sys.argv[2:])
    else:
        {"keepbest": keepbest, "degenerate": degenerate, "phase2": phase2}[sys.argv[1]]()
