# STITCH Extension: Full HPC Run Runbook

The operating manual for the three confirmatory HPC runs behind the STITCH
journal extension (Set 1, Set 2 / Twin, Set 3). It is written so that someone
who was not in any of the original sessions can rebuild the environment, re-run
any of the three studies, resume an interrupted one, and find the results.

**All three runs are complete** (2,754 runs, analyzed in `phase2/SET1_ANALYSIS.md`,
`phase2/TWIN_RUN_ANALYSIS.md`, `phase2/SET3_ANALYSIS.md`). This runbook exists so
they can be reproduced, extended, or resumed, not because anything is pending.

**How this document relates to the others**

| Document | Role |
|---|---|
| **This file** | The procedure: order of operations, go/no-go gates, what each locked parameter is and why. |
| [`HPC_COMMANDS.md`](HPC_COMMANDS.md) | The literal copy-paste commands, by Part number. This file links into it rather than repeating it. |
| [`IMP_PHASE2_RUNNER_HARDENING_REPORT.md`](IMP_PHASE2_RUNNER_HARDENING_REPORT.md) | Why pass/fail detection is a registry and what the golden-reference gate proves. |
| `phase2/TWIN_RUN_PREREG.md` | Pre-registered design of the Twin (Set 2) comparison. |
| `phase2/SET1_ANALYSIS.md`, `TWIN_RUN_ANALYSIS.md`, `SET3_ANALYSIS.md` | What each run found. |
| `reSTITCH.md` (repo root, gitignored) | The master narrative of the whole study. |

---

## 1. The study at a glance

| | Set 2 (Twin) | Set 1 | Set 3 |
|---|---|---|---|
| **Question** | Does fine-tuning on RTL data (RTLCoder-Deepseek-v1.1) beat its own base model? | Does STITCH help small models, and where does always-on interpretation hurt? | Does the harmful regime persist, shrink or vanish on larger models? |
| **Models** | `rtlcoder-deepseek-v1.1` (HF `transformers`; native and shared prompt) plus `deepseek-coder:6.7b`, `gemma3:4b`, `llama3.1:latest` (Ollama, shared prompt) | `gemma3:4b`, `llama3.1:latest` (8B), `deepseek-coder:6.7b` (Ollama) | `qwen2.5-coder:14b`, `qwen2.5-coder:32b`, `gemma3:27b` (Ollama) |
| **Conditions** | `baseline` only (interpreter never runs, so this is a model comparison, never a STITCH result) | `baseline`, `sem_adv`, `sem_escalate`, `sem_escalate_restart` | same four as Set 1 |
| **Modules** | 42 | 42 | 17 (recoverable band only) |
| **N / temperature** | 3 / 0.5 | 3 / 0.1 | 3 / 0.1 |
| **Runs** | 630 | 1,512 | 612 |
| **Errors** | 0 | 6 | 2 |
| **Node / partition** | `<GPU_NODE>`, `gpu_h100_4` | `<GPU_NODE>`, `gpu_a100_8` | `<GPU_NODE>`, `gpu_a100_8` |
| **`--time` / sbatches** | 72h / ~2 | 120h / ~2 | 120h / ~1 |
| **Scratch dir** | `/scratch/<HPC_USER>/RTLCoderHPC/` | `/scratch/<HPC_USER>/Set1_HPC/` | `/scratch/<HPC_USER>/Set3_HPC/` |
| **Runner / slurm** | `twin_run_runner.py` / `twin_run.slurm` | `set1_runner.py` / `set1_run.slurm` | `set3_runner.py` / `set3_run.slurm` |
| **Commands** | HPC_COMMANDS Part 2 | Part 3 | Part 6 |

Set 1 and Set 2 ran concurrently on two different physical nodes. Set 3 ran
alone afterwards, and only makes sense once Set 1 exists, since its whole point
is to compare against Set 1's tier-split result on the same conditions.

The four STITCH conditions: `baseline` (no tools), `sem_adv` (Verilator and Yosys
feedback on every iteration), `sem_escalate` (baseline until two observed
failures, then tools), `sem_escalate_restart` (escalation plus a restart
injected after 3 consecutive same-signature failures while escalated).
Pass@6 for the classic conditions, Pass@8 for the escalation conditions.

---

## 2. Locked parameters (do not change without stopping to flag it)

These were fixed before launch. Changing any of them silently produces a
differently-scoped study whose numbers cannot be compared to the published ones.

- **42 modules for Set 1 and Set 2.** The 44 RTLLM-compatible designs
  (`phase1/results/rtllm_pilot/task_a_screen.json`) minus
  `EXCLUDE = {"edge_detect", "square_wave"}`. Both excluded designs pass with
  every output stuck at a fixed wrong value, a defect in their own testbench's
  check logic, not a `detect_outcome()` problem (investigation in
  `IMP_PHASE2_RUNNER_HARDENING_REPORT.md` §4/§6). This mirrors RTLLM's own 50 to 44
  exclusion for defective golden references.
- **17 modules for Set 3.** Exactly the entries with
  `difficulty_tier == "recoverable"` in
  `phase2/twin_analysis_SET2/module_categories.json`. The tiers
  (ceiling / recoverable / floor) are computed once by Twin's `categorize.py` and
  reused verbatim by Set 1 and Set 3, never re-derived. Ceilings and floors are
  excluded from Set 3 because Set 1 already showed all four conditions coincide
  there, so paying for them at 14B-32B speed would buy no discriminating power.
- **N = 3 replicates** everywhere. N=1 is resampling noise (proven twice in this
  project), so no cell result is trusted below N=3.
- **Temperature.** 0.1 for Set 1 and Set 3 (matched so they form one capability
  ladder). 0.5 for Twin, deliberately matched across all five model-conditions to
  remove temperature as a confound in a model comparison. See `reSTITCH.md` §6.4.
- **Total counts** are asserted by each runner's `--dry-run`: 630, 1512, 612. A
  wrong number means a wrong module pool: stop.
- **RTLLM is never copied into this repo.** It is read live from `$RTLLM_ROOT`.

---

## 3. What runs where, and why there are HPC ports

The laptop toolchain is Windows plus WSL. HPC compute nodes have neither `wsl.exe`
nor a shared Ollama, so three files exist as Linux-native ports of their laptop
originals:

| HPC file | Laptop original | Why the port exists |
|---|---|---|
| `phase2/stitch_runner_hpc.py` | `src/runner/stitch_runner.py` | No WSL on compute nodes; subprocess calls run natively. Mechanically diffed against the original so both harness bug fixes are present and nothing else drifted. |
| `phase2/escalation_runner_hpc.py` | `phase1/escalation_runner.py` | The original hardcodes `from stitch_runner import ...` (the WSL runner) and would crash the moment a tool ran. Needed by every `sem_escalate*` condition. |
| `phase2/rtlcoder_adapter.py` | (none) | RTLCoder is a raw-completion HF model, not an Ollama chat model. Validated end-to-end on an H100 by `phase2/smoke_test.py`. |

Shared, platform-agnostic code (imported unchanged by every runner):
`src/interpreter/stitch_interpreter.py` (the semantic interpreter) and
`src/interpreter/pass_detection.py` (the `detect_outcome()` registry). Plus two
pure-Python helpers, `phase1/error_signature.py` and `phase1/escalation_state.py`,
needed by escalation.

**Pass/fail is decided in exactly one place.** Every runner calls
`detect_outcome(sim_log, benchmark)` with a required `benchmark` argument
(`"rtllm"` for these runs, `"phase1"` for the in-house benchmark). There is no
default, so a runner cannot silently apply the wrong benchmark's pass string.
This exists because RTLLM testbenches print `Your Design Passed`, which the
original check (`"PASS"` / `"ALL TESTS PASSED"`, case-sensitive) never matched,
silently misclassifying 31% of the Twin pilot's runs.

### Scratch layout on HPC

```
/scratch/<HPC_USER>/
  oss-cad-suite/bin/          iverilog, vvp, verilator, yosys (on PATH via each slurm)
  RTLCoderHPC/                Set 2. Also holds the shared venv, RTLLM checkout, HF cache,
    venv/ RTLLM/ hf_cache/      the Ollama models for Set 1/2, and the ollama binary in bin/
    ollama_models/ bin/ logs/ results/twin_run/ src/interpreter/
  Set1_HPC/                   Set 1. venv and RTLLM are symlinks into RTLCoderHPC.
    logs/ results/set1_run/ src/interpreter/
  Set3_HPC/                   Set 3. Fully self-contained after the scratch wipe:
    venv/ RTLLM/ bin/           own venv, own RTLLM clone, own ollama binary, own models.
    ollama_models/ logs/ results/set3_run/ src/interpreter/
```

### Environment variables the runners read

| Variable | Meaning |
|---|---|
| `RTLLM_ROOT` | Path to the RTLLM checkout. The runner defaults point at `RTLCoderHPC/RTLLM`, which is why Set 3 needs the path re-pointed (Section 5, step 3). |
| `STITCH_INTERPRETER_DIR` | The deployed `src/interpreter/` directory. Lets a flat `scp` work without guessing relative paths. |
| `TASK_A_SCREEN_JSON` | The 44-design compatibility screen. |
| `MODULE_CATEGORIES_JSON` | Set 3 only: the tier assignments (recoverable-band filter). |
| `OLLAMA_HOST`, `OLLAMA_MODELS` | Set by each slurm script. Ollama binds `127.0.0.1:11434`, which is safe across two nodes because each has its own loopback. |
| `HF_HOME` | Twin only: Hugging Face cache for the RTLCoder weights. |

---

## 4. Environment facts that explain most failures

Full list in [`HPC_COMMANDS.md`](HPC_COMMANDS.md) Part 0. The four that matter:

1. **Ollama does not run on the login node.** It runs only inside an sbatch job,
   where each slurm script starts its own `ollama serve`. Check model presence
   by listing the manifest directory, not with `ollama list`.
2. **The login node has no outbound internet.** Clones, downloads and model pulls
   run inside an sbatch job, or are downloaded on the laptop and `scp`'d.
3. **The cluster `tar` has no `--zstd`.** Use conda's `zstd` (Part 5.4).
4. **The scratch tree was wiped once mid-project.** Everything project-specific
   except `hf_cache` and `miniconda3` disappeared. Part 5 of the command
   reference is the full recovery sequence and is how Set 3's environment was
   stood up. If `RTLLM`, `oss-cad-suite` or `ollama` is missing, start there.

---

## 5. The procedure, in order

Do these in order for any run. Each step lists the gate that decides whether to
continue. **If a gate fails, stop.** Re-`scp` the file and re-check; never patch a
file by hand on the cluster, because then what ran no longer matches any commit.

**Step 0. Commit first.** Deploy only from a committed state so that what you
`scp` matches a real commit you can cite later. (Project rule: changes are staged
and the maintainer runs `git commit`.)

**Step 1. Provision the environment** (once, or after a wipe).
Part 1 of the command reference for a fresh account, Part 5 after a wipe.
Gate: `ls /scratch/<HPC_USER>/oss-cad-suite/bin/iverilog`, the RTLLM directory,
`bin/ollama --version`, and the venv with `openai` (plus `torch`/`transformers`
for Twin) all exist.

**Step 2. Pass-detection gate** (before any full run; Part 4).
Runs `phase2/verify_pass_detection.py` on HPC, not just locally, against golden
and deliberately-broken reference designs for all 44 compatible RTLLM modules.
Gate: **golden side must be 44/44 PASS.** That number is the regression guard for
the pass-string bug. The broken side is expected to show about 8 non-green rows;
each was individually root-caused (handshake designs where stuck-at-0 never
reaches a verdict, plus the two excluded weak-oracle testbenches) and none is a
`detect_outcome()` defect. Cross-check against the table in the hardening report
rather than treating them as new problems.

**Step 3. Deploy code** (Parts 2.1, 3.2, 6.2).
Each run has its own file list; the Set 3 and Set 1 lists are identical except
that Set 3 adds `module_categories.json` and its own pull script. Always
re-`scp` `stitch_interpreter.py` and `pass_detection.py` fresh, even if a copy
exists; do not assume the old one is current.
**Set 3 only:** the laptop `set3_run.slurm` points `RTLLM_ROOT` at the wiped
`RTLCoderHPC/RTLLM`. After every deploy re-point it to `Set3_HPC/RTLLM` (Part 6.3).

**Step 4. Verification greps on HPC** (Parts 2.4, 3.4, 6.4).
Run in each deployed directory. Gate (all must hold):

| Check | Expected | What it proves |
|---|---|---|
| `grep -c 'ALL TESTS PASSED" not in output' stitch_runner_hpc.py` | **0** | The original hardcoded pass check is gone. This is the precise signature to gate on. |
| `grep -c "detect_outcome" stitch_runner_hpc.py` | >= 2 | The registry is actually wired in. |
| `grep -c "cwd=iter_dir" stitch_runner_hpc.py` | >= 2 | The `vvp` working-directory fix (`$readmemh` designs) is present. |
| `grep -c "square_wave" <runner>` | >= 1 | The EXCLUDE list is deployed (Set 1, Twin). |
| `grep -c "detect_outcome" escalation_runner_hpc.py` | >= 1 | Escalation goes through the registry too (Set 1, Set 3). |
| Recoverable-tier count in `module_categories.json` | 17 | The Set 3 pool is correct. |

A bare `grep -c '"PASS"' stitch_runner_hpc.py` returning about 6 is expected, not a
red flag: those are bookkeeping labels that consume `detect_outcome()`'s answer
(`"result": "PASS" if success else "FAIL"` and similar), not a reimplementation.
Use the `ALL TESTS PASSED" not in output` grep as the gate.

**Step 5. Dry-run** (touches neither Ollama nor iverilog).
`python <runner> --dry-run` must print exactly **630** (Twin), **1512** (Set 1) or
**612** (Set 3). Gate: the number matches. A different number means a different
module pool: stop.

**Step 6. Models present** (Parts 2.3, 3.3, 6.1).
Pull once with the matching `pull_ollama_models*.slurm` (Set 1 and Set 2 share one
pull of three models; Set 3 pulls its own three, about 50 GB, into
`Set3_HPC/ollama_models`). Confirm by listing the manifest directory. Each
runner's slurm script fails loudly if a model is missing, and the Python runner
checks again; do not rely on either as a substitute for checking here.
To run hands-off, chain the run behind the pull with `--dependency=afterok:<pulljob>`
(Part 7.1) so a failed pull holds the run instead of launching it with missing
models.

**Step 7. Launch** (Parts 2.5, 3.5, 6.5).
`sbatch` the run's `.slurm`. When running Set 1 and Set 2 together, launch Set 2
first, wait about two minutes, then launch Set 1. They are independent because
they sit on different physical nodes (own loopback), have disjoint scratch dirs and
log names, and share only the read-only `ollama_models` and a symlinked venv.

**Step 8. Monitor, resume, collect.**
- Progress: read `results/<run>/master_log.json`'s entry count (the one-liners in
  the command reference), not the console log, which can lag when redirected.
- Resume: when a job hits its `--time` cap SLURM kills it mid-run. **Resubmit the
  identical script.** Every runner skips already-completed
  `(module, model, condition, replicate)` keys via `master_log.json`. There is no
  flag and no "part 2" script.
- Collect (Part 7.5): `scp -r` the `results/<run>` directory into
  `phase2/results/` (gitignored, so it is never committed).
- Outcome after a job leaves the queue: `sacct` (Part 7.3). `FAILED` with a short
  elapsed time means it crashed early; check the log tail against the failure table.

---

## 6. After the run: reproducing the analysis

Every analysis is a pure function of one file, `phase2/results/<run>/master_log.json`.
Nothing is re-derived from sim logs and nothing is hand-edited.

| Run | Scripts | Output |
|---|---|---|
| Twin | `phase2/twin_analysis_SET2/`: run `categorize.py` **first** (it writes `module_categories.json`, the tier assignment every other analysis reads), then `table1.py`, `fig1.py`, `fig2.py`, `table2.py`, `prompt_format.py` | Tables, figures, `prompt_format_verdict.md` |
| Set 1 | `phase2/set1_analysis/` (`table_full_grid.py`, `table_condition_decision.py`, `fig2_tier_split.py`, `cost_by_tier.py`, `cost_analysis.py`) | Tier-split figure, full-grid and decision tables, cost tables |
| Set 3 | `phase2/set3_analysis/` (`per_model_tier.py`, `harmful_regime_by_capability.py`, `set3_cost_by_tier.py`, `fig_capability_ladder_full.py`) | Per-model tier table, harmful-regime ladder, cost table, full 4B-32B capability ladder |

Two standing rules for anything you add to the analysis:

- **`semantic_fired`-gate every mechanism claim.** A pooled pass-rate edge is not
  evidence the interpreter caused it. Check the replicate-level trace (did
  `semantic_fired` / `interpreter_invoked` actually fire in the runs that won?)
  before calling anything a win. This is how the Set 3 "escalation wins outright"
  reading was caught and corrected.
- **Report every pass rate against its difficulty tier.** Pooled numbers over
  ceilings and floors dilute the recoverable-band signal to a flat line.

---

## 7. Known issues and history worth knowing

- **The `_data.py` import collision.** Each analysis directory has its own
  `_data.py`; a module cannot `import _data` to reach a differently-located file of
  the same name because `sys.modules` caches by bare name.
  `set3_analysis/_data.py` reimplements what it needs and
  `fig_capability_ladder_full.py` loads Twin's copy with
  `importlib.util.spec_from_file_location`. Expect this again if you add another.
- **Stale RTLLM path in `set3_run.slurm`** (Step 3). The committed slurm still says
  `RTLCoderHPC/RTLLM`; the deploy step patches it on the cluster.
- **The 8 non-green broken-reference rows** in the pass-detection gate are
  documented and expected (Step 2).
- **Errors in the runs** were all transient Ollama timeouts (`APITimeoutError`):
  6 in Set 1 and 2 in Set 3 (both `qwen2.5-coder:32b`), excluded from the analysis
  and never structural.
- **The Twin pilot** (64 of 75 runs, cut off by an 8h limit) exposed the pass-string
  bug and was superseded by the full run; its record is Appendix A of
  `phase2/TWIN_RUN_ANALYSIS.md`.

---

## 8. Quick troubleshooting

The full symptom-to-fix table is at the end of [`HPC_COMMANDS.md`](HPC_COMMANDS.md)
Part 8. The most common causes, in the order to check them:

1. Job `FAILED` within a minute: a missing file or a stale `RTLLM_ROOT` (Step 3).
2. `ModuleNotFoundError: stitch_interpreter`: `src/interpreter/` was not deployed as
   a subdirectory.
3. Dry-run count is wrong: the RTLLM path did not resolve, so the module pool came
   up short.
4. A model is reported missing: the pull did not finish, or `OLLAMA_MODELS` points
   at the wrong tree (Set 3 uses `Set3_HPC/ollama_models`, Set 1 and Set 2 use
   `RTLCoderHPC/ollama_models`).
5. Job pending with `(Resources)`: the node is busy. Wait, or override the node
   and partition at submit time (Part 7.2).

## 9. Phase 3 (planned)

Phase 3 (MPSoC composition + interpreter v3) is a separate run with its own scratch directory and its own procedure:
follow `phase3/HPC_PHASE3_COMMANDS.md`, Parts A-I (preflight, deploy, gate, model pull, pilot, full run, monitor,
compose + summary, download). The gate rule carries over from Sets 1-3 and is stricter: **nothing GPU-side is
submitted before the Part C gate job prints `ALL GATES PASSED`**, and the full 990-run job is not submitted before the
Part E pilot has been reviewed. Sections 1-8 above describe Sets 1-3 only.
