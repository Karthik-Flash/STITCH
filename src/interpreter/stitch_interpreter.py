"""
stitch_interpreter.py — the semantic interpreter itself (STITCH's core
contribution), shared verbatim between the local Windows/WSL runner
(autochip_stitch_runner.py) and the HPC port (HPC/stitch_runner_hpc.py).

Deliberately pure text-processing: no subprocess calls, no WSL/native-path
handling, nothing that differs between the two deployment environments.
Everything here operates on strings already produced by Verilator/Yosys and
on a .v file's text — this is exactly the code path both runners need to
behave IDENTICALLY on, since divergence here would silently invalidate any
cross-hardware or local-vs-HPC comparison.

Deployment note: on HPC, this file must sit in the SAME directory as
stitch_runner_hpc.py (scp it up alongside — see that file's header). Locally,
autochip_stitch_runner.py imports it as a plain sibling module.
"""

import logging
import re

_LOG = logging.getLogger(__name__)

# ── SEMANTIC INTERPRETER (STITCH core contribution) ───────────────────────────
# Maps Verilator warning codes to plain-English fix directives.
# This is a deterministic regex script — zero additional inference cost.
# The interpreter is what separates raw_adv (FAIL) from sem_adv (PASS)
# for weaker models in the 4B-14B capability range.

_VERILATOR_INTERP = {
    "UNUSEDSIGNAL": lambda sig: (
        f"*** CRITICAL: Port '{sig}' is declared but NEVER USED in your always block. ***\n"
        f"You wrote '{sig}' in the module port list but forgot to wire it into your logic.\n"
        f"You MUST condition on '{sig}':\n"
        f"  always @(*) begin\n"
        f"    if ({sig}) begin\n"
        f"      <your existing case or logic here>\n"
        f"    end else begin\n"
        f"      out = 8'b0;  // or whatever your output signal is named\n"
        f"    end\n"
        f"  end\n"
        f"The FAIL lines (with '{sig}' deasserted, the output is still non-zero)\n"
        f"are caused by '{sig}' being ignored."
    ),
    "MULTIDRIVEN": lambda sig: (
        f"*** CRITICAL: Signal '{sig}' is driven from multiple always blocks. ***\n"
        f"Only ONE always block may drive a given signal.\n"
        f"Merge all assignments to '{sig}' into a single always block."
    ),
    "UNDRIVEN": lambda sig: (
        f"*** CRITICAL: Output '{sig}' is never assigned. ***\n"
        f"Add an assignment: '{sig} = <value>;' in your always block or use assign."
    ),
    "WIDTHTRUNC": lambda sig: (
        f"*** WARNING: Bit-width truncation on '{sig}'. ***\n"
        f"You are assigning a wider value into a narrower signal.\n"
        f"Use explicit bit-select to avoid silent truncation: signal[N-1:0] = value[N-1:0];"
    ),
    "WIDTHEXPAND": lambda sig: (
        f"*** WARNING: Width expansion on '{sig}' — value is zero-extended. ***\n"
        f"Check that signal widths match your port declarations."
    ),
    "BLKSEQ": lambda sig: (
        f"*** CRITICAL: Blocking assignment (=) in clocked always block for '{sig}'. ***\n"
        f"In clocked always @(posedge clk) blocks, ALWAYS use non-blocking: '{sig} <= value;'"
    ),
    "COMBDLY": lambda sig: (
        f"*** WARNING: Delay (#) in combinational block near '{sig}'. ***\n"
        f"Remove all # delays from always @(*) blocks."
    ),
}


# ── SIGNAL-NAME EXTRACTION (fix: don't fabricate names from numeric literals) ──
# A Verilog identifier can never immediately follow the ' that introduces a
# base specifier (8'h00, 4'b1010, 16'hDEAD, ...) — that ' always marks a
# literal, not a signal reference. Two independent layers of defense:
#   1. A negative lookbehind on the fallback (unquoted) extraction regex, so
#      it never starts a match right after a bare '.
#   2. A validation gate applied to whatever comes out of EITHER regex: if the
#      "signal name" is exactly a base letter (h/d/b/o, any case) followed by
#      nothing but hex-digit-shaped characters, it's a literal fragment
#      (h0, b1010, hDEAD, ...), not a real identifier — reject it.
# Real signals that happen to start with one of those letters (data_bus,
# d_valid, ...) survive layer 2 because the rest of the name isn't hex-shaped.
_LITERAL_FRAGMENT_RE = re.compile(r"^[hHdDbBoO][0-9a-fA-F_xzXZ]+$")

# FIX 2026-08-18 (found in production): _LITERAL_FRAGMENT_RE alone is far too
# blunt. Its character class is "base specifier letter followed by only
# hex-digit-ish characters" — which matches plenty of ordinary Verilog
# identifiers, because 'o' is an octal specifier and 'e'/'a'-'f' are hex
# digits. Real signal names it silently swallowed:
#     oe   (output enable)   o + e
#     bcd  (binary-coded dec) b + c,d
#     be   (byte enable)     b + e
#     de, da, dead, ...
# Caught when a real gemma3:4b run on mux4_oe produced a genuine
# "%Warning-UNUSEDSIGNAL: Signal is not used: 'oe'" that interpret_verilator
# then dropped on the floor, reporting zero codes fired — the directive
# never reached the model even though the mechanism worked perfectly.
#
# The precise discriminator is CONTEXT, not shape: a real literal fragment is
# whatever follows the apostrophe of a Verilog sized literal (8'h00 -> "h00",
# 16'hDEAD -> "hDEAD"), i.e. it sits directly after <digits>'. An identifier
# Verilator itself quoted ('oe') never does. The shape test is kept only as a
# secondary guard, and only for candidates that actually contain a digit —
# so h00/b1010 stay rejected while oe/bcd/be are correctly accepted.
def _looks_like_literal_fragment(sig, line):
    """True if `sig` is a fragment of a Verilog sized literal rather than a
    real identifier. Context-first (directly after <digits>'), shape second."""
    if re.search(r"\d\s*'\s*" + re.escape(sig) + r"\b", line):
        return True
    if any(ch.isdigit() for ch in sig) and _LITERAL_FRAGMENT_RE.match(sig):
        return True
    return False

def _extract_signal_name(line):
    """Return a trustworthy signal identifier from one Verilator warning
    line, or None if nothing trustworthy is there. None is a real outcome —
    callers must handle it, not paper over it with a placeholder."""
    m = re.search(r"['\"]([A-Za-z_]\w*)['\"]", line)
    if not m:
        m = re.search(r"(?<!')\b([A-Za-z_]\w*)\s*$", line)
    if not m:
        return None
    sig = m.group(1)
    if _looks_like_literal_fragment(sig, line):
        return None
    return sig


# ── UNDRIVEN disambiguation (fix: two categorically different bugs, one code) ──
# Verilator's UNDRIVEN fires both when (a) a declared OUTPUT is never assigned
# — the directive "add an assignment" is correct — and (b) an identifier is
# read in the body but was never declared as a port or internal signal at all
# — where "add an assignment" is actively wrong; the real fix is adding it to
# the port list or declaring it. One canned template covering both steers the
# model at the wrong fix half the time. Disambiguate with a second, simple
# regex pass over the source file (no real Verilog parser, just enough
# structure to tell the two cases apart — matches the rest of this codebase's
# style of approximate regex parsing over exact tools elsewhere).
# Verilog-2001 ANSI-style port lists put the WHOLE list inside the parens
# with only ONE trailing semicolon (module foo (\n input a,\n output b\n);),
# not one semicolon per declaration. A naive "up to the next ;" match
# greedily swallows every later input/output keyword into the FIRST match's
# body, making every port after the first invisible to the classifier. Stop
# each capture at whichever comes first: the next direction keyword, or a
# real semicolon — correctly handles both ANSI-style (comma-separated, one
# trailing ;) and legacy style (one ; per declaration).
_PORT_DECL_RE = re.compile(
    r"\b(input|output|inout)\b((?:(?!\b(?:input|output|inout)\b)[^;])*)"
)
_INTERNAL_DECL_RE = re.compile(r"\b(wire|reg|integer|genvar|parameter|localparam)\b([^;]*);")

def _decl_names(decl_body):
    """Given the text after a direction/type keyword up to the semicolon,
    strip width specifiers and type qualifiers, return the identifiers."""
    body = re.sub(r"\[[^\]]*\]", " ", decl_body)
    body = re.sub(r"\b(reg|wire|signed|unsigned)\b", " ", body)
    return re.findall(r"[A-Za-z_]\w*", body)

def _classify_undriven_signal(sig, source_text):
    """Returns 'output_port', 'undeclared', or 'ambiguous'."""
    if not source_text:
        return "ambiguous"
    output_names, any_port_names, internal_names = set(), set(), set()
    for direction, body in _PORT_DECL_RE.findall(source_text):
        names = _decl_names(body)
        any_port_names.update(names)
        if direction == "output":
            output_names.update(names)
    for _, body in _INTERNAL_DECL_RE.findall(source_text):
        internal_names.update(_decl_names(body))

    if sig in output_names:
        return "output_port"
    if sig not in any_port_names and sig not in internal_names:
        return "undeclared"
    return "ambiguous"

def _undriven_message(sig, source_text):
    classification = _classify_undriven_signal(sig, source_text)
    if classification == "output_port":
        return (
            f"*** CRITICAL: Output '{sig}' is declared but never assigned. ***\n"
            f"Add an assignment: '{sig} = <value>;' in your always block or use assign."
        )
    if classification == "undeclared":
        return (
            f"*** CRITICAL: Identifier '{sig}' is used in the module body but NEVER DECLARED. ***\n"
            f"It is NOT in the port list and NOT declared as a wire/reg — this is a\n"
            f"missing declaration, not a missing assignment.\n"
            f"If '{sig}' should be an input, add it to the port list: input <width> {sig}\n"
            f"If '{sig}' is meant to be an internal signal, declare it: wire {sig}; or reg {sig};"
        )
    # Can't tell which case this is from the source alone — present both
    # rather than guessing and possibly steering toward the wrong fix.
    return (
        f"*** CRITICAL: '{sig}' is flagged as undriven; its declaration is ambiguous from source. ***\n"
        f"Check BOTH possibilities:\n"
        f"  A) If '{sig}' is a declared output that's never assigned: add '{sig} = <value>;'\n"
        f"     in your always block or use assign.\n"
        f"  B) If '{sig}' is used but never declared at all: add it to the port list\n"
        f"     (input <width> {sig}) or declare it internally (wire {sig}; / reg {sig};)."
    )


# -- UNUSEDSIGNAL: source-aware repair template (2026-08-18) ------------------
# The canned template used to hard-code `out = 8'b0;` as its else-branch
# example. That is exactly right for decoder_3to8 and mux4_oe -- both have a
# single 8-bit output literally named `out` -- and wrong for anything else,
# which becomes a real precision problem the moment the illustration set
# widens. Extract the module's actual output port name(s) and width(s) and
# substitute them instead.
#
# Verilator's lint output does NOT carry port widths (it reports
# file:line:col plus the signal name only), so the module source is the
# authoritative place to get them. When source is unavailable, or any output's
# width is not a literal integer range (parameterised or macro-defined), fall
# back to the original hard-coded template rather than emit a half-correct
# assignment -- and log that the fallback was taken, so it is visible instead
# of silent.
_WIDTH_RANGE_RE = re.compile(r"\[\s*([^\]:]+?)\s*:\s*([^\]]+?)\s*\]")

def _parse_width(decl_body):
    """Bit width from a declaration body: 1 when no range is present, None
    when a range exists but is not a literal integer pair (e.g. [WIDTH-1:0])."""
    m = _WIDTH_RANGE_RE.search(decl_body)
    if not m:
        return 1
    try:
        return int(m.group(1).strip()) - int(m.group(2).strip()) + 1
    except ValueError:
        return None

def _output_ports(source_text):
    """[(name, width_or_None)] for every declared output port, in source order."""
    ports = []
    if not source_text:
        return ports
    for direction, body in _PORT_DECL_RE.findall(source_text):
        if direction != "output":
            continue
        width = _parse_width(body)
        for name in _decl_names(body):
            ports.append((name, width))
    return ports

def _unusedsignal_message(sig, source_text):
    """UNUSEDSIGNAL directive whose else-branch assignment is written against
    this module's real output ports. Falls back to the generic template (and
    logs) when the ports cannot be resolved with confidence."""
    outs = [(n, w) for n, w in _output_ports(source_text) if n != sig]

    if not outs or any(w is None for _, w in outs):
        if not outs:
            why = "no output port could be extracted from the source"
        else:
            unresolved = [n for n, w in outs if w is None]
            why = "non-literal (parameterised) width on output(s): %s" % unresolved
        _LOG.info(
            "UNUSEDSIGNAL directive for %r fell back to the generic "
            "hard-coded template - %s.", sig, why,
        )
        return _VERILATOR_INTERP["UNUSEDSIGNAL"](sig)

    else_body = "\n".join("      %s = %d'b0;" % (n, w) for n, w in outs)
    return (
        f"*** CRITICAL: Port '{sig}' is declared but NEVER USED in your always block. ***\n"
        f"You wrote '{sig}' in the module port list but forgot to wire it into your logic.\n"
        f"You MUST condition on '{sig}':\n"
        f"  always @(*) begin\n"
        f"    if ({sig}) begin\n"
        f"      <your existing case or logic here>\n"
        f"    end else begin\n"
        f"{else_body}\n"
        f"    end\n"
        f"  end\n"
        f"The FAIL lines (with '{sig}' deasserted, the output is still non-zero)\n"
        f"are caused by '{sig}' being ignored."
    )


def interpret_verilator(raw_out, v_path=None):
    """
    Parse raw Verilator output and return (interpreted_text, codes_fired).
    interpreted_text is empty string if no known codes matched.

    v_path: path to the .v file being checked, used only to disambiguate
    UNDRIVEN (see _classify_undriven_signal). Optional — omitting it just
    means UNDRIVEN falls back to the combined "check both" directive.
    """
    if not raw_out or raw_out.startswith("("):
        return "", []

    source_text = None
    if v_path:
        try:
            with open(v_path, "r", encoding="utf-8", errors="ignore") as f:
                source_text = f.read()
        except OSError:
            source_text = None

    blocks = []
    codes  = []

    for code, make_msg in _VERILATOR_INTERP.items():
        if code not in raw_out:
            continue

        sig = None
        for line in raw_out.splitlines():
            if code in line:
                sig = _extract_signal_name(line)
                if sig:
                    break

        # Cross-check against the actual source when we have it: the
        # fallback (unquoted, end-of-line) regex doesn't just grab numeric-
        # literal fragments — it will just as happily grab a generic word
        # from Verilator's OWN message prose ("...combinational logic
        # process" -> extracts "process"), which isn't hex-shaped so the
        # literal-fragment gate doesn't catch it. A real signal name has to
        # actually appear in the file being checked; a word Verilator used
        # to describe the problem doesn't.
        if sig is not None and source_text is not None:
            if not re.search(r"\b" + re.escape(sig) + r"\b", source_text):
                sig = None

        if sig is None:
            # Couldn't extract a trustworthy signal name (numeric-literal
            # fragment, or a prose word that isn't actually in the source).
            # Better to say nothing than name a signal that doesn't exist —
            # the raw Verilator output is already shown separately in the
            # prompt, so the model isn't left with nothing.
            continue

        codes.append(code)
        if code == "UNDRIVEN":
            blocks.append(_undriven_message(sig, source_text))
        elif code == "UNUSEDSIGNAL":
            blocks.append(_unusedsignal_message(sig, source_text))
        else:
            blocks.append(make_msg(sig))

    return "\n\n".join(blocks), codes


# ── Yosys latch detection (fix: anchored regex, replaces substring keyword
# matching that lived in the runner files) ──────────────────────────────────
# CORRECTION 2026-08-17, found while re-verifying against real Yosys 0.33
# output (not just synthetic examples): the first version of this regex
# required a "Warning:" prefix, on the assumption Yosys emits this as one of
# its Warning-class messages. It doesn't — confirmed against a real capture:
# Yosys 0.33's proc_dlatch pass prints "Latch inferred for signal `...'" as
# plain pass-commentary text, with NO "Warning:" prefix at all (unlike the
# genuine Warning-class comb-loop message below, which does have one). The
# first version also broke on hierarchical signal names
# ("`\module.\signal'" — two embedded backslashes, one before the module
# qualifier and one before the signal name) because its optional module-name
# group was unbounded and could run past the intended field into unrelated
# text later in the line (e.g. a "." inside a file path).
#
# REVISION 2026-08-18: the `(?<!No )` lookbehind above was correct and
# already rejects real "No latch inferred" text (case-sensitive `Latch`
# alone does that — verified by re-running detect_yosys_latches() against
# the actual captured negative string from decoder_3to8's sem_adv run
# before touching this function again). What actually broke in production
# was that AutoChipAdvFB/autochip_stitch_runner.py and its copy
# STITCH_v3/runners/illustration_runner.py never called this function at
# all — they maintained their own separate, case-INsensitive substring
# check (`_LATCH_KEYWORDS`) that this file's fix never reached. That
# duplication is fixed separately (the runner now imports from here — see
# illustration_runner.py's history). This revision replaces the single
# lookbehind-regex approach with an explicit per-line scan: functionally
# equivalent on every case tested so far, but the rejection logic is
# legible without having to reason about a regex lookbehind, which matters
# now that this function is the ONLY place latch detection happens.
#
# What actually distinguishes real positives from the two false-positive
# patterns is NOT "Warning:" — it's the phrase itself, case-sensitive:
# Yosys 0.33 consistently capitalizes the affirmative message ("Latch
# inferred...") and lowercases the negated one ("No latch inferred..."),
# and the pass banner doesn't contain this phrase at all. The per-line
# "no latch"/"executing ... pass" checks below are explicit defense-in-depth
# on top of that case distinction, in case a future Yosys version
# capitalizes the negative form the same way.
#
# Real Yosys 0.33 examples (all three must be handled correctly):
#   positive, flat:          "Warning: Latch inferred for signal `\out' from process ..."
#   positive, hierarchical:  "Latch inferred for signal `\mode_mux_latch.\out' from process ..."
#   negative (reject):       "No latch inferred for signal `\decoder_3to8.\out' from process ..."
#   banner (reject):         "2.2.8. Executing PROC_DLATCH pass (convert process syncs to latches)."
_LATCH_POSITIVE_RE = re.compile(
    r"\bLatch inferred for signal\s+`\\(?:[^.'`]+\.\\)?([^'`]+)'"
)


def detect_yosys_latches(yosys_output: str) -> list:
    """Return list of signal names for which Yosys inferred a latch.

    Rejects the negative form ("No latch inferred") which Yosys 0.33 emits
    when the PROC_DLATCH pass runs and finds no latches, and rejects the
    pass-name banner ("Executing PROC_DLATCH pass ...") which prints on
    every module regardless of whether a latch exists — both explicitly,
    per line, before the positive pattern ever gets a chance to run on
    that line. Empty list means no latches.
    """
    results = []
    for line in yosys_output.splitlines():
        low = line.strip().lower()
        if low.startswith("no latch") or "no latch inferred" in low:
            continue
        if "executing" in low and "pass" in low:
            continue
        m = _LATCH_POSITIVE_RE.search(line)
        if m:
            results.append(m.group(1))
    return results


def has_latches(yosys_output: str) -> bool:
    return bool(detect_yosys_latches(yosys_output))


# ── Yosys combinational-loop detection (new — no prior coverage at all) ─────
# Real Yosys 0.33 combinational-loop warning format:
#   "Warning: found logic loop in module `\priority_chain_comb':"
# Variant seen in some versions: "found combinational loop".
# Anchored to Warning: prefix same as latch handler.
_COMB_LOOP_RE = re.compile(
    r"^\s*Warning:\s+found\s+(?:logic|combinational)\s+loop\s+in\s+module\s+[`']?\\?(\w+)[`']?",
    re.MULTILINE,
)


def detect_comb_loops(yosys_output: str) -> list:
    """Return list of module names in which Yosys detected a combinational loop."""
    return _COMB_LOOP_RE.findall(yosys_output)


def interpret_comb_loop(yosys_output: str):
    """Convert a Yosys combinational-loop warning into a fix directive.

    Returns None if no loop was detected.
    """
    modules = detect_comb_loops(yosys_output)
    if not modules:
        return None
    mod = modules[0]
    return (
        f"CRITICAL: Combinational loop detected in module '{mod}'. A wire cannot "
        "depend on itself through a cycle of pure combinational logic — the value "
        "has no defined resolution and synthesis will reject the design. Fix by "
        "either:\n"
        "  (a) building priority masks from EARLIER signals in the chain only, "
        "never later ones, or\n"
        "  (b) inserting a register on the feedback path to make it sequential.\n"
        "Do NOT try to fix this by adding an initial value or by disabling the "
        "warning — combinational logic has no state to initialize."
    )


# -- Latch directive: structure-aware repair options (2026-08-19) -------------
# Same class of defect as the pre-parameterisation UNUSEDSIGNAL template, and
# the same remedy: derive the repair from the module actually under repair
# instead of asserting a fixed one. The old template emitted two options
# unconditionally --
#
#   A) "Add else branch to every if without one"
#   B) "Add default to every case statement"
#
# -- plus a causal join reading "this is why enable=0 returns the previous
# output", naming an 'enable' port the module need not have.
#
# Found against phase0/illustrations/pending/priority_encoder_valid/broken.v, whose
# casez ALREADY has `default: begin pos = 3'd0; valid = 1'b0; end`. Option B
# is therefore a literal no-op there, option A is inapplicable (no `if`
# exists), and the real repair -- assign the signal in every branch, not only
# in the default -- was not offered at all. That shape is not exotic: it is
# what SYSTEM_PROMPT rule 3 actively steers models toward, since rule 3
# mandates a default branch and says nothing about per-output coverage inside
# the branches.
#
# The parser below is deliberately approximate, matching the regex-over-real-
# parser style used everywhere else in this file. It answers three questions
# and nothing more: does the block contain an `if`, does it contain a `case`,
# and within each case does the latching signal get assigned in every branch.

_COMMENT_RE = re.compile(r"//[^\n]*|/\*.*?\*/", re.DOTALL)
_CASE_OPEN_RE = re.compile(r"\bcase[zx]?\b")


def _strip_comments(source_text):
    """Blank out comments so keyword scans do not match prose. Newlines are
    preserved so anything downstream keeps the same line structure."""
    def _blank(m):
        return re.sub(r"[^\n]", " ", m.group(0))
    return _COMMENT_RE.sub(_blank, source_text)


def _case_block_bodies(code):
    """Bodies of every case/casez/casex block, innermost text included.

    Scans for case...endcase with a depth counter so a nested case does not
    terminate its parent early. Returns the text between the case header and
    the matching endcase.
    """
    bodies = []
    for m in _CASE_OPEN_RE.finditer(code):
        depth, i = 1, m.end()
        # Skip the case expression's parenthesised header.
        paren = code.find("(", i)
        if paren != -1 and code[i:paren].strip() == "":
            level = 0
            while paren < len(code):
                if code[paren] == "(":
                    level += 1
                elif code[paren] == ")":
                    level -= 1
                    if level == 0:
                        paren += 1
                        break
                paren += 1
            i = paren
        start = i
        for tok in re.finditer(r"\bcase[zx]?\b|\bendcase\b", code[i:]):
            depth += 1 if tok.group(0) != "endcase" else -1
            if depth == 0:
                bodies.append(code[start:i + tok.start()])
                break
    return bodies


def _assigns(text, sig):
    """True if `sig` appears as the left-hand side of an assignment."""
    return bool(re.search(r"\b" + re.escape(sig) + r"\s*(?:\[[^\]]*\])?\s*<?=", text))


def _split_case_branches(body):
    """Branch chunks of one case body, split at depth-0 branch-label colons.

    Each chunk is one branch's statements, possibly with the NEXT branch's
    label text trailing on the end -- harmless here, because a label carries
    no assignment and the only question asked of a chunk is whether it assigns
    a given signal. Colons inside begin/end blocks, bit ranges and parens are
    skipped so `[3:0]` and a nested case's labels do not split anything.
    """
    depth = bracket = paren = 0
    cuts = []
    for tok in re.finditer(r"\bbegin\b|\bend\b|[\[\]():]", body):
        t = tok.group(0)
        if   t == "begin": depth += 1
        elif t == "end":   depth -= 1
        elif t == "[":     bracket += 1
        elif t == "]":     bracket -= 1
        elif t == "(":     paren += 1
        elif t == ")":     paren -= 1
        elif t == ":" and depth <= 0 and bracket == 0 and paren == 0:
            cuts.append(tok.end())
    return [body[a:b] for a, b in zip(cuts, cuts[1:] + [len(body)])]


def _latch_repair_options(sig, source_text):
    """Repair options that actually apply to this module, most specific first.

    Returns (options, analysed). `analysed` is False when the source could not
    be inspected, which is the caller's cue to fall back to generic advice
    rather than assert a structure it never saw.
    """
    if not source_text:
        return [], False

    code = _strip_comments(source_text)
    options = []

    for body in _case_block_bodies(code):
        if not _assigns(body, sig):
            continue                      # this case does not drive sig at all
        branches = _split_case_branches(body)
        if not branches:
            continue
        has_default = bool(re.search(r"\bdefault\s*:", body))
        missing = len([b for b in branches if not _assigns(b, sig)])
        if missing == 0 and has_default:
            continue                      # already complete in this case

        hoist = (
            f"     Simplest alternative that covers every path at once: assign\n"
            f"     '{sig}' unconditionally ONCE immediately BEFORE the case, then\n"
            f"     let individual branches override it."
        )

        if missing == 0:
            # Every listed branch assigns it; only the unlisted values latch.
            options.append(
                f"Add a default branch to the case that assigns '{sig}':\n"
                f"       case (...)\n"
                f"         ... existing branches ...\n"
                f"         default: {sig} = <safe value>;   <-- ADD THIS\n"
                f"       endcase"
            )
        elif has_default:
            # The shape SYSTEM_PROMPT rule 3 steers models into: a compliant
            # default that still leaves the signal unassigned elsewhere.
            options.append(
                f"Assign '{sig}' in EVERY branch of the case, not only in the default.\n"
                f"     The default branch alone is NOT enough -- {missing} branch(es) assign\n"
                f"     other signals but not '{sig}', so on those branches '{sig}' keeps\n"
                f"     its previous value, and that is the latch.\n"
                f"       case (...)\n"
                f"         <label>: begin <other signals> = ...; {sig} = ...; end   <-- ADD '{sig}' HERE\n"
                f"         ...\n"
                f"       endcase\n"
                + hoist
            )
        else:
            # No default AND incomplete branches: both gaps must be closed.
            options.append(
                f"Close BOTH gaps in the case -- a default alone will not fix it:\n"
                f"       1. assign '{sig}' in the {missing} branch(es) that currently omit it, and\n"
                f"       2. add a default branch that also assigns '{sig}'.\n"
                + hoist
            )

    if re.search(r"\bif\s*\(", code) and not re.search(r"\belse\b", code):
        options.append(
            f"Add an else branch to every if that lacks one:\n"
            f"       if (condition) {sig} = <value>;\n"
            f"       else           {sig} = <safe value>;   <-- ADD THIS"
        )

    return options, True


def interpret_yosys_latches(latch_lines, v_path=None):
    """Convert Yosys latch-inference lines into a fix directive.

    v_path: path to the .v file under repair. Optional -- without it the
    directive still names the right signal and states the root cause, but it
    can only give the generic "assign it on every path" advice instead of the
    specific structural repair, and the fallback is logged.
    """
    if not latch_lines:
        return ""

    signals = []
    for line in latch_lines:
        # "Latch inferred for signal `\module.\signame'"
        m = re.search(r"signal\s+`\\[^.]+\.\\([^'`]+)'", line)
        if m:
            signals.append(m.group(1))
        else:
            m = re.search(r"\\([A-Za-z_]\w*)[`']", line)
            if m:
                signals.append(m.group(1))

    sig_list = ", ".join(f"'{s}'" for s in signals) if signals else "an output signal"
    first    = signals[0] if signals else "out"

    source_text = None
    if v_path:
        try:
            with open(v_path, "r", encoding="utf-8", errors="ignore") as f:
                source_text = f.read()
        except OSError:
            source_text = None

    options, analysed = _latch_repair_options(first, source_text)

    if not options:
        why = ("no source file was available to the interpreter"
               if not analysed else
               "no case/if structure in the source explained the latch on %r" % first)
        _LOG.info("Latch directive for %r fell back to generic advice - %s.", first, why)
        options = [
            f"Make sure '{first}' is assigned on EVERY path through the always\n"
            f"     block. The simplest way is one unconditional assignment at the\n"
            f"     top of the block, before any branching:\n"
            f"       always @(*) begin\n"
            f"         {first} = <safe value>;   <-- ADD THIS\n"
            f"         ... existing logic, which may override it ...\n"
            f"       end"
        ]

    if len(options) == 1:
        # Options are written with a 5-space continuation indent so they line
        # up under an "  A) " label. With no label there is nothing to line up
        # under, so pull the continuations back to match.
        fix_header = "EXACT FIX:"
        body = "  " + options[0].replace("\n     ", "\n  ")
    else:
        fix_header = "EXACT FIX (choose one):"
        body = "\n\n".join(
            "  %s) %s" % (chr(ord("A") + i), opt) for i, opt in enumerate(options)
        )

    also = ""
    if len(signals) > 1:
        others = ", ".join("'%s'" % s for s in signals[1:])
        also = f"\nApply the same repair to {others}.\n"

    return (
        f"\n\n*** YOSYS: LATCH INFERRED for signal(s) {sig_list} ***\n\n"
        f"ROOT CAUSE: Yosys inferred a latch on '{first}' because it is not\n"
        f"assigned on every code path through the always block. This means\n"
        f"'{first}' will hold its previous value on paths where no assignment\n"
        f"occurs, which is almost certainly not what you intended for a\n"
        f"combinational output.\n"
        f"{also}\n"
        f"{fix_header}\n"
        f"{body}"
    )
