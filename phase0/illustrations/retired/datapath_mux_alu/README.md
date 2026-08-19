# `datapath_mux_alu` — pending candidate (larger module, UNUSEDSIGNAL)

**Status 2026-08-19: pre-screened 4/4, READY for an LLM run.**

Built for the reviewer request: a *larger* module with internal mux/decoder
structure, showing the mechanism still works when the containing module is not
a bare primitive.

## Size, against the two proven illustrations

Yosys cell count after `synth`, reference implementation:

| Module | Cells | Structure |
|---|---|---|
| `decoder_3to8` | 21 | one case |
| `mux4_oe` | 60 | one case |
| **`datapath_mux_alu`** | **145** | case-based ALU **+** mode mux **+** enable gate |

2.4x the larger of the two proven illustrations, with three composed stages
instead of one. Six input ports instead of three.

## Design constraint this respects

**The interpreter fires on top-level ports only.** A forgotten port inside a
submodule is invisible to it, and small models do not reliably emit
hierarchical designs anyway. So the internal structure here is
mux/decoder-shaped *logic inline in one module*, and the gating port `enable`
sits at the top level, which is the only place `UNUSEDSIGNAL` can see it.

## Target mechanism

| | |
|---|---|
| Defect | `enable` declared at the top level, never read |
| Tool | Verilator, `%Warning-UNUSEDSIGNAL: Signal is not used: 'enable'` |
| Interpreter | `interpret_verilator` → `_unusedsignal_message` (parameterised) |
| Oracle | every `enable=0` vector returns the datapath result instead of `8'b0` |

Identical to `mux4_oe`'s proven mechanism, scaled up. The ALU case and the
mode mux are correct in `broken.v`; only the gate is missing.

## Spec sent to the LLM

```
Write a Verilog-2001 module named datapath_mux_alu with:
input [7:0] a, input [7:0] b, input [7:0] bypass,
input [1:0] op, input mode, input enable,
output reg [7:0] out.
Implement a datapath as follows: first compute an ALU result
from a and b based on op (00=ADD, 01=SUB, 10=AND, 11=OR). Then
select between the ALU result and bypass using mode (0=ALU,
1=bypass). Combinational logic only. Return only Verilog code.
```

`enable` behaviour is deliberately unstated — recipe rule 1, same as
`decoder_3to8` and `mux4_oe`. Registered in `BENCHMARK`.

## Pre-screen — all four gates, 2026-08-19

Real Verilator 5.020 / Yosys 0.33 / Icarus 12.0 via WSL, through the
production wrappers (`stitch_runner.run_verilator_lint`, `run_yosys_check`,
`interpret_verilator`).

### Gate 1 — warning fires: **PASS**

`broken.v`, `had_meaningful_warnings=True`:
```
%Warning-UNUSEDSIGNAL: broken.v:17:22: Signal is not used: 'enable'
%Error: Exiting due to 1 warning(s)
```
**Exactly one warning**, naming the intended port. `correct.v` lints clean
(`had_meaningful_warnings=False`, `(no warnings)`) — no false positive on the
fix, and no second warning to compete for the directive.

Yosys, recorded but not the intended source: no latch, no loop, 129 cells on
`broken.v` and 145 on `correct.v`. The gated version is *larger*, which is the
expected direction — the enable gate is real logic.

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
The parameterised template resolved the real output port and width from the
module header — `out = 8'b0;`, correct here, and correct because it was
extracted rather than assumed. `correct.v` produces no directive.

### Gate 3 — `SYSTEM_PROMPT` does not pre-empt it: **PASS**

Checked against all seven rules at `src/runner/stitch_runner.py:92-113`. Rule 3
mandates a `default` branch and an `else` branch inside combinational always
blocks — `broken.v` satisfies it (the ALU case has a `default`, the mode `if`
has an `else`) and still has the defect, because rule 3 governs branch
coverage, not whether a declared port is consulted. No rule says "use every
port you declared". Same clearance as `decoder_3to8` and `mux4_oe`.

### Gate 4 — oracle isolates the defect: **PASS**

| | Result |
|---|---|
| `correct.v` + tb | `ALL TESTS PASSED` |
| `broken.v` + tb | `FAIL: 8 test(s) failed` |

All 8 failures are gating vectors — `en0_mode0_add/sub/and/or`,
`en0_mode1_add/or`, `en0_other_operands`, `disable_again`. **Zero failures in
the `enable=1` block**, which covers all four ALU ops and both mode values, so
the ALU and the mux are provably correct in `broken.v` and cannot confound the
run.

The testbench orders `enable=1` vectors first precisely so a genuine ALU or
mux bug in model output is distinguishable from the gating defect by which
block fails.

## Residual risk

- **Recipe rule 3 (keep it small) is deliberately relaxed here** — that is the
  reviewer's request. The risk is exactly what retired `seg7_blank`:
  independent errors in the larger surface swamping the target fix. Four ALU
  ops are far simpler than ten 7-segment patterns, but if this fails watch
  *which* vectors fail. Failures in the `enable=1` block mean the model got
  the ALU or mux wrong, which is an unrelated defect, not a verdict on the
  mechanism.
- The model may name its internal ALU result something other than
  `alu_result`, or inline it. Irrelevant to the mechanism — the directive
  targets a top-level port.

## Files

- `correct.v` — reference implementation, passes the oracle
- `broken.v` — `enable` never read; hand-written for the pre-screen, **not**
  model output
- testbench: `../datapath_mux_alu_tb.v` (flat, runner-readable)
