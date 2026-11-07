"""Vivado on every pure LLM router that compiles, with the golden's flow, part and constraints
(scripts/vivado/flow.tcl, golden/constraints/router_5port.xdc). Writes reports/VIVADO_LLM.md and reports/VIVADO_LLM.json.

A pure router is one arm's 7 final files of one rep (results/<model>/outputs/<arm>/rep<r>/), nothing golden.
Status from reports/GEN_<model>.json (scripts/analyze_gen.py): `working` = router testbench, router sign-off and 2x2
mesh sign-off all pass; `failing` = compiles but fails a testbench; routers that do not compile are listed, not run.
Failing routers are reported for latches, loops, DRC, methodology and warnings; PPA is compared with the golden only
for working ones. The golden is run again through the same code first; its numbers must equal reports/VIVADO_GOLDEN.md.
Counts only, never percentages.

Run on Windows (Vivado 2022.2):  python scripts/vivado/vivado_routers.py [model ...]   (default: every results/<model>)
Run folders: vivado/llm/<model>/<arm>_rep<r>/ (gitignored). Finished runs (routed reports present) are not redone.
--projects: instead, create a GUI project (scripts/vivado/create_project.tcl) for every router that compiles and for
the golden, in vivado/projects/<model>_<arm>_rep<r>/ (list in vivado/projects/PROJECTS.md). Same part, constraints,
out-of-context synthesis and testbenches (sim_1 router, sim_mesh 2x2 mesh) as the golden project.
"""
import json
import os
import shutil
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import run_vivado as V  # noqa: E402

STUDY = V.STUDY
MODULES = ["fifo", "route_compute", "rr_arbiter", "flit_mux", "input_port", "output_port", "router_5port"]
ARMS = ["oneshot", "simloop", "stitch"]
GOLDEN = {"luts": 716, "lut_mem": 110, "ff": 245, "latch": 0, "wns": 0.209, "power_dyn": 0.010, "power_total": 0.113}
OOC_WARN = set(V.KNOWN)          # warning ids the golden run has, explained in VIVADO_GOLDEN.md


def run(name, rtl_files):
    base = os.path.join(STUDY, "vivado", "llm", name)
    impl = os.path.join(base, "impl")
    if not os.path.exists(os.path.join(impl, "power_routed.rpt")):
        rtl = os.path.join(base, "rtl")
        shutil.rmtree(rtl, ignore_errors=True)
        os.makedirs(rtl)
        for f in rtl_files:
            shutil.copy(f, rtl)
        print(f"vivado {name} ...", flush=True)
        V.flow(rtl, impl)
    try:
        return V.parse(impl)
    except (OSError, AttributeError, TypeError) as e:       # synthesis or implementation stopped: no routed reports
        log = os.path.join(impl, "vivado.log")
        err = next((l.strip() for l in open(log, errors="ignore") if l.startswith("ERROR")), repr(e)) \
            if os.path.exists(log) else repr(e)
        return {"error": err}


def projects(models):
    tcl = os.path.join(STUDY, "scripts", "vivado", "create_project.tcl")
    root = os.path.join(STUDY, "vivado", "projects")
    rows = ["# Vivado GUI projects", "", "Made by `scripts/vivado/vivado_routers.py --projects`. Open the .xpr in Vivado 2022.2;",
            "Run Synthesis / Run Implementation use the same out-of-context flow as `flow.tcl`.", "",
            "| project | status (scripts/analyze_gen.py) | .xpr |", "|---|---|---|"]
    jobs = [("golden", "reference", V.RTL)]
    for model in models:
        gen = json.load(open(os.path.join(STUDY, "reports", f"GEN_{model}.json")))["routers"]
        for arm in ARMS:
            for r in range(1, 6):
                st = gen[f"{arm}|{r}"]
                if st["tb"] == "COMPILE_ERROR":
                    continue
                rtl = os.path.join(STUDY, "vivado", "llm", model, f"{arm}_rep{r}", "rtl")
                jobs.append((f"{model}_{arm}_rep{r}", "working" if st["works"] else "failing", rtl))
    for name, status, rtl in jobs:
        pdir = os.path.join(root, name)
        xpr = os.path.join(pdir, "router.xpr")
        if not os.path.exists(xpr):
            os.makedirs(pdir, exist_ok=True)
            print(f"project {name} ...", flush=True)
            V.run([V.tool("vivado"), "-mode", "batch", "-nojournal", "-nolog", "-source", tcl, "-tclargs",
                   rtl.replace("\\", "/"), pdir.replace("\\", "/"), "router"], pdir, "create_project.out")
        rows.append(f"| {name} | {status} | `{xpr}` |" if os.path.exists(xpr) else f"| {name} | {status} | NOT CREATED |")
    open(os.path.join(root, "PROJECTS.md"), "w", newline="\n").write("\n".join(rows) + "\n")
    print("\n".join(rows))
    return 0


def main():
    if "--projects" in sys.argv:
        sys.argv.remove("--projects")
        return projects(sys.argv[1:] or sorted(d for d in os.listdir(os.path.join(STUDY, "results"))
                                               if os.path.isdir(os.path.join(STUDY, "results", d))))
    models = sys.argv[1:] or sorted(d for d in os.listdir(os.path.join(STUDY, "results"))
                                    if os.path.isdir(os.path.join(STUDY, "results", d)))
    g = run("golden", [os.path.join(V.RTL, f) for f in sorted(os.listdir(V.RTL))])
    same = {k: (g.get(k), v) for k, v in GOLDEN.items()
            if g.get(k) is None or (round(g[k], 3) != v if isinstance(v, float) else g[k] != v)}
    print("golden:", "same as VIVADO_GOLDEN.md" if not same else f"DIFFERS {same}", flush=True)
    res = {}
    for model in models:
        gen = json.load(open(os.path.join(STUDY, "reports", f"GEN_{model}.json")))["routers"]
        for arm in ARMS:
            for r in range(1, 6):
                st = gen[f"{arm}|{r}"]
                status = "working" if st["works"] else ("no compile" if st["tb"] == "COMPILE_ERROR" else "failing")
                files = [os.path.join(STUDY, "results", model, "outputs", arm, f"rep{r}", f"{m}.v") for m in MODULES]
                res[(model, arm, r)] = {"status": status, "icarus_yosys_clean": st["clean"],
                                        **({} if status == "no compile" else run(f"{model}/{arm}_rep{r}", files))}

    def drc(x):
        return {k: v for k, v in x.get("drc", {}).items() if k not in V.OOC_DRC}

    def new_warn(x):
        return {k: v for k, v in x.get("warnings", {}).items() if k not in OOC_WARN}

    def chk(x):
        return {k: v for k, v in x.get("checks", {}).items() if v}

    fmt = lambda d: ", ".join(f"{k} {v}" for k, v in sorted(d.items())) or "none"  # noqa: E731
    md = ["# LLM routers in Vivado", "",
          "Generated by `scripts/vivado/vivado_routers.py` with the golden's flow, part xc7z020clg484-1,",
          "out-of-context, 100 MHz (`golden/constraints/router_5port.xdc`). Status from `scripts/analyze_gen.py`:",
          "working = router testbench, router sign-off and 2x2 mesh sign-off all pass. PPA is compared with the golden",
          "only for working routers. Warnings: only ids the golden run does not have.", "",
          f"Golden through the same code: {'same numbers as VIVADO_GOLDEN.md' if not same else 'DIFFERS: ' + str(same)}"
          f" (LUT {g.get('luts')}, FF {g.get('ff')}, WNS {g.get('wns')} ns, dynamic {g.get('power_dyn')} W).", "",
          "| model | arm | rep | status | LUT (mem) | FF | latches | WNS ns | fmax MHz | dyn W | check_timing | "
          "latch msgs | DRC (non-OOC) | methodology | new warning ids |",
          "|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|"]
    for (model, arm, r), x in res.items():
        if x["status"] == "no compile":
            md.append(f"| {model} | {arm} | {r} | no compile | | | | | | | | | | | |")
        elif "error" in x:
            md.append(f"| {model} | {arm} | {r} | {x['status']}, Vivado stopped: {x['error'][:80]} | | | | | | | | | | | |")
        else:
            md.append(f"| {model} | {arm} | {r} | {x['status']} | {x['luts']} ({x['lut_mem']}) | {x['ff']} | {x['latch']} | "
                      f"{x['wns']:.3f} | {x['fmax']:.1f} | {x['power_dyn']:.3f} | {fmt(chk(x))} | {x['latch_msgs']} | "
                      f"{fmt(drc(x))} | {fmt(x['methodology'])} | {fmt(new_warn(x))} |")
    md += ["", "## Working routers against the golden", "",
           "| model | arm | working (of 5) | timing met | 0 latches | 0 non-OOC DRC | 0 methodology | LUT range | "
           "FF range | WNS range ns | dynamic W range |", "|---|---|---|---|---|---|---|---|---|---|---|"]
    for model in models:
        for arm in ARMS:
            w = [x for (mo, a, _), x in res.items() if mo == model and a == arm and x["status"] == "working" and "luts" in x]
            rng = lambda k, f="{}": (f.format(min(x[k] for x in w)) + " to " + f.format(max(x[k] for x in w))) if w else "-"  # noqa: E731
            md.append(f"| {model} | {arm} | {len(w)} | {sum(x['wns'] >= 0 for x in w)} | {sum(x['latch'] == 0 for x in w)} | "
                      f"{sum(not drc(x) for x in w)} | {sum(not x['methodology'] for x in w)} | {rng('luts')} | {rng('ff')} | "
                      f"{rng('wns', '{:.3f}')} | {rng('power_dyn', '{:.3f}')} |")
    md += ["", f"Golden: LUT {GOLDEN['luts']}, FF {GOLDEN['ff']}, WNS +{GOLDEN['wns']} ns, dynamic {GOLDEN['power_dyn']} W.", ""]
    open(os.path.join(STUDY, "reports", "VIVADO_LLM.md"), "w", newline="\n").write("\n".join(md))
    json.dump({"|".join(map(str, k)): v for k, v in res.items()} | {"golden": g},
              open(os.path.join(STUDY, "reports", "VIVADO_LLM.json"), "w"), indent=1)
    print("\n".join(md))
    return 0 if not same else 1


if __name__ == "__main__":
    sys.exit(main())
