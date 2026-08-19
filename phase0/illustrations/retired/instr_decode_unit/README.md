# `instr_decode_unit` — RETIRED (larger module, UNUSEDSIGNAL)

**Retired 2026-08-19. Verdict: NOISY.** N=3 replication on gemma3:4b: `sem_adv`
never passes (0/3). Full data and reasoning:
`../retired_candidates.md` §1b, `../../../evidence/n3_replication_pass2.md`.

Everything below this line is the **pre-retirement pre-screen record**,
preserved as-is for provenance. It correctly predicted the mechanism would
fire cleanly when reached (confirmed: sample 3 fired `UNUSEDSIGNAL` on
`valid` exactly as designed) — the pre-screen was not wrong. What it could not
predict, because it is not a property the four gates test for, is whether the
model reaches a target-defect-only state reliably enough across independent
samples. It did not: `baseline` and `raw_adv` were stuck on `syntax_error` for
all 6 iterations in all 3 samples, and `sem_adv` reached clean target-defect
code in only 1 of those 3. See the replication doc for the full accounting,
including why a correct directive still did not save the one sample where it
fired.

**Status below (READY, pre-screen results) reflects the state before this
retirement — historical, not current.**

## Why the original version failed

The original spec left `instr[3:0]` undefined (only `instr[7:6]` opcode and
`instr[5:4]` ALU-op bits carried meaning), so *any* correct implementation left
those bits unused. Verilator therefore emitted a **second** `UNUSEDSIGNAL`:

```
%Warning-UNUSEDSIGNAL: broken.v:12:22: Bits of signal are not used: 'instr'[3:0]
%Warning-UNUSEDSIGNAL: broken.v:13:22: Signal is not used: 'valid'
```

`interpret_verilator` emits at most one directive per code and takes the
**first** matching line, so source order decided the outcome: `instr` is
declared before `valid`, so `instr` won. The directive told the model
`if (instr) begin ... end` on an 8-bit instruction word, never mentioning
`valid`, and `correct.v` — which has no defect at all — still lint-failed on
the same partial-bus warning, so there was no clean state for the loop to
land on.

## The fix

`instr` narrowed from `[7:0]` to `[3:0]`. Every bit now carries meaning
(`instr[3:2]` opcode, `instr[1:0]` ALU-op field), so there is no unused
portion of the bus and no competing warning. `valid` is the only candidate for
`UNUSEDSIGNAL` in `broken.v`. Decode logic, control-signal semantics and the
four-opcode table are otherwise unchanged from the original design.

## Target mechanism

| | |
|---|---|
| Defect | `valid` declared at the top level, never read |
| Tool | Verilator, `%Warning-UNUSEDSIGNAL: Signal is not used: 'valid'` |
| Interpreter | `interpret_verilator` → `_unusedsignal_message` (parameterised, 4 outputs) |
| Oracle | every `valid=0` vector asserts control signals it should not |

Same mechanism as `decoder_3to8`, scaled to a module with four control
outputs instead of one.

## Spec sent to the LLM

```
Write a Verilog-2001 module named instr_decode_unit with:
input [3:0] instr, input valid,
output reg [1:0] alu_op, output reg reg_write,
output reg mem_read, output reg mem_write.
Decode instr into control signals. The upper two bits instr[3:2]
select the operation:
  00: ALU operation, reg_write=1, alu_op comes from instr[1:0]
  01: LOAD, mem_read=1, reg_write=1, alu_op=0
  10: STORE, mem_write=1, alu_op=0
  11: NOP, all zero
Combinational logic only. Return only Verilog code.
```

`valid` behaviour is deliberately unstated. Registered in `BENCHMARK`.

## Pre-screen — all four gates, re-run 2026-08-19 against the redesign

Real Verilator 5.020 / Yosys 0.33 / Icarus 12.0 via WSL, through the
production wrappers.

### Gate 1 — exactly one warning, naming `valid`: **PASS** (was FAIL)
```
run_verilator_lint(broken.v)  ->  had_meaningful_warnings=True
%Warning-UNUSEDSIGNAL: broken.v:16:22: Signal is not used: 'valid'
%Error: Exiting due to 1 warning(s)

run_verilator_lint(correct.v) ->  had_meaningful_warnings=False
(no warnings)
```
One occurrence of `UNUSEDSIGNAL`, naming the intended port. **No partial-bus
warning on `instr` this time** — the narrowed bus has no unused bits.
`correct.v` lints clean, which the previous version never achieved.

### Gate 2 — interpreter converts it, all four outputs correctly enumerated: **PASS** (was FAIL)
```
codes_fired = ['UNUSEDSIGNAL']

*** CRITICAL: Port 'valid' is declared but NEVER USED in your always block. ***
You MUST condition on 'valid':
  always @(*) begin
    if (valid) begin
      <your existing case or logic here>
    end else begin
      alu_op = 2'b0;
      reg_write = 1'b0;
      mem_read = 1'b0;
      mem_write = 1'b0;
    end
  end
The FAIL lines (with 'valid' deasserted, the output is still non-zero)
are caused by 'valid' being ignored.
```
The parameterised template correctly resolved **all four** output ports with
their real widths — `alu_op = 2'b0` (2-bit) and three 1-bit signals
(`reg_write`, `mem_read`, `mem_write`) each `= 1'b0`. The multi-output case
works cleanly; it was never the gap. `correct.v` produces no directive.

### Gate 3 — `SYSTEM_PROMPT` does not pre-empt it: **PASS**
`broken.v`'s case has a `default:` branch assigning all four outputs to zero,
satisfying rule 3, and still carries the defect. No rule requires consulting a
declared port. Unchanged from the original design's gate-3 analysis.

### Gate 4 — oracle isolates the defect: **PASS**
```
correct.v + tb  ->  ALL TESTS PASSED
broken.v  + tb  ->  FAIL: 5 test(s) failed

FAIL inv_alu_op00: valid=0 instr=0000 got alu_op=00 rw=1 mr=0 mw=0 expected 00 0 0 0
FAIL inv_alu_op11: valid=0 instr=0011 got alu_op=11 rw=1 mr=0 mw=0 expected 00 0 0 0
FAIL inv_load:     valid=0 instr=0100 got alu_op=00 rw=1 mr=1 mw=0 expected 00 0 0 0
FAIL inv_store:    valid=0 instr=1000 got alu_op=00 rw=0 mr=0 mw=1 expected 00 0 0 0
FAIL invalidate_again: valid=0 instr=0100 got alu_op=00 rw=1 mr=1 mw=0 expected 00 0 0 0
```
All 5 failures are `valid=0` vectors. Zero failures in the `valid=1` block,
which exercises all four opcodes plus both `alu_op` source bits, so the decode
logic is provably correct in `broken.v`.

`inv_nop` is not in the FAIL list — expected, since NOP already drives all
outputs to zero, making it indistinguishable from the gated-off state. Not a
gap in the oracle: the other four opcodes each assert at least one non-zero
control signal when ungated, so the failure set is not vacuous.

## Files

- `correct.v` — reference implementation, passes the oracle, lints clean
- `broken.v` — `valid` never read; hand-written for the pre-screen, **not**
  model output
- testbench: `instr_decode_unit_tb.v` (was flat under `pending/`, moved
  alongside this README on retirement — no longer used by `--testbench-dir`
  since the `BENCHMARK` entry is de-registered)
