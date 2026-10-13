"""
phase2/verify_pass_detection.py -- golden-vs-broken pre-flight check
(deliverable #3 of the runner-hardening task, 2026-08-24).

For every one of the 44 RTLLM designs already confirmed compatible by
phase1/rtllm_task_a_screen.py (phase1/results/rtllm_pilot/task_a_screen.json,
status=="pass"):
  1. Compile + simulate the GOLDEN reference (verified_<design>.v, renamed
     to declare `module <design>` the same way rtllm_task_a_screen.py
     already does -- reusing its proven discovery/rename logic, not a
     second implementation of it) and confirm detect_outcome() returns
     "PASS".
  2. Compile + simulate a deliberately BROKEN version -- a module with the
     IDENTICAL port signature (copied verbatim from the golden reference's
     own ANSI-style header, so the testbench's instantiation still
     compiles unchanged) but an EMPTY body: every output is left
     completely undriven. This is a generic "outputs tied to X/Z instead
     of a real value" corruption that needs no per-design semantic
     understanding, works uniformly across all 44 designs' actual logic,
     and is guaranteed to disagree with the testbench's expected values
     for any design that checks its outputs at all -- and confirm
     detect_outcome() returns "FAIL" (not "UNKNOWN", not "PASS").

This is the golden-reference discipline Bug #2's fix already used, applied
to Bug #3's territory (pass-detection) per the runner-hardening brief.

IMPORTANT -- read before treating a green run here as sufficient: this
script runs identically on Windows/WSL (this repo's usual local
environment) or native Linux (HPC), auto-selected via platform.system().
A LOCAL green run is useful for iterating on this script and on
pass_detection.py's registry, but per the runner-hardening brief it does
NOT satisfy the pre-sbatch gate -- the version that gates the real HPC
job must be run ON HPC, against the deployed RTLLM checkout and the same
Icarus binaries the full run will actually use (see
docs/HPC_COMMANDS.md). That HPC run is a manual step for
whoever has cluster access; this script does not attempt to SSH anywhere.

Usage:
  python phase2/verify_pass_detection.py [--rtllm-root PATH]
Exit code: 0 iff every one of the 44 designs is green (golden=PASS AND
broken=FAIL); 1 otherwise, with a table showing exactly which rows failed
and how.
"""
import argparse
import json
import os
import platform
import re
import shutil
import subprocess
import sys

_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(_HERE, "..", "src", "interpreter"))
from pass_detection import detect_outcome  # noqa: E402

DEFAULT_RTLLM_ROOT = os.environ.get("RTLLM_ROOT") or os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "RTLLM"))
TASK_A_SCREEN_JSON = os.path.join(
    _HERE, "..", "phase1", "results", "rtllm_pilot", "task_a_screen.json")
SCRATCH_ROOT = os.path.join(_HERE, "results", "verify_pass_detection")

CATEGORIES = ["Arithmetic", "Control", "Memory", "Miscellaneous"]
_MODULE_RE = re.compile(r"\bmodule\s+(verified_[A-Za-z0-9_]+)\b")
IS_WINDOWS = platform.system() == "Windows"


def win_to_wsl(win_path):
    p = os.path.abspath(win_path).replace("\\", "/")
    if len(p) > 1 and p[1] == ":":
        p = f"/mnt/{p[0].lower()}" + p[2:]
    return p


def _load_compatible_designs(rtllm_root):
    """Returns [(category, design, design_dir), ...] for the 44 designs
    phase1/rtllm_task_a_screen.py already confirmed compile+pass with
    their golden reference -- that JSON is the authoritative "44
    compatible" pool (see runner-hardening brief). Re-derives each
    design's directory the same way rtllm_task_a_screen.py's
    discover_designs() does, rather than assuming a stored path (the
    screen JSON only stores category+design name)."""
    if not os.path.exists(TASK_A_SCREEN_JSON):
        print(f"FATAL: {TASK_A_SCREEN_JSON} not found -- run "
              f"phase1/rtllm_task_a_screen.py first (it produces the "
              f"44-compatible-design pool this script iterates).")
        sys.exit(1)
    with open(TASK_A_SCREEN_JSON, encoding="utf-8") as f:
        screen = json.load(f)
    compatible = {(d["category"], d["design"]) for d in screen if d["status"] == "pass"}

    found = []
    for cat in CATEGORIES:
        cat_dir = os.path.join(rtllm_root, cat)
        if not os.path.isdir(cat_dir):
            continue
        for sub in sorted(os.listdir(cat_dir)):
            sub_dir = os.path.join(cat_dir, sub)
            if not os.path.isdir(sub_dir):
                continue
            for design in sorted(os.listdir(sub_dir)):
                design_dir = os.path.join(sub_dir, design)
                if (cat, design) in compatible and os.path.isdir(design_dir):
                    found.append((cat, design, design_dir))
    missing = compatible - {(c, d) for c, d, _ in found}
    if missing:
        print(f"WARNING: {len(missing)} design(s) from task_a_screen.json's "
              f"compatible pool were not found under {rtllm_root}: {sorted(missing)}")
    return found


def _renamed_golden(design, design_dir):
    """Returns the golden reference's content with its module renamed
    from verified_<design> (or whatever verified_XXXX it actually
    declares) to plain <design> -- the same rename rtllm_task_a_screen.py's
    screen_one() already applies for the common cases (reused pattern,
    not reimplemented independently), PLUS a documented fallback for
    fixed_point_substractor's known exception (see
    phase1/results/rtllm_pilot/task_a_screen.json's "note" field for that
    design: the reference already declares `module fixed_point_subtractor`
    -- correct spelling, no "verified_" prefix, and NOT matching the
    directory's "substractor" spelling at all -- and the testbench
    instantiates it by that exact already-correct name, so no rename is
    needed or possible via the verified_/bare-design patterns). Falls back
    to using the file's content completely unchanged (with a printed
    warning) for any other design that hits neither pattern, rather than
    raising -- task_a_screen.json already proved this file compiles and
    passes as originally screened, so an unrecognized rename shape is a
    reason to use it as-is and flag it, not a reason to abort."""
    verified_files = [f for f in os.listdir(design_dir)
                       if f.startswith("verified_") and f.endswith(".v")]
    if len(verified_files) != 1:
        raise ValueError(f"expected exactly 1 verified_*.v in {design_dir}, found {verified_files}")
    with open(os.path.join(design_dir, verified_files[0]), encoding="utf-8", errors="replace") as f:
        content = f.read()

    already_bare = re.search(r"\bmodule\s+" + re.escape(design) + r"\b", content)
    if already_bare:
        return content
    m = _MODULE_RE.search(content)
    if m:
        return content.replace(m.group(1), design)

    print(f"\n  NOTE: {verified_files[0]} declares a module name that's "
          f"neither {design!r} nor a verified_* pattern -- using its "
          f"content UNCHANGED (see fixed_point_substractor's documented "
          f"exception in task_a_screen.json for the known precedent).")
    return content


def _matching_paren(text, open_idx):
    """Returns the index of the ')' matching the '(' at open_idx."""
    depth = 0
    i = open_idx
    while i < len(text):
        if text[i] == "(":
            depth += 1
        elif text[i] == ")":
            depth -= 1
            if depth == 0:
                return i
        i += 1
    raise ValueError("unbalanced parens")


def _strip_comments(text):
    """Strips // line comments and /* */ block comments -- needed before
    any port-declaration regex runs, since RTLLM's golden references
    routinely comment individual ports (e.g. "output done  // flag
    signal"), which otherwise defeats a `$` end-of-string anchor."""
    text = re.sub(r"/\*.*?\*/", " ", text, flags=re.DOTALL)
    text = re.sub(r"//[^\n]*", "", text)
    return text


def _find_module_decl(content, design):
    """Locates 'module <design>' OR, when the file's declared name
    doesn't match `design` at all (fixed_point_substractor's documented
    exception -- see _renamed_golden()), the file's own actual module
    name. Returns (match_start_of_'module', name_actually_declared)."""
    m = re.search(r"\bmodule\s+" + re.escape(design) + r"\b", content)
    if m:
        return m.start(), design
    m2 = re.search(r"\bmodule\s+(\w+)", content)
    if m2:
        return m2.start(), m2.group(1)
    raise ValueError(f"could not find any 'module NAME' declaration for {design!r}")


def _extract_port_header(renamed_content, design):
    """Extracts the full 'module <name> [#( ...parameters... )] ( ...ports... )'
    text verbatim (paren-balanced, so bit-range brackets like [7:0] and
    any nested parens don't truncate it early), for building the broken
    stub's signature -- copied byte-for-byte from the golden reference,
    so the stub's port directions/widths/types (and any #(parameter ...)
    block a port width depends on, e.g. `output [WIDTH-1:0] out`) are
    guaranteed identical and the testbench's instantiation compiles
    unchanged. Handles every module header shape actually present in
    RTLLM's golden references, confirmed by direct inspection: ANSI
    `module NAME (input ..., output ...);`, parameterized ANSI
    `module NAME #(parameters) (input ..., output ...);` (e.g.
    adder_pipe_64bit), and non-ANSI `module NAME (a, b, c);` with
    directions declared separately in the body (e.g. adder_32bit) --
    the non-ANSI case is handled by _leading_port_decls() below, not
    here; this function only ever returns the header line itself.

    Returns (header_text, actual_name) -- actual_name may differ from
    `design` for the fixed_point_substractor-shaped exception."""
    start, actual_name = _find_module_decl(renamed_content, design)
    pos = re.search(r"\bmodule\s+" + re.escape(actual_name) + r"\b", renamed_content[start:]).end() + start
    pos += re.match(r"\s*", renamed_content[pos:]).end()

    if renamed_content[pos:pos + 2] == "#(":
        param_close = _matching_paren(renamed_content, pos + 1)
        pos = param_close + 1
        pos += re.match(r"\s*", renamed_content[pos:]).end()

    if renamed_content[pos:pos + 1] != "(":
        raise ValueError(f"expected '(' at position {pos} for {actual_name}'s port list, "
                          f"found {renamed_content[pos:pos + 20]!r}")
    port_close = _matching_paren(renamed_content, pos)
    return renamed_content[start:port_close + 1], actual_name


_DIR_STATEMENT_RE = re.compile(r"^\s*(input|output|inout)\b")


def _leading_port_decls(renamed_content, header_end_pos):
    """Non-ANSI support: when the port list is just bare names
    (`module foo(a, b, c);`), the actual input/output/inout declarations
    are separate statements immediately following the header, before any
    other declaration (wire/reg/parameter) or logic. Collects every
    leading `;`-terminated statement that starts with input/output/inout,
    stops at the first one that doesn't, and returns them joined verbatim
    (so widths/signedness are preserved exactly) -- empty string if the
    header was already ANSI-style (contains its own direction keywords,
    checked by the caller before this is used)."""
    rest = renamed_content[header_end_pos:]
    # Skip the header's own terminating ';'.
    m = re.match(r"\s*;", rest)
    if not m:
        return ""
    rest = rest[m.end():]

    kept = []
    pos = 0
    while True:
        stmt_end = rest.find(";", pos)
        if stmt_end == -1:
            break
        stmt = rest[pos:stmt_end + 1]
        if _DIR_STATEMENT_RE.match(_strip_comments(stmt)):
            kept.append(stmt.strip())
            pos = stmt_end + 1
        else:
            break
    return "\n  ".join(kept)


def _split_ports(port_list_text):
    """Splits the text between a module's outer port-list parens into
    individual port declarations, respecting [..]/(..) nesting so a
    bit-range like [WIDTH-1:0] or a default-value expression never
    causes a false split."""
    parts, depth, current = [], 0, []
    for ch in port_list_text:
        if ch in "([":
            depth += 1
        elif ch in ")]":
            depth -= 1
        if ch == "," and depth == 0:
            parts.append("".join(current))
            current = []
        else:
            current.append(ch)
    if "".join(current).strip():
        parts.append("".join(current))
    return parts


_TYPE_KEYWORD_RE = re.compile(r"^\s*(reg|wire|signed|unsigned)\b")
_BIT_RANGE_RE = re.compile(r"^\s*\[[^\]]*\]")


def _parse_output_decl(text):
    """Parses one output port/declaration chunk (already comment-
    stripped): `output [wire|reg|signed|unsigned]* [bit_range]?
    name1, name2, ...`. Handles ANY order/repetition of the type
    keywords and the bit-range (e.g. `output wire [15:0] y`, `output reg
    [7:0] a, b`, `output signed [3:0] x`) by stripping them in a loop
    rather than encoding one fixed order in a single regex -- an earlier
    fixed-order regex here silently dropped ports shaped like
    `output wire [15:0] y` entirely (the "wire" keyword before the
    bracket didn't match anything the regex expected), which under-
    counted this design's outputs in the broken stub without raising any
    error -- found 2026-08-24 by noticing adder_16bit's `y` port was
    simply missing from the generated stub. Returns (is_reg, [names]) or
    None if `text` isn't an output declaration at all."""
    m = re.match(r"^\s*output\b", text)
    if not m:
        return None
    rest = text[m.end():]
    is_reg = False
    while True:
        tm = _TYPE_KEYWORD_RE.match(rest)
        if tm:
            if tm.group(1) == "reg":
                is_reg = True
            rest = rest[tm.end():]
            continue
        bm = _BIT_RANGE_RE.match(rest)
        if bm:
            rest = rest[bm.end():]
            continue
        break
    names = [n.strip() for n in rest.split(",") if n.strip()]
    return is_reg, names


def _output_names_from_ansi_port_list(port_list_text):
    """ANSI style: port_list_text is comma-separated at depth 0, so each
    chunk from _split_ports() is exactly one port's own declaration
    (comments already stripped by the caller)."""
    names = []
    for chunk in _split_ports(port_list_text):
        parsed = _parse_output_decl(chunk)
        if not parsed:
            continue
        is_reg, chunk_names = parsed
        names.extend((n, is_reg) for n in chunk_names)
    return names


def _output_names_from_decl_statements(decl_text):
    """Non-ANSI style: decl_text is `;`-terminated statements (comments
    already stripped by the caller), and a SINGLE statement can declare
    multiple names sharing one direction/type, e.g. `output [7:0] a, b;`
    -- unlike the ANSI case, where each comma-separated port list entry
    is independent."""
    names = []
    for stmt in decl_text.split(";"):
        stmt = stmt.strip()
        if not stmt:
            continue
        parsed = _parse_output_decl(stmt)
        if not parsed:
            continue
        is_reg, stmt_names = parsed
        names.extend((n, is_reg) for n in stmt_names)
    return names


def _broken_stub(design, renamed_content):
    """A module with the SAME port signature as the golden reference,
    but with every OUTPUT forced to the constant 0 -- `initial <name> = 0;`
    for `output reg` ports (procedural assignment, required for reg-typed
    signals), `assign <name> = 0;` for plain/wire-typed output ports
    (continuous assignment, required for net-typed signals; a `reg` port
    cannot legally take a continuous assign, and a plain `wire` output
    cannot legally take a procedural initial -- both forms are needed,
    selected per-port from its own declaration).

    This corrupts the design to genuinely wrong (not merely undriven/X)
    output values for any test vector where 0 isn't the expected result
    -- true for every one of these 44 designs' test suites. An earlier
    version of this stub left outputs completely UNDRIVEN (X) instead;
    that was found (2026-08-24, this verification run) to silently
    "pass" several designs whose testbenches compare with `!=`/`==`
    rather than 4-state-aware `!==`/`===` -- X propagates through `!=`
    as X, and `if (X)` is FALSE in Verilog, so the failure branch never
    ran and the undriven stub printed a spurious "Your Design Passed".
    That was a flaw in this script's corruption strategy, not in
    detect_outcome() (it truthfully reported what the simulator actually
    printed) -- forcing a concrete wrong value instead of X closes it,
    and matches the runner-hardening brief's own suggested corruption
    ("outputs tied to 0") more literally than the X-based version did.

    Also handles non-ANSI headers (`module foo(a, b, c);` with
    directions declared as separate statements in the body, e.g.
    adder_32bit, calendar, fsm -- confirmed by direct inspection to be
    common in RTLLM's golden references, not a one-off) via
    _leading_port_decls(): those declaration statements are copied
    verbatim into the stub alongside the bare-name header, exactly as
    they'd appear in the real body, so the stub is a legal non-ANSI
    module too."""
    header, actual_name = _extract_port_header(renamed_content, design)
    header_end_in_content = renamed_content.index(header) + len(header)
    port_close = len(header) - 1
    port_open = _matching_paren_reverse(header, port_close)
    port_list_text = _strip_comments(header[port_open + 1:port_close])

    is_ansi = bool(_DIR_STATEMENT_RE.match(port_list_text) or
                    re.search(r"\b(input|output|inout)\b", port_list_text))

    extra_decls = ""
    if is_ansi:
        outputs = _output_names_from_ansi_port_list(port_list_text)
    else:
        extra_decls = _leading_port_decls(renamed_content, header_end_in_content)
        outputs = _output_names_from_decl_statements(_strip_comments(extra_decls))

    zero_drives = []
    for name, is_reg in outputs:
        if is_reg:
            zero_drives.append(f"  initial {name} = 0;")
        else:
            zero_drives.append(f"  assign {name} = 0;")

    body = "\n".join(zero_drives) if zero_drives else "  // (no output ports found to drive)"
    extra_decls_block = f"  {extra_decls}\n\n" if extra_decls else ""
    return (
        f"{header};\n\n"
        f"{extra_decls_block}"
        f"  // DELIBERATELY BROKEN for verify_pass_detection.py:\n"
        f"  // every output forced to 0 on purpose.\n"
        f"{body}\nendmodule\n"
    )


def _matching_paren_reverse(text, close_idx):
    depth = 0
    i = close_idx
    while i >= 0:
        if text[i] == ")":
            depth += 1
        elif text[i] == "(":
            depth -= 1
            if depth == 0:
                return i
        i -= 1
    raise ValueError("unbalanced parens (reverse)")


def _compile_and_sim(work_dir, v_filename, tb_filename, data_files, timeout_s=15):
    """Compiles v_filename + tb_filename (+ any data_files already staged
    in work_dir) and runs the simulation. Returns (status, sim_output)
    where status is "PASS"|"FAIL"|"UNKNOWN"|"COMPILE_ERROR"|"TIMEOUT".
    Dual-mode: WSL wrapper on Windows (matching
    rtllm_task_a_screen.py's pattern), native subprocess on Linux
    (matching phase2/smoke_test.py's pattern) -- selected by
    platform.system(), so this script runs unmodified in both places."""
    if IS_WINDOWS:
        wsl_dir = win_to_wsl(work_dir)
        compile_cmd = ["wsl", "bash", "-lc",
                       f"cd '{wsl_dir}' && timeout {timeout_s} iverilog -o sim.vvp {v_filename} {tb_filename}"]
        sim_cmd = ["wsl", "bash", "-lc", f"cd '{wsl_dir}' && timeout {timeout_s} vvp sim.vvp"]
        run_kwargs = {}
    else:
        compile_cmd = ["timeout", str(timeout_s), "iverilog", "-o", "sim.vvp", v_filename, tb_filename]
        sim_cmd = ["timeout", str(timeout_s), "vvp", "sim.vvp"]
        run_kwargs = {"cwd": work_dir}

    try:
        comp = subprocess.run(compile_cmd, capture_output=True, text=True,
                               timeout=timeout_s + 10, **run_kwargs)
    except subprocess.TimeoutExpired:
        return "TIMEOUT", "[compile timeout]"
    if comp.returncode != 0:
        return "COMPILE_ERROR", (comp.stdout + comp.stderr)[-2000:]

    try:
        sim = subprocess.run(sim_cmd, capture_output=True, text=True,
                              timeout=timeout_s + 10, **run_kwargs)
    except subprocess.TimeoutExpired:
        return "TIMEOUT", "[sim timeout]"

    sim_out = sim.stdout + sim.stderr
    return detect_outcome(sim_out, "rtllm"), sim_out


def run_one(category, design, design_dir):
    work_dir = os.path.join(SCRATCH_ROOT, design)
    if os.path.exists(work_dir):
        shutil.rmtree(work_dir)
    os.makedirs(work_dir)

    try:
        renamed = _renamed_golden(design, design_dir)
    except ValueError as e:
        return {"design": design, "category": category, "error": str(e)}

    shutil.copy(os.path.join(design_dir, "testbench.v"), os.path.join(work_dir, "testbench.v"))
    for f in os.listdir(design_dir):
        if f in ("testbench.v", "makefile", "design_description.txt") or f.startswith("verified_"):
            continue
        shutil.copy(os.path.join(design_dir, f), os.path.join(work_dir, f))

    golden_v = os.path.join(work_dir, f"{design}.v")
    with open(golden_v, "w", encoding="utf-8") as f:
        f.write(renamed)
    golden_status, golden_out = _compile_and_sim(work_dir, f"{design}.v", "testbench.v", [])

    try:
        broken_content = _broken_stub(design, renamed)
    except ValueError as e:
        return {"design": design, "category": category,
                "golden_status": golden_status, "error": f"broken-stub generation failed: {e}"}

    os.remove(golden_v)
    with open(golden_v, "w", encoding="utf-8") as f:
        f.write(broken_content)
    broken_status, broken_out = _compile_and_sim(work_dir, f"{design}.v", "testbench.v", [])

    return {
        "design": design, "category": category,
        "golden_status": golden_status, "broken_status": broken_status,
        "golden_ok": golden_status == "PASS",
        "broken_ok": broken_status == "FAIL",
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--rtllm-root", default=DEFAULT_RTLLM_ROOT)
    args = parser.parse_args()

    print(f"Platform: {platform.system()} ({'WSL-wrapped' if IS_WINDOWS else 'native Linux'} iverilog/vvp)")
    print(f"RTLLM root: {args.rtllm_root}")
    if not IS_WINDOWS:
        print("Running on native Linux -- if this is HPC, this IS the gating run "
              "the runner-hardening brief requires before sbatch.")
    else:
        print("Running on Windows/WSL -- LOCAL iteration run only. Per the "
              "runner-hardening brief, this does NOT satisfy the pre-sbatch "
              "gate; the gating run must happen on HPC against the deployed "
              "RTLLM checkout and toolchain.")

    designs = _load_compatible_designs(args.rtllm_root)
    print(f"\n{len(designs)} compatible design(s) to verify.\n")

    results = []
    for i, (cat, design, design_dir) in enumerate(designs, 1):
        print(f"[{i}/{len(designs)}] {cat}/{design} ...", end=" ", flush=True)
        r = run_one(cat, design, design_dir)
        results.append(r)
        if r.get("error"):
            print(f"ERROR: {r['error']}")
        else:
            g = "PASS" if r["golden_ok"] else f"FAIL({r['golden_status']})"
            b = "PASS" if r["broken_ok"] else f"FAIL({r['broken_status']})"
            tag = "OK" if (r["golden_ok"] and r["broken_ok"]) else "RED"
            print(f"golden={g:14} broken_expect_FAIL={b:20} [{tag}]")

    W = 78
    print(f"\n{'=' * W}")
    print("  verify_pass_detection.py -- summary")
    print("=" * W)
    n_ok = 0
    n_broken_unknown = 0
    n_errors = 0
    for r in results:
        if r.get("error"):
            n_errors += 1
            continue
        ok = r["golden_ok"] and r["broken_ok"]
        n_ok += 1 if ok else 0
        if r["broken_status"] == "UNKNOWN":
            n_broken_unknown += 1

    print(f"  {n_ok}/{len(results)} designs fully green (golden=PASS, broken=FAIL)")
    if n_broken_unknown:
        print(f"  {n_broken_unknown} broken design(s) returned UNKNOWN rather than FAIL "
              f"-- not a false PASS, but worth reviewing (see report).")
    if n_errors:
        print(f"  {n_errors} design(s) hit a script-level ERROR before either sim ran.")

    print()
    all_green = (n_ok == len(results)) and not n_errors
    if all_green:
        print("ALL GREEN.")
    else:
        print("NOT all green -- see rows above marked RED / ERROR.")

    out_json = os.path.join(SCRATCH_ROOT, "results.json")
    os.makedirs(SCRATCH_ROOT, exist_ok=True)
    with open(out_json, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2)
    print(f"\nFull results -> {out_json}")

    sys.exit(0 if all_green else 1)


if __name__ == "__main__":
    main()
