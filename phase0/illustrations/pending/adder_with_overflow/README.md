# `adder_with_overflow` — pending candidate, **spec v2** (UNDRIVEN mechanism)

**Status 2026-08-19: spec v1 retired after a real run. Spec v2 pre-screened
4/4, READY for an LLM run.** Module, testbench and both reference
implementations are unchanged from v1 — only the spec text changed.

## What happened to v1

v1 ran gemma3:4b on all three conditions and produced **no signal**:
baseline FAIL|6, raw_adv PASS|2, sem_adv PASS|2, `semantic_fired = 0`
everywhere. The model assigned `overflow` on iteration 1 of every condition, so
the target `UNDRIVEN` defect never occurred.

Cause: recipe rule 1. The v1 spec said *"The overflow output indicates
carry-out"*, which was enough. Same failure as `counter_with_enable` and
`register_with_load`.

Full record, including a more important secondary finding about `raw_adv`
diverging from `baseline` for the first time:
`../../retired/retired_candidates.md` §1. **Read that before quoting any
number from this module.**

## Spec v2 — the only change

The explanatory clause is deleted. `overflow` is now named in the port list and
nowhere else:

```
Write a Verilog-2001 module named adder_with_overflow with:
input [7:0] a, input [7:0] b, output reg [7:0] sum, output reg overflow.
Compute sum = a + b. Combinational logic only. Return only Verilog code.
```

Already applied to `BENCHMARK` in `src/runner/stitch_runner.py`.

## Target mechanism

| | |
|---|---|
| Defect | `overflow` declared in the port list, never assigned |
| Tool | Verilator, `%Warning-UNDRIVEN: Signal is not driven: 'overflow'` |
| Interpreter path | `interpret_verilator` → `_undriven_message` → `output_port` branch |
| Oracle | `overflow` reads `x`; the testbench uses `!==` so `x` is caught |

## Pre-screen — all four gates re-run 2026-08-19 against spec v2

Real Verilator 5.020 / Yosys 0.33 / Icarus 12.0 via WSL, through the production
wrappers (`stitch_runner.run_verilator_lint`, `interpret_verilator`).

### Gate 1 — target warning fires: **PASS**
```
%Warning-UNDRIVEN: broken.v:11:22: Signal is not driven: 'overflow'
%Error: Exiting due to 1 warning(s)
```
Exit 1, so `had_meaningful_warnings = True`. `correct.v` lints clean.

### Gate 2 — interpreter converts it: **PASS**
```
codes_fired = ['UNDRIVEN']
*** CRITICAL: Output 'overflow' is declared but never assigned. ***
Add an assignment: 'overflow = <value>;' in your always block or use assign.
```
The `output_port` branch — not `undeclared`, not the `ambiguous` fallback. The
prescribed repair applies directly to this defect shape. `correct.v` yields no
directive.

### Gate 3 — `SYSTEM_PROMPT` does not pre-empt it: **PASS**
Re-checked against all seven rules at `src/runner/stitch_runner.py:92-113` for
the v2 text. Rule 3 is the only near-miss and does not apply: it mandates a
`default` branch and an `else` branch, and this module has neither a `case` nor
an `if` — it is one unconditional assignment. No rule requires assigning every
declared output.

### Gate 4 — oracle catches it: **PASS**

| | Result |
|---|---|
| `correct.v` + tb | `ALL TESTS PASSED` |
| `broken.v` + tb | `FAIL: 11 test(s) failed` |

`sum` is correct in `broken.v`, so all 11 FAIL lines are `overflow` checks —
the failure set isolates the target defect with no independent error surface.

## Residual risk — v2 may still land on outcome (c)

Stated plainly, because v1 already burned one run on this:

- v1 proved this model assigns `overflow` **spontaneously**. Deleting the
  explanatory clause removes the strongest hint, but `overflow` still sits
  beside `sum` in a two-output port list on a very small module, and
  `{overflow, sum} = a + b;` is the idiomatic 9-bit adder pattern.
- More fundamentally: **a forgotten output may be intrinsically harder to
  elicit than a forgotten input.** Both proven illustrations
  (`decoder_3to8`, `mux4_oe`) target a forgotten *input* — a port that is
  simply never consulted, which is invisible in the written module. An
  unassigned *output* is conspicuous: it is declared right there and nothing
  writes it.

If v2 also lands PASS|1 or PASS|2 with `semantic_fired = 0`, that is not a
third spec revision — it is evidence for the input/output asymmetry above, and
should be written up as such rather than iterated on further.

## Files

- `correct.v` — reference implementation, passes the oracle
- `broken.v` — hand-written defect shape, **not** model output
- testbench: `../adder_with_overflow_tb.v` (flat, runner-readable)
