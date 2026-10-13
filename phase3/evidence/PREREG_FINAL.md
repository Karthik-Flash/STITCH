# Phase 3 final batch: pre-registration

Written 2026-09-28, before any run of the final batch was submitted. Its SHA-256 (LF) is recorded in
`phase3/evidence/FREEZE_FINAL.md`. The analysis code that implements it is `phase3/runner/analyze_phase3.py --final`,
also hashed there. Nothing below changes after results exist. Anything added later is labelled POST HOC.

## 1. Data

| arm | results directory | models | conditions | tasks x reps | runs |
|---|---|---|---|---|---|
| original (990) | `phase3/results/phase3_run` | 6 original | baseline, raw_adv, sem_adv_v2, sem_adv_v3, sem_esc_restart_v3 | 11 x 3 | 990 |
| A: control arm | `phase3/results/phase3_gate_ctrl` | 6 original | baseline_gate | 11 x 3 | 198 |
| C: 32B | `phase3/results/phase3_32b` | qwen2.5-coder:32b | all six conditions | 11 x 3 | 198 |

The six original models are llama3.2:3b, gemma3:4b, deepseek-coder:6.7b, qwen2.5-coder:7b, llama3.1:latest (8B) and
qwen2.5-coder:14b. Every run uses protocol `feedback_first_v2`, T = 0.1, 6 LLM calls maximum, the production system
prompt, interpreter v3 3.0.1 on top of the unmodified production interpreter (sha256 LF `42f61a49…2abff`).
Each (model, condition) comes from exactly one results directory; the analysis refuses anything else.

`baseline_gate` is simulation feedback plus the exact gate message of `sem_esc_restart_v3` before escalation ("The
design simulates correctly but FAILS SYNTHESIS SIGN-OFF. Re-check it for synthesis problems."). It stops at clean_pass
under tb.v and never escalates or restarts, and no tool detail is fed back. For every RTL it sees, the v3 interpretation
is logged (`would_fire`, `would_class`) and never fed back.

Arm A runs after the original 990, on the same node type, with the same model tags. Pairing on (model, task, rep) is a
stratification, not a replay: runs are independent draws. The model digests of the six original models were not
recorded in the 990 runs. The pull job for this batch therefore pulls only qwen2.5-coder:32b, so the six local models
stay as they were, and every new run records its model digest.

## 2. Oracles and metrics

- The in-loop testbench is `tasks/<task>/tb.v`, unchanged for every task. It drives all feedback and all stop rules.
- The sign-off testbench is `tasks/<task>/tb_signoff.v`. It is used only offline, for scoring. The runner, the
  evaluator and the prompts never see it. It is spec-complete on two tasks where the equivalence audit found a
  testbench gap:
  - mem_wb_mux: adds `ex_mem_memwrite == 0` and `ex_mem_FWD_RS2 == 2'b11`.
  - Address_select: checks `J_addr = X + PC` on every input, as the spec defines it, with the full 32-bit PC.
    tb.v checked J_addr only on a non-flushed JAL.
- On the other nine tasks, tb_signoff.v is byte-identical to tb.v. The equivalence audit in `FREEZE_FINAL.md`
  justifies this.

| metric | definition |
|---|---|
| `loop_pass` | tb.v passes (= the logged `func_pass`) |
| `signoff_func` | tb_signoff.v passes |
| **`signoff_clean`** | signoff_func AND structurally clean (Yosys synth OK, 0 latch, 0 loop, 0 of MULTIDRIVEN / UNOPTFLAT / LATCH / WIDTHTRUNC): **the primary metric** |
| `signed_off_defective` | loop_pass AND NOT signoff_clean: the headline sign-off metric (replaces "silent structural pass") |
| `silent structural pass` | loop_pass AND NOT structurally clean: kept for continuity |
| `clean_pass` (as run) | loop_pass AND structurally clean: reported next to every contrast as a sensitivity column, never dropped |

Strata: sim-silent (6 tasks: MuxPC, execute_mux, mem_wb_mux, mux3, register_1bit, riscv_alu_flags) and sim-visible
(5 tasks: Address_select, ni_flit_pack, noc_xbar4, register_32bit, register_4bit), from each task's `meta.json`.
The stratum is defined under tb.v and does not change.

## 3. Statistics

- Contrast A − B: runs are paired on (model, task, rep), and cells are (model, task). The effect is the mean over cells
  of the within-cell difference in signoff_clean rate, in percentage points. The 95% CI is a cell bootstrap (10,000
  resamples) and p is a cell sign-flip permutation test (20,000). Both are seeded (SEED 20260925 plus a CRC of the
  contrast label), so reruns reproduce byte for byte.
- Rates carry Wilson 95% CIs. Run-level exact McNemar p is reported alongside and used only for the Holm-corrected
  per-model and per-task families.
- Headline pool: the six original models (66 cells, or 30 on sim-visible and 36 on sim-silent).

## 4. Primary contrasts (signoff_clean, six original models; pooled, sim-silent, sim-visible)

1. sem_esc_restart_v3 − baseline_gate
2. sem_adv_v3 − baseline_gate
3. baseline_gate − raw_adv
4. baseline_gate − baseline (sim-visible only; sim-silent is fixed by protocol)

Re-stated under the sign-off oracle: sem_adv_v2 − raw_adv, sem_adv_v3 − raw_adv, sem_adv_v3 − sem_adv_v2,
sem_esc_restart_v3 − sem_adv_v3, sem_esc_restart_v3 − raw_adv, and sem_esc_restart_v3 − baseline (sim-visible).

## 5. Pre-registered readings (verbatim from the plan)

- Contrasts 1 and 2 CIs exclude 0 (gate lower):
    the detail in the feedback adds value beyond the verdict.
- Contrast 1 CI includes 0:
    the verdict carries most of escalation's gain; the interpreter's value rests on v2/v3 vs raw, cost,
    first-call speed, and the tasks and models where the gate fails (from would_fire).
- Gate above always-on v3:
    terse beats verbose on some models, which is consistent with the harmful regime; escalation is
    the recommended design.

Operational rule, fixed here and implemented in `reading()` in `analyze_phase3.py`:
- The readings use the pooled six-model signoff_clean contrasts 1 and 2.
- "Exclude 0 (gate lower)" means the lower CI bound is above 0.
- "Includes 0" means lower bound ≤ 0 ≤ upper bound.
- "Gate above always-on v3" means the upper CI bound of contrast 2 is below 0.
- Readings 2 and 3 can hold together.
- If none holds (for example, contrast 1 excludes 0 but contrast 2 does not), the result is reported as observed,
  with no pre-registered interpretation.
- The sim-silent and sim-visible strata are reported as the decomposition of the pooled result. They do not choose the
  reading.
- No multiplicity correction is applied across the four primary contrasts. Each is reported with its own CI.

## 6. Secondary analyses (labelled secondary wherever they appear)

- Per-task and per-model breakdowns of the primary contrasts (Holm within each contrast's family).
- LLM calls, tokens and tool-feedback rounds per run, and tokens per signoff_clean.
- First-call clean rate (signoff_clean by LLM call 1) and cumulative signoff_clean by call.
- baseline_gate runs that are not signoff_clean while `would_fire` = 1 (where the verdict was not enough), by task.
- qwen2.5-coder:32b as a separate model row, and a seven-model sensitivity pool for all contrasts. Headline tables
  stay six-model.
- Composition (top-level synthesis pass) of the baseline_gate and 32B groups in all three designs.
- Oracle sensitivity: every contrast under as-run clean_pass next to signoff_clean, and, per task, the runs whose
  verdict changes between the two oracles.

## 7. Run completeness and errors

A run counts only if it has a `metrics.json`. A run that errored (`error.json`) is deleted and resumed until every arm
is complete (198 runs). If an arm cannot be completed, the analysis reports the pairs it has, states the missing
cells, and does not impute. No run is excluded for its outcome.

## 8. What is post hoc

The sign-off re-score of the original 990 runs (`phase3/evidence/phase3_run/POSTHOC_SIGNOFF.md`) is POST HOC. The
oracle was introduced after the equivalence audit found the mem_wb_mux and Address_select gaps, and before any
result of this batch.
The keep-best-so-far and degenerate-repair checks in `POSTHOC_CHECKS.md` are POST HOC as well.

## 9. Amendment A1

Made 2026-09-28 19:43 IST. No job of the final batch had been submitted, and no result of the final batch existed:
`phase3/results/` held only `phase3_run/` and the E0 audit files. Sections 1-8 are unchanged. The primary analysis,
contrasts and readings stand exactly as written.

- **Pre-declared sensitivity (processor-level view).**
  - Every primary contrast of section 4 is also reported with Address_select signed off by its tb.v (metric
    `signoff_clean_proc`). Every other task is scored as in the primary analysis.
  - Justification: in the MPSoC, MuxPC reads J_addr only when PCsrc = 2'b01, which is the case tb.v checks.
  - The primary classification of Address_select stays class (i). That follows the rule fixed before the audit:
    spec-defined behaviour differs.
  - The reading this sensitivity would give is printed but not used. The primary reading decides.
- **Secondary, exploratory analysis.** It covers Address_select and mem_wb_mux, the two tasks with a spec-complete
  sign-off testbench.
  - Runs are broken down by condition and model group: "gap" runs (clean_pass under tb.v, not signoff_clean) next to
    the signoff_clean runs.
  - For each group, the analysis counts how many runs received default-assignment advice in any feedback round,
    matched on fixed text patterns in the directive or raw tool text:
    - `<safe value>` (the production LATCH text, which both v2 and v3 emit);
    - `Make these the FIRST statements` (the v3 LATCH builder);
    - "add a default" / "default branch" / "default at the top".
  - Counts only; no interpretation is pre-registered. Implemented in `gap_advice_block()` in `analyze_phase3.py`.
