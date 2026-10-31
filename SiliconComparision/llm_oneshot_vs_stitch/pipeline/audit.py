#!/usr/bin/env python3
"""Failure audit of every final file that is not so_clean (one-shot, simloop, stitch). Writes reports/FAILURE_AUDIT.md.

Evidence comes from the local re-evaluation (pipeline/reeval.py: runs/analysis/<arm>/<m>/*.log):
  does not compile        first iverilog error line (file:line, message)
  compiles, tb fails      first failing line of tb.v (loop) and tb_signoff.v (sign-off); for the timing-dependent
                          modules the sign-off verdict is the property checks, cycle-exact lines are secondary
  structural fail (K)     Yosys latch / logic-loop / ERROR lines and Verilator hard warnings (MULTIDRIVEN, UNOPTFLAT,
                          LATCH, WIDTHTRUNC)
Class: LLM_BUG, SPEC_AMBIGUITY (spec allows the LLM's behaviour, golden differs) or TB_ARTIFACT (the testbench checks
something the spec does not define). Compile failures are LLM_BUG (the prompt asks for a Verilog-2001 module; every
failing file also fails with iverilog -g2001, checked here). The other verdicts are the table VERDICT below; each
quotes its spec line. asynch_comparator is decided by an exhaustive check (all 256 input combinations) against the
spec formula and the golden.
Usage: python pipeline/audit.py   (after pipeline/reeval.py; needs iverilog)
"""
from __future__ import annotations

import collections
import glob
import json
import os
import re
import subprocess
import sys
import tempfile

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import analysis_common as A  # noqa: E402
import assemble as S  # noqa: E402
import reeval  # noqa: E402

HARD_V = ("MULTIDRIVEN", "UNOPTFLAT", "LATCH", "WIDTHTRUNC")
PROMPT_LINE = "Write the complete Verilog-2001 module `{m}` that meets this specification, with exactly the port list above."
COMPILE_KINDS = [  # (regex on the iverilog error, short name)
    (r"has already been declared", "port redeclared in the body"),
    (r"not a valid l-value for a procedural assignment", "procedural assignment to a net"),
    (r"cannot be driven by a continuous assignment|also continuously assigned", "reg driven continuously"),
    (r"Output port expression must support|not valid in assign l-value", "constant tied to a child output port"),
    (r"out of range", "index out of range"),
    (r"Unable to bind", "undeclared signal"),
    (r"already bound", "port connected twice"),
    (r"is not a port of", "connection to a port the child does not have"),
    (r"invalid port declaration separator|syntax error|Invalid module item", "syntax error"),
]
# Non-compile verdicts: module -> (class, reason, regex of the quoted spec line)
VERDICT = {
    "allot_vc": ("LLM_BUG", "grant/VC outputs differ from the stated equations; a 4-bit net drives mux's 1-bit m_out",
                 r"A new grant takes the lowest-numbered free VC"),
    "encoder": ("LLM_BUG", "a one-hot input gives the wrong code", r"`g1` gives 0"),
    "falling_edge_pulse_generator": ("LLM_BUG", "samples gnt on clk instead of reacting to the gnt falling edge",
                                     r"`q0` becomes 1 on each falling edge of `gnt`"),
    "gray_mod6": ("LLM_BUG", "wrong next-state table (property: not one Gray step)", r"advances through 000, 001"),
    "ip_link": ("LLM_BUG", "per-VC rok/data_out wrong; 4-bit read-enable buses into 1-bit child ports",
                r"The read enable of VC k is the OR"),
    "irs": ("LLM_BUG", "en4/en5 properties fail; Yosys rejects the clocking (multiple edge-sensitive events)",
            r"`en4` \(packet in progress\)"),
    "router_fifo": ("LLM_BUG", "pointers count in binary and advance without the full/empty gating (property: FIFO "
                    "order)", r"Both step through the Gray sequence"),
    "rr_comb_new": ("LLM_BUG", "grants differ from the fixed-priority equations; combinational loop on g1/g2",
                    r"It is not round-robin"),
    "top_2x2_router": ("LLM_BUG", "router r1's core output stays idle; 4-bit nets on 1-bit router ports",
                       r"Router addresses"),
}
GRAY_POS = {0b000: 0, 0b001: 1, 0b011: 2, 0b010: 3, 0b110: 4, 0b100: 5}


def first(path: str, pattern: str):
    hit = A.first_line(open(path, errors="replace").read(), pattern) if os.path.exists(path) else None
    return (f"{A.rel(path)}:{hit[0]}", hit[1]) if hit else None


def spec_quote(m: str, pattern: str) -> str:
    for l in A.spec(m):
        if re.search(pattern, l):
            return l.strip().lstrip("- ")
    raise SystemExit(f"spec line /{pattern}/ not found in tasks/{m}/spec.md")


def compiles_2001(arm: str, m: str) -> bool:
    lib = sorted(glob.glob(os.path.join(A.STUDY, "tasks", m, "lib", "*.v")))
    p = subprocess.run(["iverilog", "-g2001", "-o", os.devnull, "-s", m, A.final_file(arm, m), *lib],
                       capture_output=True, text=True)
    return p.returncode == 0


def asynch_exhaustive(arm: str) -> dict:
    """All 256 (rd_ptr, wr_ptr, rd_dir, wr_dir): LLM vs golden vs the spec formula; reachable = valid Gray codes and
    occupancy 0..6 (states a 6-entry FIFO can be in)."""
    ref = open(os.path.join(A.STUDY, "golden", "reference", "asynch_comparator.v")).read().replace(
        "module asynch_comparator", "module ref_ac", 1)
    tb = ("module tb; reg [2:0] r,w; reg rd,wd; wire a,b,c,x,y,z; integer i;\n"
          "asynch_comparator d(.rd_ptr(r),.wr_ptr(w),.rd_dir(rd),.wr_dir(wd),.full_ext(a),.full_int(b),.empty(c));\n"
          "ref_ac g(.rd_ptr(r),.wr_ptr(w),.rd_dir(rd),.wr_dir(wd),.full_ext(x),.full_int(y),.empty(z));\n"
          "initial for(i=0;i<256;i=i+1) begin {r,w,rd,wd}=i; #1; $display(\"%0d %0d %0d %0d %b%b%b %b%b%b\","
          "r,w,rd,wd,a,b,c,x,y,z); end endmodule\n")
    with tempfile.TemporaryDirectory() as d:
        open(os.path.join(d, "ref.v"), "w").write(ref)
        open(os.path.join(d, "tb.v"), "w").write(tb)
        subprocess.run(["iverilog", "-o", os.path.join(d, "s"), A.final_file(arm, "asynch_comparator"),
                        os.path.join(d, "ref.v"), os.path.join(d, "tb.v")], check=True, capture_output=True)
        out = subprocess.run(["vvp", "-n", os.path.join(d, "s")], capture_output=True, text=True).stdout
    c = collections.Counter()
    for line in out.split("\n"):
        f = line.split()
        if len(f) != 6:
            continue
        r, w, rd, wd = map(int, f[:4])
        pr, pw = GRAY_POS.get(r, 5), GRAY_POS.get(w, 5)
        occ = pw - pr + (0 if rd == wd else 6)
        spec = f"{int(occ >= 4)}{int(r == w and rd != wd)}{int(r == w and rd == wd)}"
        reach = r in GRAY_POS and w in GRAY_POS and 0 <= occ <= 6
        if f[4] != f[5]:
            c["mismatch_reachable" if reach else "mismatch_unreachable"] += 1
            if not reach:
                c["unreachable_llm_equals_spec"] += f[4] == spec
                c["unreachable_golden_equals_spec"] += f[5] == spec
        if reach and f[5] != spec:
            c["golden_differs_from_spec_reachable"] += 1
    return dict(c)


def main() -> int:
    rows, counts, findings, ex = [], collections.Counter(), [], {}
    for m in A.modules():
        for arm in A.ARMS:
            e = reeval.load(arm, m)
            if e["so_clean"]:
                continue
            d = os.path.join(A.STUDY, "runs", "analysis", arm, m)
            fl = A.flags({"compile": e["compile_ok"], "func": e["func_pass"], "signoff": e["signoff"],
                          "struct_clean": e["struct_clean"]})
            ev = []
            if not e["compile_ok"]:
                loc, msg = first(os.path.join(d, "sim.log"), r"error")
                kind = next((k for p, k in COMPILE_KINDS if re.search(p, msg)), "other compile error")
                ev.append(f"compile (iverilog -g2012) {loc}: `{msg}`")
                if compiles_2001(arm, m):
                    cls, reason = "TB_ARTIFACT", f"{kind}; compiles with iverilog -g2001"
                else:
                    cls, reason = "LLM_BUG", f"{kind}; also fails with iverilog -g2001"
                quote = PROMPT_LINE.format(m=m)
                if re.search(r"syntax error|Invalid module item", msg) and re.search(
                        r"\bpriority\b", open(A.final_file(arm, m)).read()):
                    findings.append(f"{m} ({arm}): the first error is the SystemVerilog keyword `priority` used as a "
                                    "net name (the evaluator compiles with -g2012). The loop feedback shows only that "
                                    "syntax error; with `priority` renamed, real errors remain (procedural assignment "
                                    "to a net), so the verdict stays LLM_BUG.")
            else:
                for tbn, log in (("tb.v", "sim.log"), ("tb_signoff.v", "signoff.log")):
                    if (tbn == "tb.v" and not e["func_pass"]) or (tbn == "tb_signoff.v" and not e["signoff"]):
                        pat = r"FAIL property" if (tbn == "tb_signoff.v" and m in A.TIMING) else r"^FAIL"
                        hit = first(os.path.join(d, log), pat) or first(os.path.join(d, log), r"FAIL")
                        if hit:
                            ev.append(f"{tbn} {hit[0]}: `{hit[1]}`")
                if not e["struct_clean"]:
                    for log, pat in (("yosys.log", r"Latch inferred for signal|found logic loop|^ERROR"),
                                     ("verilator.log", r"%Warning-(" + "|".join(HARD_V) + r")")):
                        hit = first(os.path.join(d, log), pat)
                        if hit:
                            ev.append(f"structural {hit[0]}: `{hit[1][:160]}`")
                if m == "asynch_comparator":
                    x = ex[arm] = asynch_exhaustive(arm)
                    if not x.get("mismatch_reachable"):
                        cls = "TB_ARTIFACT"
                        reason = (f"all {x.get('mismatch_unreachable', 0)} mismatching input combinations are pointer "
                                  "pairs a 6-entry FIFO cannot reach (occupancy < 0 or > 6); there the spec formula "
                                  f"and the golden disagree (golden = spec in {x.get('unreachable_golden_equals_spec', 0)}"
                                  f", LLM = spec in {x.get('unreachable_llm_equals_spec', 0)}); the testbench drives "
                                  "random pointers")
                    else:
                        cls, reason = "LLM_BUG", f"{x['mismatch_reachable']} mismatches in reachable states"
                    quote = spec_quote(m, r"The occupancy is")
                else:
                    cls, reason, pat = VERDICT[m]
                    quote = spec_quote(m, pat)
            counts[(arm, cls)] += 1
            rows.append(f"| {m} | {arm} | {fl} | {cls} | {reason} | \"{quote}\" | {'<br>'.join(ev)} |")
    for arm, x in ex.items():
        findings.append(f"asynch_comparator ({arm}): exhaustive check {x}. The tb.v/tb_signoff.v drive random "
                        "pointer pairs, including ones no FIFO reaches; the spec formula is not the golden there. "
                        "Testbench not changed in this part.")
    md = ["# Failure audit (pipeline/audit.py)", "",
          "Every final file that is not so_clean, from the local re-evaluation (`pipeline/reeval.py`; flags identical "
          "to the cluster's `reports/summary.json` for all 102 files). Classes: LLM_BUG, SPEC_AMBIGUITY, TB_ARTIFACT.",
          "", "## Class counts per arm", "", "| arm | not so_clean | LLM_BUG | SPEC_AMBIGUITY | TB_ARTIFACT |",
          "|---|---|---|---|---|"]
    for arm in A.ARMS:
        n = sum(v for (a, _), v in counts.items() if a == arm)
        md.append(f"| {arm} | {n} | {counts[(arm, 'LLM_BUG')]} | {counts[(arm, 'SPEC_AMBIGUITY')]} | "
                  f"{counts[(arm, 'TB_ARTIFACT')]} |")
    md += ["", "## Audit findings", ""] + [f"- {f}" for f in dict.fromkeys(findings)]
    md += ["- demux_16: every arm declares the outputs in the ANSI header and again as `wire` in the body, then "
           "assigns them in `always @(*)` (iverilog: `'op1' has already been declared`). The spec states plain "
           "1-bit outputs and a combinational one-hot function; nothing in the spec or testbench causes the failure.",
           "- Data-clocked / gated-clock modules (gray_mod6, rr_arbiter, irs, round_robin_req, falling_edge_pulse_"
           "generator, memory, router_fifo): memory signs off clean in every arm; every other final either does not "
           "compile or fails a sign-off property (a spec rule), so none is decided by the secondary cycle-exact check. "
           "The loop testbench tb.v is cycle-exact for these modules too, so the feedback the loop sees is stricter "
           "than the sign-off verdict.",
           "- router_fifo: C..K in every arm; the sign-off property `FIFO order: wrong word read` fails in every arm "
           "(see rows)."]
    mcp = os.path.join(S.OUT, "module_checks.json")
    if os.path.exists(mcp):  # written by pipeline/assemble.py
        mc = {tuple(k.split("/")): v for k, v in json.load(open(mcp)).items() if not k.startswith("_")}
        rm = S.race_modules(mc)
        md += [f"- Golden RTL (mesh tb reference): the hybrid_signoff meshes fail the cycle-exact mesh tb only through "
               f"{', '.join(rm)}. " + S.race_note(rm).split(". ", 1)[1] + " Golden blocking assignments in clocked "
               "blocks: " + "; ".join(f"{m} {', '.join(S.golden_blocking_lines(m))}" for m in rm
                                      if S.golden_blocking_lines(m)) + " (reports/ASSEMBLY.md)."]
    md += ["", "## Cases", "", "| module | arm | flags | class | reason | spec line | evidence |",
           "|---|---|---|---|---|---|---|", *rows]
    A.write_report("FAILURE_AUDIT.md", md)
    for arm in A.ARMS:
        print(arm, {c: counts[(arm, c)] for c in ("LLM_BUG", "SPEC_AMBIGUITY", "TB_ARTIFACT")})
    for f in dict.fromkeys(findings):
        print("finding:", f)
    return 0


if __name__ == "__main__":
    sys.exit(main())
