# register_32bit

## Behaviour (Phase 3 spec, reused verbatim from phase3/tasks/register_32bit/spec.md)

Module `register_32bit` -- 32-bit pipeline/VC-state register used inside every NoC router.
Ports (keep exactly, same order): input [31:0] din; input clk; input clr; input ce; output [31:0] dout.
On every rising edge of clk: if clr==1, dout <= 32'h60000000; else if ce==1, dout <= din; otherwise dout holds.

## Reset

Covered by the Phase 3 spec above: synchronous `clr` loads 32'h6000_0000 (32'b0110 0000 ...).

## Ports

<!-- BEGIN generated: ports -->
5 ports, in this exact order:

```verilog
input [31:0] din;
input clk, clr, ce;
output [31:0] dout;
```

Parameters: none.
<!-- END generated: ports -->

## Children

<!-- BEGIN generated: children -->
None. This module instantiates no other module.
<!-- END generated: children -->

Unclear in golden: latch-dependent. The hand-written golden is a level-sensitive latch (`always @(clr, ce, din)`, `clk`
unused): `dout` follows `din` while `ce` is 1, is forced to 32'h6000_0000 while `clr` is 1 (Yosys:
`$adlatch`), and holds otherwise. The clocked behaviour in the Phase 3 spec exists only in the repaired
golden (latch_study B). golden/handwritten and golden/A1 both keep the latch, so neither matches this
spec cycle for cycle.
