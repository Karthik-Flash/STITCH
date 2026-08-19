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
