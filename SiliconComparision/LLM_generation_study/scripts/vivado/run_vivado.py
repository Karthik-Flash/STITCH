"""Vivado side of the golden reference: run every testbench in the Vivado simulator (xsim), run flow.tcl
(out-of-context synthesis and implementation for ZedBoard), parse the reports and write reports/VIVADO_GOLDEN.md.
Run outputs go to vivado/ (gitignored).

Run on Windows:  python scripts/vivado/run_vivado.py [--skip-sim] [--skip-flow]
"""
import os
import re
import shutil
import subprocess
import sys

VIVADO_BIN = os.environ.get("VIVADO_BIN", r"C:\Xilinx\Vivado\2022.2\bin")
STUDY = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
RTL = os.path.join(STUDY, "golden", "rtl")
TB = os.path.join(STUDY, "golden", "tb")
XDC = os.path.join(STUDY, "golden", "constraints", "router_5port.xdc")
OUT = os.path.join(STUDY, "vivado")
TOP = "router_5port"
PERIOD = 10.0
# expected in any out-of-context Zynq run: outputs drive no loads inside the design, no PS7 block
OOC_DRC = {"RTSTAT-10", "ZPS7-1"}
# what the warnings of the golden run mean
KNOWN = {"WARNING [Route 35-197]": "out-of-context: no HD.CLK_SRC on clk",
         "WARNING [Route 35-198]": "out-of-context: no HD.PARTPIN_LOCS on a port",
         "WARNING [Timing 38-242]": "out-of-context: clock delay and skew not estimated",
         "WARNING [Synth 8-7080]": "parallel synthesis not used (design too small)",
         "WARNING [Synth 8-7129]": "unused input bits (route_compute reads only the flit type and destination)"}
TESTBENCHES = ["fifo", "route_compute", "rr_arbiter", "flit_mux", "input_port", "output_port", "router_5port", "mesh2x2"]


def tool(name):
    return os.path.join(VIVADO_BIN, name + ".bat")


def run(cmd, cwd, log):
    p = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True)
    open(os.path.join(cwd, log), "w").write(p.stdout + p.stderr)
    return p.returncode, p.stdout + p.stderr


def xsim(tb):
    wd = os.path.join(OUT, "xsim", tb)
    shutil.rmtree(wd, ignore_errors=True)
    os.makedirs(wd, exist_ok=True)
    srcs = [os.path.join(RTL, f) for f in sorted(os.listdir(RTL))] + [os.path.join(TB, f"tb_{tb}.v")]
    rc, log = run([tool("xvlog")] + srcs, wd, "xvlog.out")
    if rc == 0:
        rc, log = run([tool("xelab"), "tb", "-s", "tb_sim", "-timescale", "1ns/1ps"], wd, "xelab.out")
    if rc != 0:
        return "COMPILE_ERROR", log.strip().splitlines()[-1]
    rc, log = run([tool("xsim"), "tb_sim", "-runall"], wd, "xsim.out")
    line = next((l.strip() for l in log.splitlines() if "ALL TESTS PASSED" in l or "FAIL" in l), "no result line")
    return ("PASS" if "ALL TESTS PASSED" in log and "FAIL" not in log else "FAIL"), line


def flow(rtl=RTL, out=os.path.join(OUT, TOP)):
    """flow.tcl on every .v in rtl (default: the golden); reports go to out."""
    shutil.rmtree(out, ignore_errors=True)
    os.makedirs(out, exist_ok=True)
    tcl = os.path.join(STUDY, "scripts", "vivado", "flow.tcl")
    rc, _ = run([tool("vivado"), "-mode", "batch", "-nojournal", "-log", os.path.join(out, "vivado.log"),
                 "-source", tcl, "-tclargs", rtl.replace("\\", "/"), XDC.replace("\\", "/"), TOP,
                 out.replace("\\", "/")], out, "flow.out")
    return out


def num(pat, text, cast=float):
    m = re.search(pat, text, re.M)
    return cast(m.group(1)) if m else None


def parse(out):
    rd = lambda f: open(os.path.join(out, f), errors="ignore").read()
    util, tim, chk, meth, drc, pwr, log = (rd(f) for f in ("utilization_routed.rpt", "timing_summary_routed.rpt",
                                           "check_timing.rpt", "methodology.rpt", "drc_routed.rpt",
                                           "power_routed.rpt", "vivado.log"))
    u = lambda name: num(r"^\|\s+" + re.escape(name) + r"\s+\|\s+(\d+)\s+\|", util, int)
    m = re.search(r"WNS\(ns\).*\n.*\n\s+(-?[\d.]+)\s+(-?[\d.]+)\s+(\d+)\s+(\d+)\s+(-?[\d.]+)\s+(-?[\d.]+)\s+(\d+)", tim)
    wns, tns, tns_fail, endpoints, whs, ths, ths_fail = (float(m.group(i)) for i in range(1, 8))
    checks = dict((k, int(v)) for k, v in re.findall(r"^\d+\. checking (\w+) \((\d+)\)", chk, re.M))
    rules = lambda t: dict((r, int(n)) for r, n in re.findall(r"^\| ([A-Z0-9]+-\d+)\s+\|[^|]*\|[^|]*\|\s+(\d+)\s+\|", t, re.M))
    warn = re.findall(r"^(CRITICAL WARNING|WARNING): \[([^\]]+)\]", log, re.M)
    wcount = {}
    for sev, ident in warn:
        wcount[f"{sev} [{ident}]"] = wcount.get(f"{sev} [{ident}]", 0) + 1
    return {
        "luts": u("Slice LUTs"), "lut_logic": u("LUT as Logic"), "lut_mem": u("LUT as Memory"),
        "regs": u("Slice Registers"), "ff": u("Register as Flip Flop"), "latch": u("Register as Latch"),
        "bram": num(r"^\|\s+Block RAM Tile\s+\|\s+([\d.]+)\s+\|", util), "dsp": u("DSPs"),
        "wns": wns, "tns": tns, "tns_fail": int(tns_fail), "endpoints": int(endpoints), "whs": whs, "ths": ths,
        "ths_fail": int(ths_fail), "fmax": 1000.0 / (PERIOD - wns),
        "levels": num(r"Logic Levels:\s+(\d+)", tim, int), "checks": checks,
        "methodology": rules(meth), "drc": rules(drc),
        "power_total": num(r"^\| Total On-Chip Power \(W\)\s+\|\s+([\d.]+)", pwr),
        "power_dyn": num(r"^\| Dynamic \(W\)\s+\|\s+([\d.]+)", pwr),
        "power_static": num(r"^\| Device Static \(W\)\s+\|\s+([\d.]+)", pwr),
        "power_clocks": num(r"^\| Clocks\s+\|\s+([\d.]+)", pwr),
        "power_logic": num(r"^\| Slice Logic\s+\|\s+([\d.]+)", pwr),
        "power_signals": num(r"^\| Signals\s+\|\s+([\d.]+)", pwr),
        "confidence": num(r"^\| Confidence Level\s+\|\s+(\w+)", pwr, str),
        "warnings": wcount, "latch_msgs": len(re.findall(r"\[Synth 8-327\]", log)),
        "version": num(r"^# Vivado v(\S+)", log, str) or num(r"Vivado v(\d{4}\.\d)", log, str),
    }


def main():
    args = set(sys.argv[1:])
    sims = {} if "--skip-sim" in args else {tb: xsim(tb) for tb in TESTBENCHES}
    for tb, (oc, line) in sims.items():
        print(f"xsim {tb}: {oc} {line}")
    out = os.path.join(OUT, TOP) if "--skip-flow" in args else flow()
    r = parse(out)
    fmt = lambda d: ", ".join(f"{k} {v}" for k, v in sorted(d.items())) or "none"
    nonzero = {k: v for k, v in r["checks"].items() if v}
    sim_rows = [f"| `tb_{tb}.v` | {oc} | {line} |" for tb, (oc, line) in sims.items()]
    ok = (all(oc == "PASS" for oc, _ in sims.values()) and r["wns"] >= 0 and r["whs"] >= 0 and r["latch"] == 0
          and not nonzero and r["latch_msgs"] == 0 and not (set(r["drc"]) - OOC_DRC) and not r["methodology"])
    md = ["# Golden router in Vivado", "",
          "Generated by `scripts/vivado/run_vivado.py` (Vivado " + str(r["version"]) + "). Design `router_5port`,",
          "part xc7z020clg484-1 (ZedBoard), out-of-context (340 I/O, the package has 200), clock 10 ns (100 MHz),",
          "input and output delays 2 ns (`golden/constraints/router_5port.xdc`), default synthesis and",
          "implementation (`scripts/vivado/flow.tcl`: synth_design, opt_design, place_design, route_design).", "",
          f"**Result: {'functional in xsim, timing met, no latches, no loops, every endpoint constrained' if ok else 'NOT CLEAN, see below'}.**",
          "", "## Simulation in xsim", "", "| testbench | result | summary |", "|---|---|---|", *sim_rows, "",
          "## Implementation (post-route)", "", "| metric | value |", "|---|---|",
          f"| Slice LUTs (logic / memory) | {r['luts']} ({r['lut_logic']} / {r['lut_mem']}) |",
          f"| Slice registers (flip-flops / latches) | {r['regs']} ({r['ff']} / {r['latch']}) |",
          f"| Block RAM tiles / DSPs | {r['bram']:g} / {r['dsp']} |",
          f"| WNS / TNS (failing endpoints of {r['endpoints']}) | {r['wns']:.3f} ns / {r['tns']:.3f} ns ({r['tns_fail']}) |",
          f"| WHS / THS (failing endpoints) | {r['whs']:.3f} ns / {r['ths']:.3f} ns ({r['ths_fail']}) |",
          f"| fmax = 1000 / (10 - WNS) | {r['fmax']:.1f} MHz |",
          f"| logic levels on the worst path | {r['levels']} |",
          f"| total on-chip power (dynamic / device static) | {r['power_total']:.3f} W ({r['power_dyn']:.3f} / "
          f"{r['power_static']:.3f}), vectorless, confidence {r['confidence']} |",
          f"| dynamic power: clocks / signals / logic | {r['power_clocks']:.3f} / {r['power_signals']:.3f} / "
          f"{r['power_logic']:.3f} W (static power is the chip's leakage, the same for any design on it) |",
          f"| check_timing categories with findings | {fmt(nonzero)} |",
          f"| synthesis latch messages [Synth 8-327] | {r['latch_msgs']} |",
          f"| DRC violations (RTSTAT-10, ZPS7-1 are expected out-of-context) | {fmt(r['drc'])} |",
          f"| methodology violations | {fmt(r['methodology'])} |", "",
          "check_timing categories checked (all must be 0): " + ", ".join(sorted(r["checks"])) + ".", "",
          "Vivado warnings in the log (messages by id):", "",
          *[f"- {k}: {v}" + (f" ({KNOWN[k]})" if k in KNOWN else "") for k, v in sorted(r["warnings"].items())], ""]
    open(os.path.join(STUDY, "reports", "VIVADO_GOLDEN.md"), "w", newline="\n").write("\n".join(md))
    print("OK" if ok else "NOT CLEAN")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
