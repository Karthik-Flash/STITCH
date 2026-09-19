"""
phase2/set3_runner.py -- Set 3: the scale ladder. Same STITCH-conditions
sweep as Set 1 (baseline/sem_adv/sem_escalate/sem_escalate_restart), but
on 3 larger Ollama models (14B-32B) the conference paper's Table 2 tested
and the extension has not yet run, restricted to the recoverable-band
module pool only. Runs on gpunode4 (A100, gpu_a100_8), same partition
Set 1 used -- see CC_SET3_SCALE_LADDER_BRIEF.md for the research
question this answers: does the harmful regime (`sem_adv` below
`baseline` on the recoverable band, `phase2/SET1_ANALYSIS.md`'s tier-split
result) persist as model capability rises from 4B to 32B, or does it
vanish?

Structurally identical to phase2/set1_runner.py (that file's own
docstring/comments explain the shared plumbing in full -- read it first;
only the differences are re-documented here, not the whole design).

SCOPE: 17 modules (recoverable-band only, from Twin's
module_categories.json -- see below) x 3 Ollama models x 4 conditions x
N=3 = 612 runs.

  Modules:    the 17 modules with difficulty_tier == "recoverable" in
              phase2/twin_analysis_SET2/module_categories.json (NOTE:
              the brief this script was built from, written before that
              directory's rename this session, says
              "phase2/twin_analysis/module_categories.json" -- that path
              no longer exists; the current location is
              phase2/twin_analysis_SET2/module_categories.json, used
              here). Tier assignment is NOT re-derived -- loaded
              verbatim and asserted to match exactly (see
              _load_recoverable_names()). Ceiling/floor modules are
              deliberately excluded: Set 1 already showed all four
              conditions coincide there (phase2/SET1_ANALYSIS.md's
              tier-split section), so re-paying for them at these three
              models' much slower inference would burn wall-clock on
              cells with no discriminating power.
  Models:     qwen2.5-coder:14b, qwen2.5-coder:32b, gemma3:27b -- the
              three conference-paper (Table 2) models the extension
              hasn't run yet. Already pulled on HPC under
              /scratch/soumyaj/AutoChipHPC/ollama_models (a DIFFERENT
              OLLAMA_MODELS directory from Set 1/2's RTLCoderHPC one --
              these three were pulled for the AutoChip project, not this
              one; see set3_run.slurm).
  Conditions: baseline, sem_adv, sem_escalate, sem_escalate_restart --
              identical set to Set 1 (same 4 condition strings this
              codebase's runners require; see set1_runner.py's own
              comment on why the brief's "sem_esc"/"sem_esc_restart"
              shorthand isn't used verbatim). The STITCH-conditions axis
              is the whole point of this run (harmful-regime
              persistence at scale) -- unlike Twin, baseline-only is NOT
              acceptable here.
  Replicates: N=3.
  Sampling:   T=0.1 -- matched to Set 1 (NOT Twin's T=0.5), because this
              run's question is directly comparable to Set 1's own
              tier-split result on the same 17 modules, same
              conditions, same temperature, different models only.

Module-pool resolution: the (category, relative-path-under-RTLLM_ROOT)
information a design needs for testbench staging isn't stored in
module_categories.json (which only carries tier/functional_class, and
for former-"Miscellaneous" modules the functional_class has been split
into arithmetic_misc/protocol/signal_processing sub-classes that do NOT
match RTLLM's own on-disk top-level category directories -- see
phase2/twin_analysis_SET2/categorize.py's docstring). So this script
reuses set1_runner.py's own proven discovery logic (task_a_screen.json +
directory walk -- the exact same 42-module pool Set 1 uses) purely to
resolve each recoverable-band module's real (category, rel) pair, then
filters that 42-module pool down to the 17 names module_categories.json
lists as "recoverable". The TIER assignment itself is never re-derived,
only the on-disk path lookup is reused -- see _load_module_pool() below.

Pass detection: EVERY call site below routes through the ALREADY-hardened
sr.run_one_condition()/escalation_runner_hpc.run_one_replicate(), which
route through detect_outcome(sim_log, "rtllm") internally
(src/interpreter/pass_detection.py) -- nothing here reimplements any part
of that.

Runs on gpunode4 via stitch_runner_hpc.py (the Linux-native HPC port)
and phase2/escalation_runner_hpc.py -- identical dependency set to Set 1.

Output layout (see _relocate() for why a post-run move is needed):
  <RESULTS_ROOT>/<module>/<safe_model>/<condition>/rep<k>/
    iter_<i>/{feedback.txt, llm_response.txt, <module>.v, sim_log.txt},
    plus metrics.json (classic conditions) or run_log.json (escalation
    conditions) at the rep<k>/ level.
  <RESULTS_ROOT>/master_log.json -- one entry per completed cell,
    resumable (same incremental-checkpoint pattern as every other
    runner in this project).

Usage:
  python phase2/set3_runner.py --dry-run   # prints exactly 612, exits 0
  python phase2/set3_runner.py             # the real run
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
EXPECTED_MODULE_COUNT = 17

# task_a_screen.json is gitignored (phase1/.gitignore) and never
# committed -- on HPC it's scp'd flat alongside this script (see
# SET3_RUNBOOK.md); locally it lives at its real repo path. Try the
# flat-deploy location first, fall back to the repo-relative dev path.
# Identical resolution logic to set1_runner.py.
_FLAT_SCREEN_JSON = os.path.join(_HERE, "task_a_screen.json")
_DEV_SCREEN_JSON = os.path.join(_HERE, "..", "phase1", "results", "rtllm_pilot", "task_a_screen.json")
TASK_A_SCREEN_JSON = os.environ.get("TASK_A_SCREEN_JSON") or (
    _FLAT_SCREEN_JSON if os.path.exists(_FLAT_SCREEN_JSON) else _DEV_SCREEN_JSON
)

# module_categories.json (Twin's tier assignment, REUSED VERBATIM -- see
# module docstring). Same flat-deploy-first, dev-path-fallback pattern.
# On HPC this is scp'd flat alongside this script (see SET3_RUNBOOK.md);
# locally it lives at its real current repo path (NOTE the rename this
# session -- phase2/twin_analysis/ -> phase2/twin_analysis_SET2/).
_FLAT_CATEGORIES_JSON = os.path.join(_HERE, "module_categories.json")
_DEV_CATEGORIES_JSON = os.path.join(_HERE, "twin_analysis_SET2", "module_categories.json")
MODULE_CATEGORIES_JSON = os.environ.get("MODULE_CATEGORIES_JSON") or (
    _FLAT_CATEGORIES_JSON if os.path.exists(_FLAT_CATEGORIES_JSON) else _DEV_CATEGORIES_JSON
)

RTLLM_ROOT = os.environ.get("RTLLM_ROOT", "/scratch/soumyaj/RTLCoderHPC/RTLLM")
# Deliberately the SAME checkout Set 1/Set 2 read -- RTLLM is read-only
# I/O for every job; sharing one checkout avoids yet another
# multi-hundred-MB clone. See FULL_RUN_RUNBOOK.md's two-node-independence
# section (Set 3 extends the same reasoning to a third node/job).


def _load_recoverable_names(categories_json=MODULE_CATEGORIES_JSON):
    """Returns the sorted set of module names with difficulty_tier ==
    "recoverable" in module_categories.json -- loaded verbatim, never
    recomputed (per the brief: "the tier assignment is already fixed by
    the Twin analysis and must match it exactly"). Hard-asserts exactly
    17 -- a silent change to Twin's categorization must stop this script
    immediately, not quietly run a differently-scoped study."""
    if not os.path.exists(categories_json):
        print(f"FATAL: {categories_json} not found. Deploy it alongside "
              f"this script (see SET3_RUNBOOK.md) -- it's Twin's own "
              f"tier assignment (phase2/twin_analysis_SET2/categorize.py's "
              f"output); this script does not re-derive it.")
        sys.exit(1)
    with open(categories_json, encoding="utf-8") as f:
        categories = json.load(f)
    recoverable = sorted(m for m, info in categories.items() if info["difficulty_tier"] == "recoverable")
    assert len(recoverable) == EXPECTED_MODULE_COUNT, (
        f"expected exactly {EXPECTED_MODULE_COUNT} recoverable-band modules "
        f"in {categories_json}, got {len(recoverable)}. HARD STOP -- do not "
        f"silently proceed with a different-sized study; investigate "
        f"module_categories.json first (has Twin's categorization changed?)."
    )
    return set(recoverable)


def _load_module_pool(rtllm_root=RTLLM_ROOT, task_a_screen_json=TASK_A_SCREEN_JSON,
                       categories_json=MODULE_CATEGORIES_JSON):
    """Returns [(design, category, relative_path_under_rtllm_root), ...]
    for the 17 recoverable-band modules, sorted by (category, design) for
    a deterministic run order. Discovery mechanics (task_a_screen.json +
    directory walk) are IDENTICAL to set1_runner.py's own
    _load_module_pool() -- reused here only to resolve each recoverable
    module's real on-disk (category, rel) pair, since module_categories.json
    doesn't carry that (see module docstring). The recoverable-band NAME
    filter itself comes exclusively from _load_recoverable_names(); tier
    assignment is never re-derived from task_a_screen.json or anywhere
    else."""
    recoverable_names = _load_recoverable_names(categories_json)

    if not os.path.exists(task_a_screen_json):
        print(f"FATAL: {task_a_screen_json} not found. Deploy it alongside "
              f"this script (see SET3_RUNBOOK.md) -- it's the "
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

    found = [t for t in found if t[0] in recoverable_names]
    found.sort(key=lambda t: (t[1], t[0]))

    found_names = {t[0] for t in found}
    missing = recoverable_names - found_names
    if missing:
        print(f"WARNING: {len(missing)} recoverable-band module(s) from "
              f"module_categories.json were not found under {rtllm_root} "
              f"among task_a_screen.json's compatible pool: {sorted(missing)}")

    assert len(found) == EXPECTED_MODULE_COUNT, (
        f"expected exactly {EXPECTED_MODULE_COUNT} recoverable-band modules "
        f"after path resolution, got {len(found)}. HARD STOP -- do not "
        f"silently proceed with a different-sized study; investigate "
        f"module_categories.json / task_a_screen.json / the RTLLM checkout "
        f"first."
    )
    return found


# ── config (Set-1-comparable, per the brief) ────────────────────────────
MODELS = ["qwen2.5-coder:14b", "qwen2.5-coder:32b", "gemma3:27b"]
CONDITIONS = ["baseline", "sem_adv", "sem_escalate", "sem_escalate_restart"]
N_REPLICATES = 3
REAL_STUCK_THRESHOLD = 2   # matches phase1/rtllm_pilot_runner.py / set1_runner.py exactly
TEMPERATURE = 0.1          # matches Set 1 -- see module docstring

RESULTS_ROOT = os.path.join(_HERE, "results", "set3_run")
RAW_CLASSIC_ROOT = os.path.join(RESULTS_ROOT, "_raw_classic")
RAW_ESCALATION_ROOT = os.path.join(RESULTS_ROOT, "_raw_escalation")
MASTER_LOG = os.path.join(RESULTS_ROOT, "master_log.json")
INCIDENTS_LOG = os.path.join(RESULTS_ROOT, "incidents.log")
STAGED_ROOT = os.path.join(RESULTS_ROOT, "_staged")

# ── $OLLAMA_HOST-aware client (identical pattern to set1_runner.py /
# twin_run_runner.py -- NOT stitch_runner_hpc.py's hardcoded-localhost
# OLLAMA_CLIENT). This job starts its OWN ollama serve (see
# set3_run.slurm) bound to whatever $OLLAMA_HOST that script sets; the
# client here reads the SAME env var so the two are structurally bound
# to agree, not just hoped to.
OLLAMA_HOST = os.environ.get("OLLAMA_HOST", "127.0.0.1:11434")
_OLLAMA_BASE_URL = f"http://{OLLAMA_HOST}/v1"
_ollama_client = OpenAI(base_url=_OLLAMA_BASE_URL, api_key="ollama")


def _call_ollama_set3(model, messages):
    """Same shape as set1_runner.py's _call_ollama_set1() -- via
    `_ollama_client` (bound to $OLLAMA_HOST), temperature stated
    explicitly at 0.1 rather than relying on any file's own default."""
    resp = _ollama_client.chat.completions.create(
        model=model, messages=messages, temperature=TEMPERATURE)
    u = getattr(resp, "usage", None)
    pt = getattr(u, "prompt_tokens", 0) if u else 0
    ct = getattr(u, "completion_tokens", 0) if u else 0
    return resp.choices[0].message.content, pt, ct


# Bound onto BOTH modules' own separate name bindings -- same "two
# separate bindings" gotcha set1_runner.py's own comment documents at
# length (originally learned from phase1/rtllm_pilot_runner.py's
# superseded monkeypatch history).
sr.call_llm = _call_ollama_set3
import escalation_runner_hpc as _erh  # noqa: E402
_erh.call_llm = _call_ollama_set3


def _verify_ollama_models():
    """FAIL LOUDLY before any cell runs if the Ollama server this process
    is about to talk to doesn't already have all 3 needed models --
    belt-and-suspenders on top of set3_run.slurm's own bash-level check,
    same pattern as set1_runner.py/twin_run_runner.py. Does NOT pull
    inline (would eat this job's own wall-clock budget) -- these 3
    models are already pulled under AutoChipHPC/ollama_models for the
    AutoChip project, per the brief; if they're missing here, something
    is wrong with $OLLAMA_MODELS, not with this job's own responsibility
    to pull them."""
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
              f"Available: {sorted(available)}. Set 3 does NOT pull inline -- "
              f"these 3 models are expected to already be present under "
              f"OLLAMA_MODELS=/scratch/soumyaj/AutoChipHPC/ollama_models "
              f"(pulled for the AutoChip project). Confirm with `ollama list` "
              f"against that path (see SET3_RUNBOOK.md); if genuinely "
              f"missing, pull them there first, then resubmit.")
        sys.exit(1)
    print(f"Ollama models confirmed present at {_OLLAMA_BASE_URL}: {MODELS}")


# ── RTLLM staging (identical pattern to set1_runner.py / phase1/rtllm_pilot_runner.py) ──
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


# ── output relocation (identical pattern to set1_runner.py) ─────────────
def _relocate(src_dir, dest_dir):
    """See set1_runner.py's own _relocate() docstring for the full
    reasoning -- identical here: sr.run_one_condition()/run_one_replicate()'s
    internal path composition doesn't match this run's specified final
    layout, so each cell writes to a shared `_raw_*` staging prefix and is
    moved into its real final location immediately after its own run call
    returns. Safe under this script's strictly sequential execution."""
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


# ── per-cell runners (identical to set1_runner.py) ───────────────────────
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


# ── checkpoint / incident log (identical pattern to set1_runner.py) ─────
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
    # RTLLM_ROOT is read from $RTLLM_ROOT at module import time (see the
    # top of this file) -- same env-var-only convention set1_runner.py
    # uses, no --rtllm-root CLI flag (a flag here would silently not work
    # anyway: _load_module_pool()'s default parameter is bound to
    # RTLLM_ROOT's value at function-definition time, before __main__
    # runs, so reassigning the module-level name this late wouldn't
    # change what the no-args call below actually resolves).

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
        assert total == 612, (
            f"dry-run expected exactly 612 total runs (17 recoverable-band "
            f"modules x 3 models x 4 conditions x N=3), computed {total} -- "
            f"STOP, do not launch."
        )
        print("DRY RUN OK: exactly 612 cells, as locked. Not touching Ollama/iverilog.")
        sys.exit(0)

    _verify_ollama_models()
    run_all(module_pool)
