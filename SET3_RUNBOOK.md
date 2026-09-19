# Set 3 (Scale Ladder) — Runbook

Print this and follow it on the HPC terminal, in order. No design
discussion here — that lives in `CC_SET3_SCALE_LADDER_BRIEF.md` and
`phase2/set3_runner.py`'s own module docstring. Read those first if you
haven't. This is a **later, single, sequential job** — by the time this
runs, Set 1 and Set 2 have already completed; there is no two-node
concurrency concern here the way `FULL_RUN_RUNBOOK.md` had to reason
about for those two.

| | Node | Partition | `--time` | Runs | Est. wall-clock | Expected sbatches |
|---|---|---|---|---|---|---|
| **Set 3** | `gpunode4` | `gpu_a100_8` | `120:00:00` | 612 | ~130–150h | 1–2 |

**Module count is locked at 17** — the recoverable-band subset of the
42-module pool, `difficulty_tier == "recoverable"` in
`phase2/twin_analysis_SET2/module_categories.json` (Twin's own tier
assignment, reused verbatim — see `set3_runner.py`'s module docstring for
why the tier is never re-derived here). Ceilings and floors are
deliberately excluded: Set 1 already showed all four STITCH conditions
coincide there (`phase2/SET1_ANALYSIS.md`'s tier-split section), so
re-paying for them at these three much slower (14B–32B) models would
waste wall-clock on cells with no discriminating power. **Do not change
this list** without flagging it and stopping — it's locked, same
discipline as the 42-module exclusion in `FULL_RUN_RUNBOOK.md`.

**A note on the brief's own stale path**: `CC_SET3_SCALE_LADDER_BRIEF.md`
references `phase2/twin_analysis/module_categories.json` — that
directory was renamed to `phase2/twin_analysis_SET2/` earlier this
session (see the Twin analysis delivery). `set3_runner.py` reads the
current, correct path; this runbook's scp commands below reflect it too.

---

## 1. Prereqs check

- **Set 1 / Set 2 already complete** — this run's whole point is
  comparing against Set 1's tier-split result on the identical 17
  modules, same conditions, same temperature (`phase2/SET1_ANALYSIS.md`).
  If Set 1 hasn't finished, there's nothing to compare against yet.
- **Scratch was fully wiped** — Set 3 no longer reuses AutoChipHPC's
  already-pulled `qwen2.5-coder:14b`/`qwen2.5-coder:32b`/`gemma3:27b`
  (that tree is gone). It now pulls and owns its own copy under
  `OLLAMA_MODELS=/scratch/soumyaj/Set3_HPC/ollama_models` (Section 6
  below, via `pull_ollama_models_set3.slurm`), and the `venv` builds
  fresh rather than symlinking to `RTLCoderHPC`'s (also gone/not
  assumed present — Section 2).
- **`ollama` binary and `oss-cad-suite`**: `set3_run.slurm` now points
  `PATH` at `/scratch/soumyaj/Set3_HPC/bin` for `ollama` (not
  `AutoChipHPC/bin`, wiped) and `/scratch/soumyaj/oss-cad-suite/bin` for
  `iverilog`/`verilator`/`yosys` (being re-extracted there post-wipe).
  **Confirm both actually exist before proceeding** — this runbook
  doesn't cover how the `ollama` binary itself lands at
  `Set3_HPC/bin` (copy it there, or build/install fresh, whichever this
  cluster's setup calls for) or when `oss-cad-suite`'s re-extraction
  finishes; treat both as blocking prerequisites, not assumptions.
- **Hardened-runner commit**: as of this runbook, `set3_runner.py` /
  `set3_run.slurm` / `pull_ollama_models_set3.slurm` / this file are
  **staged, not committed** (per this project's standing rule: stage and
  propose, you run `git commit`). **Commit before deploying anything
  below** so what you scp actually matches a real commit you can point
  to later.

---

## 2. Set 3 scratch dir setup

```
mkdir -p /scratch/soumyaj/Set3_HPC/{logs,results,src/interpreter,bin,ollama_models}
python3 -m venv /scratch/soumyaj/Set3_HPC/venv
source /scratch/soumyaj/Set3_HPC/venv/bin/activate
pip install openai
deactivate
```

**venv builds fresh here** — the scratch wipe took the `RTLCoderHPC`
venv this used to symlink to as well, so there's nothing left to
symlink; a plain `python -m venv` + `pip install openai` is the whole
dependency list (no `torch`/`transformers` needed — Ollama-only, no
RTLCoder, same as Set 1). No `HF_HOME`/`env.sh` needed either.
`RTLLM_ROOT`/`STITCH_INTERPRETER_DIR`/`TASK_A_SCREEN_JSON`/
`MODULE_CATEGORIES_JSON` are exported directly inside `set3_run.slurm`,
not from a separate `env.sh`.

**`bin/` and `ollama_models/` are created empty above** — `bin/` needs
the `ollama` binary placed into it (this runbook doesn't prescribe how;
copy it from wherever it's kept, or reinstall fresh) before Section 6's
pull step or Section 7's launch can succeed; `ollama_models/` is filled
by Section 6's pull job, not by hand.

---

## 3. File deployment

Same flat-deploy convention as Set 1 (`FULL_RUN_RUNBOOK.md` §3) —
`src/interpreter/` deploys as an actual subdirectory (the `mkdir` above
already set it up); `STITCH_INTERPRETER_DIR` finds it via the env var
`set3_run.slurm` sets, not a relative-path guess.

```
# On your laptop, from the STITCH repo root
scp phase2\set3_runner.py phase2\set3_run.slurm phase2\pull_ollama_models_set3.slurm `
    phase2\stitch_runner_hpc.py phase2\escalation_runner_hpc.py `
    phase1\error_signature.py phase1\escalation_state.py `
    phase1\results\rtllm_pilot\task_a_screen.json `
    phase2\twin_analysis_SET2\module_categories.json `
    soumyaj@hpc.bits-hyderabad.ac.in:/scratch/soumyaj/Set3_HPC/

scp src\interpreter\pass_detection.py src\interpreter\stitch_interpreter.py `
    soumyaj@hpc.bits-hyderabad.ac.in:/scratch/soumyaj/Set3_HPC/src/interpreter/
```

This is Set 1's exact dependency set (`FULL_RUN_RUNBOOK.md` §3b) plus two
additions — `module_categories.json` (Set 3's recoverable-band filter
input, which Set 1 never needed) and `pull_ollama_models_set3.slurm`
(Set 1 never needed its own pull script either, since it reused Set 2's
pull; Set 3 now needs one of its own post-wipe — see Section 6).
`stitch_interpreter.py` is re-scp'd fresh here even if a copy already
exists from an earlier deploy — don't assume it's current, same
discipline every prior deploy in this project follows.

---

## 4. Verification greps on HPC before launch

```
cd /scratch/soumyaj/Set3_HPC

# The precise old-bug signature -- confirms Bug #3's ORIGINAL hardcoded
# check is completely gone from the deployed stitch_runner_hpc.py.
grep -c 'ALL TESTS PASSED" not in output' stitch_runner_hpc.py
# expect: 0

# detect_outcome is actually wired in
grep -c "detect_outcome" stitch_runner_hpc.py
# expect: >= 2

# Bug #2 fix (vvp cwd) still present
grep -c "cwd=iter_dir" stitch_runner_hpc.py
# expect: >= 2

# set3_runner.py never reimplements pass detection -- any "PASS"/
# "Your Design Passed"/"ALL TESTS PASSED" hit outside detect_outcome()
# itself should be bookkeeping only (e.g. an err_type comparison that
# CONSUMES detect_outcome()'s answer, never a string match against raw
# sim output). Verified locally before this runbook was written: the
# only hit in set3_runner.py is `if et in (None, "PASS")` in
# _count_stuck_fires(), consuming an already-assigned label -- same
# "expected, not a red flag" shape FULL_RUN_RUNBOOK.md §4 documents for
# stitch_runner_hpc.py's own 6 bookkeeping hits.
grep -n '"PASS"\|"Your Design Passed"\|"ALL TESTS PASSED"' set3_runner.py
# expect: exactly one hit, the _count_stuck_fires() bookkeeping line above

# module_categories.json deployed and has exactly 17 recoverable-band modules
python3 -c "import json; d=json.load(open('module_categories.json')); r=[m for m,i in d.items() if i['difficulty_tier']=='recoverable']; print(len(r), sorted(r))"
# expect: 17 [...]
```

If any of these come back wrong: **STOP. Do not launch.** Re-scp the
file and re-check — do not patch by hand on the cluster.

---

## 5. Dry-run on HPC

```
cd /scratch/soumyaj/Set3_HPC
export STITCH_INTERPRETER_DIR=/scratch/soumyaj/Set3_HPC/src/interpreter
export TASK_A_SCREEN_JSON=/scratch/soumyaj/Set3_HPC/task_a_screen.json
export MODULE_CATEGORIES_JSON=/scratch/soumyaj/Set3_HPC/module_categories.json
export RTLLM_ROOT=/scratch/soumyaj/RTLCoderHPC/RTLLM
python set3_runner.py --dry-run
# expect: "DRY RUN OK: exactly 612 cells, as locked."
```

Touches neither Ollama nor iverilog — pure module-pool + count
validation. If the total is wrong, **STOP** — don't launch a
differently-scoped study. (Locally, before deploying, this was already
verified against a laptop RTLLM checkout: `RTLLM_ROOT=<local path>
python phase2/set3_runner.py --dry-run` → exactly 612, 17 modules listed,
matching `module_categories.json`'s recoverable set exactly.)

---

## 6. Pull the 3 models (only if not already present)

```
sbatch /scratch/soumyaj/Set3_HPC/pull_ollama_models_set3.slurm
tail -f /scratch/soumyaj/Set3_HPC/logs/ollama_pull_*.log
```

Pulls `qwen2.5-coder:14b`, `qwen2.5-coder:32b`, `gemma3:27b` into Set 3's
own `OLLAMA_MODELS=/scratch/soumyaj/Set3_HPC/ollama_models` — **post-wipe,
this is no longer a reuse of AutoChipHPC's already-pulled copy** (that
tree is gone); Set 3 now owns its own, mirroring the exact pattern
`phase2/pull_ollama_models.slurm` already established for Set 1/Set 2's
3 (different, smaller) models. Run this **once**, before ever launching
`set3_run.slurm`. Verify afterward:

```
export OLLAMA_MODELS=/scratch/soumyaj/Set3_HPC/ollama_models
ollama list | grep -E "qwen2.5-coder:14b|qwen2.5-coder:32b|gemma3:27b"
```

Expect all 3 to appear. `set3_run.slurm` fails loudly (step (c) in the
script) and `set3_runner.py`'s own `_verify_ollama_models()` fails
loudly again at the Python level if this step was skipped and a model
turns out to be missing at launch time — but don't rely on either as a
substitute for checking here first.

---

## 7. Launch

```
sbatch /scratch/soumyaj/Set3_HPC/set3_run.slurm
squeue -u soumyaj   # confirm queued/running
```

No two-node-independence checklist needed here (unlike
`FULL_RUN_RUNBOOK.md` §7) — Set 3 runs alone, after Set 1/Set 2 have
already finished, on the same `gpunode4`/`gpu_a100_8` Set 1 used.

---

## 8. Monitoring

```
squeue -u soumyaj
tail -f /scratch/soumyaj/Set3_HPC/logs/set3_*.log
```

Progress one-liner (use `master_log.json`'s entry count, not just the
console log, which can lag when redirected — same lesson as every prior
overnight run in this project):

```
python3 -c "import json; d=json.load(open('/scratch/soumyaj/Set3_HPC/results/set3_run/master_log.json')); print(len(d), '/ 612 done;', sum(1 for e in d if e.get('error')), 'errored')"
```

---

## 9. Resubmit behavior

When the job hits its `--time` cap, it stops mid-run (SLURM kills it) —
**re-submit the exact same script**:

```
sbatch /scratch/soumyaj/Set3_HPC/set3_run.slurm
```

`set3_runner.py` skips already-completed `(module, model, condition,
replicate)` keys via `master_log.json` — no flag needed, no separate
"part 2" script. At 14B–32B inference pace, expect 1–2 sbatches total
depending on how close the 120h cap comes to the ~130–150h estimate.

---

## 10. Download results back to laptop

```
scp -r soumyaj@hpc.bits-hyderabad.ac.in:/scratch/soumyaj/Set3_HPC/logs ./set3_logs/
scp -r soumyaj@hpc.bits-hyderabad.ac.in:/scratch/soumyaj/Set3_HPC/results/set3_run ./set3_results/
```

(`phase2/results/` and any local mirror of these are gitignored — land
wherever you point the scp, not committed either way.)

---

## Analysis (separate task, after the run completes)

Noted here for planning only, per `CC_SET3_SCALE_LADDER_BRIEF.md`'s own
final section — not part of this setup:

- Recompute the recoverable-band pass rate per condition for each of the
  3 larger models, same shape as Set 1's tier table
  (`phase2/set1_analysis/fig2_tier_split.py`'s recoverable-band rows).
- **The key comparison**: is `sem_adv` still below `baseline` on the
  recoverable band for these larger models, as it was for the 3 small
  models (30.7% vs. 35.3%, `phase2/SET1_ANALYSIS.md`'s tier-split
  section)? If yes, the harmful regime is capability-independent. If it
  shrinks or vanishes at 32B, that's the more nuanced finding and gets
  its own subsection.
- Extend the capability-ladder figure (currently 5 model-conditions from
  Twin, `phase2/twin_analysis_SET2/fig2.py`) with these 3 larger models
  to show the full 4B–32B span.
