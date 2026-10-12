# STITCHAdv Research Plan v4 — Pre-Phase-1 Consolidation

**Status:** current. Consolidates every decision taken after Plan v3, up to the
start of Phase 1.

---

## §0. Supersession

v4 supersedes **Plan v2** (`research_plan_v2.md`) and **Plan v3**
(`research_plan_v3.md`).

Both prior plans remain on disk and **must not be deleted** — they are the
record of how the current position was reached, and v4 cross-references v2
directly for the escalation spec (§4). Each now carries a one-line supersession
note at its top pointing here.

Where v4 and a prior plan disagree, v4 governs. Where v4 is silent, the prior
plan still applies.

---

## §1. State of evidence at end of pre-Phase-1 work

### Interpreter

`src/interpreter/stitch_interpreter.py` is the single source of truth for all
warning classification and directive generation.

- **39 unit tests passing.** Note: an earlier draft of this consolidation cited
  31. That was the count *before* the UNUSEDSIGNAL parameterisation work
  landed; that work added 8 further tests. 39 is the correct current figure,
  and is what `CHANGELOG.md` records.
- **Five defects found and fixed.** Full detail, including how each was found
  and the dependency chain between them, is in
  `phase0/evidence/session_2026-08-18_findings.md`. Summary:
  1. Latch-keyword substring matching false-positived on the Yosys pass banner
     and on the negated "No latch inferred" message.
  2. The latch regex required a `Warning:` prefix Yosys 0.33 does not emit for
     latch inference, dropping genuine positives.
  3. Yosys was invoked with an unquoted path containing spaces — it had never
     executed successfully in this project.
  4. The combinational-loop handler existed but was never called by the runner.
  5. The literal-fragment guard silently discarded real signal names (`oe`,
     `bcd`, `be`, `de`, `da`, `dead`), killing their directives before they
     reached the model.
- **UNUSEDSIGNAL template parameterised.** The directive now extracts the
  module's real output port name(s) and width(s) rather than hard-coding
  `out = 8'b0`. A fallback path covers parameterised widths and unparseable
  headers. **The fallback must be monitored** — see `src/interpreter/README.md`
  §Monitoring, and §7 below.

### Runner

- `src/runner/stitch_runner.py` is the **canonical runner**.
- `AutoChipAdvFB/autochip_stitch_runner.py` and `HPC/stitch_runner_hpc.py` are
  **retired**: entrypoints removed, retirement headers applied, kept on disk
  for provenance only.

### Illustrations

**Two proven end-to-end**, replicated 3/3 at `temperature=0.1`
(`phase0/results/proven_illustrations/n3_replication/`, with the `sem_adv`
condition re-verified against the post-parameterisation interpreter in
`phase0/results/proven_illustrations/n3_replication_post_parameterisation/`):

| Module | gemma3:4b | llama3.1 | Regime |
|---|---|---|---|
| `decoder_3to8` | FAIL\|6 / FAIL\|6 / **PASS\|2** | PASS\|2 / PASS\|2 / PASS\|2 | Enabling on gemma3:4b; **no effect** on llama3.1 |
| `mux4_oe` | FAIL\|6 / FAIL\|6 / **PASS\|2** | PASS\|4 / PASS\|4 / **PASS\|2** | Enabling on gemma3:4b; efficiency on llama3.1 |

`mux4_oe` is the stronger cross-model illustration: it produces the
forgotten-port defect in *both* models. `decoder_3to8` produces it only in
gemma3:4b — llama3.1 writes `if (enable)` and omits only the `else`, a
different defect class it self-corrects from testbench output alone.

**Five retired illustrations**, documented in
`phase0/illustrations/retired/retired_candidates.md` and in the findings doc's
module-status table: `priority_chain_comb`, `mode_mux_latch`,
`counter_with_enable`, `register_with_load`, `seg7_blank`. Each failed a design
or empirical gate; the reasons are recorded because they define the recipe in
§5.

### Open illustration gap — MULTIDRIVEN

The interpreter carries a `MULTIDRIVEN` handler, but **no module has been
designed that triggers it cleanly**. Two attempts on `arbiter_two_writers` both
failed: identical clocking on both drivers produced no Verilator warning at
all, and a clocked/combinational mix produced `%Error-BLKANDNBLK` (a hard error
that aborts lint) plus a `LATCH` warning instead. `MULTIDRIVEN` is therefore an
**unverified handler** — it has never fired against real model output. Carried
into §7.

---

## §2. Variance methodology

**Replaces the assumption in Plan v2 §1.2.**

### What was verified

The working assumption had been that repeated runs at `temperature=0.1` sample
the outcome distribution. Checked empirically across the 12 replication cells:

- Iteration-1 generated Verilog was **byte-identical across all three samples
  in 6 of 12 cells**.
- Where output varied (2–3 distinct variants), **verdict and iteration count
  were identical in every case**.

At `temperature=0.1` the distribution is peaked enough that repeated runs
mostly re-measure the same mode. Repetition at this temperature therefore
establishes **reproducibility**, not variance.

### Decision

**Phase 1 primary runs: `temperature=0.1`, N=1 per cell**, framed explicitly in
the write-up as a *reproducibility* study, not a variance study. This preserves
direct comparability with the MLCAD paper's methodology, which used the same
setting.

**Appendix side-study: `temperature=0.8`, N=5 per cell, 3-module subset**, to
establish an empirical variance bound for reviewer defence. Its purpose is to
*bound the variance question*, not to change any headline number. Headline
results come from the primary runs.

Subset composition — one module per regime:

| Regime | Candidate | Source |
|---|---|---|
| Enabling | `decoder_3to8` or `mux4_oe` | §1 above |
| Harmful | `sync_fifo_8` / llama3.1 | `phase0/evidence/phase_d_report.md` — the one `clean_definitional_fix` that started in the harmful bucket |
| Irrelevant | any logic-class failure | e.g. `priority_chain_comb` / gemma3:4b — wrong priority order, no EDA-visible signal |

---

## §3. Benchmark strategy

### Primary target for Phase 1 — VerilogEval

**VerilogEval-Human is the likely primary benchmark for the journal
extension.** The following are **deferred to the Phase 1 kickoff session** and
must be settled there before any sweep runs:

- Which split — Human vs Machine.
- Pass@k threshold.
- Full 156 problems vs a subset.
- Whether the runner needs a new **adapter layer** to interface with
  VerilogEval's harness, or whether its problems can be mapped onto the
  existing spec/testbench convention.

All four are carried into §7.

### v20 — fallback and diagnostic role, not retired

v20 **remains on disk as a diagnostic set**. Use it when:

- VerilogEval does not answer a specific research question, or
- the escalation-vs-unconditional comparison requires the original comparison
  anchor from the MLCAD paper's data.

**On v20's design intent, stated plainly to prevent later misreading:** v20 was
built to expose AutoChip's failure modes for the MLCAD critique. That original
role is preserved and unchanged. It was never designed as a general-purpose
repair benchmark, and its modest aggregate figure reflects that design intent
rather than a capability ceiling. Do not present v20 aggregates as though they
were general repair-rate claims.

---

## §4. Escalation architecture

**Unchanged from Plan v2.** `research_plan_v2.md` §1.1 through §1.4
remains the authoritative specification — implementation, the resampling
handling (as amended by §2 above), the claims the phase can support, and the
gate.

Deliberately not restated here: a second copy would drift.

---

## §5. Methodology note — the system prompt is experimental apparatus

Any defect the system prompt explicitly warns against is repaired **before any
tool fires**, and therefore cannot demonstrate the interpreter.

**Confirmed empirically on `mode_mux_latch`.** `SYSTEM_PROMPT` rule 3 mandates
a `default` branch in every combinational always block. The model emits
`default: out = 0;` on iteration 1 and passes — across three separate sweeps.
The module was designed around a missing `default`, so it can never produce
signal either for or against the interpreter.

The effective set of defect classes the interpreter can demonstrate is
therefore **constrained by what the system prompt does not already cover**.

### Implication for benchmark and illustration selection

Target defect classes the prompt does **not** pre-empt:

- **Forgotten modal ports** (`UNUSEDSIGNAL`) — no prompt rule says "use every
  port you declared". This is the mechanism behind both proven illustrations.
- Latch inference in constructs the prompt does not warn against.
- Combinational loops.
- Multi-driver conflicts.

Modules whose primary defect is one the prompt covers will pass on iteration 1
and produce no signal in either direction. **Before adopting any benchmark
module or designing any illustration, check it against the current
`SYSTEM_PROMPT`.**

---

## §5b. Methodology notes from the phase-0 larger-module hunt (2026-08-19)

Three findings from N=3 replication on two larger-module candidates
(`datapath_mux_alu`/llama3.1, `instr_decode_unit`/gemma3:4b — both
subsequently retired, see `phase0/illustrations/retired/retired_candidates.md`
§§1a–1b). Full data and reasoning:
`phase0/evidence/phase0_illustration_hunt_findings.md` §2. Kept here as the
methodology notes a future comparison table needs, independent of whether
either candidate is ever revisited.

**5b.1 — `sem_adv` can beat `baseline` via resampling variance with the
interpreter completely inert.** `datapath_mux_alu`/llama3.1: `sem_adv`
passed 2 of 3 samples, `semantic_fired = 0` in all three, including both
passes. Combined with the single-sample run before it, 3 of 4 total
`sem_adv` passes on this candidate carried zero interpreter involvement.
**Any three-condition table must report `semantic_fired` next to the cell it
explains — a pass rate alone, however consistent across samples, is not
evidence for the interpreter if `semantic_fired` is 0.**

**5b.2 — A correct directive does not guarantee recovery once the model is
in a degenerate generation state.** `instr_decode_unit`/gemma3:4b sample 3:
`UNUSEDSIGNAL` fired cleanly and correctly on `valid` at iteration 3, and the
run still failed — iteration 4 regressed into a syntax-error loop instead of
applying the fix. This is a scope boundary distinct from the two already on
record (§5 above; `phase0/evidence/input_vs_output_asymmetry.md` §4): those are about whether
the interpreter gets a chance to fire, this is about what happens after it
fires. A correct directive is necessary but not sufficient for recovery.

**5b.3 — `raw_adv` is not always inert relative to `baseline`.** On
`datapath_mux_alu`/llama3.1, `baseline` was stuck on `reg_wire_mismatch` for
all 6 iterations in all 3 samples; `raw_adv` escaped it by iteration 3 in
every sample using nothing but raw Verilator text — a defect class outside
the interpreter's vocabulary entirely. This is a real, symmetric,
reproducible tool-presence effect (it explains `raw_adv` and `sem_adv` both
beating `baseline`, not any `sem_adv`-over-`raw_adv` gap) and should be cited
alongside, not conflated with, 5b.1's confound. The two proven illustrations'
clean `raw_adv == baseline` result is not universal; it holds for the defect
classes the interpreter covers and may not hold outside them.

**Consequence for future illustration work:** the four-gate tool-level
pre-screen (`phase0/illustrations/pending/README.md`) verifies the mechanism is
*capable* of firing. It does not verify the model reaches a state where it
gets the chance. **Any candidate must clear a pre-registered N≥3 evaluation
before its result is used for anything** — a "READY" verdict, a citation, or
a promotion — not only before promotion to `proven/`. All three larger-module
candidates in this hunt were run and reported on the strength of a single
draw; two of the three looked clean enough at n=1 to be reported as
provisional successes before N=3 reversed the verdict.

---

## §6. Downstream directions

Queued **after** Phase 1, not concurrent with it. Priority order:

**6.1 — RTL-specific models.** RTLCoder-DeepSeek-v1.1, CodeV-R1-Qwen-7B,
CodeV-CL-7B, per Plan v3 §A. Runs against whichever benchmark Phase 1 settles
on in §3.

**6.2 — Frontier models.** claude-sonnet-5, gemini-3.1-pro, kimi-k3, per Plan
v3 §B. Deliverable: the escalation-rate scaling figure.

**6.3 — MAGE integration or comparison.** Treat as a **separate paper or a
late-stage Phase 4** — not concurrent with Phase 1.

**6.4 — OpenROAD / PPA.** **Separate paper. Explicitly out of scope** for this
extension.

---

## §7. Open questions for the Phase 1 kickoff

| # | Question | Ref |
|---|---|---|
| 1 | VerilogEval-Human split (Human vs Machine), and subset vs full 156 | §3 |
| 2 | VerilogEval adapter design — new layer, or map onto the existing spec/testbench convention | §3 |
| 3 | Pass@k threshold | §3 |
| 4 | MULTIDRIVEN illustration gap — handler exists, has never fired against real model output | §1 |
| 5 | Fallback-rate monitoring threshold for the UNUSEDSIGNAL parameteriser | `src/interpreter/README.md` §Monitoring |
| 6 | **Prerequisite for #5:** the runner does not configure logging, so the fallback log emits nothing at INFO level. Monitoring cannot operate until this is addressed. | `src/interpreter/README.md` §Monitoring |
| 7 | ~~`interpret_yosys_latches` emits inapplicable `EXACT FIX` options and a fabricated `enable`-based causal join.~~ **RESOLVED 2026-08-19.** The directive is now structure-aware: it parses the module's case/if structure and emits only the options that apply, including the previously-missing "assign the signal in every branch, not only the default". The fabricated causal join is replaced by one derived from the defect. 11 new tests, built on real captured Yosys output from `priority_encoder_valid/broken.v`. | `phase0/illustrations/pending/priority_encoder_valid/README.md` |
