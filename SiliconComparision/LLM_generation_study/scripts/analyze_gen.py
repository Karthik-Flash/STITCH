#!/usr/bin/env python3
"""Analysis of one model's generation results (results/<model>/, copied back from the HPC). Writes
reports/GEN_<model>.md and reports/GEN_<model>.json.

Per module, arm (oneshot, simloop, stitch) and rep:
  - integrity: outputs/<arm>/rep<r>/<m>.v equals the record (one-shot output_sha256) or the run's final candidate
  - from the HPC evaluation (cluster toolchain): compile, loop testbench tb.v, struct_clean (Yosys 0 latches,
    0 loops, no hard Verilator warning; lint and synthesis with port-only stubs of the children), LLM calls,
    stop reason, STITCH classes fired. One-shot = iteration 0 of the arm runs (the same file, evaluated once).
  - sign-off (hidden testbenches tb_signoff*.v, golden children), run here
  - so_clean = tb.v pass + every sign-off pass + struct_clean
  - distinct final files over the 5 reps; extraction cut (the runner's extract_code started inside a comment)
Per arm and rep, the pure router: the arm's 7 final files together, no golden file: router testbench, both sign-off
testbenches (router, 2x2 mesh), and Verilator lint + Yosys synthesis of the whole hierarchy.
Counts only, never percentages.

Run in WSL (Icarus, Verilator, Yosys):  python3 scripts/analyze_gen.py gemma4_31b-it-q4_K_M
The sign-off and pure-router simulations use the local toolchain (named in the report).
"""
import hashlib
import json
import os
import re
import shutil
import sys
import tempfile

STUDY = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(STUDY, "pipeline"))
import p3_bridge as B  # noqa: E402

E = B.E
MODULES = ["fifo", "route_compute", "rr_arbiter", "flit_mux", "input_port", "output_port", "router_5port"]
ARMS = {"oneshot": None, "simloop": "baseline", "stitch": "sem_esc_restart_v3"}
REPS = range(1, 6)
TASKS = os.path.join(STUDY, "tasks")


def sha_file(p):
    return hashlib.sha256(open(p, "rb").read().replace(b"\r\n", b"\n")).hexdigest()


def tool_line(cmd):
    rc, out, _ = E._run(cmd, ".", 30)
    return out.strip().splitlines()[0] if out.strip() else "MISSING"


def first_line(log):
    return next((l.strip() for l in log.splitlines() if E.PASS_TOKEN in l or E.FAIL_TOKEN in l), "")


def sim(files, tb):
    wd = tempfile.mkdtemp(prefix="ana_")
    try:
        shutil.copy(tb, os.path.join(wd, "tb.v"))
        r = E.simulate([os.path.abspath(f) for f in files], "tb.v", wd, timeout=600)
        return r["outcome"], first_line(r["log"])
    finally:
        shutil.rmtree(wd, ignore_errors=True)


def extraction_cut(response, m):
    """True if the runner's extract_code cut inside text: the fenced code holds `module <m>` but the extracted
    file does not start with it."""
    code = B.runner().extract_code(response) if response else ""
    return f"module {m}" in response and not code.lstrip().startswith(f"module {m}")


def main():
    model = sys.argv[1]
    work = os.path.join(STUDY, "results", model)
    rdir = lambda r, cond, m: os.path.join(work, "arms", f"rep{r}", "results", model, cond, m, "rep1")  # noqa: E731
    rows, problems = {}, []
    for m in MODULES:
        meta = json.load(open(os.path.join(TASKS, m, "meta.json")))
        lib = sorted(os.path.join(TASKS, m, "lib", f) for f in os.listdir(os.path.join(TASKS, m, "lib"))) \
            if os.path.isdir(os.path.join(TASKS, m, "lib")) else []
        for arm, cond in ARMS.items():
            for r in REPS:
                out = os.path.join(work, "outputs", arm, f"rep{r}", f"{m}.v")
                mt = json.load(open(os.path.join(rdir(r, cond or "baseline", m), "metrics.json")))
                ev = mt["per_iter"][0] if arm == "oneshot" else mt["per_iter"][-1]
                if arm == "oneshot":
                    rec = json.load(open(os.path.join(work, "oneshot", f"rep{r}", m, "record.json")))
                    resp = open(os.path.join(work, "oneshot", f"rep{r}", m, "response.txt"), encoding="utf-8").read()
                    if rec["output_sha256"] != hashlib.sha256(open(out, encoding="utf-8").read().encode()).hexdigest():
                        problems.append(f"{arm} rep{r} {m}: output differs from record")
                    calls, stop, classes, fired, think = 1, "-", [], False, rec.get("thinking_chars") or 0
                    tok = rec.get("tokens_out") or 0
                else:
                    local = mt["final_candidate"].split(f"/results/{model}/", 1)[1]
                    if sha_file(os.path.join(work, local)) != sha_file(out):
                        problems.append(f"{arm} rep{r} {m}: output differs from final candidate")
                    calls, stop, classes, fired = mt["llm_calls"], mt["stop_reason"], mt["classes_fired"], mt["semantic_fired"]
                    resp = ""
                    think = tok = 0
                    for k in range(1, calls + 1):
                        d = os.path.join(rdir(r, cond, m), f"iter{k}")
                        lm = os.path.join(d, "llm_meta.json")
                        if os.path.exists(lm):
                            j = json.load(open(lm))
                            think += j.get("thinking_chars") or 0
                            tok += j.get("eval_count") or 0
                        if k == calls and os.path.exists(os.path.join(d, "response.txt")):
                            resp = open(os.path.join(d, "response.txt"), encoding="utf-8").read()
                so = {tb: sim([out] + lib, os.path.join(TASKS, m, tb)) for tb in meta["signoff_tbs"]} \
                    if ev["compile_ok"] else {tb: ("COMPILE_ERROR", "") for tb in meta["signoff_tbs"]}
                so_pass = all(v[0] == "PASS" for v in so.values())
                rows[(m, arm, r)] = {
                    "compile": ev["compile_ok"], "tb": ev["func_pass"], "struct_clean": ev["struct_clean"],
                    "latches": ev["latch_events"], "loops": ev["yosys_loops"], "hard_lint": ev["verilator_hard"],
                    "lint_codes": ev["verilator_codes"], "signoff": {k: v[0] for k, v in so.items()},
                    "signoff_line": {k: v[1] for k, v in so.items()}, "signoff_pass": so_pass,
                    "so_clean": bool(ev["func_pass"] and so_pass and ev["struct_clean"]),
                    "calls": calls, "stop": stop, "classes": classes, "fired": fired, "thinking_chars": think,
                    "tokens_out": tok, "sha": sha_file(out), "extraction_cut": extraction_cut(resp, m) if resp else None}
                print(m, arm, r, {k: rows[(m, arm, r)][k] for k in ("compile", "tb", "signoff_pass", "struct_clean",
                                                                    "calls", "stop")}, flush=True)

    # Pure routers: the arm's own 7 files, nothing golden.
    routers = {}
    for arm in ARMS:
        for r in REPS:
            files = [os.path.join(work, "outputs", arm, f"rep{r}", f"{m}.v") for m in MODULES]
            res = {tb: sim(files, os.path.join(TASKS, "router_5port", tb))
                   for tb in ("tb.v", "tb_signoff.v", "tb_signoff_mesh.v")}
            wd = tempfile.mkdtemp(prefix="ana_r_")
            try:
                v = E.lint([os.path.abspath(f) for f in files], "router_5port", wd)
                y = E.synth([os.path.abspath(f) for f in files], "router_5port", wd)
            finally:
                shutil.rmtree(wd, ignore_errors=True)
            routers[(arm, r)] = {
                "tb": res["tb.v"][0], "signoff": res["tb_signoff.v"][0], "mesh": res["tb_signoff_mesh.v"][0],
                "lines": {k: v_[1] for k, v_ in res.items()}, "yosys_ok": y["ok"], "latches": y["latch_events"],
                "loops": y["loops"], "hard_lint": v["n_hard"], "lint_codes": v["codes"],
                "works": all(x[0] == "PASS" for x in res.values()),
                "clean": bool(y["ok"] and y["latch_events"] == 0 and y["loops"] == 0 and v["n_hard"] == 0)}
            print("router", arm, r, {k: routers[(arm, r)][k] for k in ("tb", "signoff", "mesh", "clean")}, flush=True)

    tv = "; ".join(tool_line(c) for c in ([E.IVERILOG, "-V"], [E.VERILATOR, "--version"], [E.YOSYS, "-V"]))
    count = lambda pred: sum(1 for r in REPS if pred(r))  # noqa: E731
    md = [f"# Generation results: {model}", "",
          "Generated by `scripts/analyze_gen.py` from `results/" + model + "/`. Counts are out of 5 reps. Columns:",
          "`tb` = loop testbench passes; `signoff` = every hidden sign-off testbench passes; `clean` = struct_clean",
          "(Yosys 0 latches and 0 loops, no hard Verilator warning); `so_clean` = all three. tb and clean come from the",
          f"HPC evaluation (cluster toolchain); sign-off and the pure routers were run here ({tv}).", "",
          f"Integrity: {'every output equals its record or final candidate' if not problems else 'PROBLEMS: ' + '; '.join(problems)}.",
          "", "## Modules (parents tested with the golden children)", "",
          "| module | arm | compile | tb | signoff | clean | so_clean | distinct files | LLM calls (sum) | stop reasons |",
          "|---|---|---|---|---|---|---|---|---|---|"]
    for m in MODULES:
        for arm in ARMS:
            rr = [rows[(m, arm, r)] for r in REPS]
            stops = {}
            for x in rr:
                stops[x["stop"]] = stops.get(x["stop"], 0) + 1
            md.append(f"| {m} | {arm} | {count(lambda r: rows[(m, arm, r)]['compile'])} | "
                      f"{count(lambda r: rows[(m, arm, r)]['tb'])} | {count(lambda r: rows[(m, arm, r)]['signoff_pass'])} | "
                      f"{count(lambda r: rows[(m, arm, r)]['struct_clean'])} | {count(lambda r: rows[(m, arm, r)]['so_clean'])} | "
                      f"{len({x['sha'] for x in rr})} | {sum(x['calls'] for x in rr)} | "
                      + ", ".join(f"{k} {v}" for k, v in sorted(stops.items())) + " |")
    md += ["", "Totals over the 7 modules x 5 reps (35 per arm):", "",
           "| arm | tb | signoff | clean | so_clean | LLM calls | thinking characters | output tokens |", "|---|---|---|---|---|---|---|---|"]
    for arm in ARMS:
        rr = [rows[(m, arm, r)] for m in MODULES for r in REPS]
        md.append(f"| {arm} | {sum(x['tb'] for x in rr)} | {sum(x['signoff_pass'] for x in rr)} | "
                  f"{sum(x['struct_clean'] for x in rr)} | {sum(x['so_clean'] for x in rr)} | {sum(x['calls'] for x in rr)} | "
                  f"{sum(x['thinking_chars'] for x in rr)} | {sum(x['tokens_out'] for x in rr)} |")
    md += ["", "## Pure routers (the arm's own 7 files, no golden file)", "",
           "| arm | rep | router tb | router sign-off | mesh sign-off | Yosys ok | latches | loops | hard lint | works | clean |",
           "|---|---|---|---|---|---|---|---|---|---|---|"]
    for arm in ARMS:
        for r in REPS:
            x = routers[(arm, r)]
            md.append(f"| {arm} | {r} | {x['tb']} | {x['signoff']} | {x['mesh']} | {x['yosys_ok']} | {x['latches']} | "
                      f"{x['loops']} | {x['hard_lint']} | {'yes' if x['works'] else 'no'} | {'yes' if x['clean'] else 'no'} |")
    md += ["", "Working pure routers (all three testbenches pass): " +
           ", ".join(f"{arm} {count(lambda r: routers[(arm, r)]['works'])} of 5" for arm in ARMS) + ".",
           "Working and clean: " + ", ".join(f"{arm} {count(lambda r: routers[(arm, r)]['works'] and routers[(arm, r)]['clean'])} of 5"
                                             for arm in ARMS) + ".", ""]
    # STITCH's semantic feedback on parents: lint runs on dut.v + port-only stubs of the children (p3_bridge), so
    # the stubs' unused inputs and undriven outputs reach the interpreter as if they were the module's own.
    sem = stub = 0
    for m in ("input_port", "output_port", "router_5port"):
        for r in REPS:
            d = os.path.join(rdir(r, "sem_esc_restart_v3", m))
            for k in range(1, rows[(m, "stitch", r)]["calls"] + 1):
                pr = open(os.path.join(d, f"iter{k}", "prompt.txt"), encoding="utf-8").read()
                if "SEMANTIC ANALYSIS" in pr:
                    sem += 1
                    stub += "Clock 'clk' is declared but NEVER USED" in pr
    md += [f"STITCH prompts on parent modules with semantic feedback: {sem}; of these, {stub} state that 'clk' is never"
           " used, which comes from the children's port-only stubs (the parent passes clk to its children).", ""]
    cuts = [f"{m} {arm} rep{r}" for (m, arm, r), x in rows.items() if x["extraction_cut"]]
    md += [f"Extraction cuts (runner's extract_code started inside a comment): {len(cuts)}" + (f" ({', '.join(cuts)})" if cuts else "") + ".", ""]
    open(os.path.join(STUDY, "reports", f"GEN_{model}.md"), "w", newline="\n").write("\n".join(md))
    json.dump({"rows": {"|".join(map(str, k)): v for k, v in rows.items()},
               "routers": {"|".join(map(str, k)): v for k, v in routers.items()}, "problems": problems, "tools": tv},
              open(os.path.join(STUDY, "reports", f"GEN_{model}.json"), "w"), indent=1)
    print("\n".join(md))
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main())
