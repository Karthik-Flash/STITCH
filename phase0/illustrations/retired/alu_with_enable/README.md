# `alu_with_enable` — RETIRED (larger module, UNUSEDSIGNAL)

**Retired 2026-08-19. Verdict: too easy — outcome (c).** gemma3:4b:
`PASS|1` on all three conditions, `semantic_fired=0` — it wrote the enable
gate correctly on the first try. llama3.1: `PASS|2` on all three conditions
with no differentiation between them. Neither run produced the target defect,
so neither is evidence in either direction. Full data:
`../retired_candidates.md` §1c.

Dropping the mode mux and bypass from the retired `datapath_mux_alu` (see
below) over-corrected: shrinking the module past the size where
`reg_wire_mismatch` dominated also shrank it past the size where the `enable`
omission occurs at all — the same failure mode as retired `cmp8_en`. No
further redesign attempted; this was the last phase-0 larger-module attempt.

**Status below (READY, pre-screen results) reflects the state before this
retirement — historical, not current.**

Redesign of the retired `datapath_mux_alu` — see
`../../retired/retired_candidates.md` §1a for the full failure record. This is
the last phase-0 attempt at a larger illustration; no further fallback if it
fails.

## What changed from `datapath_mux_alu`, and why

`datapath_mux_alu` (case-based ALU + mode mux + bypass, 145 Yosys cells, six
ports) was run against gemma3:4b for real. The interpreter fired correctly —
`semantic_fired=5`, `UNUSEDSIGNAL` on `enable` repeatedly — but 4 of 6
iterations in every condition failed on `reg_wire_mismatch` or `syntax_error`,
unrelated to the target defect, before the model could ever reach a state
where `enable` was the only thing wrong. Too large for gemma3:4b's convergence
horizon within 6 iterations.

This version drops the mode mux and the `bypass` port entirely: just the
case-based ALU plus the enable gate. Four ports instead of six, and — the
change that actually matters — **no internal register**. `datapath_mux_alu`
had a separate `alu_result` reg wired through a second stage; that is exactly
the kind of intermediate signal where a small model's reg/wire type or
sensitivity mistakes concentrate. Here `out` is the only reg in the module.

**Honest caveat on cell count:** Yosys reports **129 cells**, only an 11%
reduction from 145. ADD and SUB synthesize to real adder/subtractor logic
regardless of what surrounds them, and that logic is unchanged between the two
versions — most of the gate count was never the mux or the bypass path. Cell
count is not the axis that changed; **port count and internal-signal count
are**, and those map directly onto the failure modes actually observed
(`reg_wire_mismatch`, `syntax_error`).

## Size, in context

| Module | Cells | Internal registers | Ports |
|---|---|---|---|
| `decoder_3to8` | 21 | 0 | 3 |
| `mux4_oe` | 60 | 0 | 5 |
| **`alu_with_enable`** | **129** | **0** | **4** |
| `datapath_mux_alu` (retired) | 145 | 1 (`alu_result`) | 6 |

## Target mechanism

| | |
|---|---|
| Defect | `enable` declared at the top level, never read |
| Tool | Verilator, `%Warning-UNUSEDSIGNAL: Signal is not used: 'enable'` |
| Interpreter | `interpret_verilator` → `_unusedsignal_message` (parameterised) |
| Oracle | every `enable=0` vector returns the ALU result instead of `8'b0` |

Identical to `mux4_oe`'s proven mechanism on ALU-shaped logic instead of a mux.

## Spec sent to the LLM

```
Write a Verilog-2001 module named alu_with_enable with:
input [7:0] a, input [7:0] b, input [1:0] op, input enable,
output reg [7:0] out.
Implement four operations selected by op:
  00: out = a + b (addition)
  01: out = a - b (subtraction)
  10: out = a AND b (bitwise)
  11: out = a OR b (bitwise)
Combinational logic only. Return only Verilog code.
```

`enable` behaviour is deliberately unstated — recipe rule 1. Registered in
`BENCHMARK`.

## Pre-screen — all four gates, 2026-08-19

Real Verilator 5.020 / Yosys 0.33 / Icarus 12.0 via WSL, through the
production wrappers (`stitch_runner.run_verilator_lint`, `run_yosys_check`,
`interpret_verilator`).

### Gate 1 — exactly one warning, naming `enable`: **PASS**
```
run_verilator_lint(broken.v)  ->  had_meaningful_warnings=True
%Warning-UNUSEDSIGNAL: broken.v:14:22: Signal is not used: 'enable'
%Error: Exiting due to 1 warning(s)

run_verilator_lint(correct.v) ->  had_meaningful_warnings=False
(no warnings)
```
One occurrence of `UNUSEDSIGNAL` in the raw text (checked directly), naming
the intended port. `correct.v` lints clean.

Yosys, recorded but not the intended source: no latch, no loop, 121 cells on
`broken.v`, 129 on `correct.v` — the gated version is larger, the expected
direction, since the enable gate is real logic.

### Gate 2 — interpreter converts it: **PASS**
```
codes_fired = ['UNUSEDSIGNAL']

*** CRITICAL: Port 'enable' is declared but NEVER USED in your always block. ***
You MUST condition on 'enable':
  always @(*) begin
    if (enable) begin
      <your existing case or logic here>
    end else begin
      out = 8'b0;
    end
  end
The FAIL lines (with 'enable' deasserted, the output is still non-zero)
are caused by 'enable' being ignored.
```
Parameterised template resolved `out` and its 8-bit width from the header.
`correct.v` produces no directive.

### Gate 3 — `SYSTEM_PROMPT` does not pre-empt it: **PASS**
Checked against all seven rules at `src/runner/stitch_runner.py:92-113`.
`broken.v`'s case has a `default: out = 8'b0;`, satisfying rule 3, and still
carries the defect — rule 3 governs branch coverage, not whether a declared
port is consulted. There is no `if` in `broken.v` at all, so rule 3's
else-branch clause does not even apply. No rule says "use every port you
declared". Same clearance as `decoder_3to8` and `mux4_oe`.

### Gate 4 — oracle isolates the defect: **PASS**
```
correct.v + tb  ->  ALL TESTS PASSED
broken.v  + tb  ->  FAIL: 6 test(s) failed

FAIL en0_add: en=0 op=00 a=12 b=34 got 46 expected 00
FAIL en0_sub: en=0 op=01 a=12 b=34 got de expected 00
FAIL en0_and: en=0 op=10 a=12 b=34 got 10 expected 00
FAIL en0_or:  en=0 op=11 a=12 b=34 got 36 expected 00
FAIL en0_other_operands: en=0 op=00 a=f0 b=05 got f5 expected 00
FAIL disable_again: en=0 op=00 a=f0 b=05 got f5 expected 00
```
All 6 failures are `en0_*` (gating) vectors. **Zero failures in the `enable=1`
block**, which covers all four ALU ops — so the ALU is provably correct in
`broken.v` and cannot confound the run.

## Residual risk

Still larger than either proven illustration (129 cells vs `mux4_oe`'s 60).
The retirement diagnosis suggests port count and internal-signal count matter
more than raw cell count, and this version minimises both relative to the
retired one, but that is inference from one failed run, not a proven
predictor. If this also fails to converge on syntax/type errors rather than
the target defect, that is a real negative result about model capability at
this scale, not something to redesign a third time per the "last attempt"
constraint.

## Files

- `correct.v` — reference implementation, passes the oracle
- `broken.v` — `enable` never read; hand-written for the pre-screen, **not**
  model output
- testbench: `alu_with_enable_tb.v` (was flat under `pending/`, moved
  alongside this README on retirement — no longer used by `--testbench-dir`
  since the `BENCHMARK` entry is de-registered)
