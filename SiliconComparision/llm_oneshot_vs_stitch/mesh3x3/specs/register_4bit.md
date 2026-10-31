# register_4bit

## Behaviour (Phase 3 spec, reused verbatim from phase3/tasks/register_4bit/spec.md)

Module `register_4bit` -- 4-bit pipeline/VC-state register used inside every NoC router.
Ports (keep exactly, same order): input [3:0] din; input clk; input clr; input ce; output [3:0] dout.
On every rising edge of clk: if clr==1, dout <= 4'b0000; else if ce==1, dout <= din; otherwise dout holds.

## Reset

Covered by the Phase 3 spec above: synchronous `clr` loads 4'b0000.

## Ports

<!-- BEGIN generated: ports -->
5 ports, in this exact order:

```verilog
input [3:0] din;
input clk, clr, ce;
output [3:0] dout;
```

Parameters: none.
<!-- END generated: ports -->

## Children

<!-- BEGIN generated: children -->
None. This module instantiates no other module.
<!-- END generated: children -->

Unclear in golden: latch-dependent. The hand-written golden is level-sensitive on (`clr`, `ce`) with `din` missing from
the sensitivity list, and `clk` unused. In simulation `dout` samples `din` only when `clr` or `ce`
changes. Synthesis builds a transparent latch with asynchronous clear (Yosys `$adlatch`), so simulation
and synthesis differ. The clocked behaviour in the Phase 3 spec exists only in the repaired golden.
