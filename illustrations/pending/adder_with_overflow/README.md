# `adder_with_overflow` — pending candidate (UNDRIVEN mechanism, new class)

**Status 2026-08-19: all four pre-screen steps PASS. READY for an LLM run.**
Not promoted to `proven/` — promotion requires a real model run with on-disk
before/after evidence, same bar as `decoder_3to8`.

## Why this candidate exists

Both proven illustrations run through **one** interpreter code, `UNUSEDSIGNAL`,
on **one** defect shape: a forgotten *input* gate. A reviewer can reasonably
say the entire effect is one warning code on one module shape.

This candidate targets `UNDRIVEN` on a forgotten **output** — the structural
mirror image. Different Verilator code, different interpreter branch
(`_classify_undriven_signal` → `output_port`), different defect shape, same
scope boundary (a static structural fingerprint: a declared port with no
driver).

## Target mechanism

| | |
|---|---|
| Defect | `overflow` declared in the port list, never assigned |
| Tool | Verilator, `%Warning-UNDRIVEN: Signal is not driven: 'overflow'` |
| Interpreter path | `interpret_verilator` → `_undriven_message` → `output_port` branch |
| Oracle | `overflow` reads `x`; the testbench uses `!==` so `x` is caught |

## Spec sent to the LLM

Add this to `BENCHMARK` in `src/runner/stitch_runner.py`:

```
Write a Verilog-2001 module named adder_with_overflow with:
input [7:0] a, input [7:0] b, output reg [7:0] sum, output reg overflow.
Compute sum = a + b using standard binary addition. The overflow output
indicates carry-out. Combinational logic only. Return only Verilog code.
```

The spec describes the addition fully and mentions `overflow` in one clause
without saying how to compute it. That asymmetry is the intended trigger.

## Pre-screen results (2026-08-19)

Real Verilator 5.020 / Yosys 0.33 / Icarus 12.0 via WSL. Steps 1 and 2 run
through the production wrappers (`stitch_runner.run_verilator_lint`,
`interpret_verilator`), not a hand-built invocation, so the filtering and
signal-extraction path is exactly what a real run would take.

### Step 1 — does the target warning fire? **PASS**

`verilator --lint-only -Wall --bbox-unsup` on `broken.v`:
```
%Warning-UNDRIVEN: broken.v:11:22: Signal is not driven: 'overflow'
%Error: Exiting due to 1 warning(s)
```
Exit code 1, so the runner's `had_meaningful_warnings` is `True` and the
interpreter is invoked. `correct.v` lints clean — no false positive on the fix.

### Step 2 — does the interpreter convert it? **PASS**

```
codes_fired = ['UNDRIVEN']

*** CRITICAL: Output 'overflow' is declared but never assigned. ***
Add an assignment: 'overflow = <value>;' in your always block or use assign.
```

This is the `output_port` branch — not `undeclared`, not the `ambiguous`
"check BOTH possibilities" fallback. `_classify_undriven_signal` parsed the
ANSI port list correctly and knows `overflow` is a declared output. The
directive names the real signal and prescribes the applicable repair.

`correct.v` produces no directive.

### Step 3 — does `SYSTEM_PROMPT` pre-empt the bug? **PASS (it does not)**

Checked against all seven rules at `src/runner/stitch_runner.py:92-113`:

| Rule | Covers this defect? |
|---|---|
| 1 wire vs reg | no |
| 2 non-blocking in clocked | no |
| 3 default branch + else branch | **no — closest, but it constrains branch coverage inside a block, not which signals get assigned** |
| 4 sensitivity list | no |
| 5 Verilog-2001 only | no |
| 6 begin/end in case branches | no |
| 7 return only Verilog | no |

No rule says "assign every output you declared." The bug survives the prompt.

### Step 4 — does the testbench oracle catch it? **PASS**

| | Result |
|---|---|
| `correct.v` + tb | `ALL TESTS PASSED` |
| `broken.v` + tb | `FAIL: 11 test(s) failed` |

Every FAIL line is an `overflow` check. `sum` is correct in `broken.v`, so the
failure set isolates the target defect exactly — no independent error surface
(recipe rule 3).

### Supplementary — what Yosys sees

Yosys also flags it, as plain text with no interpreter handler:
```
Warning: Wire adder_with_overflow.\overflow is used but has no driver.
```
This is not converted — `detect_yosys_latches`/`detect_comb_loops` are the only
Yosys paths, and neither matches. Verilator remains the sole *interpreted*
source. It does mean `raw_adv` sees **two** tools independently naming
`overflow` and still gets no repair shape, which strengthens the control rather
than weakening it.

## Design risk — read before interpreting the run

The spec states *what* `overflow` means ("indicates carry-out"). That is closer
to the retired `counter_with_enable` / `register_with_load` failure than to
`decoder_3to8`, both of which died because the spec spelled out the behaviour
and the model simply implemented it on iteration 1.

The mitigating difference is that those two specs stated the *gate-off
behaviour of a port the model would otherwise ignore*, whereas this one names
a second output without giving its expression. But the honest expectation is a
real chance of **outcome (c), "too easy"** — PASS|1 on all three conditions,
like `cmp8_en`.

That is a decision for the run, not for the pre-screen: the mechanism is
verified sound, so a PASS|1 result is informative (it retires the candidate on
recipe rule 1) rather than ambiguous. If it does land on PASS|1, the redesign
is to drop the "indicates carry-out" clause and mention `overflow` in the port
list only.

## Files

- `correct.v` — reference implementation, passes the oracle
- `broken.v` — hand-written defect shape for the pre-screen, **not** model output
- testbench: `../adder_with_overflow_tb.v` (flat, runner-readable —
  `--testbench-dir` wants flat `<module>_tb.v`, and a single copy avoids the
  drift risk that the nested copies in `proven/` had)
