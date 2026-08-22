# Phase 1 — consolidated findings

**The committed record of what Phase 1 actually established**, in the
same spirit as phase0's consolidated illustration findings. Sourced from
`PHASE1_TASK3_ANALYSIS.md` (the 255-run escalation benchmark),
`PILOT_INSIGHTS.md` + `results/rtllm_alu_refix2/REPORT.md` (the RTLLM
pilot and its bug-fix validation re-run), and the diagnostics that
preceded each. Every number below is traceable to one of those
documents — this file draws the conclusions together, it does not
re-derive them. Written to be the honest, citable summary for the paper,
not an aspirational one.

---

## 1. The real, defensible result: cost, not pass rate

`sem_escalate` invokes heavyweight tools (Verilator + Yosys subprocess
spawns) **~35-45% less often** than unconditional `sem_adv`/`raw_adv`,
while matching or exceeding their pass rate on every category measured
(§3-§5, `PHASE1_TASK3_ANALYSIS.md`). This is the headline: **cost and
robustness, not pass-rate dominance** — the actual upgrade Phase 1 makes
over the MLCAD paper's always-on `sem_adv` design.

**Two axes, and they diverge — report both.** Tool-invocation cost drops
~35-45%, but mean *token* cost does not fall the same way (`sem_escalate`
5151 tokens/run vs `sem_adv`'s 4883 — higher, not lower), because
escalating and then burning extra iterations before passing (e.g.
`counter_4bit`'s one replicate running to iteration 8) costs tokens even
as it saves tool invocations. **The efficiency claim is scoped to the
tool-invocation axis, where it holds — it is not a claim about token
cost**, which moves the other way on some cells.

## 2. Pass-rate result on the cells that actually replicate: mixed, equal weight

Only 4 of the 17 Task 3 cells showed any real signal once labels were
re-verified at N=3 (see §5 below) — everything else tied trivially.
Reporting all four, none weighted above the others:

- **Win** — `pwm_generator`/deepseek-coder:6.7b: baseline 0/3 →
  `sem_escalate` 2/3, beating both baseline and unconditional `sem_adv`
  (1/3).
- **Structural win** — `ripple_carry_adder`/deepseek-coder:6.7b: baseline
  3/3, `sem_adv` collapses to 0/3 (tools hurt from iteration 1),
  `sem_escalate` holds 3/3 by correctly never firing. The win is staying
  out of the way, not an active rescue.
- **Cost, no pass/fail change** — `counter_4bit`/deepseek-coder:6.7b:
  all conditions 3/3, but one `sem_escalate` replicate burns 6 extra
  iterations before passing.
- **Loss** — `alu_8bit`/gemma3:4b: `sem_escalate` loses a replicate
  (2/3) that baseline, `sem_adv`, and `sem_escalate_restart` all win
  cleanly (3/3). Not explained — STUCK_THRESHOLD rescued this exact cell
  in the Task 2.5 diagnostic but doesn't here, in the escalated context.
  **Deferred to Phase 2, not forgotten.**

This is not a case for "`sem_escalate` beats `sem_adv`" on pass rate
alone. It's a small, four-cell sample with real movement in both
directions, reported at equal weight per cell.

## 3. No pass-rate advantage for `sem_escalate` on RTLLM — state plainly

Across the RTLLM pilot (3 complete modules, N=3) and the harness-fixed
`alu`/`calendar` budget-capped re-run (2 modules, 4 models, N=3, both
harness bugs fixed and confirmed clean), **no RTLLM module shows a
pass-rate win attributable to the mechanism**:

- **`alu` is genuinely hard, post-fix, not a harness artifact.** Baseline
  0/12 across 4 models, `sem_adv` 0/12, `sem_escalate` 0/12 — flat zero.
  86% of terminal failures are compile-class. The interpreter engaged
  for real (32 fires, 11 real escalation triggers) and still rescued
  nothing.
- **`calendar`'s pooled trend (baseline 6/12 → `sem_adv` 7/12 →
  `sem_escalate` 8/12) is ceiling + early-luck, not rescue, once
  decomposed.** 2 of 4 models are a pure ceiling (9/9 pass on iteration
  1 in every condition, zero interpreter fires — uninformative by
  construction). On the only 2 models where `calendar` is actually
  measurable, every one of the 3 "extra" passes over baseline happened
  *before* the mechanism ever fired (iteration 1-2, `semantic_fired=0`),
  while every run where it *did* fire for real (`fired_escalate=True`,
  4 such runs) still failed. Real engagement correlated with failure,
  not success, in this sample.
- 3 of the pilot's 3 complete original modules (`accu`, `counter_12`,
  `barrel_shifter`) showed no differentiation either — a ceiling, a
  floor, and a flat 20% across every condition respectively.

`qwen2.5-coder:14b` was never tested on `alu`/`calendar` post-fix
(dropped mid-run to fit the 8h budget cap), and `calendar` was never
reached at all in the *first* pilot attempt — both are named, real gaps,
not papered over. But on everything that *was* measured cleanly, RTLLM
shows no pass-rate win for the mechanism. This is reported as it lands,
not softened.

## 4. Methodology finding: the N=1 → N=3 replication collapse

The harmful/enabling cell labels driving Task 3's run set were built
from N=1 historical data. Re-sampled fresh at N=3, **4 of 5 "real-test"
cells and 2 of 3 "enabling" cells did not reproduce the baseline
behavior their label was built on** — including flips as stark as
`pwm_generator`/deepseek-coder going from a single documented pass to
`[FAIL, FAIL, FAIL]` at N=3. This is the same confound phase0 already
flagged in the abstract ("N=1 makes the entire result unfalsifiable")
showing up concretely at production scale: **most of a carefully
pre-registered 17-cell run set turned out not to test what it was built
to test**, once actually sampled three times instead of once. Any future
cell selection — Phase 1 or Phase 2 — needs N≥3 confirmation before it's
trusted as a basis for anything, not just as a reporting convention
after the fact.

## 5. Two harness bugs found and fixed

Both in `src/runner/stitch_runner.py`, the shared runner behind v20,
Task 3, and the RTLLM pilot:

- **Bug #2**: `run_iverilog_sim()` never set `vvp`'s working directory,
  so any testbench doing relative-path file I/O (`$readmemh`, etc.)
  could never resolve its data file — 100% reproducible whenever a
  design compiled. Zeroed out `alu`, `calendar`, `signal_generator`, and
  `multi_booth_8bit` in RTLLM by construction. Confirmed to NOT affect
  v20 (no v20 testbench does file I/O) or Task 3 (same reason).
- **Bug #1**: the code-extraction fallback didn't strip a stray,
  unclosed ` ```verilog ` fence marker, corrupting otherwise-compilable
  code. Confirmed recurring in v20 historical data. **Confirmed to have
  corrupted 58 of 659 (8.8%) of Task 3's own generated `.v` files** —
  meaning some fraction of Task 3's reported `syntax_error` terminal
  states, STUCK_THRESHOLD fires, and the §2 flip-cell findings above may
  be partly attributable to this extraction artifact rather than genuine
  model behavior. **A Task 3 re-audit against the fix is a named,
  pending item — not done in this phase, not to be treated as a
  correction to §1/§2 until it is.**

Both fixes verified before/after on golden references (file-I/O and
non-file-I/O) prior to trusting them; both confirmed clean at full scale
in the 72-run `alu`/`calendar` re-run (0 corrupted files, 0 errors).

## 6. Hypothesis for Phase 2 to test, not an established result

One qualitative trajectory, flagged clearly as a **hypothesis, not a
finding**: `llama3.1` on `alu` is flatlined under baseline (identical
`reg_wire_mismatch` × 6, zero variation, all 3 replicates) but under
`sem_escalate` reaches states it never touches on its own (3 consecutive
`logic_error` iterations — meaning the code actually compiled and
simulated for a stretch). `deepseek-coder:6.7b`, whose baseline is
already self-exploring on the same module, shows much less visible
benefit from the same tooling. The **capability-conditional hypothesis**:
escalation's mechanism may help models that get stuck in a narrow,
repeating failure mode, and add little for models that already diversify
their own attempts. This is one trajectory on one model on one module —
not validated, not quantified, and explicitly **not** cited anywhere
above as evidence for a pass-rate effect. Phase 2's model ladder
(4B→32B) is a real opportunity to test it directly: does the effect
size, if any, correlate with model capability/self-exploration the way
this single trace suggests?

---

## What Phase 1 does not claim

- No broad pass-rate superiority for `sem_escalate` over `sem_adv` —
  demonstrated on 4 cells, mixed, not broad.
- No RTLLM value established for the mechanism, positively or
  negatively — measured cleanly where it was measured, but coverage is
  partial (`qwen2.5-coder:14b`, `calendar`'s ceiling models, and 47 of
  RTLLM's 50 designs entirely untested).
- No claim that Task 3's §1/§2 findings are unaffected by bug #1's 8.8%
  contamination rate — flagged as open, not resolved.
