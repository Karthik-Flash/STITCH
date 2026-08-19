# `fsm_next_state_error` — pending candidate (UNDRIVEN on sequential logic)

**Status 2026-08-19: pre-screened 4/4, READY for an LLM run.**

## Why this candidate exists

Same interpreter path as `adder_with_overflow` (`UNDRIVEN` → `output_port`),
but on **sequential** logic, which matters for one specific reason:
`SYSTEM_PROMPT` rule 3 is explicitly scoped to *combinational* always blocks
and therefore cannot reach a clocked FSM at all. Gate 3 is not a near-miss
here, it is a clean miss.

It also follows `decoder_3to8`'s recipe shape more closely than the adder does:
the spec describes the state transitions completely and names `error` in the
port list and nowhere else.

## Target mechanism

| | |
|---|---|
| Defect | `error` declared in the port list, never assigned |
| Tool | Verilator, `%Warning-UNDRIVEN: Signal is not driven: 'error'` |
| Interpreter path | `interpret_verilator` → `_undriven_message` → `output_port` branch |
| Oracle | `error` reads `x` on every vector while `state` stays correct |

Yosys sees no latch — the block is clocked — so Verilator is the sole
interpreted source.

## Spec sent to the LLM

```
Write a Verilog-2001 module named fsm_next_state_error with:
input clk, input rst, input go,
output reg state, output reg error.
On posedge clk, if rst then state resets to 0. Otherwise if go
is asserted, transition state to 1; if go is deasserted, transition
state back to 0. Return only Verilog code.
```

Already applied to `BENCHMARK` in `src/runner/stitch_runner.py`.

## On the `error` expectation — why the oracle is fair

The spec never defines when `error` should assert. The testbench therefore
never exercises an error condition and requires only that `error` reads `1'b0`
throughout legal operation. A model that assigns `error` at all passes; a model
that leaves it undriven reads `x` and fails. No vector asks the model to guess
undefined semantics.

## Pre-screen — all four gates, 2026-08-19

Real Verilator 5.020 / Yosys 0.33 / Icarus 12.0 via WSL, through the production
wrappers.

### Gate 1 — target warning fires: **PASS** (after fixing a trap, below)
```
%Warning-UNDRIVEN: broken.v:15:16: Signal is not driven: 'error'
%Error: Exiting due to 1 warning(s)
```
`correct.v` lints clean.

### Gate 2 — interpreter converts it: **PASS**
```
codes_fired = ['UNDRIVEN']
*** CRITICAL: Output 'error' is declared but never assigned. ***
Add an assignment: 'error = <value>;' in your always block or use assign.
```
The `output_port` branch, naming the real signal, prescribing an applicable
repair. `correct.v` yields no directive.

### Gate 3 — `SYSTEM_PROMPT` does not pre-empt it: **PASS, cleanly**
Rule 3 mandates a `default` branch and an `else` branch in **combinational**
always blocks. This module's logic is `always @(posedge clk)`, so rule 3 does
not apply at all — unlike `adder_with_overflow`, where it had to be argued as a
near-miss. Rule 2 (non-blocking in clocked blocks) is satisfied by both
reference implementations and is orthogonal to the defect. No rule requires
assigning every declared output.

### Gate 4 — oracle catches it: **PASS**

| | Result |
|---|---|
| `correct.v` + tb | `ALL TESTS PASSED` |
| `broken.v` + tb | `FAIL: 10 test(s) failed` |

All 10 FAIL lines are `error` checks. `state` is correct on every vector
including both resets, so the failure set isolates the target defect.

## Trap found during gate 1 — worth knowing repo-wide

The first gate-1 run did **not** fail cleanly. Verilator returned:

```
%Error: broken.v:5:1: Unknown verilator comment:
        '/*verilator : Signal is not driven: 'error' (UNDRIVEN)*/'
```

**Verilator parses any comment whose first token is `verilator` as a
metacomment.** This file's header had a line reading
`// Verilator: "Signal is not driven: 'error'" (UNDRIVEN)` — documentation
prose, which Verilator took as a lint directive and aborted on. Lint never ran,
so the real `UNDRIVEN` warning never fired.

Two consequences:

1. **Fixed here** — the comment now reads `// Expected from Verilator:`. The
   same reword was applied to `../adder_with_overflow_tb.v`,
   `../fsm_next_state_error_tb.v` and `../priority_encoder_valid_tb.v`.
   `illustrations/proven/mux4_oe_tb.v` has the same pattern and was **not**
   touched: it is frozen evidence, and testbenches are never passed to
   `run_verilator_lint` — only the DUT is — so it is latent, not active.

2. **A genuine interpreter false positive was observed.** With the aborted
   lint, `interpret_verilator` still reported `codes_fired = ['UNDRIVEN']` and
   emitted a confident, correctly-named directive — because `interpret_verilator`
   tests `if code not in raw_out` against the whole text, and the string
   `UNDRIVEN` appeared inside Verilator's **echo of the source comment**. Zero
   real UNDRIVEN warnings were present.

   Here the directive happened to be right, since the comment described the
   real bug. In general it need not be. The runner's line filter already drops
   the `... Use "/* verilator lint_off UNDRIVEN */"` hint line, so the residual
   exposure is source-comment text echoed inside `%Error:` lines — including
   comments an LLM writes itself after being shown a directive that names the
   code. Narrow, but it is a directive-precision risk that scales with problem
   count, so it belongs in the VerilogEval precision measurement (plan v4 §7
   #1-#3) rather than being fixed reactively now.

## Residual risk

- Shares `adder_with_overflow`'s forgotten-**output** risk: an unassigned
  output is more conspicuous in a small module than an unconsulted input, and
  both proven illustrations target inputs. See that candidate's README.
- If the model splits the design into a clocked state register plus a separate
  combinational next-state block and omits `error` there, the defect routes to
  the **Yosys latch** handler instead of `UNDRIVEN` — which is currently
  blocked under plan v4 §7 #7. That outcome would be confounded; check
  `verilator_codes_seen` in the metrics before interpreting the result.

## Files

- `correct.v` — drives `error` on every path; passes the oracle
- `broken.v` — `error` never assigned; hand-written for the pre-screen,
  **not** model output
- testbench: `../fsm_next_state_error_tb.v` (flat, runner-readable)
