# `priority_encoder_valid` — pending candidate (Yosys latch mechanism)

**Status 2026-08-19: BLOCKED. Steps 1, 3 and 4 PASS. Step 2 FAILS.**
Do **not** run an LLM sweep on this candidate yet.

The module design is sound and the tool-level mechanism is exactly what was
wanted. The blocker is in `interpret_yosys_latches()`, not in this module: the
directive fires, names the right signal, and then prescribes a repair that is a
**no-op for this defect shape**. Detail in step 2 below.

## Why this candidate exists

Both proven illustrations run through `UNUSEDSIGNAL`. This one targets the
Yosys latch path — a different tool, a different interpreter function, and a
defect class that sits in a genuine gap in `SYSTEM_PROMPT`.

The gap is the point. `mode_mux_latch` was retired because prompt rule 3
mandates a `default` branch, so the model writes one and the bug never happens.
This module **has** a compliant `default` and still latches, because rule 3
constrains *branch* coverage, not *output* coverage. A `case` with a default
that assigns only some of the module's outputs satisfies the prompt and still
leaves an output unassigned on most paths.

## Target mechanism

| | |
|---|---|
| Defect | `valid` assigned only in the `default` branch; the eight `casez` branches assign `pos` only |
| Tool | Yosys, `Latch inferred for signal `\priority_encoder_valid.\valid'` |
| Interpreter path | `detect_yosys_latches` → `interpret_yosys_latches` |
| Oracle | latched `valid` holds 0 after the first idle vector and never goes high |

## Spec sent to the LLM

```
Write a Verilog-2001 module named priority_encoder_valid with:
input [7:0] req, output reg [2:0] pos, output reg valid.
For each request bit, pos should indicate the highest-priority
requesting bit (bit 7 = highest, bit 0 = lowest). valid should
indicate whether any request is active. Combinational logic only.
Return only Verilog code.
```

## Pre-screen results (2026-08-19)

Real Verilator 5.020 / Yosys 0.33 / Icarus 12.0 via WSL, through the production
wrappers (`stitch_runner.run_verilator_lint`, `stitch_runner.run_yosys_check`).

### Step 1 — does the target warning fire? **PASS — and cleanly**

Yosys on `broken.v`:
```
No latch inferred for signal `\priority_encoder_valid.\pos' from process ...
Latch inferred for signal `\priority_encoder_valid.\valid' from process ...: $auto$proc_dlatch...
```
`detect_yosys_latches()` returns exactly `['valid']` — it accepts the positive
line and rejects the negated `pos` line **in the same output**, which is a live
regression check on the false-positive bug fixed 2026-08-17.

On `correct.v`: both signals report the negative form, `has_latch = False`. No
false positive on the fix.

**Verilator is completely silent on `broken.v` — exit 0, no warnings at all.**
No `CASEINCOMPLETE` (the case is complete), no `UNDRIVEN`/`UNUSEDSIGNAL`
(`valid` is both driven in the default branch and read at the port). This is
the highest-value configuration for the paper: **Yosys is the sole source**, so
the illustration cannot be explained away as another Verilator result.

### Step 2 — does the interpreter convert it usefully? **FAIL**

It fires and names the right signal. The prescription is wrong.

Actual directive text, verbatim:
```
*** YOSYS: LATCH INFERRED for signal(s) 'valid' ***

ROOT CAUSE: Your always block does NOT assign 'valid' on every
code path. When the unhandled path is taken, synthesis infers a latch
that HOLDS THE LAST VALUE — this is why enable=0 returns the previous output.

EXACT FIX (choose one):
  A) Add else branch to every if without one:
       if (condition) begin valid = X; end
       else           begin valid = 0; end  <-- ADD THIS

  B) Add default to every case statement:
       case (sel)
         ... existing cases ...
         default: begin valid = 0; end  <-- ADD THIS
       endcase
```

Three defects against this defect shape:

1. **Fix B is a literal no-op.** `broken.v` already contains
   `default: begin pos = 3'd0; valid = 1'b0; end`. A model that follows fix B
   exactly changes nothing. The real repair — *assign `valid` in every branch,
   not only the default* — is never stated.
2. **Fix A is inapplicable.** There is no `if` in the module.
3. **The causal join is fabricated.** *"this is why enable=0 returns the
   previous output"* names an `enable` port that does not exist here. This is
   the same defect class as the pre-parameterisation `UNUSEDSIGNAL` template's
   hard-coded `out = 8'b0;` — a template written against one specific module
   and asserted generally.

The `ROOT CAUSE` sentence is correct and is the useful half. But the section
labelled `EXACT FIX (choose one)` offers two options, neither of which applies,
and the evidence doc's own account of *why* the interpreter works puts "the
repair shape" as contribution 2 of 3. Running this candidate now would confound
the experiment: a failure could not be attributed between "the mechanism does
not work on this class" and "the directive text was a no-op."

### Step 3 — does `SYSTEM_PROMPT` pre-empt the bug? **PASS (it does not)**

Rule 3 is the relevant one and it is satisfied by `broken.v`: the `casez` has a
`default`. Rule 3 says nothing about assigning every output on every path. This
is the specific gap the candidate was designed to occupy, and `broken.v`
confirms the gap is real — a fully rule-3-compliant module that still latches.

### Step 4 — does the testbench oracle catch it? **PASS**

| | Result |
|---|---|
| `correct.v` + tb | `ALL TESTS PASSED` |
| `broken.v` + tb | `FAIL: 13 test(s) failed` |

Every FAIL line is a `valid` check; `pos` is correct on every vector, so the
failure set isolates the target defect. The first vector (`req = 0`) sets the
latch to 0 and it holds for the rest of the run, which is a textbook
demonstration of the failure mode.

## What unblocks this

A bounded change to `interpret_yosys_latches()` in
`src/interpreter/stitch_interpreter.py`:

1. Add the missing repair option: *assign the signal in every branch of the
   case, not only in the default* — or hoist an unconditional default
   assignment above the case.
2. Drop the hard-coded `enable=0` clause, or derive it from the module the way
   `_unusedsignal_message` derives its output ports.

**This change cannot invalidate the proven illustrations.** Verified: all three
`metrics_*.json` in `illustrations/proven/decoder_3to8/` record
`latch_warnings: 0`, and the sem_adv result fired `['UNUSEDSIGNAL']` only.
Neither proven illustration touches `interpret_yosys_latches` at all, so its
directive text is not on the replication chain.

Any change needs new tests in `src/interpreter/tests/test_interpreter.py`
(currently 39 passing), built from the verbatim Yosys string captured above.

## Minor, non-blocking

`interpret_yosys_latches` emits a literal em-dash (U+2014) at offset 214 of the
directive. Harmless in the prompt, but the runner's `sanitize_ascii()` is
applied only to generated code, not to feedback text — and CHANGELOG records a
prior `UnicodeEncodeError` crash from printing a non-ASCII character to a
cp1252 console. Worth making ASCII the next time this function is touched.

## Files

- `correct.v` — every branch assigns both outputs; passes the oracle, no latch
- `broken.v` — rule-3-compliant default, `valid` still unassigned on 8 of 9
  paths; hand-written for the pre-screen, **not** model output
- testbench: `../priority_encoder_valid_tb.v` (flat, runner-readable)
