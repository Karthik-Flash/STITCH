# Phase 1 runbook

One entry per `phase1/*.py` (all 8), for a coauthor who wasn't in the
session and needs to know what ran, in what order, and what each script
is evidence for. Grouped by reading order: Task 0 → harness + tests →
Task 2.5 → Task 3. `phase1/tests/` and `phase1/fixtures/` are covered
inline where the file that uses them is described, not as separate
entries (they aren't `phase1/*.py` top-level scripts).

**Dead-file check:** none of the 8 is dead. Every one is cited by at
least one finding already referenced elsewhere in this repo
(`PHASE1_TASK3_ANALYSIS.md`, this runbook, or a docstring's "Produced:"
line) — see the "produced" column below. Nothing here duplicates
another file's job. If that changes later, list it here rather than
deleting silently.

---

## Task 0 — is the error-signature normalization sound?

### `error_signature.py`
- **Purpose:** normalizes raw iverilog failure text into a signature the
  escalation state machine keys on to detect "same failure recurring"
  vs. "new failure." Pure functions, no I/O.
- **Command:** not run directly — imported by `demo_error_signature.py`,
  `escalation_runner.py`, `stuck_threshold_diagnostic.py`, `task3_runner.py`.
- **Requires:** neither (pure regex/string functions).
- **Produced:** the normalization design itself — window widened from 3
  to 5 lines after review (see the file's own `DEFAULT_WINDOW` comment
  for why).
- **Runtime:** N/A (library).

### `demo_error_signature.py`
- **Purpose:** prints raw iverilog text → `classify_error()` bucket →
  `error_signature()` output for 10 real examples pulled from existing
  phase0 run logs, so the normalization can be eyeballed for
  over-/under-collapsing before anything is built on top of it.
- **Command:** `python phase1/demo_error_signature.py`
- **Requires:** neither — no WSL, no Ollama, no live run.
- **Produced:** the Task 0 sign-off. Confirmed the normalization doesn't
  over-collapse distinct failures or under-collapse genuine repeats;
  this is what motivated widening `DEFAULT_WINDOW` from 3 to 5.
- **Runtime:** instant (<1s).

---

## Harness + tests — the escalation state machine and its runner

### `escalation_state.py`
- **Purpose:** the `sem_escalate` / `sem_escalate_restart` state machine
  (`EscalationState`, `EscalationConfig`) — pure, subprocess-free,
  LLM-free. The actual "Task 1" contribution.
- **Command:** not run directly — imported by `escalation_runner.py`.
  Exercised standalone by its tests (below).
- **Requires:** neither (pure class).
- **Produced:** the transition logic itself, unit-tested in isolation so
  a bug in it couldn't silently invalidate every downstream run.
- **Runtime:** N/A (library).

### `phase1/tests/test_escalation_state.py`
- **Purpose:** 12 unit tests for `EscalationState` — escalate-after-N,
  distinct-signature reset, monotonicity, the iteration-timing edge
  case, restart firing/preemption, `sem_escalate` never restarting.
- **Command:** `python -m pytest phase1/tests/test_escalation_state.py -v`
- **Requires:** neither.
- **Produced:** confidence the state machine is correct before any real
  run depended on it.
- **Runtime:** <1s.

### `phase1/tests/test_escalation_runner_restart.py`
- **Purpose:** integration test for the `sem_escalate_restart` path —
  real WSL tool calls against a fixed, known-broken `decoder_3to8.v`
  (a real file from `phase0/illustrations/proven/`) with a mocked LLM
  that always returns the same broken code, forcing a long identical-
  failure streak deterministically.
- **Command:** `python -m pytest phase1/tests/test_escalation_runner_restart.py -v`
- **Requires:** WSL (Verilator/Yosys/Icarus). No Ollama — the LLM call
  is mocked.
- **Produced:** the STUCK_THRESHOLD-vs-restart precedence interaction,
  caught and traced exactly (restart reached at iterations 5 and 8 in
  an 8-iteration forced-stuck run, but iteration 8's is preempted by
  the older STUCK_THRESHOLD mechanism) — this is what `escalation_runner.py`'s
  "KNOWN INTERACTION" docstring section documents.
- **Runtime:** ~15s.

### `escalation_runner.py`
- **Purpose:** the actual `sem_escalate`/`sem_escalate_restart` runner —
  drives `EscalationState` from real tool/LLM outcomes. Harness only;
  every tool-invocation and directive function is imported unmodified
  from `src/runner/stitch_runner.py` / `src/interpreter/stitch_interpreter.py`.
- **Command:** not run directly — imported by `smoke_test.py` and
  `task3_runner.py`. `run_one_replicate(...)` is the entry point.
- **Requires:** WSL + Ollama (whichever model is passed in).
- **Produced:** the two escalation conditions used in Task 3.
- **Runtime:** N/A (library) — see `smoke_test.py`/`task3_runner.py` for
  real invocation timings.

### `smoke_test.py`
- **Purpose:** one real end-to-end run (`decoder_3to8`/gemma3:4b,
  `sem_escalate`) before committing to Task 3's full sweep — plan v2's
  "smoke-test before scaling" step.
- **Command:** `python phase1/smoke_test.py`
- **Requires:** WSL (Verilator/Yosys/Icarus) + Ollama serving `gemma3:4b`.
- **Produced:** caught a real bug on first run — the per-iteration
  `escalation_state` log field was reading `EscalationState.state`
  *after* `observe_failure()` had already mutated it, mislabeling the
  exact iteration that triggered escalation. Fixed in `escalation_runner.py`
  before Task 3 ran (see that file's `IterationRecord` append comments).
  Without this script that bug would have shipped silently into all 255
  Task 3 runs.
- **Runtime:** ~30-45s (single replicate, 4 iterations observed).

---

## Task 2.5 — is STUCK_THRESHOLD masking sem_adv's real effect?

### `v20_specs.py`
- **Purpose:** spec/prompt text for the 10 v20-diagnostic modules used
  by both Task 2.5 and Task 3's harmful/enabling cells — recovered
  verbatim from real recorded `feedback.txt` files (not in this repo
  otherwise), plus the `ripple_carry_adder` dependency map pointing at
  `phase1/fixtures/full_adder_dependency.v` (a real golden `full_adder.v`
  from the original AutoChip project — the historical sweep this data
  came from was missing that dependency file).
- **Command:** not run directly — imported by `stuck_threshold_diagnostic.py`
  *and* `task3_runner.py` (both Task 2.5 and Task 3 draw specs from this
  one file — not duplicated).
- **Requires:** neither (pure data module).
- **Produced:** the spec source both later scripts depend on; see the
  file's own docstring for exact provenance per module.
- **Runtime:** N/A (data module).

### `stuck_threshold_diagnostic.py`
- **Purpose:** toggles `stitch_runner.STUCK_THRESHOLD` (monkeypatched,
  `run_one_condition()` reused completely unmodified) on vs. off across
  the 13 harmful+enabling cells, N=3 each, to isolate whether the
  pre-existing rewrite mechanism was confounding `sem_adv`'s numbers.
- **Command:** `python phase1/stuck_threshold_diagnostic.py`
- **Requires:** WSL + Ollama serving `deepseek-coder:6.7b`, `llama3.1`,
  `gemma3:4b` (the 3 models these 13 cells cover).
- **Produced:** the Task 2.5 finding — STUCK_THRESHOLD is a real,
  mixed-direction confound, not a non-issue. 3/13 cells flip pass/fail
  between on and off; aggregate moves 76.9% (off) → 84.6% (on), driven
  mostly by one cell (`alu_8bit`/gemma3:4b, 0/3→3/3) while another moves
  the opposite direction (`ripple_carry_adder`/deepseek, 3/3→2/3). This
  finding is what decided Task 3's precedence (STUCK_THRESHOLD stays on,
  instrumented as a reported axis, no on/off factorial).
- **Runtime:** ~60-90 minutes for the full 78-run sweep (78 runs across
  3 models; varies with how many iterations each cell needs).
- **Output:** `phase1/results/stuck_threshold_diag/master_log.json`
  (gitignored — re-run to regenerate; not separately summarized as a
  tracked file since Task 3 supersedes it as the cited evidence for
  precedence).

---

## Task 3 — the escalation benchmark

### `task3_runner.py`
- **Purpose:** the full benchmark — 17 cells (10 harmful + 3 enabling +
  4 regression-gate) × 5 conditions (`baseline`, `raw_adv`, `sem_adv`,
  `sem_escalate`, `sem_escalate_restart`) × N=3 = 255 runs, one pass, no
  tuning, no re-runs.
- **Command:** `python phase1/task3_runner.py`
- **Requires:** WSL + Ollama serving `deepseek-coder:6.7b`, `llama3.1`,
  `gemma3:4b` (the 3 models with a cell in this run set — `qwen2.5-coder:14b`
  and `gemma3:12b` have none; see `PHASE1_TASK3_ANALYSIS.md` §1 for why).
- **Produced:** `phase1/results/task3/master_log.json` (gitignored, full
  per-iteration traces) and `phase1/task3_summary.json` (tracked, same
  255 records with `per_iteration` stripped — the reproducible backing
  for `PHASE1_TASK3_ANALYSIS.md`, which is the actual finding: a mixed
  result, not a `sem_escalate` win — see that document.
- **Runtime:** ~2 hours for the full 255-run sweep.

---

## Reproduce a result yourself

Two scripts are safe to run without committing to a long sweep:

```
python phase1/demo_error_signature.py   # no infra, instant — Task 0 sign-off
python phase1/smoke_test.py             # WSL+Ollama, ~30-45s — reproduces
                                         # the Task 1 escalation-state bug-catch
```

The unit tests are also safe and fast:

```
python -m pytest phase1/tests/test_escalation_state.py -v          # <1s, no infra
python -m pytest phase1/tests/test_escalation_runner_restart.py -v # ~15s, WSL only
```

`stuck_threshold_diagnostic.py` and `task3_runner.py` are real, hour-plus
sweeps against live WSL+Ollama — not something to run casually to "check"
a result. Both write their `master_log.json` incrementally, so an
interrupted run resumes from where it left off (already-completed
`(module, model, condition/toggle, replicate)` keys are skipped) rather
than restarting.
