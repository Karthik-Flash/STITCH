"""
_v3_parsers.py -- tool-log parsers + directive builders used ONLY by stitch_interpreter_v3.py.
Not a replacement for stitch_interpreter.py (production v2), which stays authoritative and unmodified.

Deterministic (regex + light source parsing), no LLM call, zero inference cost.

Validated against REAL tool output (fixtures in tests/fixtures, regression tests in
tests/test_interpreter.py):
    Yosys 0.33, Verilator 5.020, Icarus Verilog 12.0
Run `python -m pytest tests/` on the HPC toolchain before any experiment (Gate 0);
message formats drift between tool versions.

Public API
----------
interpret_eda_feedback(tool_name, raw_log, source=None, **opts) -> str
    Backward-compatible: returns a prompt-ready string. If nothing is recognised,
    the raw log is returned unchanged (graceful fallback, as in the MLCAD paper).

interpret_eda_feedback_ex(tool_name, raw_log, source=None, **opts) -> InterpretResult
    Structured result: .fired, .codes, .diagnostics, .directives, .text, .signature

interpret_multi(logs: dict[str,str], source=None, **opts) -> InterpretResult
    Fuses Verilator + Yosys (+ Icarus) logs for one iteration, de-duplicates the same
    defect seen by two tools, applies cross-tool rules, prioritises, caps count.

interpret_legacy(raw_log) -> str
    The MLCAD'26 Listing-1 vocabulary (UNUSEDSIGNAL + Yosys latch only), with the
    Verilator-5 quote bug fixed, for the `sem_legacy` ablation condition.

Defect classes (canonical codes)
--------------------------------
ASYNC_RESET   Yosys "Multiple edge sensitive events" (reset condition not a bare edge signal)
COMB_LOOP     Yosys `check` "found logic loop", Verilator UNOPTFLAT / ALWCOMBORDER
MULTIDRIVEN   Verilator MULTIDRIVEN (both formats), Yosys "multiple conflicting drivers"
LATCH         Yosys "Latch inferred for signal", Verilator LATCH, CASEINCOMPLETE (merged)
MISSING_CLOCK cross-tool: LATCH in a level-sensitive block + UNUSED clock input
UNDRIVEN      Verilator UNDRIVEN (whole or bits), Yosys "is used but has no driver"
WIDTHTRUNC    Verilator WIDTHTRUNC / legacy WIDTH (truncation)
WIDTHEXPAND   Verilator WIDTHEXPAND / legacy WIDTH (extension)
PINMISSING    Verilator PINMISSING / PINCONNECTEMPTY (composition-level)
UNUSEDSIGNAL  Verilator UNUSEDSIGNAL / legacy UNUSED (whole or bits)
BLKSEQ, COMBDLY  style-class; low priority, suppressed by default (MLCAD harmful regime)
REG_WIRE, PORT_MISMATCH  Icarus compile-class (kept minimal; harness may already cover)
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Dict, Iterable, List, Optional, Tuple

__all__ = [
    "Diagnostic", "Directive", "InterpretResult",
    "parse_verilator", "parse_yosys", "parse_icarus",
    "interpret_eda_feedback", "interpret_eda_feedback_ex", "interpret_multi",
    "interpret_legacy", "error_signature", "PRIORITY", "INTERPRETER_VERSION",
]

INTERPRETER_VERSION = "parsers-1.0"  # internal to v3; unrelated to production v2

# Lower number = more important. Hard synthesis blockers first, advisory last.
PRIORITY = {
    "ASYNC_RESET": 0, "COMB_LOOP": 1, "MULTIDRIVEN": 2, "MISSING_CLOCK": 3,
    "LATCH": 4, "UNDRIVEN": 5, "PINMISSING": 6, "WIDTHTRUNC": 7, "WIDTHEXPAND": 8,
    "UNUSEDSIGNAL": 9, "REG_WIRE": 1, "PORT_MISMATCH": 1,
    "BLKSEQ": 20, "COMBDLY": 21,
}
STYLE_CODES = {"BLKSEQ", "COMBDLY"}

# Names that behave like gating / control inputs (drives the UNUSEDSIGNAL template choice).
_GATE_RE = re.compile(r"^(en|ena|enable|.*_en|.*_enable|oe|.*_oe|ce|.*_ce|valid|.*_valid|"
                      r"ready|.*_ready|sel|.*_sel|we|.*_we|re|.*_re|wr_en|rd_en|start|load|.*_load|gnt.*|req.*)$", re.I)
_CLK_RE = re.compile(r"^(clk|clock|.*_clk|clk_.*|.*clock)$", re.I)
_RST_RE = re.compile(r"^(rst|reset|.*_rst|rst_.*|.*reset.*|clr|.*_clr|rst_n|resetn|aresetn)$", re.I)


# --------------------------------------------------------------------------- data model
@dataclass
class Diagnostic:
    tool: str
    code: str                      # canonical code (see module docstring)
    signal: Optional[str] = None
    module: Optional[str] = None
    file: Optional[str] = None
    line: Optional[int] = None
    detail: dict = field(default_factory=dict)
    raw: str = ""

    def key(self) -> Tuple[str, str]:
        return (self.code, (self.signal or "").split("[")[0])


@dataclass
class Directive:
    code: str
    priority: int
    text: str
    signals: List[str] = field(default_factory=list)


@dataclass
class InterpretResult:
    fired: bool
    codes: List[str]
    diagnostics: List[Diagnostic]
    directives: List[Directive]
    text: str
    signature: str
    suppressed: List[str] = field(default_factory=list)

    def as_dict(self) -> dict:
        return {"fired": self.fired, "codes": self.codes, "signature": self.signature,
                "n_diagnostics": len(self.diagnostics), "n_directives": len(self.directives),
                "suppressed": self.suppressed, "interpreter_version": INTERPRETER_VERSION}


# --------------------------------------------------------------------------- helpers
def _clean(name: Optional[str]) -> Optional[str]:
    """Strip Yosys escaping and hierarchy: `\\mod.\\sig` -> sig ; keep [idx]."""
    if name is None:
        return None
    name = name.strip().strip("`'\"")
    parts = [p.lstrip("\\") for p in re.split(r"\.(?=\\|[A-Za-z_$])", name)]
    return parts[-1] if parts else name


def _yosys_mod(name: str) -> Optional[str]:
    m = re.match(r"\\?([A-Za-z_$][\w$]*)\.", name.strip("`'"))
    return m.group(1) if m else None


def _loc(s: str) -> Tuple[Optional[str], Optional[int]]:
    m = re.search(r"([\w./\-]+\.s?v):(\d+)(?::\d+)?", s)
    return (m.group(1), int(m.group(2))) if m else (None, None)


def _dedupe(seq: Iterable[str]) -> List[str]:
    out, seen = [], set()
    for x in seq:
        if x and x not in seen:
            seen.add(x); out.append(x)
    return out


# --------------------------------------------------------------------------- parsers
_V_HDR = re.compile(r"^%(Warning|Error)-([A-Z_0-9]+):\s*(.*)$")


def parse_verilator(raw: str) -> List[Diagnostic]:
    """Parse Verilator 4.x/5.x lint output (-Wall). Multi-line records are grouped."""
    diags: List[Diagnostic] = []
    lines = raw.splitlines()
    i = 0
    while i < len(lines):
        m = _V_HDR.match(lines[i].strip())
        if not m:
            i += 1
            continue
        _sev, code, rest = m.groups()
        block = [lines[i]]
        j = i + 1
        while j < len(lines) and not lines[j].lstrip().startswith("%"):
            block.append(lines[j]); j += 1
        text = "\n".join(block)
        f, ln = _loc(rest)
        d = _verilator_record(code, rest, text, f, ln)
        if d is not None:
            diags.append(d)
        i = j
    return diags


def _q(s: str) -> Optional[str]:
    m = re.search(r"'([^']+)'", s)
    return m.group(1) if m else None


def _verilator_record(code, rest, text, f, ln) -> Optional[Diagnostic]:
    mk = lambda c, sig=None, **det: Diagnostic("verilator", c, sig, None, f, ln, det, text)
    if code in ("UNUSEDSIGNAL", "UNUSED"):
        m = re.search(r"Bits of signal are not used:\s*'([^']+)'(\[[^\]]+\])?", rest)
        if m:
            return mk("UNUSEDSIGNAL", m.group(1), bits=m.group(2))
        m = re.search(r"Signal is not used:\s*'?([\w$.]+)'?", rest)   # 5.x quotes; 4.x may not
        return mk("UNUSEDSIGNAL", m.group(1) if m else _q(rest), bits=None)
    if code == "UNDRIVEN":
        m = re.search(r"Bits of signal are not driven:\s*'([^']+)'(\[[^\]]+\])?", rest)
        if m:
            return mk("UNDRIVEN", m.group(1), bits=m.group(2))
        m = re.search(r"Signal is not driven:\s*'?([\w$.]+)'?", rest)
        return mk("UNDRIVEN", m.group(1) if m else _q(rest), bits=None)
    if code == "MULTIDRIVEN":
        # 5.x format A: "Bits [0:0] of signal 'w' have multiple combinational drivers"
        # 5.x format B: "Signal has multiple driving blocks with different clocking: 'q'"
        sig = _q(rest)
        kind = "combinational" if "combinational drivers" in rest else "clocking"
        locs = re.findall(r"([\w./\-]+\.s?v):(\d+):\d+:\s*\.\.\. Location of (first|other) driv", text)
        return mk("MULTIDRIVEN", sig, kind=kind, driver_lines=sorted({int(l) for _, l, _ in locs}))
    if code in ("WIDTHTRUNC", "WIDTHEXPAND", "WIDTH"):
        m = re.search(r"expects (\d+) bits on the (.+?), but (.+?) generates (\d+) bits", rest)
        exp, ctx, src, gen = (int(m.group(1)), m.group(2), m.group(3), int(m.group(4))) if m else (None, None, None, None)
        c = code
        if code == "WIDTH" and exp is not None:
            c = "WIDTHTRUNC" if gen > exp else "WIDTHEXPAND"
        om = re.search(r"\b[A-Z][A-Z_]* '([^']+)' generates", rest)   # e.g. "... VARREF 'a' generates"
        operand = om.group(1) if om else None                            # None => an expression, not a name
        pin = re.search(r"port connection '([^']+)'", rest)
        return mk(c if c != "WIDTH" else "WIDTHTRUNC", operand, expects=exp, generates=gen,
                  context=ctx, pin=pin.group(1) if pin else None)
    if code == "LATCH":
        return mk("LATCH", _q(rest), source="verilator")
    if code == "CASEINCOMPLETE":
        m = re.search(r"example pattern (\S+)\)", rest)
        return mk("CASEINCOMPLETE", None, example=m.group(1) if m else None)
    if code in ("UNOPTFLAT", "ALWCOMBORDER"):
        path = _dedupe(re.findall(r"Example path:\s*([\w$.]+)", text))
        path = [p.split(".")[-1] for p in path if p not in ("ASSIGNW", "ALWAYS", "ASSIGN")]
        return mk("COMB_LOOP", _q(rest).split(".")[-1] if _q(rest) else None, path=_dedupe(path))
    if code in ("PINMISSING", "PINCONNECTEMPTY"):
        return mk("PINMISSING", _q(rest), kind=code)
    if code == "BLKSEQ":
        return mk("BLKSEQ")
    if code == "COMBDLY":
        return mk("COMBDLY")
    return None   # DECLFILENAME, EOFNEWLINE, etc. are intentionally ignored


def parse_yosys(raw: str) -> List[Diagnostic]:
    diags: List[Diagnostic] = []
    lines = raw.splitlines()
    for i, line in enumerate(lines):
        s = line.strip()
        # Latch. NB: case-sensitive -- "No latch inferred for signal" must NOT match.
        if s.lower().startswith("no latch"):
            continue
        # Tolerant across Yosys versions: 0.33 prints "... from process `\\m.$proc$f.v:10$1'"; newer releases may
        # print location ranges ("f.v:10.2-24.6"), split a signal into bit-chunks ("\\dout [31]"), or omit the
        # process clause. Only the backticked signal is required (same as production's _LATCH_POSITIVE_RE).
        m = re.search(r"\bLatch inferred for signal\s+`([^'`]+)'(?:\s+from process\s+`([^'`]+)')?", s)
        if m:
            sig_full, proc = m.group(1), (m.group(2) or "")
            pl = re.search(r"\$proc\$([\w./\-]+\.s?v):(\d+)", proc)
            diags.append(Diagnostic("yosys", "LATCH", _clean(sig_full), _yosys_mod(sig_full),
                                    pl.group(1) if pl else None, int(pl.group(2)) if pl else None,
                                    {"process": proc, "source": "yosys"}, line))
            continue
        m = re.match(r"Warning: found logic loop in module ([\w$\\]+):?", s, re.I)
        if m:
            cells, wires = [], []
            for nxt in lines[i + 1:i + 60]:
                t = nxt.strip()
                cm = re.match(r"cell\s+(\S+)\s*\((\S+)\)", t)
                wm = re.match(r"wire\s+(\S+)", t)
                if cm:
                    cells.append(cm.group(1))
                elif wm:
                    wires.append(_clean(wm.group(1)))
                elif t:
                    break
            lns = sorted({int(x) for c in cells for x in re.findall(r"\.s?v:(\d+)", c)})
            diags.append(Diagnostic("yosys", "COMB_LOOP", wires[0] if wires else None,
                                    m.group(1).lstrip("\\"), None, lns[0] if lns else None,
                                    {"path": _dedupe(wires), "lines": lns}, line))
            continue
        m = re.match(r"Warning: multiple conflicting drivers for ([^:]+):", s)
        if m:
            diags.append(Diagnostic("yosys", "MULTIDRIVEN", _clean(m.group(1)), _yosys_mod(m.group(1)),
                                    None, None, {"kind": "yosys"}, line))
            continue
        m = re.match(r"Warning: [Ww]ire ([^ ]+) is used but has no driver", s)
        if m:
            diags.append(Diagnostic("yosys", "UNDRIVEN", _clean(m.group(1)), _yosys_mod(m.group(1)),
                                    None, None, {"bits": None}, line))
            continue
        if "Multiple edge sensitive events found for this signal" in s:
            # Yosys names no signal here; recover the last process/module seen (best effort).
            ctx = "\n".join(lines[max(0, i - 400):i])
            procs = re.findall(r"\$proc\$([\w./\-]+\.s?v):(\d+)\$", ctx)
            mods = re.findall(r"module `?\\?([\w$]+)'?", ctx)
            f, ln = (procs[-1][0], int(procs[-1][1])) if procs else (None, None)
            diags.append(Diagnostic("yosys", "ASYNC_RESET", None, mods[-1] if mods else None,
                                    f, ln, {}, line))
    return diags


def parse_icarus(raw: str) -> List[Diagnostic]:
    diags: List[Diagnostic] = []
    for line in raw.splitlines():
        f, ln = _loc(line)
        m = re.search(r"(\w+) is not a valid l-value", line)
        if m:
            diags.append(Diagnostic("icarus", "REG_WIRE", m.group(1), None, f, ln, {}, line)); continue
        m = re.search(r"port ``?(\w+)'?'? is not a port of (\w+)", line)
        if m:
            diags.append(Diagnostic("icarus", "PORT_MISMATCH", m.group(1), m.group(2), f, ln, {}, line)); continue
        m = re.search(r"Wrong number of ports\. Expecting (\d+), got (\d+)", line)
        if m:
            diags.append(Diagnostic("icarus", "PORT_MISMATCH", None, None, f, ln,
                                    {"expected": int(m.group(1)), "got": int(m.group(2))}, line))
    return diags


_PARSERS = {"verilator": parse_verilator, "yosys": parse_yosys,
            "icarus": parse_icarus, "iverilog": parse_icarus}


# --------------------------------------------------------------------------- light source model
@dataclass
class _Src:
    text: str
    lines: List[str]
    widths: Dict[str, int]
    inputs: List[str]
    outputs: List[str]


def _src_model(source: Optional[str]) -> Optional[_Src]:
    if not source:
        return None
    nc = re.sub(r"/\*.*?\*/", lambda m: "\n" * m.group(0).count("\n"), source, flags=re.S)
    nc = re.sub(r"//[^\n]*", "", nc)
    widths, ins, outs = {}, [], []
    for m in re.finditer(r"\b(input|output|inout|wire|reg|logic)\b\s*(?:wire|reg|logic|signed|\s)*"
                         r"(\[\s*(\d+)\s*:\s*(\d+)\s*\])?\s*([\w\s,]+?)(?=[;)\n]|\binput\b|\boutput\b)", nc):
        kind, _, hi, lo, names = m.groups()
        w = abs(int(hi) - int(lo)) + 1 if hi is not None else 1
        for n in re.split(r"[\s,]+", names.strip()):
            if re.match(r"^[A-Za-z_]\w*$", n) and n not in ("wire", "reg", "logic", "signed", "input", "output"):
                widths.setdefault(n, w)
                if kind == "input":
                    ins.append(n)
                elif kind == "output":
                    outs.append(n)
    return _Src(source, source.splitlines(), widths, _dedupe(ins), _dedupe(outs))


def _snippet(src: Optional[_Src], line: Optional[int], before=1, after=4) -> str:
    if not src or not line or line < 1 or line > len(src.lines):
        return ""
    lo, hi = max(1, line - before), min(len(src.lines), line + after)
    return "\n".join(f"  {k:>4} | {src.lines[k-1].rstrip()}" for k in range(lo, hi + 1))


def _always_header(src: Optional[_Src], line: Optional[int]) -> Optional[str]:
    """Return the sensitivity list text of the always block starting at/near `line`."""
    if not src or not line:
        return None
    for k in range(line, min(len(src.lines), line + 2) + 1):
        m = re.search(r"always\w*\s*(@\s*(\(.*?\)|\*))?", src.lines[k - 1])
        if m:
            return (m.group(1) or "").replace(" ", "")
    return None


def _async_reset_block(src: Optional[_Src]) -> Optional[Tuple[int, str, str]]:
    """Find `always @(posedge a, posedge b)` whose first if-condition is not a bare edge signal."""
    if not src:
        return None
    for i, l in enumerate(src.lines):
        m = re.search(r"always\s*@\s*\(([^)]*)\)", l)
        if not m or m.group(1).count("edge") < 2:
            continue
        edges = re.findall(r"(?:pos|neg)edge\s+(\w+)", m.group(1))
        window = " ".join(src.lines[i:i + 6])
        c = re.search(r"\bif\s*\((.*?)\)\s*(?:begin|\w)", window)
        if c:
            cond = c.group(1).strip()
            bare = {e for e in edges} | {"!" + e for e in edges} | {"~" + e for e in edges}
            if cond.replace(" ", "") not in bare and not re.fullmatch(r"!?\s*\w+\s*==\s*1'b[01]", cond):
                return (i + 1, cond, ", ".join(edges))
    return None


def _multi_assigned(src: _Src) -> Dict[str, Tuple[int, List[int]]]:
    """Source scan: names that are the LHS of more than one continuous assign / always block."""
    hits: Dict[str, List[int]] = {}
    for i, l in enumerate(src.lines, 1):
        for m in re.finditer(r"\bassign\s+([A-Za-z_]\w*)", l):
            hits.setdefault(m.group(1), []).append(i)
    return {k: (v[0], sorted(set(v))) for k, v in hits.items() if len(v) > 1}


def _dedupe_diags(ds: List[Diagnostic]) -> List[Diagnostic]:
    out, seen = [], set()
    for d in ds:
        k = (d.tool, d.code, d.signal, d.line)
        if k not in seen:
            seen.add(k); out.append(d)
    return out


# --------------------------------------------------------------------------- directive builders
def _zero(sig: str) -> str:
    return f"{sig} = 0;"


def _d_latch(ds: List[Diagnostic], src, style) -> Directive:
    sigs = _dedupe(d.signal for d in ds if d.signal)
    line = next((d.line for d in ds if d.line), None)
    mod = next((d.module for d in ds if d.module), None)
    where = f" in the always block at line {line}" if line else ""
    names = ", ".join(f"'{s}'" for s in sigs) or "one or more outputs"
    defaults = "\n".join(f"      {_zero(s.split('[')[0])}" for s in _dedupe(s.split('[')[0] for s in sigs)[:8])
    txt = (f"CRITICAL [LATCH]: Synthesis inferred a LATCH for {names}{where}"
           f"{' (module ' + mod + ')' if mod else ''}. A combinational always block must assign "
           f"every one of these signals on EVERY path; some case/if path leaves them unassigned.\n"
           f"FIX (do exactly this):\n"
           f"  1. Make these the FIRST statements inside that always @(*) block:\n{defaults}\n"
           f"  2. If the block uses `case`, add a `default:` item. If it uses if/else-if, end it with a final `else`.\n"
           f"  3. Keep every existing branch unchanged. Do NOT add a clock. Do NOT change the port list.")
    snip = _snippet(src, line) if style == "full" else ""
    if snip:
        txt += f"\n  Offending block:\n{snip}"
    return Directive("LATCH", PRIORITY["LATCH"], txt, sigs)


def _d_missing_clock(ds: List[Diagnostic], clk: str, src, style) -> Directive:
    sigs = _dedupe(d.signal for d in ds if d.signal)
    line = next((d.line for d in ds if d.line), None)
    names = ", ".join(f"'{s}'" for s in sigs)
    txt = (f"CRITICAL [MISSING CLOCK]: {names} is written in a level-sensitive always block"
           f"{' at line ' + str(line) if line else ''} and synthesis turned it into a LATCH, while the clock "
           f"input '{clk}' is never used. This is a register: it must be edge-triggered.\n"
           f"FIX: change that block's sensitivity list to  always @(posedge {clk})  "
           f"(or  always @(posedge {clk} or posedge <reset>)  for an asynchronous reset) and use '<=' for "
           f"every assignment inside it. Keep the existing if/else priority (clear before enable).")
    snip = _snippet(src, line) if style == "full" else ""
    if snip:
        txt += f"\n  Offending block:\n{snip}"
    return Directive("MISSING_CLOCK", PRIORITY["MISSING_CLOCK"], txt, sigs + [clk])


def _d_loop(ds: List[Diagnostic], src, style, hdl) -> Directive:
    path = _dedupe(p for d in ds for p in (d.detail.get("path") or [d.signal]) if p)
    line = next((d.line for d in ds if d.line), None)
    cyc = " -> ".join(path + path[:1]) if path else "(see lines reported)"
    ff = "always_ff @(posedge clk)" if hdl == "sv" else "always @(posedge clk)"
    selfref = [p for p in path if src and re.search(rf"\b{re.escape(p)}\s*=\s*[^;]*\b{re.escape(p)}\b", src.text)]
    hint = (f"  Note: '{selfref[0]}' is assigned from itself ('{selfref[0]} = ...{selfref[0]}...'); "
            f"a signal that must HOLD its value is state and belongs in a clocked block.\n") if selfref else ""
    clk = next((i for i in (src.inputs if src else []) if _CLK_RE.match(i)), None)
    head = (f"CRITICAL [COMBINATIONAL LOOP]: signals form a zero-delay cycle: {cyc}. "
            f"A combinational signal may not depend on itself.\n{hint}")
    p0 = path[0] if path else "x"
    if clk or src is None:
        ck = clk or "clk"
        ff = ff.replace("clk", ck)
        txt = head + (f"FIX: break the cycle with a register. Compute the next value combinationally from inputs "
                      f"and the REGISTERED copy, then update the register in a clocked block:\n"
                      f"      {ff} {p0}_q <= {p0}_next;\n"
                      f"  Every signal in the cycle must read the registered copy, never the combinational one. "
                      f"If no state is intended, rewrite each signal directly from module inputs only.")
    else:
        txt = head + (f"FIX: this module has no clock, so no state is allowed. Rewrite every signal in the cycle "
                      f"directly from module INPUTS only, so that none of them reads another signal of the cycle.")
    snip = _snippet(src, line) if style == "full" else ""
    if snip:
        txt += f"\n  Near:\n{snip}"
    return Directive("COMB_LOOP", PRIORITY["COMB_LOOP"], txt, path)


def _d_multidriven(ds: List[Diagnostic], src, style) -> Directive:
    # Prefer Verilator's names (Yosys reports the post-opt alias net, e.g. an input).
    vds = [d for d in ds if d.tool == "verilator"]
    if not vds:
        vds = _dedupe_diags(ds)
        if src:
            cand = _multi_assigned(src)
            if cand:
                vds = [Diagnostic("yosys", "MULTIDRIVEN", c, None, None, ln, {"kind": "yosys", "driver_lines": ln_list})
                       for c, (ln, ln_list) in cand.items()]
    sigs = _dedupe(d.signal for d in vds if d.signal)
    parts = []
    for d in vds:
        s0 = d.signal or "<sig>"
        dl = d.detail.get("driver_lines") or []
        where = f" (drivers at lines {', '.join(map(str, dl))})" if dl else ""
        if d.detail.get("kind") == "clocking":
            tmpl = (f"      always @(posedge clk or posedge rst)   // the ONLY block that writes {s0}\n"
                    f"        if (rst) {s0} <= 0;\n        else     {s0} <= <next value>;")
            why = "is written by two always blocks with different clocking/reset"
        else:
            tmpl = (f"      always @(*) begin                      // the ONLY place that writes {s0}\n"
                    f"        {s0} = <default>;\n        if (<cond>) {s0} = <value A>;\n"
                    f"        else        {s0} = <value B>;\n      end")
            why = "has more than one driver (two assigns, or assign + always)"
        parts.append(f"  - '{s0}' {why}{where}. Merge into:\n{tmpl}")
        if len(parts) >= 2:
            break
    txt = ("CRITICAL [MULTIDRIVEN]: real hardware cannot have two drivers on one net.\n" + "\n".join(parts) +
           "\n  Delete every other driver. Each signal is assigned in exactly one always block or one assign.")
    return Directive("MULTIDRIVEN", PRIORITY["MULTIDRIVEN"], txt, sigs)


def _d_unused(d: Diagnostic, src, style) -> Directive:
    s = d.signal or "<signal>"
    bits = d.detail.get("bits")
    if bits:
        txt = (f"[UNUSED BITS]: bits {bits} of '{s}' never affect any output. If the spec needs them, "
               f"use the full width of '{s}'. If they are genuinely unused, the declared width is wrong "
               f"or a width mismatch is truncating them -- check every place '{s}' is used.")
        return Directive("UNUSEDSIGNAL", PRIORITY["UNUSEDSIGNAL"] + 1, txt, [s])
    outs = (src.outputs if src else []) or ["out"]
    o = outs[0]
    if _CLK_RE.match(s):
        txt = (f"CRITICAL [UNUSED CLOCK]: input '{s}' is declared but NEVER USED, so nothing is clocked. "
               f"Registers must update in  always @(posedge {s})  using '<='.")
    elif _RST_RE.match(s):
        txt = (f"CRITICAL [UNUSED RESET]: input '{s}' is declared but NEVER USED. Every register must "
               f"respond to it:\n      always @(posedge clk) if ({s}) <reg> <= 0; else <reg> <= <next>;")
    elif _GATE_RE.match(s):
        txt = (f"CRITICAL: Port '{s}' is declared but NEVER USED. It gates the outputs. You MUST condition on it:\n"
               f"      if ({s}) begin <existing logic> end\n      else begin {o} = 0; end")
    else:
        txt = (f"CRITICAL: Input '{s}' is declared but NEVER USED. The specification requires '{s}' to "
               f"influence the outputs -- re-read the spec and use '{s}' where it describes; do not delete the port.")
    return Directive("UNUSEDSIGNAL", PRIORITY["UNUSEDSIGNAL"], txt, [s])


def _d_undriven(d: Diagnostic, src, style) -> Directive:
    s = d.signal or "<signal>"
    bits = d.detail.get("bits")
    if bits:
        txt = (f"CRITICAL [UNDRIVEN BITS]: bits {bits} of '{s}' are never assigned (they float). "
               f"Assign the FULL width, e.g. pad explicitly: {s} = {{<zeros for {bits}>, <value>}};")
    else:
        txt = (f"CRITICAL [UNDRIVEN]: '{s}' is declared but NEVER ASSIGNED. Drive it on every path, e.g.\n"
               f"      assign {s} = <expression from the spec>;\n  (or assign it in the combinational "
               f"always block, including a default at the top of that block).")
    return Directive("UNDRIVEN", PRIORITY["UNDRIVEN"], txt, [s])


def _lhs_at(src: Optional[_Src], line: Optional[int]) -> Optional[str]:
    if not src or not line or line > len(src.lines):
        return None
    m = re.search(r"(?:assign\s+)?([A-Za-z_]\w*(?:\[[^\]]+\])?)\s*<?=(?!=)", src.lines[line - 1])
    return m.group(1) if m else None


def _d_width(d: Diagnostic, src, style) -> Directive:
    s = d.signal or "the right-hand-side expression"
    e, g = d.detail.get("expects"), d.detail.get("generates")
    ctx = d.detail.get("context") or "assignment"
    pin = d.detail.get("pin")
    loc = f" at line {d.line}" if d.line else ""
    lhs = None if pin else _lhs_at(src, d.line)
    what = f"port '{pin}'" if pin else (f"destination '{lhs}'" if lhs else ctx)
    if d.code == "WIDTHTRUNC":
        sl = f"{s}[{e-1}:0]" if d.signal else f"a {e}-bit slice of it"
        fix = (f"slice explicitly to the bits you mean, e.g.  {sl}  , or widen the destination "
               f"to [{g-1}:0] if the upper {g-e} bits are needed" if e and g else "slice or widen explicitly")
        txt = (f"[WIDTH TRUNCATION]{loc}: {what} is {e} bits but '{s}' is {g} bits; the upper bits are "
               f"silently DROPPED. FIX: {fix}. Decide which from the spec; never leave it implicit.")
    else:
        pad = f"{{{e-g}'b0, {s}}}" if e and g else f"{{zeros, {s}}}"
        sx = f"{{{{{e-g}{{{s}[{g-1}]}}}}, {s}}}" if e and g else "sign-extend"
        txt = (f"[WIDTH EXTENSION]{loc}: {what} is {e} bits but '{s}' is only {g} bits. FIX: pad "
               f"explicitly -- zero-extend  {pad}  for unsigned values, or sign-extend  {sx}  for signed "
               f"values. If '{s}' was meant to be {e} bits, fix its declaration instead.")
    return Directive(d.code, PRIORITY[d.code], txt, [s])


def _d_pin(d: Diagnostic, src, style) -> Directive:
    txt = (f"[PORT NOT CONNECTED]: an instance leaves port '{d.signal}' unconnected{' at line ' + str(d.line) if d.line else ''}. "
           f"Connect every port BY NAME: .{d.signal}(<net>). Positional connections silently shift when a port is missing.")
    return Directive("PINMISSING", PRIORITY["PINMISSING"], txt, [d.signal or ""])


def _d_async(ds: List[Diagnostic], src, style) -> Directive:
    blk = _async_reset_block(src)
    if blk:
        ln, cond, edges = blk
        rst = next((e for e in edges.split(", ") if _RST_RE.match(e)), edges.split(", ")[-1])
        rest = re.sub(rf"\s*\|\|?\s*\b{rst}\b|\b{rst}\b\s*\|\|?\s*", "", cond).strip() or "<sync clear>"
        txt = (f"CRITICAL [ASYNC RESET]: synthesis FAILED. The block at line {ln} is sensitive to "
               f"({edges}) but its first test is  if ({cond})  . In an edge-triggered block with an "
               f"asynchronous reset, the first if must test ONLY the reset edge signal.\nFIX:\n"
               f"      always @(posedge clk or posedge {rst})\n        if ({rst})          q <= 0;\n"
               f"        else if ({rest}) q <= 0;   // synchronous part\n        else if (<enable>) q <= <d>;")
    else:
        txt = ("CRITICAL [ASYNC RESET]: synthesis FAILED ('Multiple edge sensitive events'). In "
               "always @(posedge clk or posedge rst), the first statement must be  if (rst)  testing ONLY "
               "the reset signal; move any other condition (e.g. a synchronous clear) into the else branch.")
    return Directive("ASYNC_RESET", PRIORITY["ASYNC_RESET"], txt, [])


def _d_style(d: Diagnostic) -> Directive:
    if d.code == "BLKSEQ":
        txt = "[STYLE]: inside always @(posedge ...) use '<=' (non-blocking), not '='."
    else:
        txt = "[STYLE]: inside always @(*) use '=' (blocking), not '<='."
    return Directive(d.code, PRIORITY[d.code], txt, [])


def _d_icarus(d: Diagnostic) -> Directive:
    if d.code == "REG_WIRE":
        txt = (f"CRITICAL [REG/WIRE]: '{d.signal}' is assigned inside an always block, so it must be "
               f"declared 'reg' (or 'output reg'); a signal driven by 'assign' must be a 'wire'.")
    else:
        det = d.detail
        txt = ("CRITICAL [PORT MISMATCH]: an instance's ports do not match the module definition"
               + (f" (expected {det['expected']}, got {det['got']})" if "expected" in det else
                  f" ('{d.signal}' is not a port of {d.module})")
               + ". Use the exact port names of the definition and connect by name.")
    return Directive(d.code, PRIORITY[d.code], txt, [d.signal or ""])


# --------------------------------------------------------------------------- fusion + prioritise
def _fuse(diags: List[Diagnostic], src: Optional[_Src], style: str, hdl: str) -> Tuple[List[Directive], List[str]]:
    by: Dict[str, List[Diagnostic]] = {}
    for d in diags:
        by.setdefault(d.code, []).append(d)
    out: List[Directive] = []
    notes: List[str] = []

    # Cross-tool rule 1: LATCH in a level-sensitive (non-*) block + an unused clock input => MISSING_CLOCK
    latches = by.get("LATCH", [])
    unused_clk = [d.signal for d in by.get("UNUSEDSIGNAL", []) if d.signal and _CLK_RE.match(d.signal)]
    if latches and unused_clk:
        seq = []
        for d in latches:
            hdr = _always_header(src, d.line)
            if hdr is None or (hdr not in ("@*", "@(*)") and "edge" not in hdr):
                seq.append(d)
        if seq:
            out.append(_d_missing_clock(seq, unused_clk[0], src, style))
            latches = [d for d in latches if d not in seq]
            by["UNUSEDSIGNAL"] = [d for d in by["UNUSEDSIGNAL"] if d.signal != unused_clk[0]]
            notes.append("MISSING_CLOCK<-LATCH+UNUSED(clk)")

    # LATCH: merge Yosys + Verilator LATCH + CASEINCOMPLETE; group by always block
    if latches:
        groups: Dict[Optional[int], List[Diagnostic]] = {}
        for d in latches:
            groups.setdefault(d.line, []).append(d)
        for _, g in sorted(groups.items(), key=lambda kv: (kv[0] is None, kv[0] or 0)):
            out.append(_d_latch(g, src, style))
    elif by.get("CASEINCOMPLETE"):
        # Verilator alone (no Yosys latch): advisory -- in a clocked block this is not a latch.
        d = by["CASEINCOMPLETE"][0]
        out.append(Directive("LATCH", PRIORITY["LATCH"] + 2,
                             f"[INCOMPLETE CASE]{' at line ' + str(d.line) if d.line else ''}: the case statement "
                             f"does not cover all values (e.g. {d.detail.get('example')}). Add a  default:  item that "
                             f"assigns every output of the block.", []))

    if by.get("COMB_LOOP"):
        out.append(_d_loop(by["COMB_LOOP"], src, style, hdl))
    if by.get("MULTIDRIVEN"):
        out.append(_d_multidriven(by["MULTIDRIVEN"], src, style))
    if by.get("ASYNC_RESET"):
        out.append(_d_async(by["ASYNC_RESET"], src, style))

    # Cross-tool rule 2: an output reported UNDRIVEN *and* LATCH is a latch problem, not undriven.
    latch_sigs = {s for dr in out for s in dr.signals}
    trunc_sigs = {d.signal for d in by.get("WIDTHTRUNC", [])}
    seen = set()
    for code, fn in (("UNDRIVEN", _d_undriven), ("WIDTHTRUNC", _d_width), ("WIDTHEXPAND", _d_width),
                     ("PINMISSING", _d_pin), ("UNUSEDSIGNAL", _d_unused)):
        for d in by.get(code, []):
            k = d.key()
            if k in seen or (code == "UNDRIVEN" and d.signal in latch_sigs):
                continue
            if code == "UNUSEDSIGNAL" and d.detail.get("bits") and d.signal in trunc_sigs:
                continue   # the truncation directive already explains the unused upper bits
            seen.add(k)
            out.append(fn(d, src, style))
    for code in ("REG_WIRE", "PORT_MISMATCH"):
        for d in by.get(code, []):
            out.append(_d_icarus(d))
    for code in ("BLKSEQ", "COMBDLY"):
        if by.get(code):
            out.append(_d_style(by[code][0]))
    out.sort(key=lambda d: d.priority)
    return out, notes


def error_signature(diags: List[Diagnostic]) -> str:
    """Normalised signature for escalation's two-strike gate: stable across line-number churn."""
    keys = sorted({f"{d.code}:{(d.signal or '').split('[')[0]}" for d in diags if d.code not in STYLE_CODES})
    return "|".join(keys) if keys else ""


def _render(directives: List[Directive], max_directives: int, include_style: bool) -> Tuple[str, List[Directive], List[str]]:
    keep = [d for d in directives if include_style or d.code not in STYLE_CODES]
    # style directives only if nothing more important is present
    if any(d.code not in STYLE_CODES for d in keep):
        keep = [d for d in keep if d.code not in STYLE_CODES] + [d for d in keep if d.code in STYLE_CODES]
    shown, dropped = keep[:max_directives], keep[max_directives:]
    txt = "\n\n".join(d.text for d in shown)
    if dropped:
        txt += (f"\n\n(After fixing the above, {len(dropped)} lower-priority issue(s) remain; "
                f"they will be reported next iteration.)")
    return txt, shown, [d.code for d in dropped] + [d.code for d in directives if d not in keep]


def interpret_multi(logs: Dict[str, str], source: Optional[str] = None, *, style: str = "full",
                    max_directives: int = 2, include_style: bool = False, hdl: str = "v2001",
                    passthrough_unmatched: bool = True) -> InterpretResult:
    diags: List[Diagnostic] = []
    for tool, raw in logs.items():
        p = _PARSERS.get(tool.lower())
        if p and raw:
            diags.extend(p(raw))
    src = _src_model(source)
    diags = _dedupe_diags(diags)
    directives, _notes = _fuse(diags, src, style, hdl)
    text, shown, suppressed = _render(directives, max_directives, include_style)
    fired = bool(shown)
    if not fired and passthrough_unmatched:
        text = "\n".join(v for v in logs.values() if v)
    return InterpretResult(fired, _dedupe(d.code for d in shown), diags, shown, text,
                           error_signature(diags), suppressed)


def interpret_eda_feedback_ex(tool_name: str, raw_log: str, source: Optional[str] = None, **opts) -> InterpretResult:
    return interpret_multi({tool_name: raw_log}, source, **opts)


def interpret_eda_feedback(tool_name: str, raw_log: str, source: Optional[str] = None, **opts) -> str:
    """Backward-compatible entry point. Returns directive text, or the raw log if nothing matched."""
    return interpret_eda_feedback_ex(tool_name, raw_log, source, **opts).text


# --------------------------------------------------------------------------- legacy (MLCAD'26 Listing 1)
def interpret_legacy(raw: str) -> str:
    """Conference vocabulary only: UNUSEDSIGNAL + generic Yosys latch. Quote bug fixed so the
    `sem_legacy` ablation isolates VOCABULARY, not the regex defect."""
    if "UNUSEDSIGNAL" in raw:
        m = re.search(r"Signal is not used: '?(\w+)'?", raw)
        if m:
            name = m.group(1)
            return (f"CRITICAL: Port '{name}' declared but NEVER USED. Condition on it:\n"
                    f"  if ({name}) begin ... end\n  else begin out = 0; end")
    if "Latch inferred" in raw:
        sigs = _dedupe(_clean(s) for s in re.findall(r"Latch inferred for signal `([^']+)'", raw))
        return (f"CRITICAL: Latch inferred for {', '.join(sigs)}. Add a default branch so every "
                f"signal is assigned on every path.")
    return raw


def legacy_fired(raw: str) -> bool:
    return interpret_legacy(raw) != raw
