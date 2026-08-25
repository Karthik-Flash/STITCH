"""
phase2/stitch_runner_hpc.py -- Linux-native port of src/runner/stitch_runner.py
for HPC compute nodes.

WHY THIS FILE EXISTS (read before touching it): src/runner/stitch_runner.py
is Windows+WSL-specific -- every tool invocation goes through `wsl.exe`
(WSL_PREFIX = ["wsl"]) with Windows-to-WSL path translation (win_to_wsl()).
None of that runs on an HPC Linux compute node -- there is no `wsl.exe`
there at all, so the Windows-side file cannot be scp'd up and run as-is.
This is a faithful port: EVERY line of logic outside the three tool-
invocation functions (run_verilator_lint, run_yosys_check,
run_iverilog_sim) is copied unchanged from src/runner/stitch_runner.py
at commit a047d78 (2026-08-22, "Fix two silent correctness bugs..."),
which is the state AFTER both harness fixes:
  - bug #2 (vvp working directory / $readmemh resolution)
  - bug #1 (unclosed ```verilog fence stripping)
Both fixes are carried into this port -- see run_iverilog_sim() and the
extraction block in run_one_condition() below for exactly where.

CONFIRMING THE FIXES ARE PRESENT, for the record (2026-08-22): this file
was derived directly from the LOCAL, git-committed copy of
src/runner/stitch_runner.py (commit a047d78, already pushed to
origin/main) via a direct read of that file's actual current content --
not from any prior copy that might already exist on HPC. That sidesteps
the "is the HPC copy old?" question entirely rather than trying to
inspect a filesystem this session has no access to: this port is
guaranteed correct at the moment it's written because it's built FROM
the verified-fixed source, and phase2/HPC_RTLCODER_COMMANDS.md's twin-run
section has the user re-deploy this exact file (not reuse whatever, if
anything, is already up there) plus a grep-based post-deploy check for
both fix signatures, so there's an independent confirmation step too.

WHAT ACTUALLY CHANGED vs. the Windows/WSL original, and why native Linux
needs LESS code, not more, for the bug #2 fix specifically: on Windows,
`subprocess.run(cwd=...)` only controls where the `wsl.exe` LAUNCHER
starts -- it has no effect on the shell environment once execution is
inside the WSL VM, which is exactly why the original fix had to `cd`
inside a `bash -lc` invocation. On native Linux there is no launcher
indirection: `subprocess.run(cwd=iter_dir)` directly sets the CHILD
PROCESS's own working directory, so `vvp` inherits the right directory
with no `cd` trick needed at all. Same fix, structurally simpler
implementation -- see run_iverilog_sim() below.

Everything else (call_llm's OpenAI/Gemini/Ollama dispatch, the feedback
builders, classify_error, run_one_condition's full loop, STUCK_THRESHOLD
handling) is UNCHANGED. This file does NOT include BENCHMARK /
print_stitch_table / the CLI __main__ block from the original -- the
twin-run orchestrator (phase2/twin_run_runner.py) supplies its own RTLLM
specs directly, the same way phase1/rtllm_pilot_runner.py already does
against the Windows-side runner.
"""

import os, subprocess, re, shutil, sys, json, time
from openai import OpenAI

# DEPLOYMENT PATH ROBUSTNESS (2026-08-25, added while building Set 1's
# full-run harness): this file is scp'd FLAT onto HPC (no repo tree
# around it -- see phase2/FULL_RUN_RUNBOOK.md), so the repo-relative
# guess "../src/interpreter" only resolves correctly if src/interpreter/
# happens to land exactly one level above wherever this file is deployed
# -- an assumption nothing actually verifies. STITCH_INTERPRETER_DIR lets
# both full-run sbatch scripts (Set 1 and Set 2) state that location
# explicitly instead of relying on relative-path guesswork; unset, this
# falls back to the original relative guess unchanged, so local/dev usage
# (where the repo tree IS there) is unaffected.
_INTERP_DIR = os.environ.get("STITCH_INTERPRETER_DIR") or os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "..", "src", "interpreter")
sys.path.insert(0, _INTERP_DIR)
from stitch_interpreter import (
    _VERILATOR_INTERP, _LITERAL_FRAGMENT_RE, _extract_signal_name,
    _PORT_DECL_RE, _INTERNAL_DECL_RE, _decl_names,
    _classify_undriven_signal, _undriven_message,
    interpret_verilator, interpret_yosys_latches,
    detect_yosys_latches, detect_comb_loops, interpret_comb_loop,
)
# FIX 2026-08-24 (Bug #3 class, structural fix): this file's
# run_iverilog_sim() used to hardcode the SAME case-sensitive "PASS" /
# "ALL TESTS PASSED" substring check as the Windows/WSL original -- tuned
# for this project's own v20/v2/phase0 testbenches, not RTLLM's "Your
# Design Passed" -- and unlike phase1/rtllm_pilot_runner.py (which
# monkeypatched around this on the Windows side), NOTHING patched it here.
# This is the actual, live Bug #3: phase2/twin_run_runner.py calls this
# file's run_one_condition() directly, with no pass-detection override at
# all, so every RTLLM pass in the twin pilot was silently recorded as a
# failure. See pass_detection.py's module docstring for the full history.
# Every caller of run_iverilog_sim()/run_one_condition() must now pass an
# explicit `benchmark` identifier -- there is no default. (Same sys.path
# entry as stitch_interpreter's import above already makes this
# resolvable -- pass_detection.py lives alongside it.)
from pass_detection import detect_outcome  # noqa: E402

# ── CONFIG ────────────────────────────────────────────────────────────────────
MAX_RETRIES      = 6
STUCK_THRESHOLD  = 2
TESTBENCH_DIR    = "testbenches_v2"
RESULTS_DIR      = "results_stitch"

# ── API CLIENTS ───────────────────────────────────────────────────────────────
GEMINI_AVAILABLE = False
GEMINI_CLIENT    = None
try:
    from google import genai as google_genai
    from google.genai import types as genai_types
    GEMINI_KEY = os.environ.get("GEMINI_API_KEY", "")
    if GEMINI_KEY:
        GEMINI_CLIENT    = google_genai.Client(api_key=GEMINI_KEY)
        GEMINI_AVAILABLE = True
except ImportError:
    pass

OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY", "")
OPENAI_CLIENT  = OpenAI(api_key=OPENAI_API_KEY) if OPENAI_API_KEY else None
OLLAMA_CLIENT  = OpenAI(base_url="http://localhost:11434/v1", api_key="ollama")

GEMINI_MODEL_MAP = {
    "gemini-2.5-flash": "models/gemini-2.5-flash",
    "gemini-2.5-pro":   "models/gemini-2.5-pro",
    "gemini-2.0-flash": "models/gemini-2.0-flash-exp",
    "gemini-1.5-flash": "models/gemini-1.5-flash",
    "gemini-1.5-pro":   "models/gemini-1.5-pro",
}

# Identical system prompt for ALL conditions -- controlled variable is
# feedback quality only, not system prompt content. Unchanged verbatim
# from src/runner/stitch_runner.py.
SYSTEM_PROMPT = """You are a Verilog-2001 expert.

MANDATORY RULES:
1. 'wire' for signals driven by 'assign' or sub-module output ports.
   'reg' ONLY for signals assigned inside 'always' blocks.
2. Non-blocking (<=) in clocked always blocks. Blocking (=) in combinational.
3. EVERY combinational always block MUST have a 'default' branch in case
   statements AND an 'else' branch in if-else chains. Omitting these infers
   LATCHES which cause wrong simulation output and are a synthesis error.
4. Sensitivity list: use @(*) or list ALL signals read inside the block.
   A partial sensitivity list causes the block to silently not re-evaluate.
5. Use ONLY Verilog-2001 syntax. No SystemVerilog: no 'logic', no 'always_comb',
   no 'always_ff', no bit-width-free literals like '1 or '0.
   Write all literals with explicit width: 1'b0, 8'hFF, 2'b01.
6. Every case branch with MULTIPLE assignments MUST use begin...end.
7. Return ONLY Verilog code inside ```verilog ... ``` fences. No prose."""


# ── UTILITIES ─────────────────────────────────────────────────────────────────
# win_to_wsl() deliberately NOT ported -- there is nothing to translate to
# on native Linux, every path used below is already a real filesystem path.
def sanitize_ascii(text):
    return text.encode("ascii", errors="ignore").decode("ascii")

_PATH_RE = re.compile(
    r"(?:[A-Za-z]:[\\/]|[\\/])(?:[^\s:'\"/\\<>|*?\n]+[\\/])*"
    r"([^\s:'\"/\\<>|*?\n]+\.v)"
)
def strip_paths(text):
    return _PATH_RE.sub(r"\1", text)


# ── LLM CALL with token counting ──────────────────────────────────────────────
def call_llm(model, messages):
    """Returns (text, prompt_tokens, completion_tokens). Unchanged from
    src/runner/stitch_runner.py -- the RTLCoder branch is added by
    twin_run_runner.py MONKEYPATCHING this name at runtime (same pattern
    phase1/rtllm_pilot_runner.py already uses for run_iverilog_sim), not
    by editing this function. Keeps this port a clean, verifiable copy of
    the Windows-side original's LLM dispatch."""
    if model.startswith("gemini"):
        if not GEMINI_AVAILABLE:
            print("ERROR: Set GEMINI_API_KEY and install google-genai"); sys.exit(1)
        api_model = GEMINI_MODEL_MAP.get(model, f"models/{model}")
        history = "\n".join(
            f"[{'USER' if m['role']=='user' else 'ASSISTANT'}]\n{m['content']}"
            for m in messages if m["role"] != "system"
        )
        resp = GEMINI_CLIENT.models.generate_content(
            model=api_model,
            config=genai_types.GenerateContentConfig(
                system_instruction=SYSTEM_PROMPT, temperature=0.1),
            contents=history,
        )
        meta = getattr(resp, "usage_metadata", None)
        pt = getattr(meta, "prompt_token_count",     0) if meta else 0
        ct = getattr(meta, "candidates_token_count", 0) if meta else 0
        return resp.text, pt, ct
    elif model.startswith("gpt-") or model.startswith("o1") or model.startswith("o3"):
        if not OPENAI_CLIENT:
            print("ERROR: Set OPENAI_API_KEY"); sys.exit(1)
        resp = OPENAI_CLIENT.chat.completions.create(
            model=model, messages=messages, temperature=0.1)
        u = resp.usage
        return resp.choices[0].message.content, u.prompt_tokens, u.completion_tokens
    else:
        resp = OLLAMA_CLIENT.chat.completions.create(
            model=model, messages=messages, temperature=0.1)
        u = getattr(resp, "usage", None)
        pt = getattr(u, "prompt_tokens",     0) if u else 0
        ct = getattr(u, "completion_tokens", 0) if u else 0
        return resp.choices[0].message.content, pt, ct


# ── LAYER 1: VERILATOR ────────────────────────────────────────────────────────
VERILATOR_SUPPRESS = [
    "-Wno-DECLFILENAME", "-Wno-TIMESCALEMOD", "-Wno-EOFNEWLINE",
]

def run_verilator_lint(v_file):
    """Returns (warnings_str, had_meaningful_warnings: bool). Native-Linux:
    verilator invoked directly, no WSL wrapper -- `v_file` is already a
    real path, no win_to_wsl() translation needed."""
    cmd = ["timeout", "18", "verilator", "--lint-only", "-Wall",
           "--bbox-unsup"] + VERILATOR_SUPPRESS + [v_file]
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=25)
    except (subprocess.TimeoutExpired, FileNotFoundError) as e:
        return f"[VERILATOR ERROR: {e}]", True

    output = result.stdout + result.stderr
    kept = [
        s.strip() for s in output.splitlines()
        if s.strip()
        and "... Use" not in s
        and "... For warning" not in s
        and (s.strip().startswith("%Warning") or s.strip().startswith("%Error")
             or s.strip().startswith("..."))
    ]
    had = result.returncode != 0 and bool(kept)
    return ("\n".join(kept) if kept else "(no warnings)"), had


# ── LAYER 2: YOSYS ────────────────────────────────────────────────────────────
_YOSYS_KEEP = re.compile(
    r"(Warning|warning|Error|error|Latch|latch|inferred|proc_dlatch|"
    r"continuous assignment|Number of cells|\$_DLATCH|\$dlatch|\$dff)",
    re.IGNORECASE,
)

def run_yosys_check(v_file, module_name):
    """Returns (report_str, has_latch, latch_lines, cell_count, has_loop,
    loop_modules). Native-Linux: yosys invoked directly, no WSL wrapper --
    `v_file` still needs quoting inside the -p script (spaces in paths are
    just as real on a Linux scratch path as on the Windows side), so that
    part of the 2026-08-18 quoting fix is kept."""
    script = f'read_verilog "{v_file}"; synth -top {module_name}; stat'
    cmd    = ["timeout", "35", "yosys", "-p", script]
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=45)
    except (subprocess.TimeoutExpired, FileNotFoundError) as e:
        return f"[YOSYS ERROR: {e}]", False, [], 0, False, []

    output = result.stdout + result.stderr

    latch_signals = detect_yosys_latches(output)
    has_latch     = bool(latch_signals)
    loop_modules  = detect_comb_loops(output)
    has_loop      = bool(loop_modules)

    kept = [l.strip() for l in output.splitlines()
            if l.strip() and _YOSYS_KEEP.search(l)]

    cell_count = 0
    for line in output.splitlines():
        if "Number of cells" in line:
            m = re.search(r"Number of cells:\s*(\d+)", line)
            if m:
                cell_count = int(m.group(1))
            if line.strip() not in kept:
                kept.append(line.strip())
            break

    latch_lines = [l for l in output.splitlines() if detect_yosys_latches(l)]

    return "\n".join(kept) if kept else "(no synthesis warnings)", \
           has_latch, latch_lines[:5], cell_count, has_loop, loop_modules


# ── LAYER 3: IVERILOG + VVP ───────────────────────────────────────────────────
def run_iverilog_sim(iter_dir, module_name, *, benchmark):
    """BUG #2 FIX carried over (2026-08-21 on the Windows/WSL original,
    ported here 2026-08-22): vvp must run with its working directory set
    to iter_dir, or any testbench doing relative-path file I/O
    ($readmemh("data.dat", ...) etc.) can never resolve its data file --
    100% reproducible whenever a design compiles, and exactly what zeroed
    out alu/calendar/signal_generator/multi_booth_8bit in RTLLM before
    this was diagnosed and fixed.

    On native Linux this is SIMPLER than the WSL original, not just
    ported: subprocess.run(cwd=iter_dir) directly sets the CHILD
    PROCESS's own working directory here, with no launcher-indirection
    problem to work around (see this file's module docstring) -- no
    `bash -lc "cd ... && vvp ..."` trick needed.

    `benchmark` is mandatory (keyword-only, no default) -- BUG #3 FIX
    (2026-08-24), see this file's module docstring and pass_detection.py.
    Returns (success: bool, feedback: str, outcome: "PASS"|"FAIL"|
    "UNKNOWN") -- same 3-tuple contract as the Windows/WSL original after
    its own Bug #3 fix."""
    vvp_out = os.path.join(iter_dir, "sim.vvp")
    v_files = [f for f in sorted(os.listdir(iter_dir)) if f.endswith(".v")]

    try:
        comp = subprocess.run(
            ["timeout", "20", "iverilog", "-o", "sim.vvp"] + v_files,
            cwd=iter_dir, capture_output=True, text=True, encoding="utf-8", timeout=25)
    except subprocess.TimeoutExpired:
        with open(os.path.join(iter_dir, "sim_log.txt"), "w", encoding="utf-8") as f:
            f.write("--- COMPILATION ---\n[TIMEOUT: iverilog did not finish in 20s]\n")
        return False, "COMPILATION ERROR:\n[TIMEOUT: iverilog did not finish in 20s]", "FAIL"

    with open(os.path.join(iter_dir, "sim_log.txt"), "w", encoding="utf-8") as f:
        f.write(f"--- COMPILATION ---\n{comp.stderr}\n")

    if comp.returncode != 0:
        err     = strip_paths(comp.stderr)
        preview = "\n".join(err.strip().splitlines()[:10])
        print("  iverilog:\n    " + preview.replace("\n", "\n    "))
        return False, f"COMPILATION ERROR:\n{err}", "FAIL"

    try:
        sim = subprocess.run(
            ["timeout", "30", "vvp", "sim.vvp"],
            cwd=iter_dir, capture_output=True, text=True, encoding="utf-8", timeout=35)
    except subprocess.TimeoutExpired:
        with open(os.path.join(iter_dir, "sim_log.txt"), "a", encoding="utf-8") as f:
            f.write("\n--- SIMULATION ---\n[TIMEOUT: vvp did not finish in 30s — likely missing $finish]\n")
        return False, "SIMULATION FAILED:\n[TIMEOUT: vvp did not finish in 30s — likely missing $finish]", "FAIL"
    output = sim.stdout + sim.stderr

    with open(os.path.join(iter_dir, "sim_log.txt"), "a", encoding="utf-8") as f:
        f.write(f"\n--- SIMULATION ---\n{output}\n")

    # Bug #3 FIX (2026-08-24): see this file's module docstring and
    # pass_detection.py. UNKNOWN reports as failure to the caller (same
    # as before this fix) but is returned distinctly so it's visible in
    # run data instead of silently indistinguishable from a real FAIL.
    outcome = detect_outcome(output, benchmark)
    if outcome != "PASS":
        preview = "\n".join(output.strip().splitlines()[:8])
        tag = "UNKNOWN OUTCOME" if outcome == "UNKNOWN" else "sim"
        print(f"  {tag}:\n    " + preview.replace("\n", "\n    "))
        return False, f"SIMULATION FAILED:\n{output}", outcome

    return True, output, outcome


# ── ERROR CLASSIFIER ──────────────────────────────────────────────────────────
def classify_error(feedback):
    fb = feedback.lower()
    if "compilation error" in fb:
        if "not a valid l-value" in fb or "continuous" in fb:
            return "reg_wire_mismatch"
        if "already declared" in fb:   return "duplicate_module"
        if "unknown module" in fb:     return "missing_module"
        if ("syntax error" in fb or "malformed" in fb
                or "incomprehensible" in fb):  return "syntax_error"
        if "systemverilog" in fb:      return "systemverilog_syntax"
        if "is not a port" in fb:      return "port_mismatch"
        if "sorry:" in fb:             return "unsupported_construct"
        return "compile_other"
    if "simulation failed" in fb:
        return "logic_error" if "fail" in fb else "sim_other"
    return "sim_other"


# ── FEEDBACK BUILDERS ─────────────────────────────────────────────────────────
_BASE_HINTS = {
    "reg_wire_mismatch":    "\nHINT: Use 'wire' for assign/submodule outputs; 'reg' for always-block only.",
    "syntax_error":         "\nHINT: Multiple assignments per case branch need begin...end. No SystemVerilog.",
    "systemverilog_syntax": "\nHINT: Use wire/reg not logic. Use 1'b1/1'b0 not '1/'0. Use always@(*) not always_comb.",
    "logic_error":          "\nHINT: Compiles but wrong output. Read each FAIL line — trace inputs to expected vs actual.",
    "duplicate_module":     "\nHINT: Delete the redefined module. Write only the requested top-level module.",
    "port_mismatch":        "\nHINT: Port names must match the specification exactly.",
    "sim_other":            "\nHINT: No PASS/FAIL printed — check all output ports are driven.",
}

def _build_baseline_feedback(iverilog_fb, err_type):
    """Condition A: iverilog output + type hint only. Replicates AutoChip."""
    hint = _BASE_HINTS.get(err_type, "")
    return (
        "The Verilog code failed. Fix ALL errors and return the COMPLETE "
        "module inside ```verilog ... ```. ASCII only.\n\n"
        f"Error output:\n{iverilog_fb}{hint}"
    )

def _build_raw_adv_feedback(verilator_out, yosys_report, latch_lines,
                              iverilog_fb, err_type, has_latch, cell_count,
                              has_loop=False, loop_modules=None):
    loop_modules = loop_modules or []
    hint = _BASE_HINTS.get(err_type, "")
    cell_ctx = f"\n  Yosys cells: {cell_count}" if cell_count else ""

    latch_raw = ""
    if has_latch:
        raw_lines = "\n".join(f"  {l.strip()}" for l in latch_lines)
        latch_raw = f"\n\nYosys raw latch output:\n{raw_lines}"

    loop_raw = ""
    if has_loop:
        loop_raw = (
            "\n\nYosys raw combinational-loop warning: found logic loop in "
            f"module(s) {', '.join(loop_modules)}"
        )

    return (
        "The Verilog code failed. Return the COMPLETE corrected module "
        "inside ```verilog ... ```. ASCII only.\n\n"
        "=== VERILATOR LINT ===\n"
        f"{verilator_out}\n\n"
        "=== IVERILOG + VVP ===\n"
        f"{iverilog_fb}{hint}\n\n"
        "=== YOSYS SYNTHESIS ==={cell_ctx}\n"
        f"{yosys_report}{latch_raw}{loop_raw}"
    ).replace("{cell_ctx}", cell_ctx)

def _build_sem_adv_feedback(verilator_out, yosys_report, latch_lines,
                              iverilog_fb, err_type, has_latch, cell_count,
                              interp_text, interp_codes,
                              has_loop=False, loop_modules=None, v_path=None):
    loop_modules = loop_modules or []
    hint = _BASE_HINTS.get(err_type, "")
    cell_ctx = f"\n  Yosys cells: {cell_count}" if cell_count else ""

    if interp_text:
        verilator_section = (
            f"Raw Verilator output:\n{verilator_out}\n\n"
            f"--- Semantic Interpreter Directive ---\n{interp_text}"
        )
    else:
        verilator_section = verilator_out

    yosys_interp = interpret_yosys_latches(latch_lines, v_path) if has_latch else ""
    loop_interp  = interpret_comb_loop(yosys_report) if has_loop else None

    if has_latch:
        yosys_section = (
            f"Yosys cells: {cell_count} (includes $_DLATCH_ latch cells)\n"
            f"Raw Yosys output:\n{yosys_report}"
            f"{yosys_interp}"
        )
    elif has_loop and loop_interp:
        yosys_section = (
            f"Yosys cells: {cell_count}\n"
            f"Raw Yosys output:\n{yosys_report}\n\n"
            f"--- Semantic Interpreter Directive ---\n{loop_interp}"
        )
    else:
        yosys_section = f"Yosys: {cell_count} cells, no latches, no combinational loops.\n{yosys_report}"

    return (
        "The Verilog code failed. Read the SEMANTIC DIRECTIVES carefully — they\n"
        "give you the exact fix. Return the COMPLETE module inside "
        "```verilog ... ```. ASCII only.\n\n"
        "=== LAYER 1: VERILATOR LINT (with semantic interpretation) ===\n"
        f"{verilator_section}\n\n"
        "=== LAYER 2: IVERILOG + VVP ===\n"
        f"{iverilog_fb}{hint}\n\n"
        "=== LAYER 3: YOSYS SYNTHESIS (with semantic interpretation) ===\n"
        f"{yosys_section}"
    )

_REWRITE_PROMPT = (
    "Your previous {n} attempts all failed with '{err_type}'.\n"
    "DISCARD all prior code. Write a BRAND-NEW Verilog-2001 module from scratch.\n\n"
    "Rules for this rewrite:\n"
    "  1. Every case branch with multiple assignments: begin...end\n"
    "  2. Every case statement: include a default branch\n"
    "  3. Every if without else: add else with safe default values\n"
    "  4. Sensitivity: use @(*)\n"
    "  5. No SystemVerilog\n\n"
    "ORIGINAL SPECIFICATION:\n{spec}\n\n"
    "Return ONLY the module inside ```verilog ... ```. ASCII only."
)


# ── MAIN LOOP ──────────────────────────────────────────────────────────────────
def run_one_condition(spec, module_name, model, condition, dependencies=None, *, benchmark):
    """
    Run one condition (baseline | raw_adv | sem_adv) for one module.
    condition controls which feedback builder is used.
    Returns metrics dict.

    BUG #1 FIX carried over (2026-08-21 on the Windows/WSL original,
    ported here unchanged): the code-extraction fallback strips a
    leading unclosed ```verilog fence marker before treating the
    response as raw text -- see the comment at the fallback branch
    below. Confirmed recurring on both v20 and RTLLM real responses.

    `benchmark` is mandatory (keyword-only, no default) -- BUG #3 FIX
    (2026-08-24), forwarded to run_iverilog_sim()'s detect_outcome() call.
    See pass_detection.py for why there is no default.
    """
    if dependencies is None:
        dependencies = []

    tb_path = os.path.join(TESTBENCH_DIR, f"{module_name}_tb.v")
    if not os.path.exists(tb_path):
        print(f"  ERROR: testbench not found: {tb_path}")
        return None

    safe_model  = model.replace(":", "_").replace(".", "")
    project_dir = os.path.join(RESULTS_DIR, safe_model, condition, module_name)
    os.makedirs(project_dir, exist_ok=True)

    cond_label = {
        "baseline": "BASELINE  (iverilog only)",
        "raw_adv":  "RAW ADV   (Verilator+Yosys, no interpretation)",
        "sem_adv":  "SEM ADV   (Verilator+Yosys+semantic interpreter)",
    }[condition]

    use_tools  = condition in ("raw_adv", "sem_adv")
    use_interp = condition == "sem_adv"

    print(f"\n{'='*68}")
    print(f"  {module_name}  |  {model}")
    print(f"  {cond_label}")
    print(f"{'='*68}")

    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user",   "content": spec},
    ]

    metrics = {
        "module": module_name, "model": model, "condition": condition,
        "benchmark": benchmark,
        "pass": False, "iterations_to_pass": None,
        "time_to_pass_sec": None, "total_time_sec": None,
        "total_iterations": MAX_RETRIES,
        "compile_errors": 0, "sim_errors": 0,
        "latch_warnings": 0, "loop_warnings": 0, "verilator_catches": 0,
        "semantic_fired": 0,
        "verilator_codes_seen": [],
        "total_prompt_tokens": 0, "total_completion_tokens": 0, "total_tokens": 0,
        "error_types": [], "per_iter_detail": [],
        # Bug #3 class fix: count of iterations where detect_outcome()
        # returned UNKNOWN -- surfaced here rather than silently folded
        # into sim_errors. See pass_detection.py.
        "unknown_outcomes": 0,
    }

    t_start         = time.time()
    consecutive     = 0
    last_err        = None
    prev_cells      = None

    for i in range(MAX_RETRIES):
        iter_dir = os.path.join(project_dir, f"iter_{i+1}")
        os.makedirs(iter_dir, exist_ok=True)
        print(f"\n  Iteration {i+1}/{MAX_RETRIES}")

        with open(os.path.join(iter_dir, "feedback.txt"), "w", encoding="utf-8") as f:
            f.write(messages[-1]["content"])

        t_llm = time.time()
        try:
            llm_out, pt, ct = call_llm(model, messages)
        except Exception as e:
            print(f"  LLM Error: {e}"); break
        llm_t = time.time() - t_llm
        print(f"  LLM {llm_t:.1f}s  [prompt={pt} completion={ct}]")

        metrics["total_prompt_tokens"]     += pt
        metrics["total_completion_tokens"] += ct
        metrics["total_tokens"]            += pt + ct

        with open(os.path.join(iter_dir, "llm_response.txt"), "w", encoding="utf-8") as f:
            f.write(llm_out)

        match = re.search(r"```(?:verilog)?(.*?)```", llm_out, re.DOTALL)
        if match:
            code = match.group(1).strip()
        else:
            # BUG #1 FIX (2026-08-21): strip a leading unclosed fence
            # marker before falling back to the raw text -- see this
            # function's docstring.
            code = re.sub(r"^```(?:verilog)?\s*\n?", "", llm_out.strip())
        code = sanitize_ascii(code)

        v_path = os.path.join(iter_dir, f"{module_name}.v")
        with open(v_path, "w", encoding="utf-8") as f:
            f.write(code)

        for dep in dependencies:
            if os.path.exists(dep): shutil.copy(dep, iter_dir)
        shutil.copy(tb_path, iter_dir)

        verilator_out  = "(baseline: skipped)"
        verilator_flag = False
        interp_text    = ""
        interp_codes   = []

        if use_tools:
            verilator_out, verilator_flag = run_verilator_lint(v_path)
            if verilator_flag:
                metrics["verilator_catches"] += 1
                if use_interp:
                    interp_text, interp_codes = interpret_verilator(verilator_out, v_path)
                    if interp_text:
                        metrics["semantic_fired"] += 1
                        metrics["verilator_codes_seen"].extend(interp_codes)
                codes_str = ",".join(interp_codes) if interp_codes else "?"
                if use_interp and interp_text:
                    print(f"  Verilator [{codes_str}] -> INTERPRETED")
                else:
                    print(f"  Verilator [{codes_str}] raw")
            else:
                print("  Verilator: clean")

        success, iverilog_fb, sim_outcome = run_iverilog_sim(
            iter_dir, module_name, benchmark=benchmark)
        if sim_outcome == "UNKNOWN":
            metrics["unknown_outcomes"] += 1
            print(f"  ** UNKNOWN OUTCOME ** (neither a registered pass nor "
                  f"fail pattern matched for benchmark={benchmark!r} -- "
                  f"treated as failure below, but flagged here so it's "
                  f"not silently indistinguishable from a real FAIL)")
        elapsed = time.time() - t_start

        yosys_report = "(baseline: skipped)"
        has_latch    = False
        latch_lines  = []
        cell_count   = 0
        cell_delta   = None
        has_loop     = False
        loop_modules = []

        if use_tools and "COMPILATION ERROR" not in iverilog_fb:
            yosys_report, has_latch, latch_lines, cell_count, has_loop, loop_modules = \
                run_yosys_check(v_path, module_name)
            if prev_cells is not None and cell_count > 0:
                cell_delta = cell_count - prev_cells
            prev_cells = cell_count

            if has_latch:
                print(f"  Yosys LATCH: {(latch_lines[0].strip()[:55] if latch_lines else '')} "
                      f"({cell_count} cells)")
                metrics["latch_warnings"] += 1
                if use_interp:
                    metrics["semantic_fired"] += 1
            elif has_loop:
                print(f"  Yosys LOOP: module(s) {', '.join(loop_modules)} ({cell_count} cells)")
                metrics["loop_warnings"] += 1
                if use_interp:
                    metrics["semantic_fired"] += 1
            else:
                delta_str = f" delta{cell_delta:+d}" if cell_delta is not None else ""
                print(f"  Yosys: clean ({cell_count} cells{delta_str})")

        iter_detail = {
            "iter": i + 1, "prompt_tokens": pt, "completion_tokens": ct,
            "llm_time_sec": round(llm_t, 2),
            "verilator_flag": verilator_flag, "interp_codes": interp_codes,
            "semantic_fired": bool(interp_text) or (use_interp and (has_latch or has_loop)),
            "yosys_latch": has_latch, "yosys_loop": has_loop, "yosys_cells": cell_count,
            "yosys_delta": cell_delta,
            "result": "PASS" if success else "FAIL",
            "sim_outcome": sim_outcome,  # "PASS" | "FAIL" | "UNKNOWN" -- detect_outcome()'s actual verdict
            "err_type": None,
        }

        if success:
            print(f"  PASSED iteration {i+1}  ({elapsed:.1f}s total)")
            iter_detail["err_type"] = "PASS"
            metrics["per_iter_detail"].append(iter_detail)
            metrics.update({
                "pass": True, "iterations_to_pass": i + 1,
                "time_to_pass_sec": round(elapsed, 2),
                "total_time_sec": round(elapsed, 2),
                "total_iterations": i + 1,
            })
            break

        err_type = classify_error(iverilog_fb)
        iter_detail["err_type"] = err_type
        metrics["per_iter_detail"].append(iter_detail)

        if "COMPILATION" in iverilog_fb: metrics["compile_errors"] += 1
        else:                            metrics["sim_errors"]     += 1
        metrics["error_types"].append(err_type)
        print(f"  FAIL: {err_type}")

        if err_type == last_err: consecutive += 1
        else:                    consecutive = 1; last_err = err_type

        messages.append({"role": "assistant", "content": llm_out})

        if consecutive >= STUCK_THRESHOLD:
            print(f"  STUCK '{err_type}' x{consecutive} - rewrite injected")
            messages.append({"role": "user", "content": _REWRITE_PROMPT.format(
                n=consecutive, err_type=err_type, spec=spec)})
            consecutive = 0
        else:
            if condition == "baseline":
                fb = _build_baseline_feedback(iverilog_fb, err_type)
            elif condition == "raw_adv":
                fb = _build_raw_adv_feedback(verilator_out, yosys_report, latch_lines,
                                              iverilog_fb, err_type, has_latch, cell_count,
                                              has_loop, loop_modules)
            else:  # sem_adv
                fb = _build_sem_adv_feedback(verilator_out, yosys_report, latch_lines,
                                              iverilog_fb, err_type, has_latch, cell_count,
                                              interp_text, interp_codes,
                                              has_loop, loop_modules, v_path)
            messages.append({"role": "user", "content": fb})

    if metrics["total_time_sec"] is None:
        metrics["total_time_sec"] = round(time.time() - t_start, 2)

    with open(os.path.join(project_dir, "metrics.json"), "w", encoding="utf-8") as f:
        json.dump(metrics, f, indent=2)

    if not metrics["pass"]:
        print(f"  FAILED all {MAX_RETRIES} iters "
              f"({metrics['total_time_sec']:.1f}s | tokens={metrics['total_tokens']})")
    return metrics
