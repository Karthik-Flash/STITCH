# Phase 3 final batch: brief for the planner (what to put in the paper, and how)

Written 2026-09-30 by the Phase 3 agent, after the final batch completed and the pre-registered analysis ran.
Every number below is copied from a generated file:
- `PHASE3_FINAL.md` / `phase3_final.json`: the pre-registered analysis (the reference for every CI).
- `PAPER_NUMBERS.md`: each Section 9 claim as run vs under the sign-off oracle, plus the final-batch numbers.
- `backend_check_output.txt`: the Vulkan check in section 1.
- `../phase3_run/POSTHOC_SIGNOFF.md`: the POST HOC sign-off re-score of the 990 runs.
- `../FREEZE_FINAL.md` and `../PREREG_FINAL.md`: freeze record and pre-registration.

Your decisions are needed in section 8. After that the Phase 3 agent edits `paper/STITCH_EXT_v7.tex` Section 9, the
abstract/conclusion sentences that quote Phase 3, and `paper/PHASE3_MPSOC.tex`, once.

## 1. What ran, and did it run as planned

- **Arm A, `baseline_gate` (control):** 198 runs, 6 original models x 11 tasks x N=3. **Arm C, qwen2.5-coder:32b:**
  198 runs, 6 conditions x 11 x 3. Both have 0 errors. Compose ran for both: 54 group-designs each.
- **Pre-registration and freeze held.**
  - The deployed code hashes matched FREEZE_FINAL (18/18), and so did the PREREG hash (`1b6eb915…`).
  - Every new run records its provenance. Protocol fields are identical across all 1,386 runs:
    `feedback_first_v2`, v3 3.0.1, production interpreter `42f61a49…`, T=0.1, 6 calls, sem_include_raw=1.
  - The task-file hashes recorded in the new runs match the analysed task files.
- **Models:** the six original model IDs were identical before and after the pull, so arm A used the same weights as
  the 990 runs. The qwen2.5-coder:32b ID is `b92d6a0bd47e`.
- **baseline_gate verified on real output:**
  - Of all its prompts, 0 contain tool text.
  - The gate message reaches the runs where simulation passes but sign-off fails.
  - toolfb, semantic_fired, escalated and restarted are 0 / False / None / False on every run.
- **Deviation 1, the inference backend of arm A.**
  - In job A, Ollama's CUDA discovery timed out, and it ran on its Vulkan backend (same H200, all layers on the GPU;
    `results/final_batch_logs/ollama_serve_369809.log`). Job C used CUDA.
  - The backend of the 990 runs was not recorded in their metrics. Their serve logs on the HPC would show it.
  - POST HOC check (`backend_check.py`): on sim-visible tasks, the first prompt of baseline_gate and baseline is
    byte-identical (90/90). On those identical prompts:
    - the first responses are byte-identical 41% of the time gate vs baseline (112/270), and 41% baseline vs
      baseline across replicates (37/90);
    - first-call func_pass is 42/90 (gate) vs 44/90 (baseline).
  - No backend effect is detectable. This belongs in the paper as one sentence in the limitations or experiment
    paragraph.
- **Deviation 2, the queue.** Jobs A and C waited about 17 h for GPUs. Both ran on gpunode7 (H200 NVL), the node of
  the 990 runs, on different GPUs (PCI `91:00.0` and `01:00.0`) with separate ollama servers.

## 2. The pre-registered result: the interpreter's detail matters, not just the alarm

Primary metric `signoff_clean`, six models, cell bootstrap over (model, task) cells:

| primary contrast | Δ pts [95% CI] | sign-flip p | A-only / B-only |
|---|---|---|---|
| 1. sem_esc_restart_v3 − baseline_gate | **+19.7 [+11.1, +29.3]** | <0.001 | 42 / 3 |
| 2. sem_adv_v3 − baseline_gate | **+14.6 [+3.0, +26.3]** | 0.021 | 43 / 14 |
| 3. baseline_gate − raw_adv | −0.5 [−9.1, +8.1] | 1.000 | 16 / 17 |
| 4. baseline_gate − baseline (sim-visible) | −1.1 [−4.4, +2.2] | 1.000 | 2 / 3 |

- **Pre-registered reading R1:** contrasts 1 and 2 both exclude 0 with the gate lower, so *the detail in the feedback
  adds value beyond the verdict.*
- The pre-declared processor-level sensitivity (Address_select signed off by tb.v) gives the same reading, and larger:
  +24.2 [+14.6, +34.3] and +19.7 [+7.6, +32.3].
- The as-run (tb.v) column agrees: +23.7 [+14.1, +33.8] and +17.7 [+5.1, +30.3].
- By stratum:
  - Contrast 1 holds on both sim-silent tasks (+23.1 [+11.1, +37.0]) and sim-visible tasks (+15.6 [+4.4, +27.8]).
  - Contrast 2 is carried by the sim-silent tasks (+23.1 [+6.5, +39.8]); on sim-visible tasks it is +4.4
    [−11.1, +20.0].

What the control arm adds (secondary, labelled as such):
- **The bare verdict is worth about as much as raw tool text, and adds nothing over simulation-only repair on
  sim-visible tasks.** signoff_clean is 103/198 for the gate, against 104/198 for raw text.
- **Where the verdict was not enough, the interpreter would have spoken.** Of the 95 baseline_gate runs that were not
  signoff_clean, v3 would have fired on the RTL the verdict was given on in all 95, and on the returned RTL in 38.
  This is logged, never fed back.
- **The verdict alone plateaus; escalation keeps climbing.** Cumulative signoff_clean by call 6: gate 52%, escalation
  72%. Both start from the same gate message; the difference appears once escalation hands over to v3.
- **The verdict alone costs simulation passes on sim-silent tasks.** At the end of the run, simulation still passes in
  80/108 baseline_gate runs against 97/108 for escalation. Told only "fails sign-off", models rewrite working logic.
- **Composition (top-level synthesis pass):** baseline_gate 11/18 in each of the 2x2 mesh, the 3x3 mesh and the
  MPSoC, against escalation 18/18, 18/18, 15/18 and v3 16/18 in all three.
- **Per model** (Holm within each contrast): escalation − gate is +39.4 on llama3.2:3b and +33.3 on gemma3:4b (Holm p
  0.006 each), and +6.1 to +18.2 on the others (not individually significant). The detail matters most for the
  smallest models, the same pattern as Phases 1-2.

## 3. The sign-off oracle: what changes in the existing Section 9 numbers

- The 990 runs are re-scored exactly under `tb_signoff.v`: the loop never saw it, so no re-run was needed.
- Two tasks had a testbench gap:
  - **mem_wb_mux:** `ex_mem_memwrite = 0` and `FWD = 2'b11` were unchecked.
  - **Address_select:** tb.v checked J_addr only on a non-flushed JAL, but the spec defines it on every input.
- The other nine tasks are proven equivalent to golden, or equivalent on the inputs the spec allows.
- It is labelled POST HOC for the 990 runs and pre-registered for the new arms.

| claim in v7 Section 9 | as run (now in the paper) | sign-off (primary) |
|---|---|---|
| Table 9 clean_pass: baseline / raw / v2 / v3 / esc | 23 / 59 / 68 / 74 / 80% | 22 / 53 / 63 / 67 / 72% |
| signed off defective (baseline) | 62% (silent structural pass) | 63% (125/198); sim-silent still 108/108 |
| v3 − raw | +14.6 [+3.5, +26.3] | +14.1 [+3.5, +24.7], p 0.014 |
| v2 − raw | +9.1 [+1.0, +17.7] | +10.1 [+2.0, +18.7], p 0.030 |
| v3 cost vs raw | −23.3% calls, −23.2% tokens | unchanged (outcome-independent) |
| tokens per clean pass, v3 / raw | 4,580 / 7,440 | 5,066 / 8,370 |
| clean after the first call, v3 / raw / baseline | 62 / 46 / 17% | 55 / 41 / 15% |
| per model v3 − raw: 3B / qwen 7B / 14B | +24.2 / +27.3 / +0.0 | +24.2 / +27.3 / +0.0 (qwen 7B 30/33 vs 21/33; 14B 30/33 each) |
| escalation tool rounds vs v3 | −47.5% | unchanged |
| esc − baseline, sim-visible | +23.3 [+8.9, +37.8] | **+14.4 [+3.3, +27.8], p 0.048** |
| llama3.2:3b sim-visible: baseline / raw / esc | 9 / 1 / 8 of 15 | 7 / 1 / 8 of 15 |
| four focus tasks, v2 → v3 | 42 → 50 of 72 | unchanged |
| composition table | as in the paper | unchanged (synthesis only) |

Every ordering and every direction survives. Two things weaken:
- esc − baseline on sim-visible tasks roughly halves (+23.3 to +14.4), though its CI still excludes 0.
- All absolute clean rates drop 5 to 8 points for the tool conditions.

Both come from Address_select (section 4).

## 4. A finding for the paper: latch-removal advice can violate the specification

- On Address_select, 41 loop-clean candidates drive `J_addr = 0` where the spec defines `J_addr = X + PC`. The
  latch is gone, synthesis is clean, the loop testbench passes, and the module violates its specification.
- The production LATCH directive, which v3 passes through on this task, says:
  "The simplest way is one unconditional assignment at the top of the block … `J_addr = <safe value>;`".
- Counts (exploratory, pre-declared in amendment A1; six models; gap = loop-clean but failing sign-off):

  | Address_select | gap runs | gap runs with the `<safe value>` advice |
  |---|---|---|
  | baseline | 3 | 0 |
  | raw_adv | 7 | 0 |
  | sem_adv_v2 | 8 | 8 |
  | sem_adv_v3 | 12 | 12 |
  | sem_esc_restart_v3 | 11 | 11 |
  | baseline_gate | 2 | 0 |

- Runs without the advice (baseline, raw, gate) also produce gap runs, so this is **not** a causal claim. On
  mem_wb_mux, 11 of the 11 signoff_clean runs in v2 and in v3 also received the advice.
- Suggested framing: honest, as a limitation of structural feedback in general, the interpreter's included.
  - A structural fix can be functionally wrong exactly where the loop testbench does not look.
  - A spec-complete sign-off oracle catches it.
  - The natural fix is a directive that says "default to the value the specification defines, not a constant". It
    goes in Directions; v3 is not changed.
- The processor-level note: in the MPSoC, MuxPC reads J_addr only when PCsrc = 01, so the violation is invisible at
  processor level. That is why the pre-declared sensitivity exists; it gives the same reading.

## 5. qwen2.5-coder:32b (one model, N=3; a separate row, never pooled into the headline)

| condition | signoff_clean | sim-silent | sim-visible | tokens/run |
|---|---|---|---|---|
| baseline | 12/33 | 0/18 | 12/15 | 663 |
| raw_adv | 30/33 | 18/18 | 12/15 | 1,492 |
| sem_adv_v2 | 30/33 | 18/18 | 12/15 | 1,655 |
| sem_adv_v3 | 30/33 | 18/18 | 12/15 | 1,660 |
| sem_esc_restart_v3 | 30/33 | 18/18 | 12/15 | 1,850 |
| baseline_gate | 28/33 | 16/18 | 12/15 | 1,824 |

- **At 32B, any tool feedback saturates the task set.** Every tool condition repairs all 18 sim-silent runs; the 3
  misses in each are the Address_select spec gap.
- **Simulation-only still signs off all 18 sim-silent runs as defective.** The guard's value does not shrink with
  scale; interpretation's pass-rate edge over raw text does, and raw text is the cheapest at 32B.
- Composition: every tool condition 3/3 in all three designs; baseline 0/3.
- **This fits the narrative ("benefit scales with how structural the failure is, and helps small models"),** and it
  matches Set 3 (Section 8.4), where the deficit and the gains are small-model phenomena.
- The seven-model pool is in PHASE3_FINAL.md. Every contrast keeps its sign; for example esc − gate is +17.7
  [+10.4, +25.6].

## 6. Limitations to state (short)

1. The v3 rules are still in-sample: no held-out defects were run.
2. The sign-off oracle was introduced after the equivalence audit of the 990 runs. It is POST HOC for them and
   pre-registered for the new arms. The as-run numbers stay beside it as a sensitivity.
3. Arm A ran on a different inference backend (Vulkan), with no detectable effect (section 1).
4. The 32B model is one model at N=3, and at ceiling.
5. Composition is synthesis only; composed systems are not simulated. The Address_select violation is invisible at
   processor level.
6. Replicates are correlated, so all general claims use the cell bootstrap.

## 7. Suggested framing (the story the data support)

- STITCH is a **deterministic sign-off guard and translator.**
  - (i) The guard: simulation-only repair signs off every sim-silent defect (108/108; 18/18 even at 32B).
  - (ii) The translation matters beyond the alarm. Telling the model *that* sign-off failed is worth about as much as
    raw tool text, and telling it *what* failed adds +14.6 (always on) to +19.7 (escalation) points. Every run where
    the bare verdict failed had an interpreter directive available.
  - (iii) Escalation is the recommended design: the highest clean rate (72%, sign-off), about 48% fewer tool rounds
    than always-on v3, and full composition of both meshes.
  - (iv) The benefit scales with how structural the failure is (sim-silent > sim-visible) and with how small the
    model is. At 32B, any tool feedback suffices, but the guard is still needed.
- **The honest counterweight:** structural advice can produce spec violations where the loop testbench is weak.
  Report it as a finding, with the fix in Directions.

## 8. Decisions needed from the planner

1. **Headline metric in Section 9.** Recommend signoff_clean as primary in every table and in the prose, with the
   as-run clean_pass as a column or parenthesis. The 990 numbers change as in section 3.
2. **Structure.** Recommend adding two results to Section 9: "(6) The detail, not the alarm" (the control arm) and
   "(7) Up the ladder: 32B", plus a short paragraph on the oracle and the Address_select finding (in Results or in a
   "What the case study establishes / limitations" paragraph). Keep PHASE3_MPSOC.tex as the full version with every
   table.
3. **Tables.**
   - Table 9 gains a baseline_gate row and a signed_off_defective column.
   - The composition table gains a baseline_gate column.
   - New small table for the four primary contrasts, and one 32B row table (or a sentence).
4. **Figures.**
   - The existing `fig_p3_*` were generated on the as-run metric without the gate.
   - Recommend regenerating `fig_p3_clean_by_condition` and `fig_p3_clean_by_call` on signoff_clean with baseline_gate
     added, which is a small extension of `phase3_figures.py`.
   - `fig_p3_composition` with the gate column.
   - Agree or drop.
5. **Abstract / introduction / conclusion.** They quote "62%" and "+14.6". Recommend "63% (all 108 sim-silent runs)",
   "+14.1 points over raw text", and a clause for the control arm ("the interpreter's detail, not the sign-off verdict
   alone, drives the gain: +19.7 points for escalation over a verdict-only control").
6. **The Address_select finding:** in Results (as a finding) or in Limitations? Recommend Results, point (8), with
   the Directions item.
7. **Directions:**
   - Remove "a control arm that separates…" (done).
   - Keep held-out defects and integration-level feedback.
   - Add the spec-valued default directive.
8. **Anything to hold back** from the paper (for example the backend check, the per-task tables): recommend they go
   to PHASE3_MPSOC.tex only.
