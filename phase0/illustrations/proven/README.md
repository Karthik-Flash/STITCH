# `illustrations/proven/` — what "proven" requires

**Frozen evidence.** Both subdirectories carry their own `LOCKED.md` — do not
edit either. If you need a working copy, copy it out to a new location first.

## What "proven" means for this project

**3/3 pass under N=3 replication at `temperature=0.1`**, per the
reproducibility methodology in `../../plans/research_plan_v4.md` §2: same
verdict and iteration count across three independent samples per condition.
That methodology is explicit that this establishes **reproducibility, not a
variance bound** — at `temperature=0.1` the model's output distribution is
peaked enough that repeated draws mostly re-measure the same mode, so N=3
confirms the result is not a fluke of that one draw, not that the effect
holds across the full range of what the model might produce.

**A single-sample `PASS` does not qualify, no matter how clean it looks.**
This bar exists because it has already been tested and failed twice in phase
0: `datapath_mux_alu` and `instr_decode_unit` both showed a clean single-draw
`sem_adv PASS` in their first run, and both reversed under N=3 — one to
`MIXED` (the pass persisted, but the interpreter turned out to have never
fired), one to `NOISY` (the pass did not reproduce at all). Full account:
`../../evidence/phase0_illustration_hunt_findings.md`. Neither is here, both
are in `../retired/`.

Passing this bar is necessary but not the only thing that matters — the
result also has to be **attributable**: `semantic_fired ≥ 1` in every
`sem_adv` sample, on the intended warning code, and `raw_adv` distinguishing
itself from `baseline` in a way `sem_adv` improves on further. A pass rate
alone, however consistent, is not evidence for the interpreter if the
interpreter never fired — see the finding above.

## The two proven illustrations

**`decoder_3to8`** — a 3-to-8 one-hot decoder with an active-high `enable`
the spec never describes for the disabled case. gemma3:4b: `baseline` and
`raw_adv` both fail all 6 iterations, 3/3 samples; `sem_adv` passes on
iteration 2, 3/3 samples, after `UNUSEDSIGNAL` fires on the unused `enable`
port. No effect on llama3.1 — it self-corrects from testbench output alone
without ever triggering the warning. Detail: `decoder_3to8/README.md`.

**`mux4_oe`** — a 4-to-1 multiplexer with an active-high output enable, same
spec pattern. The cross-model illustration: on gemma3:4b it's the same
enabling result as `decoder_3to8` (`FAIL|6` / `FAIL|6` / `PASS|2`, 3/3); on
llama3.1 it's an efficiency result instead (`PASS|4` / `PASS|4` / `PASS|2`,
3/3) — the model reaches the correct answer under every condition, but the
interpreter's directive gets it there in half the iterations. Detail:
`mux4_oe/README.md`.

In every replicated cell across both modules, `raw_adv` tracks `baseline`
exactly — the control that isolates interpretation from tool presence. That
result does not generalize past the defect classes the interpreter covers;
see `../../evidence/phase0_illustration_hunt_findings.md` §2c for a
documented counterexample outside those classes.

## Boundary rule

Do not merge either module into `benchmarks/`, and do not count either in a
pass-rate percentage — both were designed specifically to trigger a known
mechanism, which is what an illustration is for, not a benchmark result.
