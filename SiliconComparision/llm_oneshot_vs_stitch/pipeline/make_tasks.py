#!/usr/bin/env python3
"""Build tasks/<module>/ in the Phase 3 task format for every module in modules.csv.

  spec.md        specs/<m>.md without the generated-block markers and the "Unclear in golden" note
                 (the three registers: phase3/tasks/<m>/spec.md verbatim)
  golden.v       the module's file from golden/reference
  input.v        the module's file from golden/handwritten (placeholder; run_arms.py puts the one-shot output here
                 in its per-run copy of the task)
  tb.v           loop testbench: ~200 random cycles, every checked output compared with golden/reference
  tb_signoff.v   ~5,000 cycles plus spec properties. For timing-dependent modules the property checks are the
                 verdict and the cycle-exact comparison is only logged.
  meta.json      top, track, children, checked outputs, timing flag
  lib/, stubs/   parents only: golden/reference files of all descendants, and port-only stubs of direct children
The three registers reuse phase3/tasks/<m>/{tb.v,tb_signoff.v,meta.json} (meta extended with the study keys).

Usage: python pipeline/make_tasks.py
"""
from __future__ import annotations

import csv
import json
import re
import shutil
from pathlib import Path

STUDY = Path(__file__).resolve().parent.parent
REPO = STUDY.parent.parent
REFERENCE = STUDY / "golden" / "reference"
HANDWRITTEN = STUDY / "golden" / "handwritten"
TASKS = STUDY / "tasks"
P3_TASKS = REPO / "phase3" / "tasks"

PHASE3_REGISTERS = ("register_1bit", "register_4bit", "register_32bit")
TIMING = ("rr_arbiter", "irs", "round_robin_req", "falling_edge_pulse_generator", "gray_mod6", "memory",
          "router_fifo")
NOT_CHECKED = {"ip_chnl": ["nxt_reset", "reg_out"], "rr_comb_new": ["b1_logic", "b0_logic"]}
SYSCLK = {"clk", "rd_clk", "wr_clk", "rd_clk1", "rd_clk2", "rd_clk3", "rd_clk4", "rd_clk_core"}
PARENT_RESET_P = 400        # mid-run reset probability 1/P after the initial reset (parents: rare, so packets flow)
LEAF_RESET_P = 40
LOOP_CYCLES, SIGNOFF_CYCLES = 200, 5000
LOOP_SEED, SIGNOFF_SEED = 11, 29
# Output flipped by the validation mutant (default: first checked output). Timing modules: a property-checked one.
MUTANT_OUTPUT = {"rr_arbiter": "gnt1", "irs": "rd_en_out", "round_robin_req": "g1",
                 "falling_edge_pulse_generator": "q0", "gray_mod6": "gray_out", "memory": "data_out",
                 "router_fifo": "data_out"}


# --------------------------------------------------------------------------- inventory
def load_rows() -> dict[str, dict]:
    with (STUDY / "modules.csv").open(encoding="utf-8", newline="") as handle:
        rows = {r["module"]: r for r in csv.DictReader(handle)}
    for r in rows.values():
        r["port_list"] = []
        for item in r["ports"].split(";"):
            direction, rest = item.split(" ", 1)
            name, width = rest.rstrip("]").split("[")
            r["port_list"].append((direction, name, int(width)))
        r["child_list"] = [c.rsplit("x", 1)[0] for c in r["children"].split(";")] if r["children"] else []
    return rows


def descendants(rows, name) -> list[str]:
    out = []
    for child in rows[name]["child_list"]:
        for d in descendants(rows, child) + [child]:
            if d not in out:
                out.append(d)
    return out


def decl(direction, name, width) -> str:
    return f"{direction} {'[' + str(width - 1) + ':0] ' if width > 1 else ''}{name};"


def stub(row) -> str:
    """Port-only module for lint/synth of a parent. Unused/undriven warnings in the stub are switched off."""
    names = ", ".join(n for _, n, _ in row["port_list"])
    body = "\n".join("  " + decl(d, n, w) for d, n, w in row["port_list"])
    return ("/* verilator lint_off UNUSED */\n/* verilator lint_off UNDRIVEN */\n"
            f"module {row['module']}({names});\n{body}\nendmodule\n")


def spec_for_task(name: str) -> str:
    if name in PHASE3_REGISTERS:
        return (P3_TASKS / name / "spec.md").read_text(encoding="utf-8")
    text = (STUDY / "specs" / f"{name}.md").read_text(encoding="utf-8")
    text = re.sub(r"<!-- (BEGIN|END) generated: \w+ -->\n", "", text)
    text = re.sub(r"\nUnclear in golden:.*\Z", "\n", text, flags=re.S)
    return text.rstrip() + "\n"


# --------------------------------------------------------------------------- stimulus
def stimulus(name, row):
    """Per-input drive rule: ('clock',) | ('reset', P) | ('rand',) | ('sticky', P) | ('sparse', P) | ('flit',)
    | ('addr',). Defaults by port name; module overrides below come from the specs' legal-input notes."""
    parent = bool(row["child_list"])
    rules = {}
    for d, n, w in row["port_list"]:
        if d != "input":
            continue
        if n in SYSCLK:
            rules[n] = ("clock",)
        elif n in ("reset", "clr", "set"):
            rules[n] = ("reset", PARENT_RESET_P if parent else LEAF_RESET_P)
        elif n == "current_address":
            rules[n] = ("addr",)
        elif w == 32 and (n.startswith("data_in") or n.startswith("data_from") or n == "header_in"):
            rules[n] = ("flit",)
        elif n.startswith("tailer"):
            rules[n] = ("sparse", 8)
        elif re.match(r"(req|rok|full|in[0-3]$|r[1-4]$)", n):
            rules[n] = ("sticky", 6)
        elif re.match(r"rd_en\d+$", n):
            rules[n] = ("sparse", 24)
        else:
            rules[n] = ("rand",)
    over = {
        "irs": {"header": ("sticky", 3), "tailer": ("sticky", 3), "rd_en": ("sticky", 3), "empty": ("sticky", 4),
                "tailer_org": ("sticky", 3)},
        "ip_chnl": {"rd_en": ("sticky", 3), "wr_en": ("sticky", 3)},
        "falling_edge_pulse_generator": {"gnt": ("sticky", 3)},
        "rr_arbiter": {"req1": ("sticky", 6), "req2": ("sticky", 6), "req3": ("sticky", 6), "req4": ("sticky", 6)},
        "round_robin_req": {"all_vc_not_busy": ("sticky", 10)},
        # Initial reset only: after a mid-run reset the golden's wrap bits need not match (gray_mod6 dir caveat),
        # so the FIFO can look full; the spec leaves that undefined.
        "router_fifo": {"wr_en": ("sticky", 3), "rd_en": ("sticky", 3), "reset": ("reset", 0)},
        "gray_mod6": {"en": ("sticky", 3)},
        "jk_ff": {"en": ("sticky", 3)},
    }.get(name, {})
    rules.update(over)
    return rules


def onehot_groups(name):
    """Input groups that must be one-hot or all zero (spec: one grant at a time)."""
    g16 = [f"g{i}" for i in range(1, 17)]
    return {"encoder": [g16], "allot_vc": [g16]}.get(name, [])


def post_drive(name):
    """Extra legal-input constraints applied after the random drive."""
    return {
        # memory spec: a read and a write of the same address on one edge is ambiguous in the golden.
        "memory": "if (wr_en && rd_en && wr_add == rd_add) rd_en = 1'b0;",
    }.get(name, "")


def drive_code(name, row, rules):
    lines = []
    for n, rule in rules.items():
        w = next(w for d, pn, w in row["port_list"] if pn == n)
        kind = rule[0]
        if kind == "clock":
            continue
        if kind == "reset":
            lines.append(f"{n} = (tb_cyc < 4) ? 1'b1 : (tb_rand(0) % {rule[1]} == 0);" if rule[1]
                         else f"{n} = (tb_cyc < 4);")
        elif kind == "rand":
            lines.append(f"{n} = {{{', '.join(['tb_rand(0)'] * ((w + 31) // 32))}}};")
        elif kind == "sticky":
            lines.append(f"if (tb_rand(0) % {rule[1]} == 0) {n} = {{{', '.join(['tb_rand(0)'] * ((w + 31) // 32))}}};"
                         if w > 1 else f"if (tb_rand(0) % {rule[1]} == 0) {n} = ~{n};")
        elif kind == "sparse":
            lines.append(f"{n} = (tb_rand(0) % {rule[1]} == 0);")
        elif kind == "flit":
            lines.append(f"{n} = tb_flit(0);")
        elif kind == "addr":   # row and column 1 or 2, so flits to rows/columns 0..3 can go in every direction
            lines.append(("" if name == "routing_algo_mesh" else "if (tb_cyc == 0) ")
                         + f"begin tb_r = tb_rand(0); {n} = {{2'b00, 2'b01 + tb_r[4], 2'b00, 2'b01 + tb_r[0]}}; end")
    for group in onehot_groups(name):
        lines.append(f"tb_k = tb_rand(0) % {len(group) + 1};")
        lines += [f"{g} = (tb_k == {i + 1});" for i, g in enumerate(group)]
    if post_drive(name):
        lines.append(post_drive(name))
    return "\n".join("      " + l for l in lines)


# --------------------------------------------------------------------------- properties (sign-off)
def props(name, row):
    """(declarations, statements run at every sample point, module-level code, post-drive statements).
    tb_ph = 0: sample 1 ns before the rising clock edge; 1: sample 4 ns after it. tb_started: after the initial reset."""
    outs = [n for d, n, w in row["port_list"] if d == "output"]

    def onehot(sigs, what):
        s = "{" + ", ".join(sigs) + "}"
        return (f"if (^{s} === 1'bx || ({' + '.join(sigs)}) > 1) tb_prop(\"{what} not one-hot-or-zero\");")

    if name == "rr_arbiter":
        d = "integer pa_w1, pa_w2, pa_w3, pa_w4; reg pa_p1, pa_p2, pa_p3, pa_p4;"
        s = [f"if (tb_started && !reset) begin", "  " + onehot(["gnt1", "gnt2", "gnt3", "gnt4"], "grant")]
        for i in range(1, 5):
            s += [f"  if (gnt{i} && !req{i} && !pa_p{i}) tb_prop(\"gnt{i} without req{i}\");",
                  f"  if (tb_ph == 0) begin pa_w{i} = (req{i} && !gnt{i}) ? pa_w{i} + 1 : 0;"
                  f" if (pa_w{i} > 150) tb_prop(\"req{i} starved\"); end"]
        s += ["end", "if (reset) begin pa_w1 = 0; pa_w2 = 0; pa_w3 = 0; pa_w4 = 0; end",
              "pa_p1 = req1; pa_p2 = req2; pa_p3 = req3; pa_p4 = req4;"]
        return d, s, "", "if (tb_cyc == 0) begin pa_w1 = 0; pa_w2 = 0; pa_w3 = 0; pa_w4 = 0; end"
    if name == "round_robin_req":
        d = "reg [16:1] rq_p, rq_done, rq_gi_p;"
        g = [f"g{i}" for i in range(1, 17)]
        s = ["if (tb_started && !reset) begin", "  " + onehot(g, "g")]
        for i in range(1, 17):
            s += [f"  if (g{i} && !req_{i} && !rq_p[{i}]) tb_prop(\"g{i} without req_{i}\");",
                  f"  if (g{i}_int && !rq_gi_p[{i}]) begin if (rq_done[{i}]) tb_prop(\"req_{i} granted twice in one "
                  f"assertion\"); rq_done[{i}] = 1'b1; end"]
        s += ["end"]
        for i in range(1, 17):
            s += [f"if (!req_{i} || reset) rq_done[{i}] = 1'b0; rq_p[{i}] = req_{i}; rq_gi_p[{i}] = g{i}_int;"]
        return d, s, "", ""
    if name == "irs":
        d = ""
        mod = ("always @(posedge en4) if (tb_started && header !== 1'b1) tb_prop(\"en4 rose without a header edge\");\n"
               "always @(posedge en5) if (tb_started && tailer !== 1'b1) tb_prop(\"en5 rose without a tailer edge\");\n"
               "always @(posedge data_sel) if (tb_started && rd_en !== 1'b1) tb_prop(\"data_sel rose without rd_en\");")
        s = ["if (tb_started) begin",
             "  if (en1 !== ~empty) tb_prop(\"en1 != !empty\");",
             "  if (en2 !== rd_en) tb_prop(\"en2 != rd_en\");",
             "  if (rd_en_out !== (en4 ? en2 : en1)) tb_prop(\"rd_en_out != (en4 ? rd_en : !empty)\");",
             "  if (reset && {en4, en5, en6, data_sel} !== 4'b0000) tb_prop(\"state not cleared by reset\");",
             "end"]
        return d, s, mod, ""
    if name == "falling_edge_pulse_generator":
        d = "reg fp_F, fp_q0_pre, fp_gnt_prev, fp_expect; time fp_tfall;"
        mod = ("always @(posedge q0) if (tb_started && ($time != fp_tfall || gnt !== 1'b0)) "
               "tb_prop(\"q0 rose without a falling edge of gnt\");")
        s = ["if (tb_ph == 0) begin",
             "  if (tb_started && fp_expect && q0 !== 1'b1) tb_prop(\"no pulse after gnt fell\");",
             "  fp_q0_pre = q0; fp_expect = 1'b0;",
             "end else begin",
             "  if (tb_started && !reset && fp_q0_pre === 1'b1 && q0 !== 1'b0) tb_prop(\"pulse did not end at the clk edge\");",
             "  fp_F = reset ? 1'b0 : fp_q0_pre;",
             "end"]
        pd = ("if (fp_gnt_prev === 1'b1 && gnt === 1'b0) begin fp_tfall = $time; fp_expect = !reset && fp_F === 1'b0; end\n"
              "      fp_gnt_prev = gnt; if (reset) fp_F = 1'b0;")
        return d, s, mod, pd
    if name == "gray_mod6":
        d = ("reg [2:0] gm_old; reg gm_en, gm_rst, gm_dir;\n"
             "function [2:0] gm_next(input [2:0] s); case (s) 3'b000: gm_next = 3'b001; 3'b001: gm_next = 3'b011;\n"
             "  3'b011: gm_next = 3'b010; 3'b010: gm_next = 3'b110; 3'b110: gm_next = 3'b100; 3'b100: gm_next = 3'b000;\n"
             "  default: gm_next = 3'bxxx; endcase endfunction")
        s = ["if (tb_ph == 0) begin gm_old = gray_out; gm_en = en; gm_rst = reset; gm_dir = dir; end",
             "else if (tb_started && ^gm_old !== 1'bx) begin",
             "  if (gm_rst) begin if (gray_out !== 3'b000) tb_prop(\"reset did not give 000\"); end",
             "  else if (gm_en) begin if (gray_out !== gm_next(gm_old)) tb_prop(\"not one Gray step\"); end",
             "  else if (gray_out !== gm_old) tb_prop(\"changed while en = 0\");",
             "  if (gm_dir !== 1'bx) begin",
             "    if (gm_old == 3'b100 && gray_out !== 3'b100 && !gm_rst) begin if (dir !== ~gm_dir) tb_prop(\"dir did not toggle at the wrap\"); end",
             "    else if (gm_rst) begin if (dir !== gm_dir && dir !== 1'b0) tb_prop(\"dir changed to 1 under reset\"); end",
             "    else if (dir !== gm_dir) tb_prop(\"dir changed without a wrap\");",
             "  end",
             "end"]
        return d, s, "", ""
    if name == "memory":
        d = ("reg [31:0] mm [0:7]; reg [7:0] mm_known; reg [2:0] mm_wa, mm_ra; reg mm_we, mm_re, mm_rst;\n"
             "reg [31:0] mm_din, mm_old;")
        s = ["if (tb_ph == 0) begin mm_we = wr_en; mm_wa = wr_add; mm_din = data_in; mm_re = rd_en; mm_ra = rd_add;",
             "  mm_rst = reset; mm_old = data_out; end",
             "else begin",
             "  if (tb_started) begin",
             "    if (mm_rst) begin if (data_out !== 32'h60000000) tb_prop(\"read port not reset\"); end",
             "    else if (mm_re) begin if (mm_known[mm_ra] && data_out !== mm[mm_ra]) tb_prop(\"read data wrong\"); end",
             "    else if (^mm_old !== 1'bx && data_out !== mm_old) tb_prop(\"data_out changed without a read\");",
             "  end",
             "  if (mm_we) begin mm[mm_wa] = mm_din; mm_known[mm_wa] = 1'b1; end",
             "end"]
        return d, s, "", "if (tb_cyc == 0) mm_known = 8'h00;"
    if name == "router_fifo":
        d = ("reg [31:0] fq [0:7]; integer fq_n, fq_h, fq_t; reg fq_ok, fq_we, fq_re, fq_rst; reg [31:0] fq_din, fq_old;")
        s = ["if (tb_ph == 0) begin fq_we = wr_en; fq_re = rd_en; fq_rst = reset; fq_din = data_in; fq_old = data_out; end",
             "else begin",
             "  if (fq_rst) begin fq_n = 0; fq_h = 0; fq_t = 0; fq_ok = 1'b1;",
             "    if (tb_started && data_out !== 32'h60000000) tb_prop(\"data_out not reset\"); end",
             "  else if (fq_ok) begin",
             "    if (fq_re && fq_n > 0) begin",
             "      if (data_out !== fq[fq_h]) tb_prop(\"FIFO order: wrong word read\");",
             "      fq_h = (fq_h + 1) % 8; fq_n = fq_n - 1;",
             "      if (fq_we && fq_n + 1 < 6) begin fq[fq_t] = fq_din; fq_t = (fq_t + 1) % 8; fq_n = fq_n + 1; end",
             "    end else begin",
             "      if (data_out !== fq_old) tb_prop(\"data_out changed without a read (underflow)\");",
             "      if (fq_we && fq_n < 6) begin fq[fq_t] = fq_din; fq_t = (fq_t + 1) % 8; fq_n = fq_n + 1; end",
             "    end",
             "  end",
             "end",
             "if (tb_started && fq_ok && !reset) begin",
             "  if (empty !== (fq_n == 0)) tb_prop(\"empty flag wrong\");",
             "  if (full_int !== (fq_n == 6)) tb_prop(\"full_int flag wrong (overflow)\");",
             "  if (full_ext !== (fq_n >= 4)) tb_prop(\"full_ext flag wrong\");",
             "end"]
        return d, s, "", "if (tb_cyc == 0) fq_ok = 1'b0;"
    # Cheap spec properties for some non-timing modules; their verdict is the comparison plus these.
    simple = {
        "rr_comb_new": [onehot(["g1", "g2", "g3", "g4"], "grant")]
                       + [f"if (g{i} === 1'b1 && r{i} !== 1'b1) tb_prop(\"g{i} without r{i}\");" for i in range(1, 5)],
        "priority_encoder": [onehot(["out0", "out1", "out2", "out3"], "out")],
        "routing_algo_mesh": [onehot(["req_link1", "req_link2", "req_link3", "req_link4", "req_core"], "request"),
                              "if (reset && {req_link1, req_link2, req_link3, req_link4, req_core} !== 5'b0) "
                              "tb_prop(\"request while reset\");"],
        "allot_vc": [onehot(["ce_b1", "ce_b2", "ce_b3", "ce_b4"], "ce_b")],
        "demux_16": [onehot([f"op{i}" for i in range(1, 17)], "op")],
    }
    for op in ("op_core", "op_link1", "op_link2", "op_link3", "op_link4"):
        simple[op] = [onehot(["gnt_vc1", "gnt_vc2", "gnt_vc3", "gnt_vc4"], "gnt_vc")]
    if name in simple:
        return "", ["if (tb_started) begin"] + ["  " + x for x in simple[name]] + ["end"], "", ""
    return "", [], "", ""


# --------------------------------------------------------------------------- testbench text
def testbench(name, row, golden_text, cycles, seed, signoff) -> str:
    ports = row["port_list"]
    rules = stimulus(name, row)
    checked = [(n, w) for d, n, w in ports if d == "output" and n not in NOT_CHECKED.get(name, [])]
    timing = name in TIMING and signoff
    pdecl, pstmts, pmod, pdrive = props(name, row) if signoff else ("", [], "", "")
    ref = re.sub(rf"\bmodule\s+{name}\b", f"module {name}__ref", golden_text, count=1)
    # The 2x2 mesh only has rows/columns 0..1; single routers see destinations 0..3 around address 1..2.
    dmax, dest = (1, "3'b000, r[4], 3'b000, r[0]") if name == "top_2x2_router" else (3, "2'b00, r[5:4], 2'b00, r[1:0]")

    L = ["`timescale 1ns / 1ps", f"// Generated by pipeline/make_tasks.py ({'sign-off' if signoff else 'loop'}). "
         f"Reference: golden/reference ({name}__ref below).", "module tb;",
         "  reg tb_clk; integer tb_seed, tb_cyc, tb_mis, tb_perr, tb_b, tb_k, tb_ph; reg tb_started; reg [31:0] tb_r;"]
    for d, n, w in ports:
        rng = f"[{w - 1}:0] " if w > 1 else ""
        if d == "input":
            L.append(f"  wire {n} = tb_clk;" if rules[n][0] == "clock" else f"  reg {rng}{n};")
        else:
            L.append(f"  wire [{w - 1}:0] {n}; wire [{w - 1}:0] ref_{n};")   # [0:0] too: bit-select in tb_compare
    if pdecl:
        L += ["  " + x for x in pdecl.splitlines()]
    conn = ", ".join(f".{n}({n})" for _, n, _ in ports)
    rconn = ", ".join(f".{n}({n})" if d == "input" else f".{n}(ref_{n})" for d, n, _ in ports)
    L += [f"  {name} dut ({conn});", f"  {name}__ref ref_i ({rconn});", "  always #5 tb_clk = ~tb_clk;",
          "  function [31:0] tb_rand(input integer dummy); begin tb_rand = $random(tb_seed); end endfunction",
          f"  // flit: type in [30:29], VC in [28:27], destination row/column 0..{dmax} in [7:4]/[3:0]",
          "  function [31:0] tb_flit(input integer dummy); reg [31:0] r; begin r = $random(tb_seed);",
          f"    tb_flit = {{1'b0, r[30:29], r[28:27], r[26:8], {dest}}}; end endfunction",
          "  task tb_prop(input [8*64:1] msg); begin tb_perr = tb_perr + 1;",
          "    if (tb_perr <= 15) $display(\"FAIL property: %0s (t=%0t)\", msg, $time); end endtask",
          "  task tb_compare; begin"]
    tag = "MISMATCH (secondary, not part of the verdict)" if timing else "FAIL"
    for n, w in checked:
        L += [f"    for (tb_b = 0; tb_b < {w}; tb_b = tb_b + 1)",
              f"      if (ref_{n}[tb_b] !== 1'bx && ref_{n}[tb_b] !== 1'bz && {n}[tb_b] !== ref_{n}[tb_b]) begin",
              f"        tb_mis = tb_mis + 1; tb_b = {w};",
              f"        if (tb_mis <= 15) $display(\"{tag} t=%0t cycle %0d: {n} = %h, expected %h\", "
              f"$time, tb_cyc, {n}, ref_{n});",
              "      end"]
    L += ["  end endtask", "  task tb_props; begin"] + ["    " + x for x in pstmts] + ["  end endtask"]
    # Toggle coverage of the reference outputs (reported as INFO, never part of the verdict).
    L += [f"  reg [{w - 1}:0] tbc_p_{n}, tbc_t_{n};" for n, w in checked]
    L += ["  integer tbc_outs, tbc_bits;", "  task tb_cov; begin"]
    L += [f"    if (tb_cyc > 6 || tb_ph == 1) tbc_t_{n} = tbc_t_{n} | ((ref_{n} ^ tbc_p_{n}) & ~(ref_{n} ^ ref_{n}));"
          f" tbc_p_{n} = ref_{n};" for n, w in checked]
    L += ["  end endtask", "  task tb_cov_report; begin tbc_outs = 0; tbc_bits = 0;"]
    for n, w in checked:
        L += [f"    if (|tbc_t_{n}) tbc_outs = tbc_outs + 1;",
              f"    for (tb_b = 0; tb_b < {w}; tb_b = tb_b + 1) if (tbc_t_{n}[tb_b] === 1'b1) tbc_bits = tbc_bits + 1;"]
    total_bits = sum(w for _, w in checked)
    L += [f"    $display(\"INFO coverage: %0d of {len(checked)} checked outputs toggled, %0d of {total_bits} bits\", "
          "tbc_outs, tbc_bits);", "  end endtask"]
    if pmod:
        L += ["  " + x for x in pmod.splitlines()]
    init = [f"{n} = 0;" for d, n, w in ports if d == "input" and rules[n][0] != "clock"]
    init += [f"{n} = 1;" for n, r in rules.items() if r[0] == "reset"]
    L += ["  initial begin",
          f"    tb_seed = {seed}; tb_clk = 0; tb_mis = 0; tb_perr = 0; tb_started = 0; tb_ph = 0; tb_k = 0;",
          "    " + " ".join(init),
          "    " + " ".join(f"tbc_t_{n} = 0; tbc_p_{n} = 0;" for n, _ in checked),
          f"    for (tb_cyc = 0; tb_cyc < {cycles}; tb_cyc = tb_cyc + 1) begin",
          "      @(negedge tb_clk);",
          drive_code(name, row, rules)]
    if pdrive:
        L.append("      " + pdrive)
    L += ["      tb_started = (tb_cyc >= 6);",
          "      #4 tb_ph = 0; tb_compare; tb_props; if (tb_started) tb_cov;",
          "      @(posedge tb_clk); #4 tb_ph = 1; tb_compare; tb_props; if (tb_started) tb_cov;",
          "    end", "    tb_cov_report;"]
    if timing:
        L += ["    $display(\"INFO cycle-exact mismatches against golden/reference: %0d (secondary)\", tb_mis);",
              "    if (tb_perr == 0) $display(\"ALL TESTS PASSED\"); else $display(\"FAIL: %0d property errors\", tb_perr);"]
    else:
        L += ["    if (tb_mis + tb_perr == 0) $display(\"ALL TESTS PASSED\");",
              "    else $display(\"FAIL: %0d mismatches, %0d property errors\", tb_mis, tb_perr);"]
    L += ["    $finish;", "  end", "endmodule", "", "// ---- reference copy of the golden module (children come from lib/)",
          ref.rstrip(), ""]
    return "\n".join(L)


def mutant(name, row, golden_text) -> str:
    """Golden wrapped so that bit 0 of one output is inverted (validation only; never shipped as a task file)."""
    target = MUTANT_OUTPUT.get(name) or next(n for d, n, w in row["port_list"] if d == "output"
                                             and n not in NOT_CHECKED.get(name, []))
    core = re.sub(rf"\bmodule\s+{name}\b", f"module {name}__mut_core", golden_text, count=1)
    names = ", ".join(n for _, n, _ in row["port_list"])
    body = ["  " + decl(d, n, w) for d, n, w in row["port_list"]]
    w_t = next(w for d, n, w in row["port_list"] if n == target)
    body.append(f"  wire {'[' + str(w_t - 1) + ':0] ' if w_t > 1 else ''}mut_{target};")
    conn = ", ".join(f".{n}(mut_{n})" if n == target else f".{n}({n})" for _, n, _ in row["port_list"])
    body += [f"  {name}__mut_core u ({conn});", f"  assign {target} = mut_{target} ^ 1'b1;"]
    return core.rstrip() + f"\n\nmodule {name}({names});\n" + "\n".join(body) + "\nendmodule\n"


def main() -> None:
    rows = load_rows()
    if TASKS.exists():
        for child in TASKS.iterdir():
            if child.is_dir():
                shutil.rmtree(child)
    for name, row in rows.items():
        td = TASKS / name
        td.mkdir(parents=True)
        golden_text = (REFERENCE / row["file"]).read_text(encoding="utf-8")
        (td / "golden.v").write_text(golden_text, encoding="utf-8", newline="\n")
        shutil.copyfile(HANDWRITTEN / row["file"], td / "input.v")
        (td / "spec.md").write_text(spec_for_task(name), encoding="utf-8", newline="\n")
        meta = {"track": "N", "top": name, "source": f"golden/handwritten/{row['file']}",
                "children": row["child_list"], "descendants": descendants(rows, name),
                "checked_outputs": [n for d, n, w in row["port_list"] if d == "output"
                                    and n not in NOT_CHECKED.get(name, [])],
                "not_checked": NOT_CHECKED.get(name, []), "timing_dependent": name in TIMING,
                "signoff_verdict": "properties" if name in TIMING else "comparison+properties",
                "mutant_output": MUTANT_OUTPUT.get(name), "phase3_task": row["phase3_task"] or None}
        if name in PHASE3_REGISTERS:
            for f in ("tb.v", "tb_signoff.v"):
                shutil.copyfile(P3_TASKS / name / f, td / f)
            p3meta = json.loads((P3_TASKS / name / "meta.json").read_text(encoding="utf-8"))
            meta = {**p3meta, **{k: v for k, v in meta.items() if k not in ("track", "top")},
                    "signoff_verdict": "phase3 tb_signoff.v"}
        else:
            (td / "tb.v").write_text(testbench(name, row, golden_text, LOOP_CYCLES, LOOP_SEED, False),
                                     encoding="utf-8", newline="\n")
            (td / "tb_signoff.v").write_text(testbench(name, row, golden_text, SIGNOFF_CYCLES, SIGNOFF_SEED, True),
                                             encoding="utf-8", newline="\n")
        if row["child_list"]:
            (td / "lib").mkdir()
            (td / "stubs").mkdir()
            for dname in meta["descendants"]:
                shutil.copyfile(REFERENCE / rows[dname]["file"], td / "lib" / f"{dname}.v")
            for child in row["child_list"]:
                (td / "stubs" / f"{child}.v").write_text(stub(rows[child]), encoding="utf-8", newline="\n")
        (td / "meta.json").write_text(json.dumps(meta, indent=1) + "\n", encoding="utf-8", newline="\n")
    print(f"tasks: {len(rows)}")


if __name__ == "__main__":
    main()
