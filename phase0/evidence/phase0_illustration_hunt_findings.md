# Phase 0 illustration hunt — consolidated findings

**2026-08-19.** Paper-ready consolidation of everything the phase-0
illustration hunt produced: what replicated, what didn't, and three secondary
findings worth citing in the paper's methodology or limitations section
regardless of the headline result. This is the summary document — detailed
data lives in the sources it cites, not copied here.

## §1 — What the hunt proved

**Two proven illustrations, replicated 3/3.** `decoder_3to8` and `mux4_oe`,
both gated-input `UNUSEDSIGNAL` targets, both N=3 replicated at
`temperature=0.1` per the reproducibility methodology in
`../plans/research_plan_v4.md` §2. Full evidence:
`../illustrations/proven/decoder_3to8/`, `../illustrations/proven/mux4_oe/`.
These remain the only citable positive results from this hunt.

**Two mechanism classes attempted — input-omission and output-omission.**
Input-omission (a forgotten gating *input*, `decoder_3to8`/`mux4_oe`'s class)
works. Output-omission (a forgotten *output*, `adder_with_overflow` /
`fsm_next_state_error`, targeting `UNDRIVEN`) does not: both candidates
passed a full four-gate tool-level pre-screen and then had the target output
assigned unprompted on iteration 1, in every condition, in both modules. The
mechanism is sound; the defect does not occur. Full write-up, data tables and
the hypothesised mechanism (local vs non-local completeness obligations):
`input_vs_output_asymmetry.md` — referenced here, not reproduced.

**Larger-module attempt — three candidates, zero replications.**
`datapath_mux_alu`, its redesign `alu_with_enable`, and `instr_decode_unit`
were built to answer a reviewer request: does the proven `UNUSEDSIGNAL`
mechanism still work when the containing module has real internal
mux/decoder structure, at a larger scale than `mux4_oe`? All three ran
against a real model; **none replicated.** All three are retired, with the
detailed data in `../illustrations/retired/retired_candidates.md` §1a–§1c
and `n3_replication_pass2.md`. Section §2 below extracts what is actually
worth keeping from that failure, beyond "it didn't work."

## §2 — Three secondary findings worth citing

None of these depend on the larger-module hunt succeeding. They are about
the *apparatus* — what the three-condition design can and cannot
disambiguate, and what the raw tool layer does on its own — and they hold
regardless of whether a third larger-module candidate is ever built.

### 2a — `sem_adv` can outperform `baseline` via resampling variance even when the interpreter is inert

**This is not a hypothetical risk. It happened in fresh data, predicted in
advance by the project's own methodology, and confirmed by direct
measurement.**

`datapath_mux_alu` / llama3.1, N=3: `sem_adv` passes 2 of 3 samples while
`baseline` and `raw_adv` fail all 3. Read as a table-summary number, that
looks like a STITCH win. `semantic_fired = 0` in **all three** `sem_adv`
samples, including both passes — the interpreter never fired once. Whatever
produced the pass came from something other than interpretation.

This is exactly the `confounded` category `phase_d_report.md` defined for a
different sweep, extended here with a mechanism: `sem_adv`'s prompt is
near-identical to `raw_adv`'s when no directive fires (differing only in
boilerplate section-header text, not information content), and at
`temperature=0.1` with no fixed seed, two independently-sampled generations
under near-identical prompts can and do diverge. Combined with the prior
single-sample run on the same candidate (also `PASS`, also
`semantic_fired=0`), that is **3 of 4 total `sem_adv` samples passing with
the interpreter firing in zero of the four** — a pass rate consistent enough
to look clean at a glance, which is exactly why `semantic_fired` has to gate
any pass-rate claim, not sit alongside it as a secondary statistic.

**Methodological consequence:** any three-condition comparison table must
report `semantic_fired` next to the pass/fail cell it explains, not in a
separate summary row. A `sem_adv` pass with `semantic_fired = 0` is not
evidence for the interpreter under any framing, no matter how many samples
show the same pattern — more samples of an unattributed effect is still an
unattributed effect, not stronger evidence.

Source: `n3_replication_pass2.md` Table B;
`../illustrations/retired/retired_candidates.md` §1a.

### 2b — A correct directive does not guarantee recovery once the model is in a degenerate state

`instr_decode_unit` / gemma3:4b, N=3 sample 3: the interpreter fired
`UNUSEDSIGNAL` on `valid` at iteration 3, cleanly and correctly — the target
defect in isolation, textbook shape, same mechanism as `decoder_3to8`. The
run still failed. Iteration 4 did not apply the fix; it regressed into a
degenerate syntax-error loop
(`instr_decode_unit.v:1: syntax error / I give up.`) — the same failure
pattern that ends the run outright in the other two samples, which never
reach a clean directive at all.

This is a **scope boundary on the interpreter's mechanism**, distinct from
the scope boundary already established in `session_2026-08-18_findings.md`
(a defect is reachable only if it leaves a static structural fingerprint) and
from `input_vs_output_asymmetry.md`'s refinement (reachable only if the
model actually produces the defect). Both of those are about whether the
interpreter gets a chance to fire. This finding is about what happens
*after* it fires: a correct, on-target directive is necessary but not
sufficient for recovery. If the model has entered an unrelated unstable
generation mode, the directive competes with that instability for influence
over the next token stream, and here it lost. The interpreter has no
vocabulary that reaches "the model is producing malformed output for reasons
unrelated to any warning code" — nothing in its seven-code vocabulary is
built to address it, nor could it be from tool output alone.

Source: `n3_replication_pass2.md` Table A;
`../illustrations/retired/retired_candidates.md` §1b.

### 2c — `raw_adv` reliably escapes `baseline`'s trap using only raw Verilator text

A finding about the **raw tool layer**, not about interpretation, and one the
project's existing framing did not previously distinguish from noise.

`datapath_mux_alu` / llama3.1, all 3 samples: `baseline` is stuck on
`reg_wire_mismatch` for all 6 iterations, every sample, no exception (the
`alu_result` wire/reg type error). `raw_adv` escapes it by iteration 3 in
**every** sample, landing on `logic_error` and never returning to
`reg_wire_mismatch`. That's Verilator's own compile-time diagnostic —
present in `raw_adv` and absent from `baseline` — doing real, reproducible
work, with no interpretation involved at all.

This matters for how the paper frames the `raw_adv` condition. `raw_adv` was
designed as the control that isolates "having the tools" from "interpreting
the tools," and in the two proven illustrations it tracks `baseline`
exactly — the result that licenses the interpreter's contribution claim. This
finding shows `raw_adv` is not always inert: on a defect class the
interpreter has no code for (`reg_wire_mismatch` is not in
`_VERILATOR_INTERP`), raw tool presence alone produces a measurable,
symmetric effect. It is symmetric because it explains why `raw_adv` **and**
`sem_adv` both beat `baseline` here (both escape the same trap the same
way) — it does not explain any `sem_adv`-over-`raw_adv` difference, which is
where 2a's confound lives instead. The two findings sit on either side of the
same data and should be cited together, not conflated: **raw tool presence
has a real, symmetric effect on defect classes outside the interpreter's
vocabulary; interpretation's effect is what's left after that is accounted
for.**

Source: `n3_replication_pass2.md` Table B, per-iteration sequences;
`../illustrations/retired/retired_candidates.md` §1a.

## §3 — Consequences for phase 1

**Phase 1's escalation architecture proceeds on the two proven illustrations
and the `v20` diagnostic benchmark**, per `../plans/research_plan_v4.md` §§3–4.
Nothing in this hunt changes that plan; it was scoped as a phase-0 side
investigation, not a phase-1 dependency, and it did not produce a third
proven illustration to add to the set.

**Larger-module illustrations remain an open direction, not a closed one —
but the recipe for finding one needs a methodological fix before another
attempt.** All three attempts in this hunt were promoted to "READY" and
run on the strength of a single draw, and two of the three single-sample
results (`instr_decode_unit`, `datapath_mux_alu`) looked clean enough at
n=1 to warrant a paper claim before N=3 replication reversed the verdict.
That is precisely the trap 2a names. **The fix: any candidate must clear a
pre-registered N≥3 evaluation before its result is used for anything —
promotion, citation, or a "READY" verdict in a pending/ README — not only
before promotion to `proven/`.** The four-gate tool-level pre-screen already
in place (`../illustrations/pending/README.md`) verifies the mechanism is
*capable* of firing; it says nothing about whether the model reaches a state
where it gets the chance, which is exactly the question N=3 answers and a
single draw cannot.

These three findings — 2a, 2b, 2c — are added to
`../plans/research_plan_v4.md` §5b as methodology notes, since they bear on
how any future benchmark or illustration comparison should be read, not only
on the specific candidates that produced them.

## Sources

- `input_vs_output_asymmetry.md` — input vs output omission, full data
- `n3_replication_pass2.md` — the two N=3 replication tables underlying §2a and §2b
- `phase_d_report.md` — origin of the `confounded` category referenced in §2a
- `../illustrations/retired/retired_candidates.md` §1a–§1c — full retirement
  records for the three larger-module candidates
- `../plans/research_plan_v4.md` §2 — the reproducibility methodology these
  N=3 runs follow
