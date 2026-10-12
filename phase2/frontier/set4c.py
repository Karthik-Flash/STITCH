"""Set 4c (SET4_PREREG Amendment 4): one Gemini Pro reasoning model on the residual floor
(adder_pipe_64bit, alu, freq_divbyfrac; baseline + sem_escalate_restart; N=3). Descriptive, never pooled.
  python set4c.py project   worst case from Set 4b's observed per-call token maxima, at Pro prices (Step 1)
  python set4c.py after1    observed cost per run after step (i) + all-fail upper bound for the rest
  python set4c.py analyze   Q5-Q7 tables, cost, freq_divbyfrac first failing check (needs no simulator)
  python set4c.py trace     freq_divbyfrac shifted-trace comparison of every final candidate (WSL, matched suite)
"""
import collections
import glob
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
PHASE2 = os.path.dirname(HERE)
SET4 = os.path.join(PHASE2, "results", "set4_api")
ROOT_4B = os.path.join(SET4, "floor_full")
ROOT_4C = os.path.join(SET4, "set4c", "gemini")
LEDGER_4C = os.path.join(SET4, "ledgers_4c", "gemini_ledger.jsonl")
OUT = os.path.join(SET4, "analysis_4c")
MODULES = ["adder_pipe_64bit", "alu", "freq_divbyfrac"]
CONDS = ["baseline", "sem_escalate_restart"]
CAPS = {"baseline": 6, "sem_escalate_restart": 8}
THINK, ANSWER = 2048, 8192
CAP_USD = 7.5
INR = 96 * 1.18
PRO = {"gemini-3.1-pro-preview": (2.00, 12.00), "gemini-2.5-pro": (1.25, 10.00)}   # USD/1M, prompts <= 200k
sys.path.insert(0, HERE)


def ledger(paths, tag=None):
    out = []
    for p in paths:
        if os.path.exists(p):
            out += [json.loads(l) for l in open(p, encoding="utf-8") if l.strip()]
    return [c for c in out if tag is None or c.get("tag") == tag]


def project():
    paths = glob.glob(os.path.join(SET4, "ledgers_4b", "*_ledger.jsonl")) + \
        glob.glob(os.path.join(PHASE2, "results", "p3_api", "ledgers", "*_ledger.jsonl"))
    calls = [c for c in ledger(paths, "floor_full") if c.get("status") == "ok" and c.get("module") in MODULES]
    mx_in, mx_out = max(c["input_tokens"] for c in calls), max(c["output_tokens"] for c in calls)
    gem = [c for c in calls if c["provider"] == "gemini"]
    g_in, g_out = max(c["input_tokens"] for c in gem), max(c["output_tokens"] for c in gem)
    print(f"Set 4b calls on {MODULES}: {len(calls)} (all models); max input {mx_in}, max answer {mx_out} tokens; "
          f"Gemini 2.5 Flash only: {len(gem)} calls, max input {g_in}, max answer {g_out}")
    res = {}
    for m, (pi, po) in PRO.items():
        per_call = (mx_in * pi + (mx_out + THINK) * po) / 1e6
        res[m] = {"per_call_usd": per_call, "per_run_usd": 8 * per_call, "worst_usd": 18 * 8 * per_call}
        print(f"{m}: worst per call ${per_call:.4f} (max input x ${pi} + (max answer + {THINK} thinking) x ${po}); "
              f"per run (8 calls) ${8 * per_call:.4f}; 18 runs x 8 calls ${18 * 8 * per_call:.2f} "
              f"(INR {18 * 8 * per_call * INR:.0f}) -> {'over' if 18 * 8 * per_call > CAP_USD else 'within'} ${CAP_USD}")
    json.dump({"max_input": mx_in, "max_answer": mx_out, "gemini_max_input": g_in, "gemini_max_answer": g_out,
               "models": res}, open(os.path.join(OUT, "projection.json"), "w"), indent=1)


def runs_4c():
    p = os.path.join(ROOT_4C, "master_log.json")
    return json.load(open(p, encoding="utf-8")) if os.path.exists(p) else []


def after1():
    calls = [c for c in ledger([LEDGER_4C], "set4c") if c.get("status") == "ok"]
    runs = [r for r in runs_4c() if not r.get("error")]
    by_run = collections.defaultdict(float)
    for c in calls:
        by_run[(c["module"], c["condition"], c["replicate"])] += c["cost_usd"]
    spent = sum(c["cost_usd"] for c in ledger([LEDGER_4C]))
    per_run = [by_run[(r["module"], r["condition"], r["run_replicate"])] for r in runs]
    max_call = max(c["cost_usd"] for c in calls)
    mean_call = sum(c["cost_usd"] for c in calls) / len(calls)
    done = {(r["module"], r["condition"], r["run_replicate"]) for r in runs}
    rest = [(m, c, k) for m in MODULES for c in CONDS for k in (1, 2, 3) if (m, c, k) not in done]
    ub_max = sum(CAPS[c] * max_call for _, c, _ in rest)
    ub_mean = sum(CAPS[c] * mean_call for _, c, _ in rest)
    print(f"after step (i): {len(runs)} runs, {len(calls)} calls; cost per run " +
          ", ".join(f"{r['module']} {r['condition']} r{r['run_replicate']} ${v:.4f} ({r['total_iterations']} it)"
                    for r, v in zip(runs, per_run)))
    print(f"per call: mean ${mean_call:.4f}, max ${max_call:.4f}; ledger so far ${spent:.4f} (smoke included)")
    print(f"remaining {len(rest)} runs, all-fail upper bound (every run at its iteration cap): "
          f"${ub_mean:.2f} at the mean call cost, ${ub_max:.2f} at the max call cost; "
          f"projected total ${spent + ub_mean:.2f} / ${spent + ub_max:.2f} (INR {(spent + ub_mean) * INR:.0f} / "
          f"{(spent + ub_max) * INR:.0f}) vs cap ${CAP_USD}")


def iters(root, r, model_dir="*"):
    d = glob.glob(os.path.join(root, r["module"], model_dir, r["condition"], f"rep{r['run_replicate']}"))
    if not d:
        d = glob.glob(os.path.join(root, r["module"], model_dir, r["condition"], f"replicate_{r['run_replicate']}"))
    d = d[0]
    its = sorted(glob.glob(os.path.join(d, "iter_*")), key=lambda p: int(p.rsplit("_", 1)[1]))
    log = None
    if os.path.exists(os.path.join(d, "run_log.json")):
        log = json.load(open(os.path.join(d, "run_log.json")))["iterations"]
        fired = [it["interpreter_invoked"] for it in log]
    else:
        fired = [it["semantic_fired"] for it in json.load(open(os.path.join(d, "metrics.json")))["per_iter_detail"]]
    return d, its, fired


def first_fail(sim_log):
    m = re.search(r"Failed at\s+(\d+): clk=\s*(\d), clk_div=\s*(\w) \(expected\s+(\d+)\)", sim_log)
    if m:
        return f"check {m.group(1)}: clk_div={m.group(3)}, expected {m.group(4)}"
    return "compile error" if "error" in sim_log.split("--- SIMULATION ---")[0].lower() else "no failing check line"


def analyze():
    runs = [r for r in runs_4c() if not r.get("error")]
    calls = [c for c in ledger([LEDGER_4C], "set4c") if c.get("status") == "ok"]
    res = {"runs": len(runs), "errored": sum(1 for r in runs_4c() if r.get("error")), "table": {}, "runs_detail": []}
    by_run = collections.defaultdict(lambda: collections.Counter())
    for c in calls:
        k = (c["module"], c["condition"], c["replicate"])
        by_run[k]["usd"] += c["cost_usd"]
        by_run[k]["calls"] += 1
        by_run[k]["input"] += c["input_tokens"]
        by_run[k]["thinking"] += c.get("reasoning_tokens", 0)
        by_run[k]["answer"] += c["output_tokens"] - c.get("reasoning_tokens", 0)
    print(f"Set 4c: {len(runs)} valid runs, {res['errored']} errored, {len(calls)} calls")
    print("\n| module | condition | passes | iterations to pass | semantic_fired runs | directive before pass | escalated |")
    print("|---|---|---|---|---|---|---|")
    for m in MODULES:
        for c in CONDS:
            rr = sorted([r for r in runs if r["module"] == m and r["condition"] == c], key=lambda r: r["run_replicate"])
            det = []
            for r in rr:
                d, its, fired = iters(ROOT_4C, r)
                k = r.get("iterations_to_pass") or 0
                dbp = bool(r["pass"]) and any(f for i, f in enumerate(fired, 1) if i < k)
                det.append({"rep": r["run_replicate"], "pass": bool(r["pass"]), "iters_to_pass": r.get("iterations_to_pass"),
                            "total_iters": r["total_iterations"], "sf": bool(r.get("semantic_fired")),
                            "directive_before_pass": dbp, "escalated": bool(r.get("fired_escalate")),
                            **{k2: by_run[(m, c, r["run_replicate"])][k2] for k2 in ("calls", "input", "answer", "thinking", "usd")}})
            res["table"][f"{m}|{c}"] = det
            res["runs_detail"] += [dict(x, module=m, condition=c) for x in det]
            print(f"| {m} | {c} | {sum(x['pass'] for x in det)}/{len(det)} | "
                  f"{[x['iters_to_pass'] for x in det if x['pass']] or '-'} | {sum(x['sf'] for x in det)} | "
                  f"{sum(x['directive_before_pass'] for x in det)} | {sum(x['escalated'] for x in det) if c != 'baseline' else '-'} |")
    print("\ncost per run (tokens input / answer / thinking; USD; INR):")
    for x in res["runs_detail"]:
        print(f"  {x['module']:16s} {x['condition']:21s} r{x['rep']} pass={x['pass']!s:5s} it={x['total_iters']} calls={x['calls']} "
              f"in={x['input']} ans={x['answer']} think={x['thinking']} ${x['usd']:.4f} INR {x['usd'] * INR:.2f}")
    for scope in [None] + CONDS:
        xs = [x for x in res["runs_detail"] if scope in (None, x["condition"])]
        if not xs:
            continue
        usd, k = sum(x["usd"] for x in xs), sum(x["pass"] for x in xs)
        print(f"  {scope or 'all':21s} runs {len(xs)}, passes {k}: INR/run {usd * INR / len(xs):.2f}, "
              f"INR/pass {'-' if not k else round(usd * INR / k, 2)}; tokens in/ans/think "
              f"{sum(x['input'] for x in xs)}/{sum(x['answer'] for x in xs)}/{sum(x['thinking'] for x in xs)}")
    res["spend_usd_all_tags"] = sum(c["cost_usd"] for c in ledger([LEDGER_4C]))
    res["max_thinking_per_call"] = max((c.get("reasoning_tokens", 0) for c in calls), default=0)
    res["truncated"] = sum(1 for c in calls if str(c.get("finish_reason")) in ("MAX_TOKENS",))
    print(f"\nmax thinking tokens per call {res['max_thinking_per_call']} (budget {THINK}); truncated {res['truncated']}; "
          f"ledger total ${res['spend_usd_all_tags']:.4f} (INR {res['spend_usd_all_tags'] * INR:.1f})")

    # Q7: first failing check of every freq_divbyfrac iteration-final log, Set 4c vs Set 4b models
    q7 = collections.defaultdict(collections.Counter)
    for label, root, rs in [("Set 4c", ROOT_4C, runs)] + [
            (p, os.path.join(ROOT_4B, p), [r for r in json.load(open(os.path.join(ROOT_4B, p, "master_log.json")))
                                            if not r.get("error")]) for p in ("openai", "gemini", "anthropic")]:
        for r in rs:
            if r["module"] != "freq_divbyfrac":
                continue
            d, its, _ = iters(root, r)
            last = open(os.path.join(its[-1], "sim_log.txt"), encoding="utf-8", errors="replace").read()
            q7[label]["PASS" if r["pass"] else first_fail(last)] += 1
    res["Q7_first_fail_final_iteration"] = {k: dict(v) for k, v in q7.items()}
    print("\nQ7 freq_divbyfrac, first failing check on each run's final iteration:")
    for k, v in q7.items():
        print(f"  {k:10s} {dict(v)}")
    os.makedirs(OUT, exist_ok=True)
    json.dump(res, open(os.path.join(OUT, "set4c_analysis.json"), "w"), indent=1)


def trace():
    """For the final candidate of every freq_divbyfrac run (Set 4b models and Set 4c) and for the reference: run the
    ORIGINAL testbench with one added line that prints clk_div at each of its 20 checks (same statement position, so the
    same event ordering as the check itself). Compare with the expected sequence at shifts of -2..+2 checks (half
    clock steps) over the overlapping checks, and give the high/low run lengths (shape)."""
    rtllm = os.environ.get("RTLLM_ROOT", "/mnt/d/Projects/RTLLM")
    src = os.path.join(rtllm, "Miscellaneous", "Frequency divider", "freq_divbyfrac")
    tb = open(os.path.join(src, "testbench.v"), encoding="utf-8").read()
    anchor = "for (i = 0; i < 20; i = i + 1) begin"
    assert tb.count(anchor) == 1
    tb = tb.replace(anchor, anchor + '\n            $display("C %0d %0d", i, clk_div);')
    exp = [1 if (i < 3 or 7 <= i < 10 or 14 <= i < 17) else 0 for i in range(20)]   # testbench.v lines 18, 38-44

    def sample(code):
        with tempfile.TemporaryDirectory() as tmp:
            open(os.path.join(tmp, "freq_divbyfrac.v"), "w").write(code)
            open(os.path.join(tmp, "tb.v"), "w").write(tb)
            if subprocess.run(["iverilog", "-o", "s.vvp", "freq_divbyfrac.v", "tb.v"], cwd=tmp,
                              capture_output=True, text=True).returncode:
                return None, None
            out = subprocess.run(["vvp", "-n", "s.vvp"], cwd=tmp, capture_output=True, text=True, timeout=30).stdout
        tr = [int(v) if v in "01" else -1 for v in re.findall(r"^C \d+ (\w)", out, re.M)]
        return tr, "Your Design Passed" in out

    def shape(tr):
        runs, cur, n = [], None, 0
        for v in tr:
            if v == cur:
                n += 1
            else:
                if cur is not None:
                    runs.append(f"{'H' if cur == 1 else 'L' if cur == 0 else 'X'}{n}")
                cur, n = v, 1
        return " ".join(runs + [f"{'H' if cur == 1 else 'L' if cur == 0 else 'X'}{n}"])

    def compare(tr):   # shift d: candidate check i+d against expected check i, over the overlap
        return {d: (sum(tr[i + d] == exp[i] for i in range(20) if 0 <= i + d < 20), 20 - abs(d)) for d in (-2, -1, 0, 1, 2)}

    ref, ref_pass = sample(open(os.path.join(src, "verified_freq_divbyfrac.v")).read().replace("verified_freq_divbyfrac", "freq_divbyfrac"))
    out = {"expected": exp, "reference": {"trace": ref, "passes": ref_pass, "shape": shape(ref), "by_shift": compare(ref)}}
    print(f"expected at checks 0..19: {''.join(map(str, exp))} (shape {shape(exp)})")
    print(f"reference: passes={ref_pass} trace {''.join(map(str, ref))} by shift {compare(ref)}")
    rows, first = collections.defaultdict(collections.Counter), collections.defaultdict(collections.Counter)
    for label, root in [("Set 4c gemini-2.5-pro", ROOT_4C)] + [(p, os.path.join(ROOT_4B, p)) for p in ("openai", "gemini", "anthropic")]:
        ml = os.path.join(root, "master_log.json")
        if not os.path.exists(ml):
            continue
        for r in json.load(open(ml)):
            if r.get("error") or r["module"] != "freq_divbyfrac":
                continue
            d, its, _ = iters(root, r)
            tr, ok = sample(open(os.path.join(its[-1], "freq_divbyfrac.v"), encoding="utf-8", errors="replace").read())
            if tr is None:
                rows[label]["compile error"] += 1
                continue
            cm = compare(tr)
            pure = [k for k in (-1, 1, -2, 2) if cm[k][0] == cm[k][1]]
            key = "matches expected (0 shift)" if cm[0][0] == 20 else (
                f"pure shift {pure[0]:+d} check(s)" if pure else f"other shape: {shape(tr)}")
            rows[label][key] += 1
            first[label][next((f"check {i}: clk_div={tr[i]}, expected {exp[i]}" for i in range(20) if tr[i] != exp[i]), "none")] += 1
    out["final_candidates"] = {k: dict(v) for k, v in rows.items()}
    out["first_mismatch"] = {k: dict(v) for k, v in first.items()}
    for k in rows:
        print(f"  {k}: {dict(rows[k])}")
        print(f"     first mismatching check: {dict(first[k])}")
    os.makedirs(OUT, exist_ok=True)
    json.dump(out, open(os.path.join(OUT, "freq_divbyfrac_trace.json"), "w"), indent=1)


def refcheck():
    """Reference design under its own testbench, logged at every clk edge ($strobe = end-of-timestep values):
    counter period in half clock steps, clk_div periods per counter wrap, clk_div high/low run lengths. Compares with
    spec line 17 ("The counter cycles through 7 half clock steps")."""
    rtllm = os.environ.get("RTLLM_ROOT", "/mnt/d/Projects/RTLLM")
    src = os.path.join(rtllm, "Miscellaneous", "Frequency divider", "freq_divbyfrac")
    tb = open(os.path.join(src, "testbench.v"), encoding="utf-8").read()
    assert tb.rstrip().endswith("endmodule")
    tb = tb.rstrip()[:-len("endmodule")] + (
        '    always @(clk) $strobe("E %0t %0d %0d %0d %0d %0d", $time, clk, uut.cnt, clk_div, uut.clk_ave_r, uut.clk_adjust_r);\n'
        'endmodule\n')
    ref = open(os.path.join(src, "verified_freq_divbyfrac.v")).read().replace("verified_freq_divbyfrac", "freq_divbyfrac")
    with tempfile.TemporaryDirectory() as tmp:
        open(os.path.join(tmp, "dut.v"), "w").write(ref)
        open(os.path.join(tmp, "tb.v"), "w").write(tb)
        subprocess.run(["iverilog", "-o", "s.vvp", "dut.v", "tb.v"], cwd=tmp, check=True)
        out = subprocess.run(["vvp", "-n", "s.vvp"], cwd=tmp, capture_output=True, text=True, timeout=30).stdout
    ev = [tuple(int(x) for x in m) for m in re.findall(r"^E (\d+) (\d) (\d+) (\d) (\d) (\d)", out, re.M)]
    ev = [e for e in ev if e[0] >= 10000]            # after reset release (t = 10 ns = 10000 ps)
    print("t(ps) clk cnt clk_div ave adj")
    for e in ev[:30]:
        print(" ".join(map(str, e)))
    # posedges where cnt reads 1 (cnt is already 1 at the posedge that releases reset, t = 10 ns); one sample = 5 ns
    wraps = [i for i, e in enumerate(ev) if e[1] == 1 and e[2] == 1]
    res_cnt = {"cnt_increments_per_posedge": all((ev[i + 2][2] - ev[i][2]) % 7 == 1 for i in range(0, len(ev) - 2, 2)),
               "cnt_changes_on_negedge": any(ev[i][2] != ev[i - 1][2] for i in range(1, len(ev)) if ev[i][1] == 0)}
    period = [wraps[k + 1] - wraps[k] for k in range(len(wraps) - 1)]
    div = [e[3] for e in ev]
    rises = [i for i in range(1, len(div)) if div[i] == 1 and div[i - 1] == 0]
    div_period = [rises[k + 1] - rises[k] for k in range(len(rises) - 1)]      # rise to rise, half-steps
    per_wrap = [p / d for p in period for d in sorted(set(div_period))]
    runs, cur, n = [], div[0], 0
    for v in div:
        if v == cur:
            n += 1
        else:
            runs.append(f"{'H' if cur else 'L'}{n}")
            cur, n = v, 1
    res = {"counter_period_half_steps": period, "clk_div_period_half_steps": div_period,
           "clk_div_periods_per_counter_wrap": per_wrap,
           "clk_div_runs_half_steps": " ".join(runs), "passes": "Your Design Passed" in out, **res_cnt}
    print(json.dumps(res))
    json.dump(res, open(os.path.join(OUT, "freq_divbyfrac_refcheck.json"), "w"), indent=1)


if __name__ == "__main__":
    os.makedirs(OUT, exist_ok=True)
    {"project": project, "after1": after1, "analyze": analyze, "trace": trace, "refcheck": refcheck}[sys.argv[1]]()
