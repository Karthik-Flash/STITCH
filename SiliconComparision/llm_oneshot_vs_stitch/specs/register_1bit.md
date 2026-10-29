# register_1bit

## Behaviour (Phase 3 spec, reused verbatim from phase3/tasks/register_1bit/spec.md)

Module `register_1bit` -- 1-bit router state register with asynchronous reset and synchronous clear.
Ports (keep exactly, same order): input din, reset, clk, clr, ce; output reg dout.
reset is ASYNCHRONOUS and active-high: dout goes to 0 immediately when reset rises.
On a rising clk edge (reset low): if clr==1 dout <= 0; else if ce==1 dout <= din; else hold.

## Reset

Covered by the Phase 3 spec above: asynchronous active-high `reset`, synchronous `clr`.

## Ports

<!-- BEGIN generated: ports -->
6 ports, in this exact order:

```verilog
input din, reset, clk, clr, ce;
output dout;
```

Parameters: none.
<!-- END generated: ports -->

## Children

<!-- BEGIN generated: children -->
None. This module instantiates no other module.
<!-- END generated: children -->

Unclear in golden: the hand-written golden puts `clr` inside the async-reset process (`always @(posedge clk, posedge
reset) if (clr | reset) ...`). Simulation matches the Phase 3 spec, but Yosys rejects it (`Multiple
edge sensitive events`). golden/A1 already uses the Phase 3 golden. Not latch-dependent.
