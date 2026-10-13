# STITCH: Handoff (Phases 0 to 3 and the API study done; journal paper v9 drafted)

Written 2026-09-27. Replaces the 2026-09-23 version (git history has it). For a fresh Claude Code chat and for a
planner agent. Read the message to the next chat at the end first.

---

## 0. State as of 2026-10-13 (final)

- **Paper.** `paper/STITCH_EXT_v9.tex` (16 pages including references) and
  `paper/STITCH_EXT_supplement.tex` (S1 to S9, 16 pages) compile with pdflatex, with 0 undefined references
  and 0 overfull boxes. Every change and every new number source is in `paper/V9_CHANGES.md`. v8 is kept;
  superseded drafts are in `docs/archive/paper/`. The compiled PDFs are in `paper/build/` (ignored).
- **API study (`phase2/frontier/`), all complete except one optional item.**
  - Set 4 (recoverable band): complete for 3 models.
  - Set 4b (floor): GPT-4.1 mini 228/228, Gemini 2.5 Flash 228/228, Claude Haiku 4.5 143/228.
  - The Phase 3 ladder has three API rows, all in the paper.
  - Set 4c (reasoning) was closed by its pre-registered stop rule (Amendment 5); it has no results.
  - freq_divbyfrac: genuine model failures and a spec-wording defect in the counter description, not a testbench
    defect (`FREQ_DIVBYFRAC_AUDIT.md`).
  - Spend since Set 4: $13.70 (INR 1,552).
- **Only pending work:** Haiku's 85 Set 4b runs (optional; `phase2/frontier/PENDING.md`). If they are run,
  `make_numbers_set4.py` refreshes every paper number and table that depends on them.
- **Where things are:** `REPO_INDEX.md` (per phase; evidence per paper section; regeneration commands; what is
  ignored).

---

## 1. What STITCH is, in one paragraph

An LLM repairs Verilog in a loop: generate, simulate, feed the result back, retry. STITCH adds a deterministic
**semantic interpreter** (no AI) that turns Verilator lint and Yosys synthesis output into short, targeted repair
directives. The project measures when that helps, how much, at what cost, and for which models. Conditions used
throughout: `baseline` (simulation feedback only, AutoChip style), `raw_adv` (plus raw tool text), `sem_adv`
(plus interpreter directives on every iteration), `sem_escalate` / `sem_escalate_restart` (start as baseline,
switch to the interpreter only after two identical failure signatures; restart variant adds one blank-slate retry).

## 2. What each phase achieved

| Phase | What was done | What it established | Main write-up |
|---|---|---|---|
| 0 | Hunt for clean interpreter illustrations, N=3 | Two replicated illustrations (`decoder_3to8`, `mux4_oe`, gated-input `UNUSEDSIGNAL`, 3/3); the input/output reachability asymmetry; 15 retired candidates with reasons | `phase0/evidence/phase0_illustration_hunt_findings.md` |
| 1 | Built `sem_escalate` + restart; 255-run in-house benchmark; RTLLM pilot; fixed two harness bugs | Escalation cuts heavyweight tool calls ~35-45% at equal or better pass rate; N=1 benchmark labels collapse at N=3 | `phase1/PHASE1_FINDINGS.md` |
| 2 | HPC infrastructure; pass-detection registry; three confirmatory runs on RTLLM v2.1 (42 modules): Set 2 Twin 630, Set 1 1,512, Set 3 612 runs | Tier-decomposed results (ceiling 6 / recoverable 17 / floor 19); escalation matches baseline with a structural worst-case guarantee; tool-cost reduction 75% on ceilings, 16.6% -> 27.6% on the recoverable band as models grow; RTLCoder fine-tuning shows no net gain over its base | `phase2/SET1_ANALYSIS.md`, `SET3_ANALYSIS.md`, `TWIN_RUN_ANALYSIS.md`; narrative `reSTITCH.md` |
| 3 | Real RISC-V MPSoC benchmark (11 repair tasks, 3 real designs); additive interpreter v3; 990 runs; composition back into the designs | Simulation-only repair signs off 62% of runs structurally defective (all 108 sim-silent runs), STITCH v3 1%; interpretation beats raw text +14.6 pts (cell CI +3.5..+26.3) with ~23% fewer calls and tokens; escalation highest clean rate (80%) and +23.3 pts over baseline on sim-visible defects; repaired leaves restore synthesis of the 4- and 9-router meshes and the MPSoC top (baseline 0/18) | `phase3/evidence/phase3_run/PHASE3_RESULTS.md`; paper `paper/PHASE3_MPSOC.tex` |

## 3. Which runner and interpreter ran where (exact)

Interpreter files: `src/interpreter/stitch_interpreter.py` = production interpreter ("v2"; never edited since
Phase 2; sha256 of the LF-normalised file `42f61a493e4544e027b880ba5ae16ef1677c52f9b328cce2e13c25028fb2abff`, recorded in
every Phase 3 `metrics.json`). `src/interpreter/stitch_interpreter_v3.py` + `_v3_parsers.py` = additive v3 layer,
version 3.0.1 in every Phase 3 run; it imports production unchanged and `interpret(..., version="v2")` reproduces
production byte for byte. `src/interpreter/pass_detection.py` = `detect_outcome(..., benchmark=)` registry
(Phases 1-2).

| Run | Runner (entry point -> engine) | Interpreter | LLM backend, models | Budget | Results on disk |
|---|---|---|---|---|---|
| Phase 0 illustrations | `src/runner/stitch_runner.py` (Windows + WSL tools) | production | Ollama local; gemma3:4b, llama3.1 | 6 iters | `phase0/results/` |
| Phase 1 Task 3 (255 runs) | `phase1/task3_runner.py` -> `phase1/escalation_runner.py` + `escalation_state.py` + `error_signature.py`, on top of `src/runner/stitch_runner.py` | production | Ollama local; gemma3:4b, llama3.1, deepseek-coder:6.7b | baseline/sem_adv 6, escalation 8 | `phase1/results/task3/` |
| Phase 1 RTLLM pilot | `phase1/rtllm_pilot_runner.py` (same engine) | production | Ollama local; 5 models | as above | `phase1/results/rtllm_pilot*/`, `rtllm_alu_refix2/` |
| Set 2 Twin (630) | `phase2/twin_run_runner.py` -> `phase2/stitch_runner_hpc.py` + `rtlcoder_adapter.py` (HF transformers for RTLCoder) | none (condition fixed at `baseline`) | RTLCoder-Deepseek-v1.1 native + shared, deepseek-coder:6.7b, gemma3:4b, llama3.1; T=0.5 | 8 | `phase2/results/twin_run/` |
| Set 1 (1,512) | `phase2/set1_runner.py` -> `stitch_runner_hpc.py` + `escalation_runner_hpc.py` | production | Ollama on HPC; gemma3:4b, llama3.1, deepseek-coder:6.7b; T=0.1 | baseline/sem_adv 6, escalation 8 | `phase2/results/set1_run/` |
| Set 3 (612) | `phase2/set3_runner.py` (same engine as Set 1) | production | Ollama on HPC; qwen2.5-coder:14b, qwen2.5-coder:32b, gemma3:27b; T=0.1; 17 recoverable modules | baseline/sem_adv 6, escalation 8 | `phase2/results/set3_run/` |
| Phase 3 (990) | `phase3/runner/stitch_runner_p3.py` (own evaluator `phase3/runner/p3_eval.py`; does not use `stitch_runner*.py` or `pass_detection.py`) | `sem_adv_v2` = production via v3's `version="v2"`; `sem_adv_v3` and `sem_esc_restart_v3` = v3 | Ollama on HPC; llama3.2:3b, gemma3:4b, deepseek-coder:6.7b, qwen2.5-coder:7b, llama3.1:latest (8B), qwen2.5-coder:14b; T=0.1; system prompt `phase3/runner/system_prompt.txt` (= production `SYSTEM_PROMPT`) | 6 model calls, every condition | `phase3/results/phase3_run/` (gitignored) |

Phase 3 protocol `feedback_first_v2`: the defective input is evaluated first and its feedback goes into call 1.
Every candidate is fully evaluated (Icarus + Verilator + Yosys) whatever the condition. Phase 3 raw feedback is
filtered by `raw_tool_text()` (Verilator warnings/errors, Yosys latch/error/loop lines, max 40 per tool), so Phase 3
prompts are not byte-comparable to Set 1/3 `sem_adv` prompts. Phase 3 toolchain on the HPC: Yosys 0.69+71, Verilator
5.053, Icarus 14.0 (devel); local tests and fixtures: Yosys 0.33, Verilator 5.020, Icarus 12.0 (WSL).

## 4. Where things are

```
handoff.md                  this file
reSTITCH.md                 master narrative, Phases 0-2 (gitignored, disk only; leave as is)
reSTITCH_PHASE3_EXPLAINED.md  user's private Phase 3 explainer (gitignored; leave as is)
note.txt                    user's scratch notes + git workflow (gitignored)
STITCH_EXT_FINAL.pdf        last compiled journal draft (v6)
paper_112_final.pdf         OLD MLCAD '26 conference paper (superseded; do not review)
paper/                      journal sources (untracked until the user commits)
  STITCH_EXT_v7.tex         current journal draft: v6 + Section 9 (MPSoC) + wording fixes
  PHASE3_MPSOC.tex          full Phase 3 write-up with every table (standalone)
  V7_CHANGES.md             every v6 -> v7 edit, revertible one by one
  figures/                  all PNGs both .tex files use (\graphicspath{{figures/}}); copies, sources in the .tex headers
src/interpreter/            stitch_interpreter.py (production), stitch_interpreter_v3.py + _v3_parsers.py (v3),
                            pass_detection.py, WARNING_TAXONOMY.md, tests/
src/runner/stitch_runner.py Phase 0/1 local runner
phase0/  phase1/            closed phases (READMEs + findings docs)
phase2/                     HPC runners, slurm, *_ANALYSIS.md, set1_analysis/ set3_analysis/ twin_analysis_SET2/
                            (figure + table scripts), results/ (gitignored run trees)
phase3/                     see phase3/README.md (layout table, source of truth, how to do a new run)
  runner/                   stitch_runner_p3.py, p3_eval.py, compose.py, analyze_phase3.py, phase3_figures.py, ...
  tasks/ designs/ tests/ hpc/
  results/phase3_run/       the 990 runs (gitignored)
  evidence/phase3_run/      generated analysis: PHASE3_RESULTS.md, phase3_analysis.json, tables, regressions, figures
  evidence/                 pre-run evidence (PROD_V2_ON_REAL_LOGS.md, compose_bounds.jsonl, E0 audit, ...)
  docs/                     PHASE3_EXPLAINED.md, taxonomy addendum, archive/ (superseded)
docs/                       HPC_COMMANDS.md, FULL_RUN_RUNBOOK.md (Phase 2 HPC), EXT_FINAL_REVIEW.md (paper
                            wording notes), IMP_* reports
MPSoC/MPSoC Source Codes/   original MPSoC sources (phase3/designs/ holds the sanitised copies actually used)
analysis/ benchmarks/ plans/  older utilities, the v20 diagnostic benchmark, research plans (archive)
```

RTLLM is never copied into the repo: `<RTLLM_ROOT>` locally, `$RTLLM_ROOT` on the HPC.

**Regenerate the Phase 3 numbers and figures:** `python phase3/runner/analyze_phase3.py`
(default `--results phase3/results/phase3_run`; output to `phase3/evidence/phase3_run/`). Deterministic (seeded).

## 5. Phase 3 in numbers (from `phase3/evidence/phase3_run/PHASE3_RESULTS.md`)

| condition (198 runs each) | func_pass | clean_pass | silent structural pass | calls/run | tokens/run |
|---|---|---|---|---|---|
| baseline | 85% | 23% | 62% | 1.34 | 1,425 |
| raw_adv | 65% | 59% | 6% | 3.27 | 4,396 |
| sem_adv_v2 | 71% | 68% | 3% | 2.83 | 3,831 |
| sem_adv_v3 | 74% | 74% | 1% | 2.51 | 3,377 |
| sem_esc_restart_v3 | 85% | 80% | 5% | 2.99 | 3,798 |

Composition (top-level synthesis pass, 18 groups): baseline 0/18 in all three designs; v3 16/18 in each; escalation
18/18 in both meshes, 15/18 MPSoC. Every group whose composed leaves were all clean reached the golden bound
(32/32, 32/32, 27/27).

## 6. For the planner: where refinement and new runs would pay off

Strong and stable (keep as is): simulation-only sign-off of sim-silent defects; v3 (and v2) vs raw text, pooled and
on sim-silent tasks; the cost and first-call speed of v3; escalation vs baseline on sim-visible tasks; composition.

Open, with the run or change that would settle each:

| Item | Evidence now | Candidate action | Rough cost |
|---|---|---|---|
| Escalation's gate message vs the interpreter | 110 of escalation's 158 clean passes had no interpreter output (generic "fails synthesis sign-off" message only) | control arm `baseline_gate` (baseline + the same message, no tool detail); small additive runner change | 198 runs, ~5 h H100 |
| v3 rules are in-sample (written from these tasks' logs) | coverage 0/18 -> 18/18 on two tasks; pass-rate gain over v2 on the 4 focus tasks +11.1 pts, CI includes 0 | held-out defect set (new real leaves or seeded defects the rules were not written from), v2 vs v3 vs raw | depends on task count; ~18 runs per task-condition |
| Functional regressions under tool feedback | 92 runs lost a simulation pass they had (raw 36, v2 22, v3 23, escalation 11); keep-best-so-far would restore func_pass to 86% (v3) post hoc | return best-so-far candidate in the runner (no new model calls) and/or a sim-regression guard directive; rerun the tool conditions | 792 runs, or re-score only if implemented post hoc |
| Flat tasks | `noc_xbar4` at baseline level under all conditions (interpreter fires 18/18); `riscv_alu_flags` max 9/18; v3 below raw on `mem_wb_mux`, `ni_flit_pack` | inspect v3 directives and responses on these four; improve rules; more replicates | analysis first, then ~72 runs per task set |
| Power | replicates correlated (83-94% of (model, task) cells unanimous); per-model/per-task contrasts underpowered | N=5 on the tool conditions, or more tasks rather than more reps | 660 runs for +2 reps |
| Small-model compile errors | 124 final candidates do not compile (66 gemma3:4b, 42 llama3.2:3b), genuine syntax errors | compile-error directive class, or exclude sub-4B models from claims | runner + interpreter change |
| Composition-only defects | 1-bit PC port driven by 32 bits; FIFO with a missing positional port: invisible to leaf checks | integration-level feedback (top-level lint/synth fed back) | design work first |

Paper: `paper/STITCH_EXT_v7.tex` needs one Overleaf compile check and the bibliography check listed in
`paper/V7_CHANGES.md`. Minor wording notes on Sections 1-8 are in `docs/EXT_FINAL_REVIEW.md` (the user folds them in).

## 7. HPC

BITS Hyderabad, `<HPC_USER>@<HPC_HOST>`, scratch `/scratch/<HPC_USER>/`: `RTLCoderHPC/` (Set 2 + shared venv),
`Set1_HPC/`, `Set3_HPC/`, `Phase3_HPC/` (Phase 3, self-contained: `$BASE/phase3`, `$BASE/src`, `$BASE/results`).
oss-cad-suite at `/scratch/<HPC_USER>/oss-cad-suite/bin`. Ollama runs only inside sbatch jobs; the login node has no
internet. Nodes: `<GPU_NODE>` A100 (`gpu_a100_8`) ran Sets 1 and 3; `<GPU_NODE>` H100 (`gpu_h100_4`) ran Set 2; the
Phase 3 manifests record `<GPU_NODE>`. Phase 3 procedure: `phase3/HPC_PHASE3_COMMANDS.md`
(gate must print `ALL GATES PASSED` before any GPU job). New Phase 3 runs: set `P3_OUT=$BASE/results/<new_run>` for
both `phase3_run.slurm` and `phase3_compose.slurm`. Phase 2 procedure: `docs/FULL_RUN_RUNBOOK.md`, `docs/HPC_COMMANDS.md`.
Claude Code never runs ssh/scp/sbatch; the user does.

## 8. Git state and standing conventions

- Branch `phase3-setup` (from `main` at `61535aa`). On 2026-10-13 the Phase 3, API-study and paper work was
  committed there in staged, logical commits, at the user's request (closure brief). Pushing and merging into
  `main` wait for the user's explicit "PUSH". Never force-push.
- Before every commit: `scan_secrets.py` must report 0 matches, and the staged diff must contain no key prefix.
- No `Co-Authored-By: Claude` trailer in commit messages.
- Never edit `src/interpreter/stitch_interpreter.py`. Extend through the v3 layer.
- N >= 3 before any cell is trusted; `semantic_fired`-gate every interpreter claim; report pass rates against the
  difficulty tier (Phase 2) or the sim-silent / sim-visible split (Phase 3).
- Every number in a document comes from a script run on the raw `metrics.json` / `master_log.json`, not from memory.
- `reSTITCH.md` and `reSTITCH_PHASE3_EXPLAINED.md` are the user's; leave them as they are.
- Never frame Set 2 (Twin) as a STITCH result: its condition is fixed at `baseline`.

---

## Message to the next Claude Code chat

You are picking up STITCH after all study phases and the journal draft (v9). Read this file, then
`REPO_INDEX.md`, then `paper/V9_CHANGES.md`. For Phase 3, read `phase3/evidence/phase3_final/PHASE3_FINAL.md`. For
the API study, read `phase2/frontier/SET4_REPORT.md`. Read `reSTITCH.md` if you need Phases 0-2 in depth. Take direction
from the user and from the planner agent: they decide which refinements and runs come next. Contribute fully: check
their plans against the data, point out problems, propose better options, and do the work well. If a request looks
like it heads in the wrong direction (for example, it would overstate a result or mix protocols in one results
directory), say so explicitly and explain why before acting, then follow the decision. Do not commit, push, or run
anything on the HPC unless asked.
