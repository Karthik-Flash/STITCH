"""
phase2/set1_runner.py -- Set 1: STITCH conditions sweep at full RTLLM
scale, on <GPU_NODE> (A100, gpu_a100_8). Paper Graph Set 1: does
sem_escalate beat MLCAD's always-on sem_adv on cost + pass rate.

Setup brief: see git history / handoff for the "STITCH Full HPC Run"
task this was built under. Read docs/IMP_PHASE2_RUNNER_HARDENING_REPORT.md,
docs/HPC_COMMANDS.md, and phase2/TWIN_RUN_PREREG.md first --
this run reuses the hardened pass-detection registry and the twin run's
already-solved Ollama-on-HPC infrastructure, doesn't reinvent either.

SCOPE: 42 modules (44-compatible RTLLM pool minus EXCLUDE, see below) x
3 Ollama models x 4 conditions x N=3 = 1,512 runs.

  Modules:    loaded from task_a_screen.json at runtime (NOT hardcoded --
              see _load_module_pool()), minus EXCLUDE.
  Models:     gemma3:4b, llama3.1:latest, deepseek-coder:6.7b (Ollama only
              -- no RTLCoder in this run; that's Set 2's axis).
  Conditions: baseline, sem_adv, sem_escalate, sem_escalate_restart.
              NOTE: the setup brief's prose shorthand for the last two was
              "sem_esc"/"sem_esc_restart" -- the actual condition strings
              this codebase's runners require (stitch_runner_hpc.py's
              run_one_condition() and escalation_runner_hpc.py's
              run_one_replicate() both validate against the full names)
              are "sem_escalate"/"sem_escalate_restart", used here
              verbatim rather than introducing new identifiers that
              would raise ValueError against the real, existing harness.
              raw_adv is deliberately dropped -- Phase 1 already
              isolated interpreter-vs-tool-presence; Set 1's question is
              escalation vs. always-on, not tools-vs-no-tools again.
  Replicates: N=3.
  Sampling:   T=0.1 -- matches Phase 1 for cross-benchmark comparability
              (NOT T=0.5 like the twin run; that run's T=0.5 is specific
              to removing temperature as a confound in a MODEL
              comparison, which isn't this run's question).

EXCLUDE = {"edge_detect", "square_wave"}: both are in the 44-compatible
pool but pass with every output stuck at a constant wrong value --
confirmed (docs/IMP_PHASE2_RUNNER_HARDENING_REPORT.md §4) to be a defect in
each design's OWN testbench check logic (edge_detect's error condition
ANDs two independently-wrong-or-not checks instead of ORing them;
square_wave's check only looks for "too many consecutive 1s", never
"does the output toggle at all") -- not a detect_outcome()/STITCH issue.
This is the RTLLM-precedent move: matches RTLLM's own original 50->44
exclusion for designs whose OWN golden reference/testbench had a defect.
Locked at 42 -- do not silently change this list; if there's a reason to
reconsider it, that's a report-and-stop situation, not a silent edit.

Pass detection: EVERY call site below routes through the ALREADY-hardened
sr.run_one_condition()/escalation_runner_hpc.run_one_replicate(), which
route through detect_outcome(sim_log, "rtllm") internally
(src/interpreter/pass_detection.py) -- nothing here reimplements any part
of that. See docs/IMP_PHASE2_RUNNER_HARDENING_REPORT.md.

Runs on <GPU_NODE> via stitch_runner_hpc.py (the Linux-native HPC port,
NOT src/runner/stitch_runner.py -- there is no wsl.exe on a compute
node) and phase2/escalation_runner_hpc.py (the equivalent HPC port of
phase1/escalation_runner.py, built alongside this file -- see that
file's module docstring for why it had to exist before sem_escalate
could run here at all).

Output layout (see _relocate() for why a post-run move is needed):
  <RESULTS_ROOT>/<module>/<safe_model>/<condition>/rep<k>/
    iter_<i>/{feedback.txt, llm_response.txt, <module>.v, sim_log.txt},
    plus metrics.json (classic conditions) or run_log.json (escalation
    conditions) at the rep<k>/ level.
  <RESULTS_ROOT>/master_log.json -- one entry per completed cell,
    resumable (same incremental-checkpoint pattern as every other
    runner in this project).

Usage:
  python phase2/set1_runner.py --dry-run   # prints exactly 1512, exits 0
  python phase2/set1_runner.py             # the real run
"""
import argparse
import json
import os
import shutil
import sys
import traceback

from openai import OpenAI

_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, _HERE)
import stitch_runner_hpc as sr           # noqa: E402
from escalation_runner_hpc import run_one_replicate  # noqa: E402
sys.path.insert(0, os.path.join(_HERE, "..", "phase1"))
from escalation_state import EscalationConfig  # noqa: E402

# ── module pool ──────────────────────────────────────────────────────────
CATEGORIES = ["Arithmetic", "Control", "Memory", "Miscellaneous"]
EXCLUDE = {"edge_detect", "square_wave"}  # see module docstring
EXPECTED_MODULE_COUNT = 42

# task_a_screen.json is gitignored (phase1/.gitignore) and never
# committed -- on HPC it's scp'd flat alongside this script (see
# docs/FULL_RUN_RUNBOOK.md); locally it lives at its real repo path. Try the
# flat-deploy location first, fall back to the repo-relative dev path.
_FLAT_SCREEN_JSON = os.path.join(_HERE, "task_a_screen.json")
_DEV_SCREEN_JSON = os.path.join(_HERE, "..", "phase1", "results", "rtllm_pilot", "task_a_screen.json")
TASK_A_SCREEN_JSON = os.environ.get("TASK_A_SCREEN_JSON") or (
    _FLAT_SCREEN_JSON if os.path.exists(_FLAT_SCREEN_JSON) else _DEV_SCREEN_JSON
)

RTLLM_ROOT = os.environ.get("RTLLM_ROOT", os.path.expandvars("/scratch/$USER/RTLCoderHPC/RTLLM"))
# Deliberately the SAME checkout the twin run (Set 2) reads -- RTLLM is
# read-only I/O for both jobs, on different physical nodes, so sharing
# one checkout is safe and avoids a second multi-hundred-MB clone. See
# docs/FULL_RUN_RUNBOOK.md's two-node-independence section.


def _load_module_pool(rtllm_root=RTLLM_ROOT, task_a_screen_json=TASK_A_SCREEN_JSON):
    """Returns [(design, category, relative_path_under_rtllm_root), ...],
    sorted by (category, design) for a deterministic run order. Loads
    the 44-compatible pool from task_a_screen.json (which stores only
    category+design, not a path) and resolves each survivor's real
    directory by walking RTLLM_ROOT -- same discovery pattern
    phase1/rtllm_task_a_screen.py's discover_designs() and
    phase2/verify_pass_detection.py's _load_compatible_designs() already
    use, not reinvented here. Excludes EXCLUDE, then HARD ASSERTS the
    result is exactly 42 -- a silent JSON or RTLLM-checkout change must
    stop this script immediately, not quietly run a differently-scoped
    study."""
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


# ── config (Phase-1-comparable, per the setup brief) ────────────────────
MODELS = ["gemma3:4b", "llama3.1:latest", "deepseek-coder:6.7b"]
CONDITIONS = ["baseline", "sem_adv", "sem_escalate", "sem_escalate_restart"]
N_REPLICATES = 3
REAL_STUCK_THRESHOLD = 2   # matches phase1/rtllm_pilot_runner.py exactly
TEMPERATURE = 0.1          # matches Phase 1 -- see module docstring

RESULTS_ROOT = os.path.join(_HERE, "results", "set1_run")
RAW_CLASSIC_ROOT = os.path.join(RESULTS_ROOT, "_raw_classic")
RAW_ESCALATION_ROOT = os.path.join(RESULTS_ROOT, "_raw_escalation")
MASTER_LOG = os.path.join(RESULTS_ROOT, "master_log.json")
INCIDENTS_LOG = os.path.join(RESULTS_ROOT, "incidents.log")
STAGED_ROOT = os.path.join(RESULTS_ROOT, "_staged")

# ── $OLLAMA_HOST-aware client (same pattern as twin_run_runner.py's
# _ollama_client -- NOT stitch_runner_hpc.py's hardcoded-localhost:11434
# OLLAMA_CLIENT). This job starts its OWN ollama serve (see
# set1_run.slurm) bound to whatever $OLLAMA_HOST that script sets; the
# client here reads the SAME env var so the two are structurally bound
# to agree, not just hoped to. Default is Ollama's own standard default,
# for local/laptop testing of this script in isolation only -- on HPC,
# set1_run.slurm always sets this explicitly.
OLLAMA_HOST = os.environ.get("OLLAMA_HOST", "127.0.0.1:11434")
_OLLAMA_BASE_URL = f"http://{OLLAMA_HOST}/v1"
_ollama_client = OpenAI(base_url=_OLLAMA_BASE_URL, api_key="ollama")


def _call_ollama_set1(model, messages):
    """Same shape as stitch_runner_hpc.call_llm()'s own Ollama branch,
    but via `_ollama_client` (bound to $OLLAMA_HOST) instead of that
    file's hardcoded-localhost:11434 client. Temperature is stated
    explicitly at 0.1 rather than omitted -- it happens to already be
    that file's own hardcoded default, but stated here so this doesn't
    silently drift if either default ever changes independently (same
    "state it explicitly" discipline twin_run_runner.py's own
    _call_ollama() already follows for its T=0.5)."""
    resp = _ollama_client.chat.completions.create(
        model=model, messages=messages, temperature=TEMPERATURE)
    u = getattr(resp, "usage", None)
    pt = getattr(u, "prompt_tokens", 0) if u else 0
    ct = getattr(u, "completion_tokens", 0) if u else 0
    return resp.choices[0].message.content, pt, ct


# Bound onto BOTH modules' own separate name bindings -- `from X import
# call_llm` in escalation_runner_hpc.py creates an independent local
# name, rebinding stitch_runner_hpc.call_llm alone would NOT change what
# escalation_runner_hpc.py actually calls. This exact "two separate
# bindings" gotcha is already documented at length in
# phase1/rtllm_pilot_runner.py's history (the superseded monkeypatch) --
# applying the lesson here, not re-learning it.
sr.call_llm = _call_ollama_set1
import escalation_runner_hpc as _erh  # noqa: E402
_erh.call_llm = _call_ollama_set1


def _verify_ollama_models():
    """FAIL LOUDLY before any cell runs if the Ollama server this process
    is about to talk to doesn't already have all 3 needed models --
    belt-and-suspenders on top of set1_run.slurm's own bash-level check,
    same pattern as twin_run_runner.py's _verify_ollama_models(). Does
    NOT pull inline (would eat this job's own wall-clock budget)."""
    try:
        resp = _ollama_client.models.list()
        available = {m.id for m in resp.data}
    except Exception as e:
        print(f"FATAL: could not reach the Ollama server at {_OLLAMA_BASE_URL} "
              f"({type(e).__name__}: {e}). Is `ollama serve` actually running "
              f"in this job, and does $OLLAMA_HOST match what it's bound to?")
        sys.exit(1)
    missing = [m for m in MODELS if m not in available]
    if missing:
        print(f"FATAL: Ollama server at {_OLLAMA_BASE_URL} is missing: {missing}. "
              f"Available: {sorted(available)}. Run "
              f"phase2/pull_ollama_models.slurm once (it already pulls exactly "
              f"these 3 models -- Set 1 reuses Set 2's pull, see "
              f"docs/FULL_RUN_RUNBOOK.md), then resubmit.")
        sys.exit(1)
    print(f"Ollama models confirmed present at {_OLLAMA_BASE_URL}: {MODELS}")


# ── RTLLM staging (identical pattern to phase1/rtllm_pilot_runner.py) ──
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


def _count_stuck_fires(err_type_seq, threshold=REAL_STUCK_THRESHOLD):
    consecutive, last_err, fires, fire_iters = 0, None, 0, []
    for i, et in enumerate(err_type_seq, start=1):
        if et in (None, "PASS"):
            continue
        if et == last_err:
            consecutive += 1
        else:
            consecutive, last_err = 1, et
        if consecutive >= threshold:
            fires += 1
            fire_iters.append(i)
            consecutive = 0
    return fires, fire_iters


# ── output relocation ────────────────────────────────────────────────────
def _relocate(src_dir, dest_dir):
    """sr.run_one_condition()/run_one_replicate()'s own internal path
    composition (RESULTS_DIR/<safe_model>/<condition>/<module>[/replicate_N])
    doesn't match this run's specified final layout
    (<module>/<safe_model>/<condition>/rep<k>) -- deliberately NOT fixed
    by editing stitch_runner_hpc.py/escalation_runner_hpc.py (both are
    shared, already-verified code; reordering their internal layout
    would also change Set 2's/every other runner's output shape). Instead,
    each cell writes to a shared `_raw_*` staging prefix and is moved
    into its real final location immediately after its own run call
    returns -- safe under this script's strictly sequential execution,
    since the next cell that could reuse the same raw path never starts
    until this one's move has already completed.

    Removes any stale `dest_dir` first (a prior crashed attempt's
    partial output) so a retried cell doesn't merge with old files."""
    if not os.path.isdir(src_dir):
        raise RuntimeError(f"expected raw output at {src_dir!r}, found nothing -- "
                            f"the run call above should have created it")
    if os.path.exists(dest_dir):
        shutil.rmtree(dest_dir)
    os.makedirs(os.path.dirname(dest_dir), exist_ok=True)
    shutil.move(src_dir, dest_dir)


def _final_dir(design, model, condition, replicate):
    safe_model = model.replace(":", "_").replace(".", "")
    return os.path.join(RESULTS_ROOT, design, safe_model, condition, f"rep{replicate}")


# ── per-cell runners ─────────────────────────────────────────────────────
def _run_classic(design, category, model, condition, spec, testbench_dir, deps, replicate):
    sr.STUCK_THRESHOLD = REAL_STUCK_THRESHOLD
    sr.TESTBENCH_DIR = testbench_dir
    safe_model = model.replace(":", "_").replace(".", "")
    sr.RESULTS_DIR = RAW_CLASSIC_ROOT

    m = sr.run_one_condition(
        spec=spec, module_name=design, model=model, condition=condition, dependencies=deps,
        benchmark="rtllm",
    )
    raw_dir = os.path.join(RAW_CLASSIC_ROOT, safe_model, condition, design)
    _relocate(raw_dir, _final_dir(design, model, condition, replicate))

    err_seq = [it.get("err_type") for it in m["per_iter_detail"]]
    fires, fire_iters = _count_stuck_fires(err_seq)

    return {
        "module": design, "category": category, "model": model, "condition": condition,
        "run_replicate": replicate, "iteration_cap": sr.MAX_RETRIES,
        "pass": m["pass"], "iterations_to_pass": m["iterations_to_pass"],
        "total_iterations": m["total_iterations"], "total_tokens": m["total_tokens"],
        "semantic_fired": m["semantic_fired"], "unknown_outcomes": m.get("unknown_outcomes", 0),
        "stuck_threshold_fires": fires, "stuck_threshold_fire_iters": fire_iters,
        "escalation_iteration": None, "fired_escalate": None,
        "restart_iterations": None, "restart_threshold_reached_iterations": None,
        "restart_preempted_by_stuck_threshold": None,
    }


def _run_escalation(design, category, model, condition, spec, testbench_dir, deps, replicate):
    config = EscalationConfig(
        escalate_after=2, restart_after=3,
        allow_restart=(condition == "sem_escalate_restart"),
        signature_window=5, max_iterations=8,
    )
    safe_model = model.replace(":", "_").replace(".", "")

    run_log = run_one_replicate(
        spec=spec, module_name=design, model=model, condition=condition,
        run_replicate=replicate, config=config,
        testbench_dir=testbench_dir, results_dir=RAW_ESCALATION_ROOT, dependencies=deps,
        benchmark="rtllm",
    )
    raw_dir = os.path.join(RAW_ESCALATION_ROOT, safe_model, condition, design, f"replicate_{replicate}")
    _relocate(raw_dir, _final_dir(design, model, condition, replicate))

    s = run_log["summary"]
    err_seq = [it["err_type"] for it in run_log["iterations"]]
    fires, fire_iters = _count_stuck_fires(err_seq)
    semantic_fired = sum(1 for it in run_log["iterations"] if it["interpreter_invoked"])

    return {
        "module": design, "category": category, "model": model, "condition": condition,
        "run_replicate": replicate, "iteration_cap": 8,
        "pass": s["pass"], "iterations_to_pass": s["iterations_to_pass"],
        "total_iterations": s["total_iterations"], "total_tokens": s["total_tokens"],
        "semantic_fired": semantic_fired,
        "stuck_threshold_fires": fires, "stuck_threshold_fire_iters": fire_iters,
        "escalation_iteration": s["escalation_iteration"], "fired_escalate": s["fired_escalate"],
        "restart_iterations": s.get("restart_iterations"),
        "restart_threshold_reached_iterations": s.get("restart_threshold_reached_iterations"),
        "restart_preempted_by_stuck_threshold": s.get("restart_preempted_by_stuck_threshold"),
    }


# ── checkpoint / incident log (identical pattern to phase1/rtllm_pilot_runner.py) ──
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
    """Same run-autonomy boundary as every other runner in this project:
    retries transient infra failures VERBATIM, never branches on WHAT
    the exception was to change harness behavior mid-run."""
    os.makedirs(RESULTS_ROOT, exist_ok=True)
    module, model, condition, replicate = key
    ts = __import__("datetime").datetime.now().isoformat(timespec="seconds")
    status = "GIVING UP -- cell errored, logged to master_log.json, moving on" if final \
        else f"retrying (attempt {attempt+1}/{max_attempts})"
    with open(INCIDENTS_LOG, "a", encoding="utf-8") as f:
        f.write(f"[{ts}] {module} / {model} / {condition} / replicate {replicate}\n")
        f.write(f"  attempt {attempt}/{max_attempts} -- {status}\n")
        f.write(f"  exception: {type(exc).__name__}: {exc}\n")
        f.write("  traceback:\n")
        for line in traceback.format_exception(type(exc), exc, exc.__traceback__):
            f.write("    " + line)
        f.write("\n")


def _all_cells(module_pool):
    """Yields (design, category, rel, model, condition, replicate) for
    every cell in the study, in run order. Shared by --dry-run and the
    real run_all() so the two can never silently disagree on scope."""
    for design, category, rel in module_pool:
        for model in MODELS:
            for condition in CONDITIONS:
                for replicate in range(1, N_REPLICATES + 1):
                    yield design, category, rel, model, condition, replicate


def run_all(module_pool):
    entries = _load_master_log()
    done = {(e["module"], e["model"], e["condition"], e["run_replicate"]) for e in entries}

    total = len(module_pool) * len(MODELS) * len(CONDITIONS) * N_REPLICATES
    done_count = len(done)

    testbench_cache = {}
    for design, category, rel, model, condition, replicate in _all_cells(module_pool):
        if design not in testbench_cache:
            testbench_cache[design] = _stage_testbench(design, rel) + (_get_spec(rel),)
        testbench_dir, deps, spec = testbench_cache[design]

        key = (design, model, condition, replicate)
        if key in done:
            continue

        done_count += 1
        print(f"\n[{done_count}/{total}] {design} / {model} / {condition} / rep {replicate}")

        entry = None
        last_exc = None
        for attempt in range(1, RETRY_ATTEMPTS + 1):
            try:
                if condition in ("baseline", "sem_adv"):
                    entry = _run_classic(design, category, model, condition, spec, testbench_dir, deps, replicate)
                else:
                    entry = _run_escalation(design, category, model, condition, spec, testbench_dir, deps, replicate)
                entry["error"] = None
                entry["attempts"] = attempt
                break
            except Exception as e:
                last_exc = e
                print(f"  ERROR (attempt {attempt}/{RETRY_ATTEMPTS}): {e}")
                _log_incident(key, attempt, RETRY_ATTEMPTS, e, final=(attempt == RETRY_ATTEMPTS))

        if entry is None:
            entry = {
                "module": design, "category": category, "model": model, "condition": condition,
                "run_replicate": replicate, "error": f"{type(last_exc).__name__}: {last_exc}",
                "attempts": RETRY_ATTEMPTS,
            }

        entries.append(entry)
        _save_master_log(entries)

    print(f"\nDone. {len(entries)} entries -> {MASTER_LOG}")
    n_errored = sum(1 for e in entries if e.get("error"))
    if n_errored:
        print(f"{n_errored} cell(s) errored after {RETRY_ATTEMPTS} attempts each -- see {INCIDENTS_LOG}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true",
                         help="Print the total cell count and exit 0 -- does NOT "
                              "touch Ollama or iverilog. Pre-flight sanity check "
                              "before ever launching the real job.")
    args = parser.parse_args()

    module_pool = _load_module_pool()
    total = len(module_pool) * len(MODELS) * len(CONDITIONS) * N_REPLICATES

    print(f"Modules ({len(module_pool)}): {[m[0] for m in module_pool]}")
    print(f"Models: {MODELS}")
    print(f"Conditions: {CONDITIONS}")
    print(f"Replicates: N={N_REPLICATES}")
    print(f"Temperature: {TEMPERATURE}")
    print(f"Ollama client bound to: {_OLLAMA_BASE_URL}")
    print(f"Total runs: {total}")

    if args.dry_run:
        assert total == 1512, (
            f"dry-run expected exactly 1512 total runs (42 modules x 3 models "
            f"x 4 conditions x N=3), computed {total} -- STOP, do not launch."
        )
        print("DRY RUN OK: exactly 1512 cells, as locked. Not touching Ollama/iverilog.")
        sys.exit(0)

    _verify_ollama_models()
    run_all(module_pool)
