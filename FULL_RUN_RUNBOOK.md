# Full HPC Run — Runbook

Print this and follow it on the HPC terminal, in order. No design
discussion here — that lives in `IMP_PHASE2_RUNNER_HARDENING_REPORT.md`,
`phase2/TWIN_RUN_PREREG.md`, and `phase2/HPC_RTLCODER_COMMANDS.md`. Read
those first if you haven't.

**Two parallel jobs, two nodes:**

| | Node | Partition | `--time` | Runs | Est. wall-clock | Expected sbatches |
|---|---|---|---|---|---|---|
| **Set 1** | `gpunode4` | `gpu_a100_8` | `120:00:00` | 1,512 | ~198h | 2 |
| **Set 2** | `gpunode6` | `gpu_h100_4` | `72:00:00` | 630 | ~82h | 2 |

Module count is **locked at 42** for both (44-compatible RTLLM pool minus
`EXCLUDE = {"edge_detect", "square_wave"}` — both pass with every output
stuck at a fixed wrong value, a confirmed defect in their own testbench's
check logic, not a `detect_outcome()` issue — see
`IMP_PHASE2_RUNNER_HARDENING_REPORT.md` §4/§6 for the investigation).
This is the RTLLM-precedent move: matches their own 50→44 exclusion for a
defect in a golden reference. **Do not change this list** without
flagging it and stopping — it's locked.

---

## 0. A note on what got added beyond the original file list

Building Set 1's runner surfaced one real, hard dependency not in the
original plan: `phase1/escalation_runner.py` (which `sem_escalate`/
`sem_escalate_restart` need) hardcodes `from stitch_runner import (...)`
— the **Windows/WSL** runner. There is no `wsl.exe` on an HPC compute
node, so it would crash the moment any tool actually ran. Fixed the only
way that doesn't touch the already-verified files: a new
`phase2/escalation_runner_hpc.py`, a faithful port following the exact
precedent `stitch_runner_hpc.py` itself already set (same pattern, one
file, import source swapped). This pulls in two more small, pure-Python
dependencies (`error_signature.py`, `escalation_state.py`) that need
deploying alongside it. All three are in the file lists below —
**flagging this now since it's beyond the original Set 1 file list**,
not silently added.

---

## 1. Prereqs check

- **Hardened-runner commit**: as of this runbook, the pass-detection
  hardening (`IMP_PHASE2_RUNNER_HARDENING_REPORT.md` and everything it
  covers) is **staged, not committed** — repo HEAD is `a66f9b5`, with
  the hardening + this Set 1/Set 2 scale-up staged on top (per this
  project's standing rule: stage and propose, you run `git commit`).
  **Commit it before deploying anything below** so what you scp actually
  matches a real commit you can point to later. Suggested message is at
  the end of this runbook's delivery summary (not here — keep this
  runbook to steps only).
- **HPC-side `verify_pass_detection.py` green output**: **not yet
  captured.** `IMP_PHASE2_RUNNER_HARDENING_REPORT.md` §4/§6 documents a
  LOCAL run only (36/44 fully green, golden side 44/44 — the number that
  matters for Bug #3's regression guard — with all 8 non-green broken
  rows individually root-caused, none a `detect_outcome()` defect). Run
  it for real on HPC before trusting anything below:
  ```
  scp d:\Projects\STITCH\phase2\verify_pass_detection.py `
    soumyaj@hpc.bits-hyderabad.ac.in:/scratch/soumyaj/RTLCoderHPC/
  # on HPC:
  cd /scratch/soumyaj/RTLCoderHPC
  export STITCH_INTERPRETER_DIR=/scratch/soumyaj/RTLCoderHPC/src/interpreter
  python verify_pass_detection.py --rtllm-root "$RTLLM_ROOT"
  ```
  Expect golden 44/44 PASS. The same 8 broken-side stragglers explained
  in the report are expected here too — don't treat them as a new
  problem, cross-check against that table.
- **Ollama models present**: `deepseek-coder:6.7b`, `gemma3:4b`,
  `llama3.1:latest` — confirm with `ollama list` against
  `OLLAMA_MODELS=/scratch/soumyaj/RTLCoderHPC/ollama_models` (Section 6
  below pulls them if missing).

---

## 2. Set 1 scratch dir setup

```
mkdir -p /scratch/soumyaj/Set1_HPC/{logs,results,src/interpreter}
ln -s /scratch/soumyaj/RTLCoderHPC/venv /scratch/soumyaj/Set1_HPC/venv
```

(No `HF_HOME`/`env.sh` needed for Set 1 — Ollama-only, no RTLCoder.
`RTLLM_ROOT`/`STITCH_INTERPRETER_DIR`/`TASK_A_SCREEN_JSON` are exported
directly inside `set1_run.slurm`, not from a separate `env.sh`.)

Also confirm Node 2's own `src/interpreter/` subdirectory exists (needed
in Section 3):

```
mkdir -p /scratch/soumyaj/RTLCoderHPC/src/interpreter
```

---

## 3. File deployment

**Both `stitch_runner_hpc.py` and `escalation_runner_hpc.py` now resolve
`src/interpreter/` via the `STITCH_INTERPRETER_DIR` env var** (both
slurm scripts set it explicitly — see Section 0's note and each script's
own comments) **rather than guessing a relative path from a flat
deploy.** This removes the ambiguity a purely-relative guess would carry
across a flat scp — deploy `src/interpreter/` as an actual subdirectory
under each node's own scratch root, exactly as the `mkdir` in Section 2
already set up, and the env var will find it correctly regardless of
where the top-level scripts themselves land.

### 3a. Node 2 — RTLCoderHPC (Set 2 / twin comparison)

```
# On your laptop, from the STITCH repo root
scp phase2\twin_run.slurm phase2\twin_run_runner.py phase2\stitch_runner_hpc.py `
    phase1\results\rtllm_pilot\task_a_screen.json `
    soumyaj@hpc.bits-hyderabad.ac.in:/scratch/soumyaj/RTLCoderHPC/

scp src\interpreter\pass_detection.py src\interpreter\stitch_interpreter.py `
    soumyaj@hpc.bits-hyderabad.ac.in:/scratch/soumyaj/RTLCoderHPC/src/interpreter/
```

(`stitch_interpreter.py` is re-scp'd here even though it may already be
present from the earlier smoke-test/pilot deploys — don't assume the
existing copy is current or in the right place; overwrite it fresh, same
discipline `HPC_RTLCODER_COMMANDS.md` already applies to
`stitch_runner_hpc.py` itself.)

### 3b. Node 1 — Set1_HPC (Set 1 / STITCH conditions)

```
# On your laptop, from the STITCH repo root
scp phase2\set1_runner.py phase2\set1_run.slurm phase2\stitch_runner_hpc.py `
    phase2\escalation_runner_hpc.py `
    phase1\error_signature.py phase1\escalation_state.py `
    phase1\results\rtllm_pilot\task_a_screen.json `
    soumyaj@hpc.bits-hyderabad.ac.in:/scratch/soumyaj/Set1_HPC/

scp src\interpreter\pass_detection.py src\interpreter\stitch_interpreter.py `
    soumyaj@hpc.bits-hyderabad.ac.in:/scratch/soumyaj/Set1_HPC/src/interpreter/
```

---

## 4. Verification greps on HPC before launch

Run these in **both** `RTLCoderHPC/` and `Set1_HPC/` (adjust the `cd`).
Expected counts below are **verified against the actual shipped files**,
not guessed — if your numbers differ, something didn't deploy as
expected; investigate before proceeding, don't rationalize a mismatch
away.

```
cd /scratch/soumyaj/RTLCoderHPC   # then repeat for /scratch/soumyaj/Set1_HPC

# The precise old-bug signature -- confirms Bug #3's ORIGINAL hardcoded
# check is completely gone, not just "some PASS-shaped text still exists"
# (see the note below on why the brief's original `'"PASS"'` grep alone
# is misleading for this file).
grep -c 'ALL TESTS PASSED" not in output' stitch_runner_hpc.py
# expect: 0

# detect_outcome is actually wired in
grep -c "detect_outcome" stitch_runner_hpc.py
# expect: >= 2 (verified real count in the shipped file: 5)

# Bug #2 fix (vvp cwd) still present
grep -c "cwd=iter_dir" stitch_runner_hpc.py
# expect: >= 2 (verified real count: 4)

# EXCLUDE constant present in both runners (adjust filename per node)
grep -c "square_wave" set1_runner.py        # Node 1 only
grep -c "square_wave" twin_run_runner.py    # Node 2 only
# expect: >= 1 each (verified real counts: 3 and 1 respectively)
```

**A note on the literal `'"PASS"'` grep** (from the original setup
brief): running it against `stitch_runner_hpc.py` returns **6**, not 0 —
this is EXPECTED, not a red flag. Those 6 are downstream bookkeeping
labels that *consume* `detect_outcome()`'s answer (`"result": "PASS" if
success else "FAIL"`, `iter_detail["err_type"] = "PASS"`, a docstring
noting the `"PASS"|"FAIL"|"UNKNOWN"` return shape) — none of them
re-implement the check. The `'ALL TESTS PASSED" not in output'` grep
above is the precise, correct signature for "is the OLD hardcoded check
gone" and is the one that actually matters; use that one as the gate, not
a bare `'"PASS"'` count.

If any of these come back wrong: **STOP. Do not launch.** Re-scp the
file and re-check — do not patch by hand on the cluster.

---

## 5. Dry-run both runners on HPC

```
cd /scratch/soumyaj/RTLCoderHPC
export STITCH_INTERPRETER_DIR=/scratch/soumyaj/RTLCoderHPC/src/interpreter
export TASK_A_SCREEN_JSON=/scratch/soumyaj/RTLCoderHPC/task_a_screen.json
export RTLLM_ROOT=/scratch/soumyaj/RTLCoderHPC/RTLLM
python twin_run_runner.py --dry-run
# expect: "DRY RUN OK: exactly 630 cells, as locked."

cd /scratch/soumyaj/Set1_HPC
export STITCH_INTERPRETER_DIR=/scratch/soumyaj/Set1_HPC/src/interpreter
export TASK_A_SCREEN_JSON=/scratch/soumyaj/Set1_HPC/task_a_screen.json
export RTLLM_ROOT=/scratch/soumyaj/RTLCoderHPC/RTLLM
python set1_runner.py --dry-run
# expect: "DRY RUN OK: exactly 1512 cells, as locked."
```

Both dry-runs touch neither Ollama nor iverilog — pure module-pool +
count validation. If either total is wrong, **STOP** — don't launch a
differently-scoped study.

---

## 6. Ollama pull (only if not already present)

```
sbatch /scratch/soumyaj/RTLCoderHPC/pull_ollama_models.slurm
tail -f /scratch/soumyaj/RTLCoderHPC/logs/ollama_pull_*.log
```

Pulls exactly `deepseek-coder:6.7b`, `gemma3:4b`, `llama3.1:latest` — the
same 3 models **both** Set 1 and Set 2 need. Run this **once**; Set 1
reuses this exact `OLLAMA_MODELS` directory read-only. There is no
separate pull script for Set 1.

---

## 7. Launch order

```
sbatch /scratch/soumyaj/RTLCoderHPC/twin_run.slurm      # Node 2 first
# wait ~2 min
sbatch /scratch/soumyaj/Set1_HPC/set1_run.slurm         # then Node 1

squeue -u soumyaj   # confirm both queued/running
```

Two-node independence, confirmed (see also each slurm script's own
comments): both bind Ollama to `127.0.0.1:11434`, safe because they run
on **different physical nodes** (each has its own loopback) — zero port
collision. Scratch dirs are fully disjoint (`Set1_HPC/` vs.
`RTLCoderHPC/`). Log filenames are disjoint (`set1_%j.log` vs.
`twin_%j.log`). `OLLAMA_MODELS` is shared but read-only from both sides
— safe. `venv` is symlinked, not copied — one source of truth.

---

## 8. Monitoring

```
squeue -u soumyaj
tail -f /scratch/soumyaj/RTLCoderHPC/logs/twin_*.log
tail -f /scratch/soumyaj/Set1_HPC/logs/set1_*.log
```

Progress one-liners (use `master_log.json`'s entry count, not just the
console log, which can lag when redirected — same lesson as every prior
overnight run in this project):

```
python3 -c "import json; d=json.load(open('/scratch/soumyaj/RTLCoderHPC/results/twin_run/master_log.json')); print(len(d), '/ 630 done;', sum(1 for e in d if e.get('error')), 'errored')"

python3 -c "import json; d=json.load(open('/scratch/soumyaj/Set1_HPC/results/set1_run/master_log.json')); print(len(d), '/ 1512 done;', sum(1 for e in d if e.get('error')), 'errored')"
```

---

## 9. Resubmit behavior

When a job hits its `--time` cap, it stops mid-run (SLURM kills it) —
**re-submit the exact same script**:

```
sbatch /scratch/soumyaj/RTLCoderHPC/twin_run.slurm     # if Set 2 timed out
sbatch /scratch/soumyaj/Set1_HPC/set1_run.slurm        # if Set 1 timed out
```

Both runners skip already-completed `(module, model, condition,
replicate)` keys via `master_log.json` — no flag needed, no separate
"part 2" script. Expect Set 1 to need 2 sbatches total (120h fills, then
a ~78h remainder), Set 2 to need 2 (72h fills, then a ~10h remainder).

---

## 10. Download results back to laptop

```
scp -r soumyaj@hpc.bits-hyderabad.ac.in:/scratch/soumyaj/RTLCoderHPC/logs/twin_*.log ./phase2_twin_logs/
scp -r soumyaj@hpc.bits-hyderabad.ac.in:/scratch/soumyaj/RTLCoderHPC/results/twin_run ./phase2_twin_results/

scp -r soumyaj@hpc.bits-hyderabad.ac.in:/scratch/soumyaj/Set1_HPC/logs ./set1_logs/
scp -r soumyaj@hpc.bits-hyderabad.ac.in:/scratch/soumyaj/Set1_HPC/results/set1_run ./set1_results/
```

(`phase2/results/` and any local mirror of these are gitignored — land
wherever you point the scp, not committed either way.)
