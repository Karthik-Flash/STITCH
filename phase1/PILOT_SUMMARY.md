# RTLLM v2.1 pilot — wrap-up summary

**Status: TRIAL / DEMO, stopped early by deliberate decision, not a
publishable result.** 3 of 5 pilot modules ran to full completion
(5 models × 5 conditions × N=3 = 225 runs each... i.e. 75 runs per
module); the run was stopped there rather than continuing through the
two remaining modules. The full 50-design pass@5 study on HPC is the
actual benchmark this stands in for — nothing here should be cited.

Raw data: `phase1/results/rtllm_pilot/master_log.json` (gitignored).
Screen/selection: `phase1/RTLLM_PILOT_PREREG.md`.

---

## STEP 1 — clean stop and manifest

Stopped by sending a terminate signal to the runner process (PID 583)
only once no write was in progress -- the last `master_log.json` write
had already completed (entry #288), and the only thing in flight was an
HTTP call to Ollama for the next cell's LLM response, which carries zero
risk to the JSON file regardless of when it's interrupted. Confirmed
after stopping: `master_log.json` parses as valid JSON, 288 entries,
0 errored records, no orphaned WSL/iverilog/verilator/yosys subprocesses
left running.

**288 / 375 done. 87 not done.**

| module | done | not done |
|---|---|---|
| accu | 75 / 75 | 0 |
| counter_12 | 75 / 75 | 0 |
| barrel_shifter | 75 / 75 | 0 |
| alu | 63 / 75 | 12 |
| calendar | 0 / 75 | 75 |

The 12 not-done `alu` cells are all `qwen2.5-coder:14b` (the last model
processed for that module before the stop), across
`raw_adv`/`sem_adv`/`sem_escalate`/`sem_escalate_restart` x 3 replicates
each (`baseline` for that model had already finished). `calendar` never
started -- all 75 of its cells are not done. Resuming later (same
`--conditions core5` launch command) would pick up exactly these 87
cells and skip the 288 already-done ones, per the incremental-checkpoint
design.

## STEP 2 — the 3-module demo graph (accu, counter_12, barrel_shifter)

**PILOT / TRIAL — 3 of 5 modules, not a result.** Pass rate per
condition, pooled across the 5 Tier-1 models (15 runs per condition per
module, 45 runs per condition pooled across all 3):

### Per module (pooled across 5 models)

| module | baseline | raw_adv | sem_adv | sem_escalate | sem_escalate_restart |
|---|---|---|---|---|---|
| accu | 1/15 (6.7%) | 0/15 (0%) | 0/15 (0%) | 0/15 (0%) | 0/15 (0%) |
| counter_12 | 15/15 (100%) | 14/15 (93.3%) | 15/15 (100%) | 15/15 (100%) | 15/15 (100%) |
| barrel_shifter | 3/15 (20%) | 3/15 (20%) | 3/15 (20%) | 3/15 (20%) | 3/15 (20%) |

### Per model (pooled across the 3 complete modules, 9 runs/condition)

| model | baseline | raw_adv | sem_adv | sem_escalate | sem_escalate_restart |
|---|---|---|---|---|---|
| gemma3:4b | 3/9 (33%) | 2/9 (22%) | 3/9 (33%) | 3/9 (33%) | 3/9 (33%) |
| llama3.1:latest | 3/9 (33%) | 3/9 (33%) | 3/9 (33%) | 3/9 (33%) | 3/9 (33%) |
| deepseek-coder:6.7b | 3/9 (33%) | 3/9 (33%) | 3/9 (33%) | 3/9 (33%) | 3/9 (33%) |
| gemma3:12b | 3/9 (33%) | 3/9 (33%) | 3/9 (33%) | 3/9 (33%) | 3/9 (33%) |
| qwen2.5-coder:14b | 7/9 (78%) | 6/9 (67%) | 6/9 (67%) | 6/9 (67%) | 6/9 (67%) |

### Pooled aggregate (all 3 modules × 5 models, 45 runs/condition)

| condition | pass rate |
|---|---|
| baseline | 19/45 (42.2%) |
| raw_adv | 17/45 (37.8%) |
| sem_adv | 18/45 (40.0%) |
| sem_escalate | 18/45 (40.0%) |
| sem_escalate_restart | 18/45 (40.0%) |

**Read this plainly, not optimistically:** the pooled number shows
essentially **no differentiation between conditions** on this 3-module
demo. That's because per-module behavior is almost binary — `counter_12`
is solved by nearly everyone regardless of condition (a ceiling, no
room to show any effect), `accu` is essentially unsolved by everyone
(a floor, same problem), and `barrel_shifter` sits at a flat, identical
20% across every single condition. **Three modules is not enough
diversity to say anything about the escalation mechanism** — this
demo graph exists to prove the harness produces a real, readable result
end-to-end, not to make any claim about `sem_escalate`'s value. The one
model-level signal worth a glance — `qwen2.5-coder:14b` outperforming
the other four across every condition — is a single-model, 3-module
observation and not something to build on yet.

## The alu finding, reported separately (not folded into the graph above)

**`alu` (Miscellaneous/RISC-V, file-I/O design): 0/62 pass across every
model and every condition attempted, and every one of those 62 runs
burned its full iteration budget** (38 completed at cap=6 for the
classic three conditions, 24 at cap=8 for the escalation conditions —
zero early exits). This held before the run was stopped, 62 of the
module's 75 planned runs in.

This is real signal about benchmark difficulty for this Tier-1 model
set, not a harness problem — the pass-detection fix was verified
against the golden reference before launch (see the pilot-setup
report), and `alu`'s companion data file (`reference.dat`) was
confirmed staged and readable. No model in this 5-model set produced a
working RISC-V ALU implementation against RTLLM's testbench within 6-8
iterations, under any condition.

**Input to HPC planning, stated as such:** treat `alu`-class designs as
a worst-case cost estimate, not the average. A module that never exits
early costs roughly its full iteration cap in LLM calls and tool
invocations on every single replicate, every condition, every model —
scaling the full 50-design study using an "average module" cost
estimate (e.g. extrapolating from `accu`/`counter_12`/`barrel_shifter`'s
mostly-short runs) would understate wall-clock and API/compute cost for
however many of the 50 designs turn out to be `alu`-shaped. Budget HPC
time off the slowest observed module, not the mean.

## STEP 3 — speedup ideas for the full 50-design run, labeled

See the separate list below in the chat response (kept out of this
committed doc so it doesn't read as a decision already made — it's
options for you to pick from, not a plan).

## STEP 4 — incidents

**1 incident, resolved by retry, no data lost:**

```
[2026-08-21T03:23:16] accu / llama3.1:latest / sem_escalate / replicate 2
  attempt 1/3 -- retrying (attempt 2/3)
  exception: APITimeoutError: Request timed out.
```

Attempt 2 succeeded (no further log entry for that cell) — an ordinary
Ollama request timeout, the exact kind of transient infra hiccup the
retry mechanism exists for. Nothing else logged in `incidents.log` for
the entire run.
