# `priority_encoder_valid` — pending candidate (Yosys latch mechanism)

**Status 2026-08-19: READY. All four gates PASS.** Gate 2 was blocked earlier
the same day; the interpreter fix landed and it now passes. Registered in
`BENCHMARK` as `priority_encoder_valid`.

This is the only candidate whose defect **Verilator cannot see at all** — Yosys
is the sole source — and the only live one targeting *path completeness* rather
than output existence, the distinction that retired both forgotten-output
candidates. See `../../../evidence/input_vs_output_asymmetry.md` §5.

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

### Step 2 — does the interpreter convert it usefully? **PASS** (fixed 2026-08-19)

Actual directive text, verbatim, through the runner's own
`_build_sem_adv_feedback`:

```
*** YOSYS: LATCH INFERRED for signal(s) 'valid' ***

ROOT CAUSE: Yosys inferred a latch on 'valid' because it is not
assigned on every code path through the always block. This means
'valid' will hold its previous value on paths where no assignment
occurs, which is almost certainly not what you intended for a
combinational output.

EXACT FIX:
  Assign 'valid' in EVERY branch of the case, not only in the default.
  The default branch alone is NOT enough -- 8 branch(es) assign
  other signals but not 'valid', so on those branches 'valid' keeps
  its previous value, and that is the latch.
    case (...)
      <label>: begin <other signals> = ...; valid = ...; end   <-- ADD 'valid' HERE
      ...
    endcase
  Simplest alternative that covers every path at once: assign
  'valid' unconditionally ONCE immediately BEFORE the case, then
  let individual branches override it.
```

The branch count (8) is derived from this module, and the option offered is
the one that actually repairs it.

#### What gate 2 originally caught

Recorded because it is the reason the interpreter changed. The previous
template emitted two options unconditionally and a fixed causal join:

- **Fix B, "add default to every case statement", was a literal no-op** —
  `broken.v` already contains `default: begin pos = 3'd0; valid = 1'b0; end`.
  A model following it exactly would change nothing.
- **Fix A, "add else to every if", was inapplicable** — there is no `if`.
- **The causal join was fabricated** — *"this is why enable=0 returns the
  previous output"*, naming an `enable` port this module does not have.

Only the `ROOT CAUSE` line was correct. Running the candidate in that state
would have confounded any failure between "the mechanism does not work on this
class" and "the directive was a no-op". Tracked and closed as
`plans/research_plan_v4.md` §7 #7.

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

## How gate 2 was unblocked

`interpret_yosys_latches` now parses the module and emits only the repair
options that apply to its actual structure — the same treatment
`_unusedsignal_message` already had. It distinguishes four shapes: a case with
a default that still omits the signal (this module), a case with complete
branches but no default, a case with neither, and no case at all. The
fabricated `enable` clause is replaced by a causal join derived from the
defect, and the em-dash is gone.

**The change cannot invalidate the proven illustrations.** Verified: all three
`metrics_*.json` in `illustrations/proven/decoder_3to8/` record
`latch_warnings: 0` and fired `['UNUSEDSIGNAL']` only. Neither proven
illustration touches `interpret_yosys_latches`, so its text is not on the
replication chain.

Test suite is 50 passing, up from 39. The 11 new tests include the real
captured Yosys output for this module, stored as
`src/interpreter/tests/fixtures/priority_encoder_valid_yosys_synth.txt`.

## Files

- `correct.v` — every branch assigns both outputs; passes the oracle, no latch
- `broken.v` — rule-3-compliant default, `valid` still unassigned on 8 of 9
  paths; hand-written for the pre-screen, **not** model output
- testbench: `../priority_encoder_valid_tb.v` (flat, runner-readable)
