"""
stitch_runner.py - STITCH three-condition experiment runner.

Runs a module through the repair loop under three feedback conditions, which
is the comparison the project's central claim rests on:

  baseline : iverilog + vvp only (replicates the AutoChip baseline)
  raw_adv  : Verilator + iverilog + Yosys, raw tool output, no interpretation
  sem_adv  : the same three tools plus the semantic interpreter

Comparing raw_adv against sem_adv separates "having the tools" from
"interpreting the tools". Comparing either against baseline gives the
end-to-end effect.

PROVENANCE: derived from the runner used for the MLCAD conference paper
(archived at github.com/aathirasun/HDLLLM). The loop logic, prompt
construction, code-extraction regex and feedback builders are unchanged from
that version, so results remain directly comparable. What changed: the
interpreter import now resolves to src/interpreter/, Yosys is invoked with a
quoted path, latch and combinational-loop classification are delegated to the
interpreter rather than duplicated here, and --testbench-dir / --modules were
added. See CHANGELOG.md.

Results are written to results_stitch/<model>/<condition>/<module>/ relative
to the current working directory; run from the directory you want output in.

Usage:
  python src/runner/stitch_runner.py --model gemma3:4b --condition all       --modules decoder_3to8 --testbench-dir illustrations/proven
"""

import os, subprocess, re, shutil, sys, json, time, argparse
from collections import Counter
from openai import OpenAI

# The semantic interpreter is shared verbatim with the HPC port
# (HPC/stitch_runner_hpc.py) via stitch_interpreter.py — this runner's copy
# now lives at STITCH_v3/interpreter/stitch_interpreter.py, one directory up
# from this file. sys.path insert only — the import statement below is
# character-for-character identical to the original.
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "interpreter"))
from stitch_interpreter import (
    _VERILATOR_INTERP, _LITERAL_FRAGMENT_RE, _extract_signal_name,
    _PORT_DECL_RE, _INTERNAL_DECL_RE, _decl_names,
    _classify_undriven_signal, _undriven_message,
    interpret_verilator, interpret_yosys_latches,
    # Added 2026-08-18: this runner used to maintain its own local, separately
    # buggy Yosys-latch substring check (_LATCH_KEYWORDS) instead of calling
    # the interpreter — that duplication is exactly why the decoder_verify
    # run got a false "LATCH INFERRED" directive even after the interpreter's
    # own detect_yosys_latches() had already been fixed to reject that case.
    # One source of truth now: detect_yosys_latches/detect_comb_loops are
    # imported directly, not reimplemented. (has_latches() the *function* is
    # deliberately NOT imported — bool(detect_yosys_latches(x)) is identical
    # and this avoids a name collision with the `has_latch`-shaped local
    # variables already used throughout this file.)
    detect_yosys_latches, detect_comb_loops, interpret_comb_loop,
)

# ── CONFIG ────────────────────────────────────────────────────────────────────
MAX_RETRIES      = 6
STUCK_THRESHOLD  = 2
TESTBENCH_DIR    = "testbenches_v2"
RESULTS_DIR      = "results_stitch"
WSL_PREFIX       = ["wsl"]

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

# Identical system prompt for ALL three conditions — controlled variable is
# feedback quality only, not system prompt content.
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
def win_to_wsl(win_path):
    p = os.path.abspath(win_path).replace("\\", "/")
    if len(p) > 1 and p[1] == ":":
        p = f"/mnt/{p[0].lower()}" + p[2:]
    return p

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
    """Returns (text, prompt_tokens, completion_tokens)."""
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
    """Returns (warnings_str, had_meaningful_warnings: bool)."""
    wsl_path = win_to_wsl(v_file)
    # `timeout` runs INSIDE the WSL VM so the kill actually reaches the process —
    # subprocess.run(timeout=...) alone only kills the Windows-side `wsl.exe`
    # launcher, which can leave the real verilator/yosys process hung forever.
    cmd = WSL_PREFIX + ["timeout", "18", "verilator", "--lint-only", "-Wall",
                        "--bbox-unsup"] + VERILATOR_SUPPRESS + [wsl_path]
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


# ── SEMANTIC INTERPRETER (STITCH core contribution) ───────────────────────────
# _VERILATOR_INTERP, interpret_verilator, interpret_yosys_latches, and the
# UNDRIVEN-disambiguation/signal-extraction helpers now live in
# stitch_interpreter.py (imported above) — shared with the HPC port so the
# two runners' interpreter behavior can't silently drift apart.

# ── LAYER 2: YOSYS ────────────────────────────────────────────────────────────
# _LATCH_KEYWORDS deleted 2026-08-18 — was a local, duplicate, independently
# buggy substring check (case-insensitive, matched "No latch inferred" and
# the PROC_DLATCH pass banner as false positives). Classification now comes
# exclusively from interpreter.stitch_interpreter's detect_yosys_latches()/
# detect_comb_loops() (imported above) — one source of truth, 27 tests
# behind it including regressions built from this exact bug. _YOSYS_KEEP
# below is unrelated to classification (it only trims what raw text gets
# shown to the model) and is unchanged.

_YOSYS_KEEP = re.compile(
    r"(Warning|warning|Error|error|Latch|latch|inferred|proc_dlatch|"
    r"continuous assignment|Number of cells|\$_DLATCH|\$dlatch|\$dff)",
    re.IGNORECASE,
)

def run_yosys_check(v_file, module_name):
    """Returns (report_str, has_latch, latch_lines, cell_count, has_loop, loop_modules)."""
    wsl_path = win_to_wsl(v_file)
    # FIX 2026-08-18: wsl_path must be quoted inside the -p script string.
    # Every path in this project has spaces (D:\BITS Files\Year 3\...\LLM_Verilog
    # Project\AgenticAI\...) and Yosys's own -p parser tokenizes read_verilog's
    # argument on whitespace — unquoted, it only ever read "/mnt/d/BITS" and
    # failed with "Can't open input file". Confirmed this was silently failing
    # on every raw_adv/sem_adv iteration in this project's history (has_latches
    # was always False as a direct result — not a Yosys-version difference, as
    # earlier speculated). Verified fix via direct subprocess.run reproduction
    # before applying — see docs/illustrations/pending/README.md.
    script   = f'read_verilog "{wsl_path}"; synth -top {module_name}; stat'
    # See run_verilator_lint — `timeout` runs inside WSL so the kill lands on
    # the actual yosys process, not just the wsl.exe launcher on the Windows side.
    cmd      = WSL_PREFIX + ["timeout", "35", "yosys", "-p", script]
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=45)
    except (subprocess.TimeoutExpired, FileNotFoundError) as e:
        return f"[YOSYS ERROR: {e}]", False, [], 0, False, []

    output = result.stdout + result.stderr

    # Single source of truth for classification (see module-level comment above).
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

    # Genuine latch lines only — per-line application of the same interpreter
    # function, so a line only survives if it independently passes the same
    # banner/negative rejection logic as the whole-output classification above.
    latch_lines = [l for l in output.splitlines() if detect_yosys_latches(l)]

    return "\n".join(kept) if kept else "(no synthesis warnings)", \
           has_latch, latch_lines[:5], cell_count, has_loop, loop_modules


# ── LAYER 3: IVERILOG + VVP ───────────────────────────────────────────────────
def run_iverilog_sim(iter_dir, module_name):
    vvp_out     = os.path.join(iter_dir, "sim.vvp")
    v_files_wsl = [win_to_wsl(os.path.join(iter_dir, f))
                   for f in sorted(os.listdir(iter_dir)) if f.endswith(".v")]
    vvp_wsl     = win_to_wsl(vvp_out)

    # Neither of these had ANY timeout before — a hung compile or a testbench
    # missing $finish could stall the whole run forever. Same WSL-side `timeout`
    # fix as verilator/yosys, so the kill actually reaches the process.
    try:
        comp = subprocess.run(WSL_PREFIX + ["timeout", "20", "iverilog", "-o", vvp_wsl] + v_files_wsl,
                              capture_output=True, text=True, encoding="utf-8", timeout=25)
    except subprocess.TimeoutExpired:
        with open(os.path.join(iter_dir, "sim_log.txt"), "w", encoding="utf-8") as f:
            f.write("--- COMPILATION ---\n[TIMEOUT: iverilog did not finish in 20s]\n")
        return False, "COMPILATION ERROR:\n[TIMEOUT: iverilog did not finish in 20s]"

    with open(os.path.join(iter_dir, "sim_log.txt"), "w", encoding="utf-8") as f:
        f.write(f"--- COMPILATION ---\n{comp.stderr}\n")

    if comp.returncode != 0:
        err     = strip_paths(comp.stderr)
        preview = "\n".join(err.strip().splitlines()[:10])
        print("  iverilog:\n    " + preview.replace("\n", "\n    "))
        return False, f"COMPILATION ERROR:\n{err}"

    try:
        sim = subprocess.run(WSL_PREFIX + ["timeout", "30", "vvp", vvp_wsl],
                             capture_output=True, text=True, encoding="utf-8", timeout=35)
    except subprocess.TimeoutExpired:
        with open(os.path.join(iter_dir, "sim_log.txt"), "a", encoding="utf-8") as f:
            f.write("\n--- SIMULATION ---\n[TIMEOUT: vvp did not finish in 30s — likely missing $finish]\n")
        return False, "SIMULATION FAILED:\n[TIMEOUT: vvp did not finish in 30s — likely missing $finish]"
    output = sim.stdout + sim.stderr

    with open(os.path.join(iter_dir, "sim_log.txt"), "a", encoding="utf-8") as f:
        f.write(f"\n--- SIMULATION ---\n{output}\n")

    if "FAIL" in output or (
            "ALL TESTS PASSED" not in output and "PASS" not in output):
        preview = "\n".join(output.strip().splitlines()[:8])
        print("  sim:\n    " + preview.replace("\n", "\n    "))
        return False, f"SIMULATION FAILED:\n{output}"

    return True, output


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
    """
    Condition B: All three tool outputs passed through RAW (no interpretation).
    This isolates the effect of tool presence from interpretation quality.
    Comparison with sem_adv shows that raw output alone is insufficient
    for weaker models.
    """
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
                              has_loop=False, loop_modules=None):
    """
    Condition C: All three tools + semantic interpreter.
    The interpreter translates raw warning codes into targeted fix directives.
    This is the STITCH contribution — directives resolve weaker-model failures
    that raw output cannot.
    """
    loop_modules = loop_modules or []
    hint = _BASE_HINTS.get(err_type, "")
    cell_ctx = f"\n  Yosys cells: {cell_count}" if cell_count else ""

    # Verilator layer: raw + interpreted (when applicable)
    if interp_text:
        verilator_section = (
            f"Raw Verilator output:\n{verilator_out}\n\n"
            f"--- Semantic Interpreter Directive ---\n{interp_text}"
        )
    else:
        verilator_section = verilator_out

    # Yosys layer: raw + interpreted (when latches or a combinational loop
    # are genuinely found — added 2026-08-18, this is the interpreter's
    # already-existing interpret_comb_loop() actually getting called for the
    # first time; it had a working handler with no wiring into this runner
    # before today, so priority_chain_comb-shaped modules never got a
    # converted directive despite the interpreter supporting it).
    yosys_interp = interpret_yosys_latches(latch_lines) if has_latch else ""
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
def run_one_condition(spec, module_name, model, condition, dependencies=None):
    """
    Run one condition (baseline | raw_adv | sem_adv) for one module.
    condition controls which feedback builder is used.
    Returns metrics dict.
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
        "pass": False, "iterations_to_pass": None,
        "time_to_pass_sec": None, "total_time_sec": None,
        "total_iterations": MAX_RETRIES,
        "compile_errors": 0, "sim_errors": 0,
        "latch_warnings": 0, "loop_warnings": 0, "verilator_catches": 0,
        "semantic_fired": 0,          # key metric: how many iters interpreter fired
        "verilator_codes_seen": [],   # which codes triggered interpretation
        "total_prompt_tokens": 0, "total_completion_tokens": 0, "total_tokens": 0,
        "error_types": [], "per_iter_detail": [],
    }

    t_start         = time.time()
    consecutive     = 0
    last_err        = None
    prev_cells      = None

    for i in range(MAX_RETRIES):
        iter_dir = os.path.join(project_dir, f"iter_{i+1}")
        os.makedirs(iter_dir, exist_ok=True)
        print(f"\n  Iteration {i+1}/{MAX_RETRIES}")

        # Persist the exact directive text driving THIS iteration — previously
        # only lived in the in-memory `messages` list. messages[-1] is always
        # what's about to be sent: the initial spec for iteration 1, or
        # whatever _build_*_feedback/_REWRITE_PROMPT produced at the end of
        # the previous iteration for iterations 2-6.
        with open(os.path.join(iter_dir, "feedback.txt"), "w", encoding="utf-8") as f:
            f.write(messages[-1]["content"])

        # LLM call
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
        code  = sanitize_ascii(match.group(1).strip() if match else llm_out.strip())

        v_path = os.path.join(iter_dir, f"{module_name}.v")
        with open(v_path, "w", encoding="utf-8") as f:
            f.write(code)

        for dep in dependencies:
            if os.path.exists(dep): shutil.copy(dep, iter_dir)
        shutil.copy(tb_path, iter_dir)

        # Layer 1: Verilator (tools conditions only)
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

        # Layer 2: iverilog + vvp
        success, iverilog_fb = run_iverilog_sim(iter_dir, module_name)
        elapsed = time.time() - t_start

        # Layer 3: Yosys (tools conditions, compile success only)
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
                # FIX 2026-08-18: semantic_fired previously only counted the
                # Verilator-path interpretation (interpret_verilator's
                # interp_text). The Yosys path (interpret_yosys_latches/
                # interpret_comb_loop, wired into _build_sem_adv_feedback in
                # Task 2) genuinely fires directives too under sem_adv but was
                # never counted here — found while reading this exact run's
                # own semantic_fired=1 for priority_chain_comb and realizing
                # it was attributable to an unrelated, later UNUSEDSIGNAL hit,
                # not the genuine loop directive from iteration 1.
                if use_interp:
                    metrics["semantic_fired"] += 1
            elif has_loop:
                print(f"  Yosys LOOP: module(s) {', '.join(loop_modules)} ({cell_count} cells)")
                metrics["loop_warnings"] += 1
                if use_interp:
                    metrics["semantic_fired"] += 1
            else:
                # FIX 2026-08-18: was f" Δ{cell_delta:+d}" — crashed with
                # UnicodeEncodeError under cp1252 console encoding (Windows
                # default unless explicitly set to UTF-8). Never hit before
                # today because cell_count was always 0 pre-Yosys-path-fix,
                # so this branch never executed. ASCII-safe now, no console-
                # encoding dependency either way.
                delta_str = f" delta{cell_delta:+d}" if cell_delta is not None else ""
                print(f"  Yosys: clean ({cell_count} cells{delta_str})")

        # Record iteration
        iter_detail = {
            "iter": i + 1, "prompt_tokens": pt, "completion_tokens": ct,
            "llm_time_sec": round(llm_t, 2),
            "verilator_flag": verilator_flag, "interp_codes": interp_codes,
            # FIX 2026-08-18: same undercount as metrics["semantic_fired"]
            # above — this per-iteration field must reflect Yosys-sourced
            # firing too, not just the Verilator path.
            "semantic_fired": bool(interp_text) or (use_interp and (has_latch or has_loop)),
            "yosys_latch": has_latch, "yosys_loop": has_loop, "yosys_cells": cell_count,
            "yosys_delta": cell_delta,
            "result": "PASS" if success else "FAIL",
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
                                              has_loop, loop_modules)
            messages.append({"role": "user", "content": fb})

    if metrics["total_time_sec"] is None:
        metrics["total_time_sec"] = round(time.time() - t_start, 2)

    with open(os.path.join(project_dir, "metrics.json"), "w", encoding="utf-8") as f:
        json.dump(metrics, f, indent=2)

    if not metrics["pass"]:
        print(f"  FAILED all {MAX_RETRIES} iters "
              f"({metrics['total_time_sec']:.1f}s | tokens={metrics['total_tokens']})")
    return metrics


# ── THREE-COLUMN COMPARISON TABLE ─────────────────────────────────────────────
def print_stitch_table(all_results, model):
    """
    Prints the three-condition comparison table for the paper.
    Columns: Module | Category | Baseline | Raw Advanced | Semantic Advanced
    This is Table 7 in the STITCH paper.
    """
    CONDITIONS = ["baseline", "raw_adv", "sem_adv"]
    LABELS     = ["Baseline", "Raw Adv", "Sem Adv"]
    W = 90

    print(f"\n{'='*W}")
    print(f"  STITCH TABLE - Three-Condition Comparison  |  Model: {model}")
    print(f"  (Table 7 in paper)")
    print(f"{'='*W}")
    print(f"  {'Module':<22} {'Cat':<12} {'Baseline':^14} {'Raw Adv':^14} {'Sem Adv':^14} "
          f"{'dB->S':>5} {'SemanFired':>10}")
    print(f"  {'':22} {'':12} {'P|Iters':^14} {'P|Iters':^14} {'P|Iters':^14}")
    print(f"  {'-'*88}")

    # Group results by condition
    cond_map = {c: {} for c in CONDITIONS}
    for m in all_results:
        cond_map[m["condition"]][m["module"]] = m

    grand = {c: {"pass": 0, "iters": 0, "tokens": 0} for c in CONDITIONS}
    grand["sem_adv"]["sem_fired"] = 0

    for mod, cfg in BENCHMARK.items():
        row = {}
        for c in CONDITIONS:
            row[c] = cond_map[c].get(mod)
        if not any(row.values()):
            continue

        cat = cfg["category"].replace("_", " ")
        cells = []
        for c in CONDITIONS:
            m = row[c]
            if m:
                p = "PASS" if m["pass"] else "FAIL"
                it = m["iterations_to_pass"] or MAX_RETRIES
                grand[c]["pass"]   += 1 if m["pass"] else 0
                grand[c]["iters"]  += it
                grand[c]["tokens"] += m.get("total_tokens", 0)
                cells.append(f"{p}|{it}")
            else:
                cells.append("n/a")

        # Delta: baseline iters - sem_adv iters (positive = sem_adv needed fewer)
        delta_str = ""
        if row["baseline"] and row["sem_adv"]:
            b_it = row["baseline"]["iterations_to_pass"] or MAX_RETRIES
            s_it = row["sem_adv"]["iterations_to_pass"]  or MAX_RETRIES
            d    = b_it - s_it
            delta_str = f"+{d}" if d > 0 else str(d)

        sf = row["sem_adv"].get("semantic_fired", 0) if row["sem_adv"] else 0
        grand["sem_adv"]["sem_fired"] = grand["sem_adv"].get("sem_fired", 0) + sf

        print(f"  {mod:<22} {cat:<12} {cells[0]:^14} {cells[1]:^14} {cells[2]:^14} "
              f"{delta_str:>5} {sf:>10}")

    n = len(BENCHMARK)
    print(f"\n  {'Pass rate':<34} "
          f"{grand['baseline']['pass']}/{n}".center(14) +
          f" {grand['raw_adv']['pass']}/{n}".center(14) +
          f" {grand['sem_adv']['pass']}/{n}".center(14))
    print(f"  {'Total iterations':<34} "
          f"{grand['baseline']['iters']}".center(14) +
          f" {grand['raw_adv']['iters']}".center(14) +
          f" {grand['sem_adv']['iters']}".center(14))
    print(f"  {'Total tokens':<34} "
          f"{grand['baseline']['tokens']}".center(14) +
          f" {grand['raw_adv']['tokens']}".center(14) +
          f" {grand['sem_adv']['tokens']}".center(14))
    print(f"\n  Semantic interpreter fired: {grand['sem_adv'].get('sem_fired',0)} "
          f"iteration(s) across all modules (sem_adv only)")

    # Error transition matrix
    _CODE = {
        "PASS":"PASS","logic_error":"LGIC","syntax_error":"SYNT",
        "systemverilog_syntax":"SV!!","reg_wire_mismatch":"RWMX",
        "compile_other":"COMP","sim_other":"SIMO","duplicate_module":"DUPL",
        "port_mismatch":"PORT","missing_module":"MISS",
        "unsupported_construct":"UNSP", None:"----",
    }
    print(f"\n  Error Transition Matrix:")
    print(f"  {'Module':<22} {'Cond':<8}  " +
          "  ".join(f"I{j+1}" for j in range(MAX_RETRIES)))
    print(f"  {'-'*82}")
    for mod in BENCHMARK:
        for c, label in zip(CONDITIONS, ["base", "raw ", "sem "]):
            m = cond_map[c].get(mod)
            if not m:
                continue
            codes = [_CODE.get(it.get("err_type"), "????")
                     for it in m["per_iter_detail"]]
            codes += ["    "] * (MAX_RETRIES - len(codes))
            print(f"  {mod:<22} {label}      " + "  ".join(codes))
        print()

    print(f"{'='*W}\n")


# ── BENCHMARK ─────────────────────────────────────────────────────────────────
BENCHMARK = {

    "seg7_decoder": {
        "category": "latch_target",
        "spec": (
            "Create a Verilog-2001 module named 'seg7_decoder'.\n"
            "Ports: input [3:0] bcd; output reg [6:0] seg\n"
            "Implement a combinational 7-segment display decoder.\n"
            "Segment bit ordering: seg[6:0] = {g, f, e, d, c, b, a} (1 = segment ON)\n"
            "Use a case statement in a combinational always block.\n"
            "Encodings for BCD digits 0 through 9:\n"
            "  0: 7'b0111111    1: 7'b0000110    2: 7'b1011011\n"
            "  3: 7'b1001111    4: 7'b1100110    5: 7'b1101101\n"
            "  6: 7'b1111101    7: 7'b0000111    8: 7'b1111111\n"
            "  9: 7'b1101111\n"
            "The valid input range is 0-9. Behavior for inputs 10-15 is not\n"
            "specified by the application - implement only the 10 defined cases.\n"
        ),
    },

    "alu_ops": {
        "category": "latch_target",
        "spec": (
            "Create a Verilog-2001 module named 'alu_ops'.\n"
            "Ports: input [7:0] a, b; input [2:0] opcode;\n"
            "       output reg [7:0] result; output reg carry_out, zero\n"
            "Implement a combinational ALU. Use a case statement inside a\n"
            "combinational always block. Every case branch assigns result,\n"
            "carry_out, AND zero - wrap each branch in begin...end.\n"
            "Operations:\n"
            "  3'b000 ADD: {carry_out, result} = a + b; zero = (result==8'd0);\n"
            "  3'b001 SUB: result = a - b; carry_out = (a < b); zero = (result==8'd0);\n"
            "  3'b010 AND: result = a & b; carry_out = 1'b0; zero = (result==8'd0);\n"
            "  3'b011 OR : result = a | b; carry_out = 1'b0; zero = (result==8'd0);\n"
            "  3'b100 XOR: result = a ^ b; carry_out = 1'b0; zero = (result==8'd0);\n"
            "Implement only the five operations listed above.\n"
        ),
    },

    "decoder_3to8": {
        "category": "latch_target",
        "spec": (
            "Create a Verilog-2001 module named 'decoder_3to8'.\n"
            "Ports: input enable; input [2:0] in; output reg [7:0] out\n"
            "Implement a 3-to-8 one-hot decoder with an active-high enable.\n"
            "When enable is asserted, use a case statement to drive the\n"
            "corresponding output bit high and all others low:\n"
            "  in=3'd0 -> out=8'b0000_0001\n"
            "  in=3'd1 -> out=8'b0000_0010\n"
            "  in=3'd2 -> out=8'b0000_0100\n"
            "  in=3'd3 -> out=8'b0000_1000\n"
            "  in=3'd4 -> out=8'b0001_0000\n"
            "  in=3'd5 -> out=8'b0010_0000\n"
            "  in=3'd6 -> out=8'b0100_0000\n"
            "  in=3'd7 -> out=8'b1000_0000\n"
            "All logic is combinational - no clock, no reset.\n"
        ),
    },

    "comb_sensitivity": {
        "category": "verilator_target",
        "spec": (
            "Create a Verilog-2001 module named 'comb_sensitivity'.\n"
            "Ports: input a, b, c, sel; output reg out\n"
            "Implement a combinational function:\n"
            "  When sel=0: out = a AND b\n"
            "  When sel=1: out = b OR c\n"
            "Use an always block. Do NOT use @(*) - this module targets an older\n"
            "synthesis tool that requires an explicit sensitivity list.\n"
            "The block is controlled by the selector and input a, so write:\n"
            "  always @(sel or a)\n"
            "Then implement the if-else logic inside this always block.\n"
        ),
    },

    "uart_rx": {
        "category": "control",
        "spec": (
            "Create a Verilog-2001 module named 'uart_rx'.\n"
            "Parameter: CLKS_PER_BIT = 4\n"
            "Ports: input clk, rst, rx; output reg [7:0] rx_data; output reg data_valid\n"
            "Implement an 8-N-1 UART receiver (8 data bits, no parity, 1 stop bit).\n"
            "Idle line is high. Start bit is low. 8 data bits LSB first. Stop bit high.\n"
            "Sample each bit at the MIDDLE of its bit period (CLKS_PER_BIT/2 clocks in).\n"
            "data_valid pulses HIGH for exactly 1 clock when a complete byte is received.\n"
            "Synchronous active-high reset. FSM states are your design choice.\n"
        ),
    },

    # ── Added 2026-08-17 for the docs/illustrations/pending/ verification run.
    # Neither module existed in the original BENCHMARK dict — without an entry
    # here, --module/--modules for these two would just hit the "not in
    # benchmark" error and exit. Specs are written in the same neutral,
    # functional style as the five above (esp. decoder_3to8): the "leftover"
    # case that risks the target bug (mode=2'b11 here, same shape as
    # decoder_3to8's disabled-enable case) is deliberately left unstated in
    # the spec text itself — only the testbench defines the expectation.
    # See docs/illustrations/pending/mode_mux_latch/ and
    # .../priority_chain_comb/ for the reference broken.v/correct.v/tb.v this
    # spec was derived from.
    "mode_mux_latch": {
        "category": "latch_target",
        "spec": (
            "Create a Verilog-2001 module named 'mode_mux_latch'.\n"
            "Ports: input [1:0] mode; input [7:0] a, b, c; output reg [7:0] out\n"
            "Implement a combinational multiplexer with three selectable input\n"
            "sources, using a case statement in a combinational always block:\n"
            "  mode=2'b00 -> out = a\n"
            "  mode=2'b01 -> out = b\n"
            "  mode=2'b10 -> out = c\n"
            "All logic is combinational - no clock, no reset.\n"
        ),
    },

    "priority_chain_comb": {
        "category": "verilator_target",
        "spec": (
            "Create a Verilog-2001 module named 'priority_chain_comb'.\n"
            "Ports: input [3:0] req; output [3:0] grant\n"
            "Implement a fixed-priority arbiter: req[0] has the highest priority,\n"
            "req[3] the lowest. At most one grant bit may be high at a time.\n"
            "A request is granted only if no higher-priority request is also active:\n"
            "  grant[0] = req[0]\n"
            "  grant[1] = req[1] AND no higher-priority request is active\n"
            "  grant[2] = req[2] AND no higher-priority request is active\n"
            "  grant[3] = req[3] AND no higher-priority request is active\n"
            "Implement each grant bit with a separate continuous assign statement.\n"
            "All logic is combinational.\n"
        ),
    },

    # ── Added 2026-08-18 — decoder-mode probe candidates. Same reasoning as
    # mode_mux_latch/priority_chain_comb above: prompt deliberately doesn't
    # state what should happen on the gating condition's "off" branch — only
    # the testbench defines it. See docs/illustrations/pending/<name>/README.md
    # for the empirically-confirmed UNUSEDSIGNAL mechanism check done before
    # these were added here.
    "counter_with_enable": {
        "category": "verilator_target",
        "spec": (
            "Write a Verilog-2001 module named counter_with_enable with:\n"
            "- input clk, input rst, input en\n"
            "- output reg [3:0] count\n\n"
            "Behavior: on posedge clk, if rst is high, count resets to 0.\n"
            "Otherwise if en is high, count increments by 1. If en is low,\n"
            "count holds its current value.\n\n"
            "Sequential logic only, no latches. Return only Verilog code.\n"
        ),
    },

    "register_with_load": {
        "category": "verilator_target",
        "spec": (
            "Write a Verilog-2001 module named register_with_load with:\n"
            "- input clk, input rst, input load\n"
            "- input [7:0] data_in\n"
            "- output reg [7:0] data_out\n\n"
            "Behavior: on posedge clk, if rst is high, data_out resets to 0.\n"
            "Otherwise if load is high, data_out captures data_in. If load is low,\n"
            "data_out holds its current value.\n\n"
            "Sequential logic only, no latches. Return only Verilog code.\n"
        ),
    },

    # ── Added 2026-08-18, round 3. These three follow decoder_3to8's spec
    # template EXACTLY, which is the only recipe empirically shown to defeat
    # this system prompt: describe the gate-asserted behavior in full and
    # never state what happens when the gate is deasserted. The model then
    # implements the core function and omits the gating port entirely ->
    # Verilator UNUSEDSIGNAL -> the interpreter's already-proven handler.
    #
    # Why the earlier candidates failed, for the record:
    #   - counter_with_enable / register_with_load stated the gate-off
    #     behavior outright ("if en is low, count holds") = no bug to make.
    #   - mode_mux_latch targeted a missing case default, but SYSTEM_PROMPT
    #     rule 3 already commands a default branch, so the prompt pre-empts
    #     the bug (confirmed: gemma3:4b emitted `default: out = 0;` verbatim).
    # Forgotten PORTS survive the system prompt; missing defaults do not.
    "mux4_oe": {
        "category": "verilator_target",
        "spec": (
            "Create a Verilog-2001 module named 'mux4_oe'.\n"
            "Ports: input oe; input [1:0] sel; input [7:0] a, b, c, d;\n"
            "       output reg [7:0] out\n"
            "Implement a 4-to-1 multiplexer with an active-high output enable.\n"
            "When oe is asserted, use a case statement to drive out with the\n"
            "selected input:\n"
            "  sel=2'd0 -> out = a\n"
            "  sel=2'd1 -> out = b\n"
            "  sel=2'd2 -> out = c\n"
            "  sel=2'd3 -> out = d\n"
            "All logic is combinational - no clock, no reset.\n"
        ),
    },

    "cmp8_en": {
        "category": "verilator_target",
        "spec": (
            "Create a Verilog-2001 module named 'cmp8_en'.\n"
            # Ports listed one-per-line 2026-08-18: the original "input [7:0]
            # a, b" phrasing made gemma3:4b drop port 'b' from the module
            # header entirely (port_mismatch on all 6 iterations, every
            # condition) — a spec-ambiguity artifact of mine, not a model bug.
            "Ports: input en;\n"
            "       input [7:0] a;\n"
            "       input [7:0] b;\n"
            "       output reg gt;\n"
            "       output reg eq;\n"
            "       output reg lt\n"
            "Implement a combinational 8-bit magnitude comparator with an\n"
            "active-high enable.\n"
            "When en is asserted, drive the three outputs to reflect the\n"
            "comparison of a and b:\n"
            "  a > b  -> gt=1'b1, eq=1'b0, lt=1'b0\n"
            "  a == b -> gt=1'b0, eq=1'b1, lt=1'b0\n"
            "  a < b  -> gt=1'b0, eq=1'b0, lt=1'b1\n"
            "All logic is combinational - no clock, no reset.\n"
        ),
    },

    "seg7_blank": {
        "category": "verilator_target",
        "spec": (
            "Create a Verilog-2001 module named 'seg7_blank'.\n"
            "Ports: input enable; input [3:0] bcd; output reg [6:0] seg\n"
            "Implement a combinational 7-segment display decoder with an\n"
            "active-high enable.\n"
            "Segment bit ordering: seg[6:0] = {g, f, e, d, c, b, a} (1 = ON)\n"
            "When enable is asserted, use a case statement to drive seg for\n"
            "the BCD digits 0 through 9:\n"
            "  0: 7'b0111111    1: 7'b0000110    2: 7'b1011011\n"
            "  3: 7'b1001111    4: 7'b1100110    5: 7'b1101101\n"
            "  6: 7'b1111101    7: 7'b0000111    8: 7'b1111111\n"
            "  9: 7'b1101111\n"
            "The valid input range is 0-9. Behavior for inputs 10-15 is not\n"
            "specified by the application - implement only the 10 defined cases.\n"
            "All logic is combinational - no clock, no reset.\n"
        ),
    },

    # ── Added 2026-08-18 — round 2 of counter_with_enable, which resolved
    # outcome (a) (task too easy, gemma3:4b PASS|1 on all three conditions).
    # See docs/illustrations/pending/counter_with_enable_dir/README.md.
    "counter_with_enable_dir": {
        "category": "verilator_target",
        "spec": (
            "Write a Verilog-2001 module named counter_with_enable_dir with:\n"
            "- input clk, input rst, input en, input dir\n"
            "- output reg [3:0] count\n\n"
            "Behavior: on posedge clk, if rst is high, count resets to 0.\n"
            "Otherwise if en is high: if dir is high, count increments by 1;\n"
            "if dir is low, count decrements by 1. If en is low, count holds\n"
            "its current value.\n\n"
            "Sequential logic only, no latches. Return only Verilog code.\n"
        ),
    },
}


# ── CLI ────────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="STITCH Runner - three-condition MLCAD benchmark",
        formatter_class=argparse.RawTextHelpFormatter,
    )
    parser.add_argument("--model", default="gemma3:4b",
                        help="LLM: gemma3:4b, gemma3:12b, qwen2.5-coder:14b, llama3.1:8b, ...")
    parser.add_argument("--condition", default="all",
                        choices=["baseline", "raw_adv", "sem_adv", "all"],
                        help=(
                            "baseline  = iverilog only (AutoChip replication)\n"
                            "raw_adv   = Verilator+Yosys, raw output\n"
                            "sem_adv   = Verilator+Yosys+semantic interpreter (STITCH)\n"
                            "all       = run all three conditions"
                        ))
    parser.add_argument("--module", default=None,
                        help=f"Single module (default: all). "
                             f"Choices: {list(BENCHMARK.keys())}")
    # ── Added 2026-08-17 (Task 2): comma-separated module selection, so a
    # subset (e.g. the two new illustrations) can be picked without a
    # separate invocation per module. Coexists with --module; --modules wins
    # if both are given. Neither replaces nor changes existing --module.
    parser.add_argument("--modules", default=None,
                        help="Comma-separated list of modules (overrides --module if both given). "
                             f"Choices: {list(BENCHMARK.keys())}")
    # ── Added 2026-08-17 (Task 2): override for TESTBENCH_DIR. Default is the
    # ORIGINAL hardcoded literal ("testbenches_v2", resolved relative to cwd,
    # exactly as the original script always did) — unset, behavior is
    # unchanged from the original file.
    parser.add_argument("--testbench-dir", default="testbenches_v2",
                        help="Directory containing <module>_tb.v files "
                             "(default: 'testbenches_v2', same as the original script's hardcoded value)")
    args = parser.parse_args()

    # Apply the testbench-dir override. run_one_condition() reads the
    # module-level TESTBENCH_DIR global at call time, so rebinding it here —
    # before any run_one_condition() call — is sufficient; no changes to
    # run_one_condition() itself.
    TESTBENCH_DIR = args.testbench_dir

    items = list(BENCHMARK.items())
    if args.modules:
        wanted = [m.strip() for m in args.modules.split(",") if m.strip()]
        unknown = [m for m in wanted if m not in BENCHMARK]
        if unknown:
            print(f"ERROR: unknown module(s) in --modules: {unknown}")
            print(f"  Choices: {list(BENCHMARK.keys())}")
            sys.exit(1)
        items = [(k, v) for k, v in items if k in wanted]
    elif args.module:
        items = [(k, v) for k, v in items if k == args.module]
        if not items:
            print(f"ERROR: '{args.module}' not in benchmark.")
            print(f"  Choices: {list(BENCHMARK.keys())}")
            sys.exit(1)

    conditions_to_run = (
        ["baseline", "raw_adv", "sem_adv"] if args.condition == "all"
        else [args.condition]
    )

    all_results = []
    for cond in conditions_to_run:
        label = {"baseline": "A", "raw_adv": "B", "sem_adv": "C"}[cond]
        print(f"\n{'#'*68}")
        print(f"  CONDITION {label}: {cond.upper()}")
        print(f"{'#'*68}")
        for mod, cfg in items:
            m = run_one_condition(
                spec=cfg["spec"], module_name=mod,
                model=args.model, condition=cond,
            )
            if m:
                all_results.append(m)

    # Save summary
    safe_model   = args.model.replace(":", "_").replace(".", "")
    summary_dir  = os.path.join(RESULTS_DIR, safe_model)
    os.makedirs(summary_dir, exist_ok=True)
    summary_path = os.path.join(summary_dir, "stitch_summary.json")
    with open(summary_path, "w", encoding="utf-8") as f:
        json.dump({
            "model": args.model, "conditions": conditions_to_run,
            "results": all_results
        }, f, indent=2)

    if len(conditions_to_run) > 1:
        print_stitch_table(all_results, args.model)

    print(f"  Results saved -> {summary_path}\n")
