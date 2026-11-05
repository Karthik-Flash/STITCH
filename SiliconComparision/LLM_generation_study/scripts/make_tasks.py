#!/usr/bin/env python3
"""Build tasks/<module>/ in the Phase 3 task format (the format phase3/runner/stitch_runner_p3.py and the
llm_oneshot_vs_stitch pipeline read) for the 7 modules of the golden router. tasks/ is generated; edit specs/ or
golden/ and run this again.

  spec.md            specs/<m>.md without the generated-block markers: the only text the LLM gets about the module
  golden.v           golden/rtl/<m>.v from its `module` line on. The header comment is left out: the runner's
                     extract_code() starts at the first "module" in a reply, and router_5port's comment says
                     "top_module", so the runner's mock (which replies with golden.v) would cut the code there.
  input.v            port-only stub of the module (placeholder: the pipeline puts the one-shot output here in its
                     per-run copy of the task)
  tb.v               golden/tb/tb_<m>.v, unchanged: the testbench whose results the loop arms see
  tb_signoff.v       hidden from the LLM: the same testbench with other random seeds (seed + 1000) and, where it is
                     random-length, twice the traffic
  tb_signoff_mesh.v  router_5port only: golden/tb/tb_mesh2x2.v with the same changes (2x2 mesh of 4 routers)
  meta.json          top, children, descendants, checked outputs, sign-off testbenches
  lib/, stubs/       parents only: golden files of all descendants (simulation), and port-only stubs of the direct
                     children (lint and synthesis see only the parent's own code)

Usage (from the study folder): python scripts/make_tasks.py
"""
import json
import os
import re
import shutil
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import spec_ports as SP  # noqa: E402

STUDY = SP.STUDY
TB = os.path.join(STUDY, "golden", "tb")
TASKS = os.path.join(STUDY, "tasks")
MARKER = re.compile(r"^<!-- (BEGIN|END) generated: \w+ -->\n", re.M)
# Sign-off changes per testbench: (text, replacement); each text must occur exactly once. Every seed moves by 1000.
LONGER = {
    "tb_fifo.v": [("cyc < 20000", "cyc < 40000")],
    "tb_rr_arbiter.v": [("cyc < 20000", "cyc < 40000")],
    "tb_input_port.v": [("cyc < 30000", "cyc < 60000")],
    "tb_output_port.v": [("cyc < 30000", "cyc < 60000")],
    "tb_flit_mux.v": [],                 # every select value already; new random data only
    "tb_route_compute.v": [],            # exhaustive over type, destination and address; new random other bits only
    "tb_router_5port.v": [("NPKT = 400, QN = 4096", "NPKT = 800, QN = 8192"), ("cyc < 100000", "cyc < 200000")],
    "tb_mesh2x2.v": [("NPKT = 300, QN = 2048", "NPKT = 600, QN = 4096"), ("cyc < 200000", "cyc < 400000")],
}


def signoff(tb_name):
    src = open(os.path.join(TB, tb_name)).read()
    seeds = re.findall(r"\bseed = (\d+)", src)
    assert len(seeds) == 1, (tb_name, seeds)
    src = src.replace(f"seed = {seeds[0]}", f"seed = {int(seeds[0]) + 1000}")
    for old, new in LONGER[tb_name]:
        assert src.count(old) == 1, (tb_name, old)
        src = src.replace(old, new)
    return f"// SIGN-OFF copy of golden/tb/{tb_name}, made by scripts/make_tasks.py: seed + 1000" + \
        (", twice the traffic" if LONGER[tb_name] else "") + ".\n" + src


def stub(m):
    ps = SP.ports(m)
    return f"module {m} (\n" + ",\n".join(f"    {SP.decl(p)[:-1]}" for p in ps) + "\n);\nendmodule\n"


def descendants(m):
    out = []
    for c, _ in SP.children(m):
        for d in descendants(c) + [c]:
            if d not in out:
                out.append(d)
    return out


def write(path, text):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    open(path, "w", encoding="utf-8", newline="\n").write(text)


def main():
    if os.path.isdir(TASKS):
        shutil.rmtree(TASKS)
    for m in SP.MODULES:
        d = os.path.join(TASKS, m)
        write(os.path.join(d, "spec.md"), MARKER.sub("", open(os.path.join(SP.SPECS, m + ".md"), encoding="utf-8").read()))
        src = open(os.path.join(SP.RTL, m + ".v")).read()
        write(os.path.join(d, "golden.v"), src[src.index(f"module {m} ("):])
        write(os.path.join(d, "input.v"), stub(m))
        write(os.path.join(d, "tb.v"), open(os.path.join(TB, f"tb_{m}.v")).read())
        write(os.path.join(d, "tb_signoff.v"), signoff(f"tb_{m}.v"))
        tbs = ["tb_signoff.v"]
        if m == "router_5port":
            write(os.path.join(d, "tb_signoff_mesh.v"), signoff("tb_mesh2x2.v"))
            tbs.append("tb_signoff_mesh.v")
        kids, desc = [c for c, _ in SP.children(m)], descendants(m)
        for c in desc:
            write(os.path.join(d, "lib", c + ".v"), open(os.path.join(SP.RTL, c + ".v")).read())
        for c in kids:
            write(os.path.join(d, "stubs", c + ".v"), stub(c))
        meta = {"track": "N", "top": m, "source": f"golden/rtl/{m}.v", "children": kids, "descendants": desc,
                "checked_outputs": [n for dr, _, n in SP.ports(m) if dr == "output"], "not_checked": [],
                "timing_dependent": False, "signoff_verdict": "testbench", "signoff_tbs": tbs,
                "mutant_output": None, "phase3_task": None}
        write(os.path.join(d, "meta.json"), json.dumps(meta, indent=1) + "\n")
        print(f"{m}: children {kids or 'none'}, lib {desc or 'none'}, sign-off {tbs}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
