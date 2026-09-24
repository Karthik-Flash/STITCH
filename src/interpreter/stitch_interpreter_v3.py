"""
stitch_interpreter_v3.py -- Phase 3 ADDITIVE upgrade layer over the production interpreter.

Contract (non-negotiable):
  * stitch_interpreter.py (production v2) is imported, never edited. Its SHA-256 is recorded in every
    result so Phase 1/2 numbers stay reproducible.
  * version="v2" reproduces the production functions' output exactly (tests/test_v3_layer.py proves it).
  * version="v3" only intervenes where a production directive was shown WRONG or MISSING on real
    Yosys 0.33 / Verilator 5.020 output (evidence: phase3/evidence/PROD_V2_ON_REAL_LOGS.md). Everything
    else is passed straight through to the production functions.

v3 rules (each is individually switchable for ablation via `rules=`):
  R1  CLOCK_UNUSED   UNUSEDSIGNAL on a clock-named port. v2 emits an `if (clk) ... else out=0` gate inside
                     always @(*) -> a clock-gated latch. v3: MISSING_CLOCK (if Yosys latched a level-sensitive
                     block) or an edge-trigger directive.                     [real: register_4bit, register_32bit]
  R2  RESET_UNUSED   UNUSEDSIGNAL on a reset-named port -> reset-branch template, not an output gate.
  R3  PARTIAL_BITS   "Bits of signal are not used: 'x'[a:b]" -- v2 treats it as a whole unused PORT and gates
                     outputs on it (even for internal wires). v3 suppresses it (logged).
                                                                       [real: Address_select, multiply]
  R4  STYLE_FIX      BLKSEQ/COMBDLY: v2 extracts the prose word 'process' (named in the directive when no
                     source is given, dropped when it is); v2's COMBDLY text describes '#' delays, but
                     Verilator 5 COMBDLY means '<=' in a combinational block. v3 names the real LHS from the
                     reported line, correct text, lowest priority.
  R5  SCOPE_MODULE   multi-module files: v2's output-port scan reads every module in the file (multiply.v
                     listed 9 'outputs'). v3 hands v2 a temp file holding only the module under repair.
  N1  ASYNC_RESET    Yosys "Multiple edge sensitive events" ERROR (no signal named by Yosys; recovered from
                     source). v2 has no handler -> silent.                                 [real: register_1bit]
  N2  VERILATOR_LOOP UNOPTFLAT loop when Yosys `check` is silent. v2 is Yosys-only for loops.   [real: IFU PC=PC]
  N3  LOOP_SIGNALS   when Yosys reports a loop, append the wire path (v2 names only the module).
  N4  MULTI_SIGNALS  v2 names only the first signal per code; v3 appends the remaining MULTIDRIVEN/UNDRIVEN
                     signals (both Verilator 5 MULTIDRIVEN formats).
  N5  PINMISSING     composition class: unconnected instance port (positional-binding hazard).
  N6  WIDTH_EXPR     WIDTHTRUNC/WIDTHEXPAND whose operand is an expression ("... CONCAT generates 50 bits."):
                     v2's extractor finds no identifier and drops the warning silently.     [seeded: ni_flit_pack]
  L1  LATCH_LINES    always call v2 interpret_yosys_latches() with raw Yosys LINES (passing
                     detect_yosys_latches() names yields "signal(s) an output signal ... 'out'").
Directives are priority-ordered and capped (max_directives) to respect the harmful-regime finding.
"""
from __future__ import annotations

import hashlib
import os
import re
import tempfile
from typing import Dict, List, Optional

import stitch_interpreter as base  # production v2 -- DO NOT EDIT

from _v3_parsers import (_CLK_RE, _RST_RE, _always_header, _async_reset_block, _snippet, _src_model,
                         parse_verilator, parse_yosys)

V3_VERSION = "3.0.0"
ALL_RULES = ("R1", "R2", "R3", "R4", "R5", "N1", "N2", "N3", "N4", "N5", "N6", "L1")
PRIO = {"ASYNC_RESET": 0, "COMB_LOOP": 1, "MULTIDRIVEN": 2, "MISSING_CLOCK": 3, "LATCH": 4,
        "UNDRIVEN": 5, "PINMISSING": 6, "WIDTHTRUNC": 7, "WIDTHEXPAND": 8, "UNUSEDSIGNAL": 9,
        "CLOCK_UNUSED": 3, "RESET_UNUSED": 9, "BLKSEQ": 20, "COMBDLY": 21}


def base_fingerprint() -> str:
    p = base.__file__
    b = open(p, "rb").read().replace(b"\r\n", b"\n")
    return hashlib.sha256(b).hexdigest()


# --------------------------------------------------------------------------- source scoping (R5)
def module_text(source: str, top: Optional[str]) -> str:
    if not top:
        return source
    m = re.search(rf"^\s*module\s+{re.escape(top)}\b.*?^\s*endmodule\b", source, re.S | re.M)
    if not m:
        return source
    # Blank (not slice) everything outside the module so tool line numbers still index correctly.
    blank = lambda t: re.sub(r"[^\n]", " ", t)
    return blank(source[:m.start()]) + m.group(0) + blank(source[m.end():])


def _scoped_path(v_path: Optional[str], top: Optional[str], enabled: bool):
    if not v_path or not enabled or not top:
        return v_path, None
    try:
        src = open(v_path, encoding="utf-8", errors="ignore").read()
    except OSError:
        return v_path, None
    if len(re.findall(r"^\s*module\s", src, re.M)) <= 1:
        return v_path, None
    fd, tmp = tempfile.mkstemp(suffix=".v")
    with os.fdopen(fd, "w") as fh:
        fh.write(module_text(src, top))
    return tmp, tmp


# --------------------------------------------------------------------------- v2 reproduction
def interpret_v2(verilator_out: str, yosys_out: str, v_path: Optional[str] = None) -> Dict:
    """Exactly the production functions, composed in the documented order (Verilator, latch, loop)."""
    vt, vcodes = base.interpret_verilator(verilator_out or "", v_path)
    latch_lines = [l for l in (yosys_out or "").splitlines() if base._LATCH_POSITIVE_RE.search(l)
                   and "no latch" not in l.lower()]
    lt = base.interpret_yosys_latches(latch_lines, v_path) if base.detect_yosys_latches(yosys_out or "") else ""
    ct = base.interpret_comb_loop(yosys_out or "") or ""
    codes = list(vcodes) + (["LATCH"] if lt else []) + (["COMB_LOOP"] if ct else [])
    text = "\n\n".join(t.strip("\n") for t in (vt, lt, ct) if t)
    return {"text": text, "codes_fired": codes, "classes_fired": sorted(set(codes)), "version": "v2",
            "fired": bool(codes), "rules_applied": [], "suppressed": []}


# --------------------------------------------------------------------------- v3
def _drop_lines(raw: str, pred) -> str:
    """Remove whole Verilator records (header + continuation lines) whose header matches pred."""
    out, skip = [], False
    for l in raw.splitlines():
        if l.lstrip().startswith("%"):
            skip = bool(pred(l))
        if not skip:
            out.append(l)
    return "\n".join(out)


def _lhs_on_line(src, line):
    if not src or not line or line > len(src.lines):
        return None
    m = re.search(r"([A-Za-z_]\w*)\s*(?:\[[^\]]*\])?\s*<?=(?!=)", src.lines[line - 1])
    return m.group(1) if m else None


def interpret_v3(verilator_out: str, yosys_out: str, v_path: Optional[str] = None, *, top: Optional[str] = None,
                 rules=ALL_RULES, max_directives: int = 3) -> Dict:
    rules = set(rules)
    vraw, yraw = verilator_out or "", yosys_out or ""
    source = None
    if v_path:
        try:
            source = open(v_path, encoding="utf-8", errors="ignore").read()
        except OSError:
            source = None
    scoped = module_text(source, top) if (source and "R5" in rules) else source
    src = _src_model(scoped)
    vd, yd = parse_verilator(vraw), parse_yosys(yraw)
    applied, suppressed, extra = [], [], []   # extra: list of (class, prio, text)

    latch_sigs = {d.signal.split("[")[0] for d in yd if d.code == "LATCH" and d.signal}
    missing_clock_sigs = set()

    # ---- R1 / R2: clock / reset named UNUSEDSIGNAL
    def _is_named_unused(l, rx):
        if "UNUSEDSIGNAL" not in l or "Bits of signal" in l:
            return False
        s = base._extract_signal_name(l)
        return bool(s and rx.match(s))

    clk_unused = [d.signal for d in vd if d.code == "UNUSEDSIGNAL" and not d.detail.get("bits")
                  and d.signal and _CLK_RE.match(d.signal)]
    if "R1" in rules and clk_unused:
        clk = clk_unused[0]
        seq = [d for d in yd if d.code == "LATCH" and
               ((_always_header(src, d.line) or "") not in ("@*", "@(*)")) and "edge" not in (_always_header(src, d.line) or "")]
        if seq:
            sigs = sorted({d.signal.split("[")[0] for d in seq if d.signal})
            missing_clock_sigs |= set(sigs)
            ln = seq[0].line
            txt = (f"*** CRITICAL: MISSING CLOCK -- {', '.join(repr(s) for s in sigs)} is a REGISTER but is written in a "
                   f"level-sensitive always block{' (line ' + str(ln) + ')' if ln else ''}, so synthesis built a LATCH, "
                   f"and the clock port '{clk}' is never used. ***\n"
                   f"EXACT FIX: change that block's header to\n"
                   f"    always @(posedge {clk})\n"
                   f"(or  always @(posedge {clk} or posedge <reset>)  for an asynchronous reset), use '<=' for every "
                   f"assignment inside it, and keep the existing if/else priority. Do NOT add 'if ({clk})' anywhere.")
            snip = _snippet(src, ln)
            if snip:
                txt += "\nOffending block:\n" + snip
            extra.append(("MISSING_CLOCK", PRIO["MISSING_CLOCK"], txt))
        else:
            extra.append(("CLOCK_UNUSED", PRIO["CLOCK_UNUSED"],
                          f"*** CRITICAL: Clock '{clk}' is declared but NEVER USED -- nothing in this module is clocked. ***\n"
                          f"Every register must be updated in  always @(posedge {clk})  with '<='. "
                          f"Never use '{clk}' as a data/enable condition (no 'if ({clk})')."))
        vraw = _drop_lines(vraw, lambda l: _is_named_unused(l, _CLK_RE))
        applied.append("R1")
    if "R2" in rules:
        rst_unused = [d.signal for d in vd if d.code == "UNUSEDSIGNAL" and not d.detail.get("bits")
                      and d.signal and _RST_RE.match(d.signal) and not _CLK_RE.match(d.signal)]
        if rst_unused:
            r = rst_unused[0]
            extra.append(("RESET_UNUSED", PRIO["RESET_UNUSED"],
                          f"*** CRITICAL: Reset '{r}' is declared but NEVER USED. Every register must respond to it: ***\n"
                          f"    always @(posedge clk) if ({r}) <reg> <= 0; else <reg> <= <next>;\n"
                          f"(use  always @(posedge clk or posedge {r})  if the spec says asynchronous)."))
            vraw = _drop_lines(vraw, lambda l: _is_named_unused(l, _RST_RE) and not _is_named_unused(l, _CLK_RE))
            applied.append("R2")

    # ---- R3: partial-bit unused / undriven are not port-level defects
    if "R3" in rules and re.search(r"Bits of signal are not (used|driven)", vraw):
        n = len(re.findall(r"Bits of signal are not used", vraw))
        m_und = [d for d in vd if d.code == "UNDRIVEN" and d.detail.get("bits")]
        vraw = _drop_lines(vraw, lambda l: "Bits of signal are not used" in l or "Bits of signal are not driven" in l)
        if n:
            suppressed.append(f"UNUSEDSIGNAL(bits)x{n}")
        for d in m_und:
            extra.append(("UNDRIVEN", PRIO["UNDRIVEN"],
                          f"*** CRITICAL: bits {d.detail['bits']} of '{d.signal}' are never assigned (they float). ***\n"
                          f"Assign the FULL width of '{d.signal}', padding explicitly, e.g. {d.signal} = {{<zeros>, <value>}};"))
        applied.append("R3")

    # ---- R4: style codes
    if "R4" in rules and re.search(r"%Warning-(BLKSEQ|COMBDLY)", vraw):
        for d in vd:
            if d.code in ("BLKSEQ", "COMBDLY"):
                lhs = _lhs_on_line(src, d.line) if d.file and v_path and os.path.basename(d.file) == os.path.basename(v_path) else None
                who = f" (line {d.line}: '{lhs}')" if lhs else ""
                if d.code == "BLKSEQ":
                    t = f"[STYLE] Blocking '=' inside a clocked always block{who}. Inside always @(posedge ...) use '<=': {lhs or '<reg>'} <= <value>;"
                else:
                    t = f"[STYLE] Non-blocking '<=' inside a combinational always block{who}. Inside always @(*) use '=': {lhs or '<sig>'} = <value>;"
                extra.append((d.code, PRIO[d.code], t))
                break
        vraw = _drop_lines(vraw, lambda l: re.search(r"%Warning-(BLKSEQ|COMBDLY)", l))
        applied.append("R4")

    # ---- N4: remaining MULTIDRIVEN signals beyond v2's first
    if "N4" in rules:
        md, seen_sig = [], set()
        for d in vd:
            if d.code == "MULTIDRIVEN" and d.signal and d.signal not in seen_sig:
                seen_sig.add(d.signal); md.append(d)
        if len(md) > 1:
            for d in md[1:3]:
                kind = d.detail.get("kind")
                how = ("two always blocks with different clocking/reset -- keep ONE always @(posedge clk or posedge rst) block"
                       if kind == "clocking" else "more than one assign/always -- keep ONE driver")
                extra.append(("MULTIDRIVEN", PRIO["MULTIDRIVEN"] + 0.5,
                              f"*** CRITICAL: '{d.signal}' is ALSO multiply driven ({how}). Delete every other driver. ***"))
            applied.append("N4")

    # ---- N6: WIDTHTRUNC/WIDTHEXPAND whose operand is an EXPRESSION (no quoted name -> v2 extracts nothing)
    if "N6" in rules:
        done = 0
        for d in vd:
            if d.code in ("WIDTHTRUNC", "WIDTHEXPAND") and d.signal is None and d.detail.get("expects") and done < 2:
                e, g = d.detail["expects"], d.detail["generates"]
                lhs = _lhs_on_line(src, d.line) if src else None
                code_line = src.lines[d.line - 1].strip() if (src and d.line and d.line <= len(src.lines)) else ""
                where = f" at line {d.line}" + (f": `{code_line}`" if code_line else "")
                if d.code == "WIDTHTRUNC":
                    t = (f"*** CRITICAL: WIDTH TRUNCATION{where} -- the right-hand expression is {g} bits but "
                         f"{repr(lhs) if lhs else 'the destination'} is only {e} bits, so the top {g - e} bits are "
                         f"SILENTLY DROPPED. ***\nFIX: make the expression exactly {e} bits. Take each field's width from the "
                         f"spec, slice wider operands explicitly (x[N-1:0]) and write padding as sized constants (<k>'d0), "
                         f"so that the widths of all concatenated parts add up to exactly {e}.")
                else:
                    t = (f"*** WIDTH EXTENSION{where} -- the expression is {g} bits but the destination is {e} bits. "
                         f"Pad explicitly: {{{e - g}'b0, <expr>}} (unsigned) or sign-extend for signed values. ***")
                extra.append((d.code, PRIO[d.code], t))
                done += 1
        if done:
            applied.append("N6")

    # ---- N1: async reset crash
    if "N1" in rules and "Multiple edge sensitive events" in yraw:
        blk = _async_reset_block(src)
        if blk:
            ln, cond, edges = blk
            rst = next((e for e in edges.split(", ") if _RST_RE.match(e)), edges.split(", ")[-1])
            rest = re.sub(rf"\s*\|\|?\s*\b{re.escape(rst)}\b|\b{re.escape(rst)}\b\s*\|\|?\s*", "", cond).strip() or "<sync clear>"
            clk = next((e for e in edges.split(", ") if e != rst), "clk")
            win = "\n".join(src.lines[ln - 1:ln + 12])
            mq = re.search(r"([A-Za-z_]\w*)\s*(?:\[[^\]]*\])?\s*<=", win)
            q = mq.group(1) if mq else "q"
            txt = (f"*** CRITICAL: SYNTHESIS FAILED (Yosys: 'Multiple edge sensitive events'). The block at line {ln} is "
                   f"sensitive to ({edges}) but its first test is  if ({cond}). In an edge-triggered block with an "
                   f"asynchronous reset the FIRST if must test ONLY the reset signal. ***\nEXACT FIX:\n"
                   f"    always @(posedge {clk} or posedge {rst})\n      if ({rst})            {q} <= 0;\n"
                   f"      else if ({rest})   {q} <= 0;   // synchronous part\n      else if (<enable>) {q} <= <d>;")
            snip = _snippet(src, ln)
            if snip:
                txt += "\nOffending block:\n" + snip
        else:
            txt = ("*** CRITICAL: SYNTHESIS FAILED (Yosys: 'Multiple edge sensitive events'). In "
                   "always @(posedge clk or posedge rst) the first statement must be  if (rst)  testing ONLY the reset; "
                   "move every other condition (e.g. a synchronous clear) into the else branches. ***")
        extra.append(("ASYNC_RESET", PRIO["ASYNC_RESET"], txt))
        applied.append("N1")

    # ---- N2 / N3: loops
    yosys_loop = bool(base.detect_comb_loops(yraw))
    vloops = [d for d in vd if d.code == "COMB_LOOP"]
    if "N2" in rules and vloops and not yosys_loop:
        path = [p for d in vloops for p in (d.detail.get("path") or [d.signal]) if p]
        path = list(dict.fromkeys(path)) or [vloops[0].signal]
        selfref = [p for p in path if src and re.search(rf"\b{re.escape(p)}\s*=\s*{re.escape(p)}\s*;", src.text)]
        hint = (f"\n'{selfref[0]} = {selfref[0]};' holds a value with no clock -- that is state, and state belongs in "
                f"always @(posedge clk) with '<='.") if selfref else ""
        extra.append(("COMB_LOOP", PRIO["COMB_LOOP"],
                      f"*** CRITICAL: Combinational loop (Verilator UNOPTFLAT): {' -> '.join(path + path[:1])} depends on "
                      f"itself with no register in between.{hint} ***\nFIX: either (a) move the signal that must hold its "
                      f"value into a clocked block (always @(posedge clk) x <= x_next;) and read the registered copy, or "
                      f"(b) compute it only from module inputs."))
        applied.append("N2")
    if "N3" in rules and yosys_loop:
        wires = [p for d in yd if d.code == "COMB_LOOP" for p in d.detail.get("path", [])]
        if wires:
            extra.append(("COMB_LOOP", PRIO["COMB_LOOP"] + 0.5,
                          f"Signals on that loop: {' -> '.join(list(dict.fromkeys(wires)))}. Break the cycle at one of them."))
            applied.append("N3")

    # ---- N5: pin missing (composition)
    if "N5" in rules:
        pins = [d for d in vd if d.code == "PINMISSING" and d.signal]
        if pins:
            names = sorted({d.signal for d in pins})[:6]
            extra.append(("PINMISSING", PRIO["PINMISSING"],
                          f"*** Instance port(s) left unconnected: {', '.join(names)}. Connect every port BY NAME "
                          f"(.port(net)); positional connections silently shift when a port is missing. ***"))
            applied.append("N5")

    # ---- production v2 on the (filtered) Verilator text, scoped source, raw latch LINES
    vpath2, tmp = _scoped_path(v_path, top, "R5" in rules)
    try:
        vt, vcodes = base.interpret_verilator(vraw, vpath2)
        lines = [l for l in yraw.splitlines() if base._LATCH_POSITIVE_RE.search(l) and "no latch" not in l.lower()]
        if missing_clock_sigs:
            lines = [l for l in lines if not any(re.search(rf"\\{re.escape(s)}\b", l) for s in missing_clock_sigs)]
        lt = base.interpret_yosys_latches(lines, vpath2) if lines else ""
        ct = base.interpret_comb_loop(yraw) or ""
    finally:
        if tmp:
            os.unlink(tmp)
    if "R5" in rules and tmp:
        applied.append("R5")
    if "L1" in rules and lines:
        applied.append("L1")

    blocks = [(c, PRIO.get(c, 10), b) for c, b in zip(vcodes, vt.split("\n\n")) if b.strip()] if vt else []
    if len(blocks) != len(vcodes):          # defensive: keep v2 text whole if split is ambiguous
        blocks = [(vcodes[0] if vcodes else "VERILATOR", min((PRIO.get(c, 10) for c in vcodes), default=10), vt)] if vt else []
    if lt:
        blocks.append(("LATCH", PRIO["LATCH"], lt.strip("\n")))
    if ct:
        blocks.append(("COMB_LOOP", PRIO["COMB_LOOP"], ct))
    allb = blocks + extra
    hard = [b for b in allb if b[0] not in ("BLKSEQ", "COMBDLY")]
    ordered = sorted(hard, key=lambda b: b[1]) + ([b for b in allb if b[0] in ("BLKSEQ", "COMBDLY")] if not hard else [])
    shown, dropped = ordered[:max_directives], ordered[max_directives:]
    text = "\n\n".join(b[2] for b in shown)
    if dropped:
        text += f"\n\n(Fix the above first; {len(dropped)} lower-priority issue(s) will be reported next iteration.)"
    classes = sorted({b[0] for b in shown})
    sig_keys = sorted({f"{d.code}:{(d.signal or '').split('[')[0]}" for d in vd + yd
                       if d.code not in ("BLKSEQ", "COMBDLY", "CASEINCOMPLETE")})
    if "Multiple edge sensitive events" in yraw:
        sig_keys.append("ASYNC_RESET:")
    return {"text": text, "codes_fired": [b[0] for b in shown], "classes_fired": classes, "fired": bool(shown),
            "version": "v3", "v3_version": V3_VERSION, "rules_applied": sorted(set(applied)),
            "suppressed": suppressed + [b[0] for b in dropped], "base_codes": vcodes,
            "signature": "|".join(sorted(set(sig_keys)))}


def interpret(verilator_out: str, yosys_out: str, v_path: Optional[str] = None, *, version: str = "v3",
              top: Optional[str] = None, **kw) -> Dict:
    r = interpret_v2(verilator_out, yosys_out, v_path) if version == "v2" else \
        interpret_v3(verilator_out, yosys_out, v_path, top=top, **kw)
    r["base_sha256_lf"] = base_fingerprint()
    return r
