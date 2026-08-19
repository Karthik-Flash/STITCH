# N=3 replication, round 2 — `instr_decode_unit` and `datapath_mux_alu`

**2026-08-19.** Three independent samples per candidate, run by the user,
temperature 0.1, no fixed seed. Read directly from
`results/replication_pass2/*/sample_*/results_stitch/*/stitch_summary.json` —
not from console output. Neither candidate replicates its single-sample
result from the previous round. **Both retire.**

## Why this round exists

Both candidates showed a single-sample `PASS` under `sem_adv` last round with
a specific confound risk each:

- `instr_decode_unit` / gemma3:4b — `PASS|4` with the interpreter firing
  cleanly once (`UNUSEDSIGNAL` on `valid`, iteration 3→4), but `raw_adv` and
  `sem_adv`'s rewrite-injection prompts at iteration 3 were confirmed
  byte-identical, so the point where `sem_adv` reached syntactically valid
  code and `raw_adv` did not was resampling variance on an identical prompt,
  not an interpreter effect.
- `datapath_mux_alu` / llama3.1 — `PASS|4` with `semantic_fired=0`. The
  interpreter never fired at all; whatever caused `sem_adv` to pass was
  already known to be unattributable before this round started.

Both needed N=3 to tell mechanism from luck. Neither survives it.

## Table A — `instr_decode_unit`, gemma3:4b

| Sample | Baseline pass\|iters | Raw_adv pass\|iters | Sem_adv pass\|iters | Sem_adv semantic_fired | Sem_adv verilator_codes_seen |
|---|---|---|---|---|---|
| 1 | FAIL\|6 | FAIL\|6 | FAIL\|6 | 0 | `[]` |
| 2 | FAIL\|6 | FAIL\|6 | FAIL\|6 | 0 | `[]` |
| 3 | FAIL\|6 | FAIL\|6 | FAIL\|6 | 1 | `['UNUSEDSIGNAL']` |

**Verdict: NOISY.** `sem_adv` never passes across the 3 samples — the NOISY
criterion is met outright, nothing else needs to be weighed.

The one interesting wrinkle is sample 3: the interpreter fired **correctly**
— `UNUSEDSIGNAL` on `valid`, the same clean mechanism as `decoder_3to8` and
`mux4_oe` — and the run still ended `FAILED all 6 iters`. Per-iteration error
sequence: `SYNT, SYNT, LGIC, SYNT, SYNT, SYNT`. Iteration 3 is exactly the
target-defect-only state (`logic_error`, five `FAIL` lines all naming
`valid`-gated control signals), the interpreter converted it, and iteration 4
should have been the fix — instead it regressed back into a **new** kind of
syntax failure (`instr_decode_unit.v:1: syntax error \n I give up.`, the same
degenerate pattern seen at the tail of samples 1 and 2). A correct directive
does not guarantee recovery once the model has entered this failure mode;
whatever produces `I give up.`-style output is a separate, unresolved
instability the interpreter has no vocabulary for and cannot reach.

All three samples' `baseline` and `raw_adv` are **stuck on `syntax_error` for
all 6 iterations, in every sample, with zero exceptions** (9/9 baseline
iterations, 9/9 raw_adv iterations, all `syntax_error` or the degenerate
`give up` variant). Across all three fresh samples plus the two controls, not
one single condition-sample pair ever passed except nothing — this module is
not converging reliably on gemma3:4b in this benchmark regardless of feedback
condition.

**Context — the prior single-sample run does not change the verdict.** That
run (`results/new_illustrations/instr_decode_unit/`, not part of this N=3
batch) showed `sem_adv PASS|4, semantic_fired=1`. Folded in as a fourth data
point: **1 pass out of 4 total `sem_adv` samples**, and the interpreter fired
in 2 of those 4 (the prior run, and sample 3 here) but only converted to a
pass in 1 of those 2. The mechanism engages sometimes and even then does not
reliably rescue the run. That is not the profile of a reproducible
illustration.

## Table B — `datapath_mux_alu`, llama3.1

| Sample | Baseline pass\|iters | Raw_adv pass\|iters | Sem_adv pass\|iters | Sem_adv semantic_fired | Sem_adv verilator_codes_seen |
|---|---|---|---|---|---|
| 1 | FAIL\|6 | FAIL\|6 | FAIL\|6 | 0 | `[]` |
| 2 | FAIL\|6 | FAIL\|6 | PASS\|4 | 0 | `[]` |
| 3 | FAIL\|6 | FAIL\|6 | PASS\|4 | 0 | `[]` |

**Verdict: MIXED.** `sem_adv` wins in 2 of 3 samples and loses in the third —
the "wins in some samples, controls win in others" clause applies on its own.
It is also disqualified a second, independent way: **`semantic_fired=0` in
all three `sem_adv` samples**, including both passes. Either criterion alone
is sufficient; both apply here.

Stated in the required terms: **sem_adv passed without the interpreter
firing. This is raw_adv/sem_adv divergence via resampling variance, not
evidence for the STITCH mechanism. Reinforces the confound category defined
in `evidence/phase_d_report.md`.**

One structural pattern is real and worth recording separately from the
confound, because it does not depend on the interpreter at all. Per-iteration
error sequences, all 3 samples:

```
baseline: reg_wire_mismatch x6                                    (every sample)
raw_adv:  reg_wire_mismatch x2, logic_error x4                     (every sample)
sem_adv:  reg_wire_mismatch x2, logic_error x4                     (sample 1)
          reg_wire_mismatch x3, PASS                               (samples 2, 3)
```

`baseline` never escapes `reg_wire_mismatch` — stuck on the `alu_result`
wire/reg type error for all 6 iterations, every sample, no exception.
`raw_adv` escapes it at iteration 3 in every sample, landing on
`logic_error` and staying there through iteration 6. Verilator's own
compile-time diagnostic (present in `raw_adv` and `sem_adv`, absent from
`baseline`) is doing real work here — that is a genuine, reproducible
tool-presence effect, and it is symmetric: `sem_adv` sample 1 shows the exact
same two-iteration escape as every `raw_adv` sample.

Samples 2 and 3 diverge from that pattern rather than mirroring it: `sem_adv`
stays on `reg_wire_mismatch` for a **third** iteration — one more
unproductive iteration than `raw_adv` ever needed — then jumps straight from
`reg_wire_mismatch` to `PASS`, skipping the intermediate `logic_error` stage
`raw_adv` always passes through. With `semantic_fired=0` confirmed at every
iteration in every sample, that jump carries no interpreter content
whatsoever — `raw_adv` and `sem_adv` are receiving materially the same
Verilator/Yosys text at this point, differing only in prompt framing text
around it, so two different resulting code paths under independent sampling
is exactly what the phrase "resampling variance" means. The tool-presence
effect (escaping `baseline`'s trap) is reproducible and real; the specific
`sem_adv`-over-`raw_adv` iteration-3-to-4 jump is not, and the interpreter
(which has no entry for `reg_wire_mismatch` at all — it only acts on
`UNUSEDSIGNAL`, `MULTIDRIVEN`, `UNDRIVEN`, width and blocking-assignment
codes) cannot be the explanation for it in any sample.

**Context — the prior single-sample run reinforces this, it does not soften
it.** That run (`results/new_illustrations/datapath_mux_alu_llama/`) also
showed `sem_adv PASS|4, semantic_fired=0`. Folded in as a fourth data point:
**3 of 4 total `sem_adv` samples passed, and the interpreter fired in zero of
the four.** A pass rate this consistent looks clean at a glance — that is
exactly why the `semantic_fired` check exists and why it must gate the
verdict ahead of the pass rate, not alongside it.

## Verdicts, stated plainly

| Candidate | Verdict | Deciding criterion |
|---|---|---|
| `instr_decode_unit` / gemma3:4b | **NOISY** | `sem_adv` never passes across the 3 samples (0/3) |
| `datapath_mux_alu` / llama3.1 | **MIXED** | Wins in some samples, controls win in others (2/3) — independently also disqualified by `semantic_fired=0` on every pass |

Neither is a promotion candidate. Neither requires user approval to not
promote — there is nothing here to approve. Retirement entries follow in
`illustrations/retired/retired_candidates.md`.

## What this round does establish

Not nothing. Two things survive the confound analysis:

1. **`instr_decode_unit`'s core mechanism is real when it fires** — sample 3
   shows a clean `UNUSEDSIGNAL`-on-`valid` conversion, textbook shape. The
   module's problem is a **separate, unrelated instability**
   (`syntax_error`/`give up` loops) that swamps the target defect often
   enough that the mechanism rarely gets a clean shot, and even a clean shot
   is not sufficient to guarantee a pass. This is a different failure mode
   from `seg7_blank`'s "correct mechanism, module too complex" — here the
   module is small (11 Yosys cells) and the instability looks like a
   degenerate generation mode, not scale.
2. **`datapath_mux_alu`'s `reg_wire_mismatch`-to-`logic_error` transition is a
   real, symmetric tool-presence effect** — both `raw_adv` and `sem_adv`
   reliably escape a defect `baseline` cannot, using nothing but raw
   Verilator/Yosys text. That is evidence for the value of running the tools
   at all, which is a real result and a different claim than the interpreter
   claim. It belongs in the `raw_adv` vs `baseline` comparison, not in any
   claim about interpretation.

Neither observation changes the retirement verdict above. Both are recorded
in the retirement entries so the reasoning survives, not just the outcome.
