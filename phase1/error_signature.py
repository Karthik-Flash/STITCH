"""
error_signature.py — normalizes raw tool failure text into a signature the
sem_escalate / sem_escalate_restart state machines use to detect "the model
is stuck on the same failure" vs. "a new failure appeared".

Scope note: this is deliberately NOT part of src/interpreter/stitch_interpreter.py
and does not touch it. The interpreter's job is turning a genuine EDA
warning into a fix directive (semantic content, reused unmodified per the
Phase 1 handoff). This module's job is much shallower: given the raw
iverilog COMPILATION/SIMULATION feedback text that already gates pass/fail
in every condition (baseline, raw_adv, sem_adv alike — see
classify_error()/run_iverilog_sim() in src/runner/stitch_runner.py), decide
whether iteration i's failure is the "same kind" as iteration i-1's. It does
not classify defects and does not generate directives.

tool is always "iverilog" for the escalation state machine today — iverilog
+vvp is the sole pass/fail arbiter across all three conditions, so it is the
only feedback the "baseline" pre-escalation state ever sees, and it stays
the outcome signal after escalation too (Verilator/Yosys inform the
DIRECTIVE, not the verdict). The parameter is kept generic rather than
hardcoded so a future signature source (e.g. distinguishing a Verilator
hard-error class) doesn't require a new function.

NORMALIZATION RULES:

  1. Absolute WSL/Windows paths -> bare filename; the module-specific
     filename itself -> <FILE>. Only the file's ROLE (.v under repair vs.
     _tb.v testbench) is ever diagnostic, never its module-specific name.
  2. All digit runs -> <N>. Covers line/column numbers, "N error(s)",
     $finish timestamps, and testbench data values in one rule — none of
     these are diagnostic of the error CLASS on their own.
  3. Hierarchical instance paths (`foo_tb.dut`-shaped dotted identifier
     chains) -> <PATH>.
  4. Icarus's quoted-identifier forms (``x'', `x', 'x') -> <ID>.
  5. Bare identifiers sitting directly in front of a small fixed set of
     Icarus message anchors ("is not a valid l-value", "is declared here
     as", "cannot be driven by", "has already been declared") -> <ID>.
     These anchors are the actual message template; the word in front of
     them is always a signal name, never template text.
  6. Repeated per-vector SIMULATION FAIL lines ("FAIL a=.. b=..: got ..,
     exp ..") collapse to one "FAIL <VECTOR>" line — a testbench failing
     on 6 input vectors and one failing on 1 are the same KIND of failure
     (wrong logic), not 6 distinct signatures.

Requires: nothing external — pure regex/string functions, no WSL, no
Ollama, no subprocess. See phase1/demo_error_signature.py for the worked
examples (real captured tool output, not synthetic) this design was
checked against.

SIGNATURE SHAPE: "<tool>:<err_type>:<first up-to-WINDOW distinct normalized
lines, joined by ' | '>". WINDOW defaults to 5 (DEFAULT_WINDOW below).

  - err_type is classify_error()'s existing coarse bucket (syntax_error,
    reg_wire_mismatch, logic_error, ...) — passed in, not re-derived here,
    so this signature can never disagree with whatever bucket the runner
    is already using for hints/logging. It is the first line of defense
    against over-collapsing: a compile_other and a logic_error never
    collapse into the same signature no matter what their text looks like.
  - The line window is deliberately short, not the whole body. A stuck
    model regenerates the SAME root defect near the same source lines
    iteration after iteration; downstream cascade lines (a second error
    caused by the first) vary with irrelevant details the model changed
    elsewhere in the file. Keying on the head of the message, not the
    whole body, is what lets "stuck on the same root cause" survive a
    varying tail.
  - WIDENED from 3 to 5 lines (2026-08-20, on review): 3 lines was tuned
    against the "stuck on the same root cause" case (instr_decode_unit
    iter_1 vs iter_3) but under-served the opposite case
    sem_escalate_restart exists to catch — instr_decode_unit sample 3 from
    phase 0, where the interpreter fired a CORRECT directive and the model
    then regressed into a *different* syntax-error loop (§5b.2 in
    plans/research_plan_v4.md). That regressed state must read as a
    different signature from the pre-fire state, or the restart trigger
    can never see it. 5 lines is deep enough to reach the second distinct
    error in a short cascade (see demo_error_signature.py examples 9/10,
    which still collapse correctly at width=5 — both changes were
    verified together, not assumed compatible) while still being shallow
    enough that unrelated tail noise (a differing count of repeated l-value
    errors, e.g.) doesn't leak into the signature.
"""
import re

_WIN_OR_WSL_PATH = re.compile(
    r"(?:[A-Za-z]:[\\/]|/mnt/)[^\s:'\"]*?([A-Za-z0-9_.\-]+\.(?:v|sv))"
)
_FILENAME = re.compile(r"\b[A-Za-z_][A-Za-z0-9_]*(?:_tb)?\.v\b")
_QUOTED_ID = re.compile(r"``([^`']*)''|`([^`']*)'|'([^']*)'")
_DOTTED_PATH = re.compile(r"\b[A-Za-z_][A-Za-z0-9_]*(?:\.[A-Za-z_][A-Za-z0-9_]*)+\b")
_NUMBER = re.compile(r"\d+")
_FAIL_VECTOR = re.compile(r"(?m)^FAIL\b.*:.*$")

_TRIGGER_ANCHORS = [
    re.compile(r"\b([A-Za-z_][A-Za-z0-9_]*)\b(?=\s+is not a valid l-value)"),
    re.compile(r"\b([A-Za-z_][A-Za-z0-9_]*)\b(?=\s+is declared here as)"),
    re.compile(r"\b([A-Za-z_][A-Za-z0-9_]*)\b(?=\s*;\s*cannot be driven by)"),
    re.compile(r"\b([A-Za-z_][A-Za-z0-9_]*)\b(?=\s+has already been declared)"),
]


def _normalize_text(raw: str) -> str:
    text = _WIN_OR_WSL_PATH.sub(r"\1", raw)   # drop directory noise, keep bare filename
    text = _FILENAME.sub("<FILE>", text)      # module-specific filename -> generic token
    text = _QUOTED_ID.sub("<ID>", text)       # quoted identifiers (before dotted-path pass:
                                               # quoted text can itself contain dots, e.g.
                                               # ``adder_with_overflow_tb.dut'')
    text = _DOTTED_PATH.sub("<PATH>", text)   # remaining hierarchical instance paths
    for anchor in _TRIGGER_ANCHORS:
        text = anchor.sub("<ID>", text)
    text = _FAIL_VECTOR.sub("FAIL <VECTOR>", text)
    text = _NUMBER.sub("<N>", text)           # numbers last: line nums, counts, timestamps
    return text


DEFAULT_WINDOW = 5  # see "WIDENED from 3 to 5 lines" above for why


def error_signature(tool: str, raw_text: str, err_type: str, window: int = DEFAULT_WINDOW) -> str:
    """
    tool: source of raw_text — "iverilog" for the escalation state machine.
    raw_text: unnormalized tool feedback (the iverilog_fb body already
      extracted by run_iverilog_sim() in stitch_runner.py — the
      "COMPILATION ERROR:\\n..." / "SIMULATION FAILED:\\n..." text before
      any hint is appended).
    err_type: classify_error()'s bucket for the same raw_text — reused
      unmodified from stitch_runner.py, not re-derived here.
    window: how many distinct normalized lines to key on. Config-driven,
      not hardcoded — the escalation runner should read this from the same
      config surface as N (the consecutive-failure threshold), not from a
      literal in this module.
    """
    normalized = _normalize_text(raw_text)
    lines = []
    for line in normalized.splitlines():
        line = line.strip()
        if not line:
            continue
        if lines and line == lines[-1]:
            continue  # collapse consecutive duplicate normalized lines
        lines.append(line)
        if len(lines) == window:
            break
    body = " | ".join(lines) if lines else "(empty)"
    return f"{tool}:{err_type}:{body}"
