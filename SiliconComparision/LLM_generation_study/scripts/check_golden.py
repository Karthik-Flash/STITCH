"""Check the golden router with the same functions the STITCH runner uses (phase3/runner/p3_eval.py, imported
read-only): Icarus testbench, Verilator lint, Yosys synthesis (latches, logic loops). Also proves with Yosys that
route_compute is equivalent to routing_algo_mesh of the board-verified original. Writes reports/GOLDEN_CHECKS.md.

Run in WSL (Icarus, Verilator and Yosys on PATH):  python3 scripts/check_golden.py
"""
import hashlib
import os
import re
import shutil
import subprocess
import sys
import tempfile

STUDY = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REPO = os.path.dirname(os.path.dirname(STUDY))
RTL = os.path.join(STUDY, "golden", "rtl")
TB = os.path.join(STUDY, "golden", "tb")
ORIG_SRC = os.path.join(STUDY, "original_2x2_mesh_zedboard", "project_4on2014edition",
                        "project_4on2014edition.srcs", "sources_1", "imports", "untitled folder")
sys.path.insert(0, os.path.join(REPO, "phase3", "runner"))
import p3_eval as E  # noqa: E402

# module -> files it needs (itself first), in hierarchy order
DEPS = {
    "fifo": ["fifo"],
    "route_compute": ["route_compute"],
    "rr_arbiter": ["rr_arbiter"],
    "flit_mux": ["flit_mux"],
    "input_port": ["input_port", "fifo", "route_compute"],
    "output_port": ["output_port", "rr_arbiter", "flit_mux"],
    "router_5port": ["router_5port", "input_port", "output_port", "fifo", "route_compute", "rr_arbiter", "flit_mux"],
}


def files(m, rtl=RTL):
    return [os.path.join(rtl, f + ".v") for f in DEPS[m]]


def check_module(m, rtl=RTL, tb_dir=TB, timeout=600):
    wd = tempfile.mkdtemp(prefix=f"golden_{m}_")
    try:
        sim = E.simulate(files(m, rtl), os.path.join(tb_dir, f"tb_{m}.v"), wd, timeout=timeout)
        lint = E.lint(files(m, rtl), m, wd)
        syn = E.synth(files(m, rtl), m, wd)
    finally:
        shutil.rmtree(wd, ignore_errors=True)
    line = next((l for l in sim["log"].splitlines() if E.PASS_TOKEN in l or E.FAIL_TOKEN in l), "")
    i = syn["log"].rfind("=== design hierarchy ===")
    sec = syn["log"][i:] if i >= 0 else syn["log"][syn["log"].rfind("=== "):]
    cells = re.findall(r"^\s+Number of cells:\s+(\d+)|^\s+(\d+)\s+cells$", sec, re.M)
    n_cells = next((int(a or b) for a, b in reversed(cells)), None)
    return {"sim": sim["outcome"], "sim_line": line.strip(), "lint_codes": lint["codes"], "lint_hard": lint["n_hard"],
            "lint_errors": lint["errors"], "yosys_ok": syn["ok"], "latches": syn["latch_events"],
            "latch_cells": syn["latch_cells"], "loops": syn["loops"], "cells": n_cells,
            "struct_clean": bool(syn["ok"] and syn["latch_events"] == 0 and syn["loops"] == 0 and lint["n_hard"] == 0)}


WRAP = """module mpsoc_route(input [31:0] flit, input [7:0] current_address, output [4:0] req);
    wire l1, l2, l3, l4, c;
    routing_algo_mesh r(.header_in(flit), .current_address(current_address), .reset(1'b0),
                        .req_link1(l1), .req_link2(l2), .req_core(c), .req_link3(l3), .req_link4(l4));
    assign req = {c, l4, l3, l2, l1};
endmodule
"""


def route_equivalence():
    wd = tempfile.mkdtemp(prefix="route_equiv_")
    try:
        shutil.copy(os.path.join(ORIG_SRC, "routing_algo_mesh.v"), os.path.join(wd, "orig.v"))
        shutil.copy(os.path.join(RTL, "route_compute.v"), os.path.join(wd, "gold.v"))
        open(os.path.join(wd, "wrap.v"), "w").write(WRAP)
        script = ("read_verilog orig.v wrap.v gold.v; proc; opt_clean; "
                  "miter -equiv -flatten -make_assert mpsoc_route route_compute miter; "
                  "hierarchy -top miter; sat -verify -prove-asserts -set-init-zero miter")
        p = subprocess.run([E.YOSYS, "-p", script], cwd=wd, capture_output=True, text=True, timeout=300)
        log = p.stdout + p.stderr
    finally:
        shutil.rmtree(wd, ignore_errors=True)
    proved = p.returncode == 0 and "SUCCESS!" in log and "ERROR" not in log
    return proved, next((l.strip() for l in log.splitlines() if "SUCCESS!" in l or "FAIL" in l), "no result line")


def tool_versions():
    out = {}
    for k, cmd in (("Icarus", [E.IVERILOG, "-V"]), ("Verilator", [E.VERILATOR, "--version"]), ("Yosys", [E.YOSYS, "-V"])):
        p = subprocess.run(cmd, capture_output=True, text=True)
        out[k] = (p.stdout + p.stderr).strip().splitlines()[0]
    return out


def mesh_test():
    wd = tempfile.mkdtemp(prefix="golden_mesh_")
    try:
        sim = E.simulate(files("router_5port"), os.path.join(TB, "tb_mesh2x2.v"), wd, timeout=600)
    finally:
        shutil.rmtree(wd, ignore_errors=True)
    line = next((l for l in sim["log"].splitlines() if E.PASS_TOKEN in l or E.FAIL_TOKEN in l), "")
    return sim["outcome"], line.strip()


def golden_hashes():
    rows = []
    for sub in ("rtl", "tb", "constraints"):
        d = os.path.join(STUDY, "golden", sub)
        for f in sorted(os.listdir(d)):
            rows.append(f"| `golden/{sub}/{f}` | `{hashlib.sha256(open(os.path.join(d, f), 'rb').read()).hexdigest()}` |")
    return rows


def main():
    res = {m: check_module(m) for m in DEPS}
    mesh, mesh_line = mesh_test()
    proved, eq_line = route_equivalence()
    tv = tool_versions()
    rows = []
    for m, r in res.items():
        lint = ", ".join(f"{k} {v}" for k, v in sorted(r["lint_codes"].items())) or "none"
        rows.append(f"| {m} | {r['sim']} | {lint} | {r['lint_hard']} | {r['latches']} | {r['latch_cells']} | "
                    f"{r['loops']} | {r['cells']} | {'yes' if r['struct_clean'] else 'NO'} |")
    ok = all(r["sim"] == "PASS" and r["struct_clean"] for r in res.values()) and proved and mesh == "PASS"
    md = ["# Golden checks", "",
          "Generated by `scripts/check_golden.py`. The checks are the STITCH runner's own (`phase3/runner/p3_eval.py`):",
          "testbench pass = `ALL TESTS PASSED` and no `FAIL`; struct_clean = Yosys synthesis succeeds with 0 latches",
          "and 0 logic loops, and Verilator `-Wall` reports none of MULTIDRIVEN, UNOPTFLAT, LATCH, WIDTHTRUNC.", "",
          f"Toolchain: {tv['Icarus']}; {tv['Verilator']}; {tv['Yosys']}.", "",
          f"**Result: {'all modules pass and are struct_clean' if ok else 'NOT CLEAN, see table'}.**", "",
          "| module | testbench | Verilator -Wall warnings | hard | Yosys latches | latch cells | logic loops | "
          "Yosys cells | struct_clean |",
          "|---|---|---|---|---|---|---|---|---|", *rows, "",
          "Testbench summaries:", "",
          *[f"- `tb_{m}.v`: {r['sim_line']}" for m, r in res.items()], "",
          "Verilator warnings are UNUSEDSIGNAL only: route_compute reads only the flit type and destination bits, and",
          "router_5port leaves each input's U-turn request bit unconnected (an output never serves its own input).", "",
          "## 2x2 mesh (tb_mesh2x2.v)", "",
          "Four golden routers wired as `top_4_router` of the original. Part 1 replays the ZedBoard test packets",
          "(`original_2x2_mesh_zedboard/Outputs_2x2/`: r1's core sends head, payload and tail flits to r2, r3, r4);",
          "part 2 is random all-to-all traffic with router-to-router flow control.", "",
          f"- {mesh}: {mesh_line}", "",
          "## Routing equals the board-verified original", "",
          "Yosys equivalence (miter + SAT over all 2^40 input values) between `golden/rtl/route_compute.v` and",
          "`routing_algo_mesh` of the original ZedBoard project (`original_2x2_mesh_zedboard/.../routing_algo_mesh.v`,",
          "reset tied low; outputs ordered link1, link2, link3, link4, core):", "",
          f"- {'PROVED equivalent' if proved else 'NOT PROVED'} (`{eq_line}`)", "",
          "## Files checked (sha256)", "",
          "The golden is frozen at these contents; any change means rerunning every check.", "",
          "| file | sha256 |", "|---|---|", *golden_hashes(), ""]
    open(os.path.join(STUDY, "reports", "GOLDEN_CHECKS.md"), "w", newline="\n").write("\n".join(md))
    print("\n".join(rows))
    print("route equivalence:", proved, eq_line)
    print("OK" if ok else "NOT CLEAN")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
