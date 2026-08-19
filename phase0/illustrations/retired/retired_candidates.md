# Retired illustration candidates — the single register

Every candidate that was designed, probed or run and then dropped. One file on
purpose: the reasons are only useful together, because collectively they define
the design recipe.

Consolidated 2026-08-19 from `retired_candidates.md`,
`tool_level_verification_report.md` and `adder_with_overflow_v1_run.md`.
Nothing was discarded in the merge — the tool-level captures and the
`arbiter_two_writers` / MULTIDRIVEN analysis are preserved in §4 and §5.

**Read `../../evidence/input_vs_output_asymmetry.md` first.** It supersedes the
per-module reasoning for the two 2026-08-19 retirements in §1.

---

## Register

| Module | Target | Retired | Reason |
|---|---|---|---|
| `adder_with_overflow` | `UNDRIVEN` on output | 2026-08-19 | Forgotten-output class is unreachable — §1 |
| `fsm_next_state_error` | `UNDRIVEN` on output | 2026-08-19 | Forgotten-output class is unreachable — §1 |
| `datapath_mux_alu` | `UNUSEDSIGNAL` | 2026-08-19 | Too large for gemma3:4b's convergence horizon; llama3.1 N=3 confirms MIXED, not attributable — §1a |
| `instr_decode_unit` | `UNUSEDSIGNAL` | 2026-08-19 | Mechanism fires cleanly when reached, but gemma3:4b N=3 is NOISY — never passes in 3/3 samples — §1b |
| `alu_with_enable` | `UNUSEDSIGNAL` | 2026-08-19 | Too easy after the redesign; gemma3:4b PASS\|1 all conditions, `semantic_fired=0` — §1c |
| `counter_with_enable` | `UNUSEDSIGNAL` | 2026-08-18 | Spec stated the gate-off behaviour — §2 |
| `counter_with_enable_dir` | `UNUSEDSIGNAL` | 2026-08-18 | Same — §2 |
| `register_with_load` | `UNUSEDSIGNAL` | 2026-08-18 | Same — §2 |
| `cmp8_en` | `UNUSEDSIGNAL` | 2026-08-18 | Too easy; model used `en` correctly, PASS\|1 all conditions |
| `seg7_blank` | `UNUSEDSIGNAL` | 2026-08-18 | Mechanism fires, module too complex to converge — §2 |
| `mode_mux_latch` | Yosys latch | 2026-08-18 | System prompt rule 3 pre-empts the bug — §3 |
| `priority_chain_comb` | Comb loop | 2026-08-18 | Model's actual defect was a logic error, not a structural one — §3 |
| `arbiter_two_writers` | `MULTIDRIVEN` | 2026-08-17 | Two designs, neither triggers MULTIDRIVEN — §5 |
| `traffic_light_fsm` | Yosys latch | 2026-08-17 | Failed the tool-level mechanism check before any run — §6 |
| `shift_reg_with_enable` | `UNUSEDSIGNAL` | 2026-08-18 | Never built; superseded — §6 |

Still live: `../pending/priority_encoder_valid/` (path-completeness class,
distinct from everything above).

---

## §1 — The forgotten-output retirements (2026-08-19)

`adder_with_overflow` and `fsm_next_state_error` both retire for **one shared
reason, not two individual quirks**: the defect class they target does not
occur.

Both passed a full four-gate pre-screen against real Verilator 5.020 / Yosys
0.33 / Icarus 12.0 before running. The warning fires, the interpreter takes the
`output_port` branch and names the right signal, the prescribed repair applies,
and the oracle isolates the defect. The mechanism is sound. The model simply
never produces the defect: it assigned the target output unprompted on
iteration 1, in every condition, in both modules.

| Module | Target port | Iteration-1 behaviour | Result |
|---|---|---|---|
| `adder_with_overflow` | `overflow` | `overflow = carry;` | `semantic_fired = 0` in all three conditions |
| `fsm_next_state_error` | `error` | `error <= 0;` on **all three branches** | PASS\|1 in all three conditions, 521 tokens total |

Against the two proven illustrations, which target a forgotten **input**, the
split is 2-for-2 in both directions. Full data, the hypothesised mechanism and
the refined scope claim are in `../../evidence/input_vs_output_asymmetry.md`.
Do not re-derive them here and do not build a third forgotten-output variant.

Notably, `fsm_next_state_error` was built so that `SYSTEM_PROMPT` rule 3 could
not reach it — rule 3 is scoped to combinational always blocks and the module
is clocked. The model assigned `error` anyway, so unlike `mode_mux_latch` (§3)
this is the model's own prior, not the apparatus.

### Subsidiary note — why `adder_with_overflow` baseline showed FAIL|6

Worth recording because the number is misleading in isolation, and **it is not
evidence for STITCH**.

Iteration 1 reached for a temporary it never declared:

```verilog
{carry, sum} = a + b;
overflow = carry;      // 'carry' declared nowhere
```

Under `baseline`, the model tried to fix this by declaring the variable inside
the unnamed always block —

```verilog
always @(*) begin
  reg [7:0] carry;     // Verilog-2001 cannot do this
```

— which iverilog rejects as `Variable declaration in unnamed block requires
SystemVerilog`. It then repeated that identical error for five straight
iterations, through two rewrite injections. That is an **incidental defect,
unrelated to the target**, and it is the entire content of the FAIL|6.

Two things follow:

1. **This is the first observed cell where `raw_adv` != `baseline`.** Verilator
   emitted `%Error: Can't find definition of variable: 'carry'` — an `%Error`,
   not one of the seven interpreted codes, so the interpreter correctly
   produced nothing. The raw text alone was enough: `raw_adv` and `sem_adv`
   both repaired to `{overflow, sum} = a + b;` on iteration 2 and passed. The
   claim *"`raw_adv` == `baseline` in every cell"* must therefore be scoped to
   the proven illustration set, not stated universally.
2. **Table trap.** The printed `dB->S` column reads `+4` (baseline 6 minus
   sem_adv 2). Read alone that looks like a win. The honest interpretation
   delta is `raw_adv - sem_adv = 0`. Never quote `dB->S` without the `raw_adv`
   column beside it.

`sem_adv` and `raw_adv` are identical here (PASS|2 both, `semantic_fired = 0`),
so interpretation contributed exactly nothing either way.

### §1a — `datapath_mux_alu`: too large for the model, not for the tools

Reviewer-requested illustration: a larger module (case-based ALU feeding a
mode mux feeding an enable gate, 145 Yosys cells) demonstrating the proven
`UNUSEDSIGNAL` mechanism still holds when the containing module has real
internal structure. All four pre-screen gates passed. Run against gemma3:4b,
all three conditions, real evidence at
`results/new_illustrations/datapath_mux_alu/` (gitignored, not in this repo's
git history).

**The mechanism fired. The model never got far enough to benefit.** From
`sem_adv/datapath_mux_alu/metrics.json`:

```
semantic_fired: 5
verilator_codes_seen: ['UNUSEDSIGNAL', 'WIDTHEXPAND', 'UNUSEDSIGNAL', 'UNUSEDSIGNAL', 'UNUSEDSIGNAL']
per-iteration err_type: reg_wire_mismatch, syntax_error, reg_wire_mismatch,
                        reg_wire_mismatch, logic_error, syntax_error
```

`UNUSEDSIGNAL` on `enable` fired correctly and repeatedly — the interpreter
did its job every time it had a chance. But four of six iterations failed on
`reg_wire_mismatch` or `syntax_error`: basic compile-level defects in the
model's handling of internal signals, unrelated to the enable gate. `baseline`
and `raw_adv` show the same pattern (`reg_wire_mismatch`/`syntax_error`
dominant, `semantic_fired = 0` since neither has the interpreter). None of the
three conditions ever reached a state where the target defect was the only
thing wrong, so none passed.

**Retired for module size, not mechanism failure.** 145 cells and six
declared ports (against `mux4_oe`'s 60 cells, five ports) exceeded
gemma3:4b's convergence horizon within 6 iterations — the same failure shape
as retired `seg7_blank` (§2), one level up in scale. Consistent with the
recipe's "keep it small" condition, which this candidate deliberately relaxed
at the reviewer's request and which turned out to still bind.

Superseded by `../pending/alu_with_enable/` — same top-level mechanism
(`UNUSEDSIGNAL` on `enable`), ALU only, mode mux and bypass path dropped.
Files preserved at `datapath_mux_alu/` in this directory for provenance.

**Update 2026-08-19, same day — llama3.1 cross-model check, N=3: MIXED,
confirms the module was not attributable evidence either way.** The retired
`BENCHMARK` entry was temporarily restored (marked explicitly as a
single-purpose re-registration, not a promotion) to ask a narrower question:
does a stronger model converge on the same module gemma3:4b could not?
Three independent samples, gemma3:4b's original spec unchanged, llama3.1
instead of gemma3:4b:

| Sample | Baseline | Raw_adv | Sem_adv | `semantic_fired` |
|---|---|---|---|---|
| 1 | FAIL\|6 | FAIL\|6 | FAIL\|6 | 0 |
| 2 | FAIL\|6 | FAIL\|6 | **PASS\|4** | 0 |
| 3 | FAIL\|6 | FAIL\|6 | **PASS\|4** | 0 |

`sem_adv` passes 2/3 — llama3.1 CAN converge on this module where gemma3:4b
never did in 6 tries in any of its own runs, so "too large for the tools" is
ruled out; it was specifically too large for gemma3:4b. But
**`semantic_fired=0` in all three samples, including both passes** — the
interpreter never fired once. Sem_adv passed without the interpreter firing.
This is raw_adv/sem_adv divergence via resampling variance, not evidence for
the STITCH mechanism. Reinforces the confound category defined in
`../../evidence/phase_d_report.md`. Combined with the single-sample run from
the previous round (also `PASS|4`, `semantic_fired=0`), that is 3 of 4 total
`sem_adv` samples passing with the interpreter firing in zero of the four.

One real, reproducible, non-interpreter effect: `baseline` is stuck on
`reg_wire_mismatch` for all 6 iterations in all 3 samples; `raw_adv` escapes
it by iteration 3 in every sample via Verilator's raw diagnostic alone.
`sem_adv` needs one more unproductive iteration on `reg_wire_mismatch` in 2
of 3 samples before jumping straight to `PASS`, skipping the `logic_error`
stage `raw_adv` always passes through — a different resampled path under a
near-identical prompt, not a directive effect. Full per-iteration sequences
and analysis: `../../evidence/n3_replication_pass2.md`.

`BENCHMARK` entry re-commented out after this check, per the note left with
it when it was restored. Not re-promoted; not moved out of `retired/`.

---

### §1b — `instr_decode_unit`: mechanism fires cleanly, module does not converge reliably

Real gemma3:4b run, all three conditions, N=3 replication after a single-
sample `sem_adv PASS|4` in the previous round.

| Sample | Baseline | Raw_adv | Sem_adv | `semantic_fired` |
|---|---|---|---|---|
| 1 | FAIL\|6 | FAIL\|6 | FAIL\|6 | 0 |
| 2 | FAIL\|6 | FAIL\|6 | FAIL\|6 | 0 |
| 3 | FAIL\|6 | FAIL\|6 | FAIL\|6 | **1**, `UNUSEDSIGNAL` |

**Verdict: NOISY.** `sem_adv` never passes across the 3 samples — 0/3, the
decisive criterion on its own. Folded in with the previous round's single
sample (`PASS|4`, `semantic_fired=1`): 1 pass out of 4 total `sem_adv`
samples collected.

**The mechanism itself is not the problem.** Sample 3's per-iteration
sequence is `SYNT, SYNT, LGIC, SYNT, SYNT, SYNT`. Iteration 3 is exactly the
target-defect-only state — `logic_error`, five `FAIL` lines all naming
`valid`-gated control signals, nothing else wrong — and the interpreter
converted it correctly: `UNUSEDSIGNAL` on `valid`, the same clean shape as
`decoder_3to8` and `mux4_oe`. The run still failed. Iteration 4 regressed
into a degenerate syntax failure
(`instr_decode_unit.v:1: syntax error \n I give up.`) instead of applying the
fix — the same failure mode that ends samples 1 and 2 outright. A correct
directive does not guarantee recovery once the model has entered this state,
and the interpreter has no vocabulary that reaches it.

`baseline` and `raw_adv` are stuck on `syntax_error` for all 6 iterations, in
every one of the 3 samples, with zero exceptions across 18 iterations each —
this module is not reliably reaching a state where any condition's feedback
can help, gemma3:4b or otherwise, within this benchmark's 6-iteration budget.
Full per-iteration data: `../../evidence/n3_replication_pass2.md`.

Distinct from `seg7_blank`'s retirement reason (§2): that module is too
*complex* for convergence at its scale. `instr_decode_unit` is small (11
Yosys cells) and the blocking failure is a degenerate generation instability,
not scale.

---

### §1c — `alu_with_enable`: too easy after the redesign

Real run, both models, single sample each — no N=3 needed, same bar as
`cmp8_en`'s original retirement: a `PASS|1` with `semantic_fired=0`
unambiguously shows the target defect did not occur, which is a design-gate
failure, not a statistical question.

| Model | Baseline | Raw_adv | Sem_adv | `semantic_fired` |
|---|---|---|---|---|
| gemma3:4b | PASS\|1 | PASS\|1 | PASS\|1 | 0 |
| llama3.1 | PASS\|2 | PASS\|2 | PASS\|2 | 1 (no efficiency gain) |

`alu_with_enable` was built specifically to fix `datapath_mux_alu`'s
convergence failure (§1a) by dropping the mode mux, the `bypass` port, and
the internal `alu_result` register — four ports instead of six, zero internal
registers. The fix over-corrected: on gemma3:4b the module became simple
enough that the `enable` gate was written correctly on the very first
iteration, in every condition. On llama3.1 all three conditions converge in
the same 2 iterations — `sem_adv` fires `UNUSEDSIGNAL` but produces no
efficiency gain, the same "no effect" pattern `decoder_3to8` showed on
llama3.1.

This is the third and last attempt at a larger-module illustration in phase
0 (`datapath_mux_alu` → `alu_with_enable`, plus the separate
`instr_decode_unit` line, §1b). None replicated. See
`../../evidence/phase0_illustration_hunt_findings.md` §3 for what this means
for the larger-module direction going forward.

---

## §2 — The recipe, learned from the 2026-08-18 retirements

Three conditions, all required. Each retirement below failed exactly one.

| # | Condition | Failed by |
|---|---|---|
| 1 | Spec describes **only** the gate-asserted behaviour; never states what happens when the gate is off | `counter_with_enable`, `counter_with_enable_dir`, `register_with_load` — all spelled out "if X is low, hold", handing over the answer |
| 2 | Target a **forgotten port**, not a missing case `default` | `mode_mux_latch` — see §3 |
| 3 | Module must be **small** — no independent error surface beyond the target bug | `seg7_blank` — fires `UNUSEDSIGNAL` correctly but ten 7-bit segment patterns introduce unrelated errors it never converges past |

`cmp8_en` failed none of these on paper and was still too easy: gemma3:4b used
`en` correctly on iteration 1, PASS|1 on all three conditions. Its ports were
also originally written as `input [7:0] a, b`, which made the model drop `b`
from the header entirely — a spec-ambiguity artifact, since fixed, worth
remembering when writing port lists.

As of 2026-08-19 add a fourth condition, from §1: **target a forgotten input,
not a forgotten output.**

---

## §3 — The system prompt is experimental apparatus

**`mode_mux_latch`.** `SYSTEM_PROMPT` rule 3 mandates "EVERY combinational
always block MUST have a `default` branch". The module was designed around a
missing `default`, so the prompt pre-empts the bug before any tool runs.
Confirmed across three separate sweeps: gemma3:4b emits `default: out = 0;`
verbatim and passes on iteration 1. The module can never produce signal either
for or against the interpreter.

**`priority_chain_comb`.** Retired for a different reason: the defect gemma3:4b
actually wrote was a **wrong priority order** — clean syntax, sound structure,
wrong values. No static analysis has anything to say about it. llama3.1 passes
the module outright on iteration 1. This is the cleanest negative in the set
and it is what the original scope boundary was built from.

Corollary: any defect class the system prompt explicitly warns against cannot
demonstrate the interpreter. Check `SYSTEM_PROMPT` at
`src/runner/stitch_runner.py:92-113` before designing any target.

---

## §4 — Tool-level verification captures (2026-08-17)

From the superseded `tool_level_verification_report.md`. Its *verdicts* were
wrong — it called `mode_mux_latch` and `priority_chain_comb` "viable, needs LLM
run" and both were retired after real runs — but its captures against real
Verilator 5.020 / Yosys 0.33 are accurate and are recorded nowhere else.

**`mode_mux_latch`.** Verilator's code for this bug is `CASEINCOMPLETE`, which
is **not** in `_VERILATOR_INTERP` and contributes nothing. Yosys genuinely
fires, with **no `Warning:` prefix**:

```
Latch inferred for signal `\mode_mux_latch.\out' from process `\mode_mux_latch.$proc$broken.v:9$1': $auto$proc_dlatch.cc:427:proc_dlatch$29
```

This is the exact case the 2026-08-17 regex fix was for. Latch inference is
therefore a **Yosys-only** class end to end.

**`priority_chain_comb`.** Verilator's code is `UNOPTFLAT`, also not in
`_VERILATOR_INTERP`. Yosys fires 6 loop-chain reports:

```
Warning: found logic loop in module priority_chain_comb:
    cell $and$broken.v:15$4 ($and)
```

Combinational loops are likewise Yosys-only. Before this round there was no
interpreter code for the class at all.

**Methodology, retained as the standard:** real tools via WSL, using both a
direct lint/synth invocation and the pipeline's exact invocation, with the
interpreter run against the captured text rather than a hand-written guess.
That discipline is what caught `traffic_light_fsm` (§6) for free.

---

## §5 — `arbiter_two_writers` and the MULTIDRIVEN gap

`MULTIDRIVEN` is in `_VERILATOR_INTERP` and **has never fired against real
model output**. Two designs were tried; neither produces it.

**Design 1** — identical clocking on both driving blocks. Verilator does not
flag it at all.

**Design 2** — clocked block plus a combinational override block, the canonical
pattern. `verilator --lint-only broken.v | grep MULTIDRIVEN` gives **no match**.
Real output:

```
%Warning-LATCH: broken.v:26:5: Latch inferred for signal 'grant0' (not all control paths of combinational always assign a value)
%Error-BLKANDNBLK: broken.v:10:17: Unsupported: Blocked and non-blocking assignments to same variable: 'grant0'
%Error: Exiting due to 1 error(s), 1 warning(s)
```

Mixing blocking `=` and non-blocking `<=` on the same reg is an **unsupported
hard error** (`BLKANDNBLK`) that aborts lint before `MULTIDRIVEN` is reached.
`BLKANDNBLK` is not in `_VERILATOR_INTERP` either, so nothing converts.

A genuine unrelated finding from design 2, worth keeping: the override block
`always @(*) if (preempt) grant0 = 1'b0;` is itself a real incomplete
combinational assignment, and Yosys correctly reports a latch on `grant0`.
`detect_yosys_latches()` catches it as a **true positive**. But that makes the
module a second latch example wearing an arbiter's name, not a MULTIDRIVEN
illustration.

**Two directions remain open** (plan v4 §7 #4):

1. A clock-edge mismatch — `always @(posedge clk)` and `always @(negedge clk)`
   both driving the same reg. Genuinely different clocking, which is what
   Verilator's check appears to require. **Not yet tried, and the most
   promising.**
2. Accept the module as a second latch illustration under a different framing
   and let MULTIDRIVEN stay unverified, recorded honestly in
   `../../src/interpreter/WARNING_TAXONOMY.md`.

---

## §6 — Candidates dropped before they were built

**`traffic_light_fsm`** — intended target was a latch on `next_state` from a
missing `case` default. **Failed the mechanism check, empirically, before any
LLM run.** Verilator gives `CASEINCOMPLETE` (not handled), and Yosys reports
**no genuine latch line at all** — only the `PROC_DLATCH` pass banner, which is
a known non-positive.

The reason is instructive: `state <= ...` sits inside a *clocked* always block,
so `state` is assigned on every clock edge regardless of which branch executes.
That is a flip-flop, and Yosys correctly declines to infer a latch. A missing
`default` in a *registered* case is functionally harmless, unlike
`mode_mux_latch`'s combinational case.

To revive it, the redesign is to split a registered `state` from a separately
computed combinational `next_state` in an **unclocked** `always @(*) case(state)`
with no default — reproducing `mode_mux_latch`'s mechanism on FSM-shaped logic
rather than copying its surface pattern. But `mode_mux_latch` is itself retired
under §3, so this is low value unless the system prompt changes.

**`shift_reg_with_enable`** — structurally near-identical to
`counter_with_enable`: same gating-signal omission, same warning code. Never
built. `counter_with_enable` retired under recipe rule 1, and a shift register
would have been a fourth variation on the same theme; §1 now retires the whole
forgotten-output direction and recipe rule 1 covers this one.

---

## Boundary rule

Nothing here may be copied into `benchmarks/`, and nothing here may be counted
in a pass-rate percentage. Promotion to `../proven/` requires a real LLM run
producing a genuine before/after flip with on-disk evidence — the standard
`../proven/decoder_3to8/` meets.
