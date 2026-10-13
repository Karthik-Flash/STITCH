"""
phase2/twin_run_runner.py -- Phase 2 RTLCoder twin-comparison run.

Design doc: phase2/TWIN_RUN_PREREG.md (read that first). Not yet
launched -- built for review, per the 2026-08-22 "STOP before launching"
instruction.

SCOPE (75 runs, revised 2026-08-23): 5 MODEL-CONDITIONS (not a full
model x prompt-condition cross -- see below) x 5 modules (accu,
counter_12, barrel_shifter, alu, calendar -- same set as the phase1
laptop pilot, for direct comparability) x N=3.

  rtlcoder-deepseek-v1.1 / native  -- RTLCoder's own stub-completion prompt
  rtlcoder-deepseek-v1.1 / shared  -- the harness SYSTEM_PROMPT, reformatted
  deepseek-coder:6.7b   / shared   -- harness SYSTEM_PROMPT (its only condition)
  gemma3:4b             / shared   -- harness SYSTEM_PROMPT (its only condition)
  llama3.1:latest       / shared   -- harness SYSTEM_PROMPT (its only condition)

REVISION 2026-08-23: the original design crossed all 4 models x both
prompt conditions (120 runs). Cut to this 5-cell list because "native"
and "shared" are procedurally IDENTICAL for the 3 Ollama models (both
are the harness SYSTEM_PROMPT -- there is no other native convention for
them), so the other 60 runs would have been redundant replicates, not a
second experimental condition, for those 3 models. Only RTLCoder has a
real native-vs-shared contrast. The two readable comparisons this design
answers:
  (a) RTLCoder/shared vs. deepseek-coder:6.7b/shared -- the pure
      fine-tuning twin comparison (same prompt, same everything else).
  (b) RTLCoder/native vs. RTLCoder/shared -- the prompt-format effect,
      isolated on the one model where it's actually a variable.

TEMPERATURE (revised 2026-08-23): matched at T=0.5, top_p=0.9 for ALL
FIVE model-conditions, including the 3 Ollama models -- a deliberate
override of stitch_runner_hpc.py's hardcoded T=0.1 Ollama default (see
_call_ollama() below) and of the project's usual T=0.1 convention. See
TWIN_RUN_PREREG.md's temperature note for why and what this run is (and
isn't) comparable to as a result.

This is a MODEL comparison (does fine-tuning on RTLCoder's data help,
isolated from prompt-format effects) -- NOT a test of STITCH's
interpreter. `CONDITION` below is fixed at "baseline" (iverilog-only
feedback loop, no Verilator/Yosys/interpreter involvement at all) for
every single cell, deliberately, so nothing here can be mistaken for a
STITCH validation result.

Runs through stitch_runner_hpc.run_one_condition() -- the Linux-native
port of the doubly-bugfixed src/runner/stitch_runner.py (see that file's
module docstring for exactly how the port was verified) -- UNMODIFIED.
RTLCoder is bridged into the SAME call_llm() dispatch point via a
monkeypatch (same "monkeypatch as config" pattern
phase1/rtllm_pilot_runner.py already uses for run_iverilog_sim), not by
editing stitch_runner_hpc.py -- see _rtlcoder_aware_call_llm() below.
The 3 Ollama models are ALSO routed through a small local wrapper
(_call_ollama()) rather than stitch_runner_hpc.call_llm()'s own Ollama
branch, for TWO reasons, not just temperature: (1) overriding its
hardcoded temperature for this run, and (2) 2026-08-23 -- on HPC, unlike
the laptop, Ollama does not listen on the OpenAI-python default
(localhost:11434) reliably -- this run starts its OWN `ollama serve`
inside the slurm job (see phase2/twin_run.slurm), bound to whatever
$OLLAMA_HOST that script sets. sr.OLLAMA_CLIENT's base_url is a
HARDCODED "http://localhost:11434/v1" baked into stitch_runner_hpc.py at
import time -- reusing it here would silently point at the wrong
host:port if OLLAMA_HOST is ever anything else. Both reasons are the
same non-edited-file principle: the override lives here, not in the
verified port.
Because RTLCoder's adapter returns already-clean, already-postprocessed
Verilog (no fences), it passes through stitch_runner_hpc.py's own
fence-extraction regex as a no-op -- the entire iteration loop,
feedback-building, and STUCK_THRESHOLD logic is exercised identically
regardless of which model-condition is active.

RTLLM is never copied into this repo (same policy as phase1/phase2's
earlier work) -- read live from $RTLLM_ROOT.

Usage: python phase2/twin_run_runner.py
Output: phase2/results/twin_run/master_log.json (gitignored, resumable)
"""
import argparse
import json
import os
import re
import shutil
import sys
import traceback

from openai import OpenAI

_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, _HERE)
import stitch_runner_hpc as sr  # noqa: E402
import rtlcoder_adapter as rc   # noqa: E402

RTLLM_ROOT = os.environ.get("RTLLM_ROOT", os.path.expandvars("/scratch/$USER/RTLCoderHPC/RTLLM"))
# FIX 2026-08-25: this default used to be "/scratch/$USER/RTLLM" --
# inconsistent with docs/HPC_COMMANDS.md's actual documented layout
# (RTLLM lives at RTLCoderHPC/RTLLM, section 0). Harmless in practice
# since twin_run.slurm always sources env.sh first, which sets
# $RTLLM_ROOT explicitly before this module ever loads -- but a latent
# inconsistency worth closing while touching this file for the 42-module
# update below, not left for the next person to trip over.
RESULTS_ROOT = os.path.join(_HERE, "results", "twin_run")
STAGED_ROOT = os.path.join(RESULTS_ROOT, "_staged")
MASTER_LOG = os.path.join(RESULTS_ROOT, "master_log.json")
INCIDENTS_LOG = os.path.join(RESULTS_ROOT, "incidents.log")

# The Ollama server this run talks to is started BY twin_run.slurm, bound
# to $OLLAMA_HOST (that script sets it explicitly, e.g. "127.0.0.1:11434")
# -- read the SAME env var here rather than hardcoding a port, so the
# server and the client are structurally guaranteed to agree, not just
# hoped to. Defaults to Ollama's own standard default (127.0.0.1:11434)
# ONLY for local/laptop testing of this script in isolation -- on HPC,
# twin_run.slurm always sets this explicitly.
OLLAMA_HOST = os.environ.get("OLLAMA_HOST", "127.0.0.1:11434")
_OLLAMA_BASE_URL = f"http://{OLLAMA_HOST}/v1"
_ollama_client = OpenAI(base_url=_OLLAMA_BASE_URL, api_key="ollama")

RTLCODER_MODEL = "rtlcoder-deepseek-v1.1"

# (model, prompt_condition) pairs -- NOT a full cross of MODELS x
# PROMPT_CONDITIONS. See module docstring's 2026-08-23 revision note:
# only RTLCoder has a real native-vs-shared contrast; the 3 Ollama
# models get exactly one condition each (labeled "shared" since that's
# what it is -- the harness SYSTEM_PROMPT, their only convention).
MODEL_CONDITIONS = [
    (RTLCODER_MODEL,        "native"),
    (RTLCODER_MODEL,        "shared"),
    ("deepseek-coder:6.7b", "shared"),
    ("gemma3:4b",           "shared"),
    ("llama3.1:latest",     "shared"),
]

TEMPERATURE = 0.5  # matched across ALL FIVE model-conditions -- 2026-08-23
                   # revision, see module docstring and TWIN_RUN_PREREG.md.
                   # Deliberate deviation from the project's usual T=0.1.

CONDITION = "baseline"  # fixed -- see module docstring; not a measured axis here
N_REPLICATES = 3
MAX_ITERS = 8  # Pass@8, per the prereg -- overrides stitch_runner_hpc's
               # default MAX_RETRIES=6. NOTE this means this run's
               # "baseline" condition is NOT cap-comparable to Task 3's
               # or the laptop pilot's baseline (both cap=6) -- flagged
               # here and in TWIN_RUN_PREREG.md, not silently glossed.
sr.MAX_RETRIES = MAX_ITERS

# ── module pool: full 42-module scope (revised 2026-08-25) ─────────────
# SUPERSEDED: this used to be a hardcoded 5-module pilot subset
# (accu/counter_12/barrel_shifter/alu/calendar), matching the phase1
# laptop pilot for direct comparability during pilot-scale validation.
# The real full run scales to the full 44-compatible-design pool minus
# EXCLUDE (42) -- loaded dynamically from task_a_screen.json, same
# pattern phase2/set1_runner.py uses (not shared into a common module;
# this project's convention is small per-runner staging/loading logic,
# not a premature shared abstraction -- see e.g. _stage_testbench()
# below, already duplicated near-identically from
# phase1/rtllm_pilot_runner.py).
CATEGORIES = ["Arithmetic", "Control", "Memory", "Miscellaneous"]
EXCLUDE = {"edge_detect", "square_wave"}  # weak-oracle testbenches -- see
                                           # docs/IMP_PHASE2_RUNNER_HARDENING_REPORT.md
                                           # §4/§6. RTLLM-precedent move:
                                           # matches their own 50->44
                                           # exclusion for a defect in a
                                           # golden reference's own
                                           # testbench, not a
                                           # detect_outcome()/STITCH issue.
EXPECTED_MODULE_COUNT = 42

_FLAT_SCREEN_JSON = os.path.join(_HERE, "task_a_screen.json")
_DEV_SCREEN_JSON = os.path.join(_HERE, "..", "phase1", "results", "rtllm_pilot", "task_a_screen.json")
TASK_A_SCREEN_JSON = os.environ.get("TASK_A_SCREEN_JSON") or (
    _FLAT_SCREEN_JSON if os.path.exists(_FLAT_SCREEN_JSON) else _DEV_SCREEN_JSON
)


def _load_module_pool(rtllm_root=RTLLM_ROOT, task_a_screen_json=TASK_A_SCREEN_JSON):
    """Returns [(design, category, relative_path_under_rtllm_root), ...],
    sorted by (category, design). See phase2/set1_runner.py's identical
    function for the full rationale -- duplicated here rather than
    imported, matching this project's existing per-runner-duplication
    convention. HARD ASSERTS exactly 42 survive the EXCLUDE filter."""
    if not os.path.exists(task_a_screen_json):
        print(f"FATAL: {task_a_screen_json} not found. Deploy it alongside "
              f"this script (see docs/FULL_RUN_RUNBOOK.md) -- it's the "
              f"44-compatible-design pool phase1/rtllm_task_a_screen.py "
              f"already confirmed; this script does not re-derive it.")
        sys.exit(1)
    with open(task_a_screen_json, encoding="utf-8") as f:
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
                    rel = os.path.relpath(design_dir, rtllm_root).replace("\\", "/")
                    found.append((design, cat, rel))

    all_found_pairs = {(cat, design) for design, cat, _ in found}
    missing = compatible - all_found_pairs
    if missing:
        print(f"WARNING: {len(missing)} design(s) from task_a_screen.json's "
              f"compatible pool were not found under {rtllm_root}: {sorted(missing)}")

    excluded = [t for t in found if t[0] in EXCLUDE]
    found = [t for t in found if t[0] not in EXCLUDE]
    found.sort(key=lambda t: (t[1], t[0]))

    if len(excluded) != len(EXCLUDE):
        print(f"WARNING: expected to exclude {sorted(EXCLUDE)} (2 designs) "
              f"but only found {[t[0] for t in excluded]} in the discovered "
              f"pool -- EXCLUDE may not match what's actually compatible.")

    assert len(found) == EXPECTED_MODULE_COUNT, (
        f"expected exactly {EXPECTED_MODULE_COUNT} modules after excluding "
        f"{sorted(EXCLUDE)} from the 44-compatible pool, got {len(found)}. "
        f"HARD STOP -- do not silently proceed with a different-sized "
        f"study; investigate task_a_screen.json / the RTLLM checkout first."
    )
    return found


MODULES = _load_module_pool()


# ── RTLCoder-into-call_llm bridge ───────────────────────────────────────────
# _CURRENT_MODULE_NAME / _CURRENT_PROMPT_MODE: set once per cell by
# _run_one_cell() below, read by _call_rtlcoder() -- same "set a global
# right before the call that needs it" pattern already used for
# sr.TESTBENCH_DIR/sr.RESULTS_DIR elsewhere in this project (e.g.
# phase1/rtllm_pilot_runner.py's _run_classic()).
_CURRENT_MODULE_NAME = None
_CURRENT_PROMPT_MODE = None

_original_call_llm = sr.call_llm


def _call_rtlcoder(messages):
    """Builds a completion-style prompt for RTLCoder from the SAME
    `messages` list stitch_runner_hpc.run_one_condition() builds for
    every model (system prompt + growing user/assistant history), then
    calls rc.generate(prompt) -- the real, HPC-validated, stub-rejoined
    function, not a hand-reconstruction of it. Returns (text, pt, ct)
    matching call_llm()'s contract; `text` is already clean Verilog (no
    fences), which stitch_runner_hpc's own fence-extraction regex passes
    through as a no-op, so the rest of the iteration loop is unmodified.

    messages[1] is always the ORIGINAL spec (index 1 = the first user
    turn, set once at the top of run_one_condition() and never mutated
    afterward, regardless of how many repair turns get appended) -- safe
    to read on every call, any iteration.
    """
    spec = messages[1]["content"]
    module_name = _CURRENT_MODULE_NAME
    mode = _CURRENT_PROMPT_MODE

    if len(messages) == 2:
        # Iteration 1: no feedback yet.
        if mode == "native":
            prompt = rc.build_prompt(spec, module_name)
        else:  # shared -- RTLCoder sees the identical harness SYSTEM_PROMPT
               # + spec the Ollama models get, reformatted as a completion
               # prompt (RTLCoder can't consume chat-role turns natively)
               # with the same trailing module-header stub appended.
            prompt = f"{sr.SYSTEM_PROMPT}\n\n{spec}\n\nmodule {module_name}(\n"
    else:
        # Repair iteration: messages[-1] is whatever
        # _build_baseline_feedback()/_REWRITE_PROMPT produced at the end
        # of the previous iteration -- the same text an Ollama model
        # would receive as its next user turn.
        feedback = messages[-1]["content"]
        if mode == "native":
            if "ORIGINAL SPECIFICATION:" in feedback:
                # STUCK_THRESHOLD's _REWRITE_PROMPT fired -- it already
                # embeds the spec verbatim (see stitch_runner_hpc.py's
                # _REWRITE_PROMPT), don't prepend it a second time.
                prompt = f"{feedback}\n\nmodule {module_name}(\n"
            else:
                prompt = (f"{spec}\n\nA previous attempt failed. Here is what "
                          f"went wrong:\n{feedback}\n\nGive me the complete "
                          f"corrected code.\n\nmodule {module_name}(\n")
        else:  # shared -- flatten the FULL chat history the same way
               # sr.call_llm()'s own Gemini branch already does (see
               # stitch_runner_hpc.py), so "shared" mode's repair prompts
               # carry exactly the same information an Ollama model's
               # chat history would, just linearized.
            history = "\n\n".join(
                f"[{'USER' if m['role']=='user' else 'ASSISTANT'}]\n{m['content']}"
                for m in messages if m["role"] != "system"
            )
            prompt = f"{sr.SYSTEM_PROMPT}\n\n{history}\n\nmodule {module_name}(\n"

    # TEMPERATURE matches the module-level constant (0.5) explicitly --
    # this happens to already be rc.generate()'s own default, but stated
    # explicitly here rather than relying on that default staying in
    # sync with this run's TEMPERATURE if either ever changes separately.
    code = rc.generate(prompt, temperature=TEMPERATURE, top_p=0.9)

    # Real token counts via the adapter's own tokenizer -- not stubbed to
    # zero. Counted on (prompt, POSTPROCESSED code) rather than the
    # pre-cut raw generation, since that's the meaningful "usable
    # content" measure -- differs slightly in spirit from Ollama's
    # usage.completion_tokens (which counts the full raw generation
    # including any cut-off overrun past the intended module). Flagged
    # here, not hidden; see TWIN_RUN_PREREG.md's cost-reporting note.
    _, tokenizer = rc.load_model()
    pt = len(tokenizer(prompt).input_ids)
    ct = len(tokenizer(code).input_ids)
    return code, pt, ct


def _call_ollama(model, messages):
    """Same shape of request sr.call_llm()'s own Ollama branch makes
    (stitch_runner_hpc.py, OLLAMA_CLIENT.chat.completions.create), but
    via `_ollama_client` (bound to $OLLAMA_HOST -- see module docstring)
    instead of that file's hardcoded-localhost:11434 client, and with
    temperature=TEMPERATURE (0.5) instead of that file's hardcoded 0.1
    -- see module docstring's 2026-08-23 notes on both. Not implemented
    by editing stitch_runner_hpc.py (kept a faithful, unmodified port of
    the fixed harness); both overrides live here, one level up."""
    resp = _ollama_client.chat.completions.create(
        model=model, messages=messages, temperature=TEMPERATURE)
    u = getattr(resp, "usage", None)
    pt = getattr(u, "prompt_tokens",     0) if u else 0
    ct = getattr(u, "completion_tokens", 0) if u else 0
    return resp.choices[0].message.content, pt, ct


def _rtlcoder_aware_call_llm(model, messages):
    if model == RTLCODER_MODEL:
        return _call_rtlcoder(messages)
    if model.startswith("gemini") or model.startswith(("gpt-", "o1", "o3")):
        # Not used by this run's MODEL_CONDITIONS -- kept for parity with
        # stitch_runner_hpc.call_llm()'s full dispatch, in case this
        # bridge is ever reused for a run that does include one.
        return _original_call_llm(model, messages)
    return _call_ollama(model, messages)


sr.call_llm = _rtlcoder_aware_call_llm


# ── RTLLM staging (identical pattern to phase1/rtllm_pilot_runner.py) ──────
def _stage_testbench(design, rel):
    src_dir = os.path.join(RTLLM_ROOT, rel)
    staged_dir = os.path.join(STAGED_ROOT, design)
    os.makedirs(staged_dir, exist_ok=True)

    tb_dst = os.path.join(staged_dir, f"{design}_tb.v")
    shutil.copy(os.path.join(src_dir, "testbench.v"), tb_dst)

    deps = []
    for f in os.listdir(src_dir):
        if f in ("testbench.v", "makefile", "design_description.txt") or f.startswith("verified_"):
            continue
        dep_dst = os.path.join(staged_dir, f)
        shutil.copy(os.path.join(src_dir, f), dep_dst)
        deps.append(dep_dst)

    return staged_dir, deps


def _get_spec(rel):
    with open(os.path.join(RTLLM_ROOT, rel, "design_description.txt"), encoding="utf-8") as f:
        return f.read()


def _run_one_cell(design, category, model, prompt_condition, spec, testbench_dir, deps, replicate):
    global _CURRENT_MODULE_NAME, _CURRENT_PROMPT_MODE
    _CURRENT_MODULE_NAME = design
    _CURRENT_PROMPT_MODE = prompt_condition

    sr.TESTBENCH_DIR = testbench_dir
    safe_model = model.replace(":", "_").replace(".", "")
    sr.RESULTS_DIR = os.path.join(RESULTS_ROOT, prompt_condition, f"replicate_{replicate}")

    m = sr.run_one_condition(
        spec=spec, module_name=design, model=model, condition=CONDITION, dependencies=deps,
        # BUG #3 FIX (2026-08-24): this call used to carry NO pass-
        # detection override at all -- stitch_runner_hpc.py's
        # run_iverilog_sim() hardcoded the "PASS"/"ALL TESTS PASSED"
        # check, which RTLLM's "Your Design Passed" testbenches never
        # matched, so every genuine pass in the twin pilot was silently
        # recorded as a failure (see phase2/TWIN_RUN_ANALYSIS.md Appendix A's
        # preamble). All MODULES here are RTLLM designs -- see
        # pass_detection.py for the registry this now routes through.
        benchmark="rtllm",
    )
    return {
        "module": design, "category": category, "model": model,
        "prompt_condition": prompt_condition, "run_replicate": replicate,
        "iteration_cap": MAX_ITERS,
        "pass": m["pass"], "iterations_to_pass": m["iterations_to_pass"],
        "total_iterations": m["total_iterations"], "total_tokens": m["total_tokens"],
        "per_iteration": m["per_iter_detail"],
    }


def _load_master_log():
    if os.path.exists(MASTER_LOG):
        with open(MASTER_LOG, encoding="utf-8") as f:
            return json.load(f)
    return []


def _save_master_log(entries):
    os.makedirs(RESULTS_ROOT, exist_ok=True)
    with open(MASTER_LOG, "w", encoding="utf-8") as f:
        json.dump(entries, f, indent=2)


RETRY_ATTEMPTS = 3


def _log_incident(key, attempt, max_attempts, exc, final):
    """Same run-autonomy boundary as phase1/rtllm_pilot_runner.py's
    _log_incident(): retries transient infra failures VERBATIM, never
    branches on WHAT the exception was to change harness behavior."""
    os.makedirs(RESULTS_ROOT, exist_ok=True)
    module, model, prompt_condition, replicate = key
    ts = __import__("datetime").datetime.now().isoformat(timespec="seconds")
    status = "GIVING UP -- cell errored, logged to master_log.json, moving on" if final \
        else f"retrying (attempt {attempt+1}/{max_attempts})"
    with open(INCIDENTS_LOG, "a", encoding="utf-8") as f:
        f.write(f"[{ts}] {module} / {model} / {prompt_condition} / replicate {replicate}\n")
        f.write(f"  attempt {attempt}/{max_attempts} -- {status}\n")
        f.write(f"  exception: {type(exc).__name__}: {exc}\n")
        f.write("  traceback:\n")
        for line in traceback.format_exception(type(exc), exc, exc.__traceback__):
            f.write("    " + line)
        f.write("\n")


def run_all():
    entries = _load_master_log()
    done = {(e["module"], e["model"], e["prompt_condition"], e["run_replicate"]) for e in entries}

    # 5 model-conditions, NOT a full MODELS x PROMPT_CONDITIONS cross --
    # see module docstring's 2026-08-23 revision note.
    total = len(MODULES) * len(MODEL_CONDITIONS) * N_REPLICATES
    done_count = len(done)

    for design, category, rel in MODULES:
        testbench_dir, deps = _stage_testbench(design, rel)
        spec = _get_spec(rel)
        for model, prompt_condition in MODEL_CONDITIONS:
            for replicate in range(1, N_REPLICATES + 1):
                key = (design, model, prompt_condition, replicate)
                if key in done:
                    continue

                done_count += 1
                print(f"\n[{done_count}/{total}] {design} / {model} / {prompt_condition} / replicate {replicate}")

                entry = None
                last_exc = None
                for attempt in range(1, RETRY_ATTEMPTS + 1):
                    try:
                        entry = _run_one_cell(design, category, model, prompt_condition,
                                               spec, testbench_dir, deps, replicate)
                        entry["error"] = None
                        entry["attempts"] = attempt
                        break
                    except Exception as e:
                        last_exc = e
                        print(f"  ERROR (attempt {attempt}/{RETRY_ATTEMPTS}): {e}")
                        _log_incident(key, attempt, RETRY_ATTEMPTS, e, final=(attempt == RETRY_ATTEMPTS))

                if entry is None:
                    entry = {
                        "module": design, "category": category, "model": model,
                        "prompt_condition": prompt_condition, "run_replicate": replicate,
                        "error": f"{type(last_exc).__name__}: {last_exc}",
                        "attempts": RETRY_ATTEMPTS,
                    }

                entries.append(entry)
                _save_master_log(entries)

    print(f"\nDone. {len(entries)} entries -> {MASTER_LOG}")
    n_errored = sum(1 for e in entries if e.get("error"))
    if n_errored:
        print(f"{n_errored} cell(s) errored after {RETRY_ATTEMPTS} attempts each -- see {INCIDENTS_LOG}")


def _verify_ollama_models():
    """FAIL LOUDLY, before any cell runs, if the Ollama server this
    process is about to talk to doesn't already have all 3 needed
    models -- belt-and-suspenders on top of twin_run.slurm's own
    `ollama list` check, in case this script is ever invoked directly
    without going through that script. Does NOT attempt to pull a
    missing model itself: an inline pull mid-run risks silently eating
    real wall-clock budget on a multi-GB download inside the timed job;
    missing models are a setup gap to fix and re-launch, not something
    to paper over here (see docs/HPC_COMMANDS.md's
    pull_ollama_models.slurm, a dedicated one-time step)."""
    needed = sorted({m for m, cond in MODEL_CONDITIONS if m != RTLCODER_MODEL})
    try:
        resp = _ollama_client.models.list()
        available = {m.id for m in resp.data}
    except Exception as e:
        print(f"FATAL: could not reach the Ollama server at {_OLLAMA_BASE_URL} "
              f"({type(e).__name__}: {e}). Is `ollama serve` actually running "
              f"in this job, and does $OLLAMA_HOST match what it's bound to? "
              f"See phase2/twin_run.slurm's readiness-check step.")
        sys.exit(1)
    missing = [m for m in needed if m not in available]
    if missing:
        print(f"FATAL: Ollama server at {_OLLAMA_BASE_URL} is missing: {missing}. "
              f"Available: {sorted(available)}. Run "
              f"phase2/pull_ollama_models.slurm once before launching this run "
              f"-- see docs/HPC_COMMANDS.md §10. Not pulling "
              f"inline here (would eat this job's own wall-clock budget on a "
              f"multi-GB download).")
        sys.exit(1)
    print(f"Ollama models confirmed present at {_OLLAMA_BASE_URL}: {needed}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true",
                         help="Print the total cell count and exit 0 -- does NOT "
                              "touch Ollama or iverilog. Pre-flight sanity check "
                              "before ever launching the real job.")
    args = parser.parse_args()

    total = len(MODULES) * len(MODEL_CONDITIONS) * N_REPLICATES
    print(f"Modules ({len(MODULES)}): {[m[0] for m in MODULES]}")
    print(f"Model-conditions: {MODEL_CONDITIONS}")
    print(f"Temperature (all model-conditions): {TEMPERATURE}")
    print(f"Ollama client bound to: {_OLLAMA_BASE_URL}")
    print(f"Total runs: {total}")

    if args.dry_run:
        assert total == 630, (
            f"dry-run expected exactly 630 total runs (42 modules x 5 "
            f"model-conditions x N=3), computed {total} -- STOP, do not launch."
        )
        print("DRY RUN OK: exactly 630 cells, as locked. Not touching Ollama/iverilog.")
        sys.exit(0)

    _verify_ollama_models()
    run_all()
