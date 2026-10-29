# priority_encoder

## Behaviour

Registered 4-way priority grant with grant hold. On every rising edge of `clk`, using the current
outputs:
- requester i is eligible if `in_i` = 1 and no other output `out_j` (j not equal to i) is currently 1;
- if `en` is 1, the eligible requester with the lowest index (`in0` first, then `in1`, `in2`, `in3`)
  gets its output set to 1 and all others are 0. If `en` is 0, all outputs are 0.
A held grant therefore continues while its request stays 1. When a held request drops, all outputs are
0 for that edge (the other requests are still masked), and a new grant follows on the next edge.

## Reset

None. `reset` is an input with no effect. Outputs are unknown until the first rising `clk` edge.

## Ports

<!-- BEGIN generated: ports -->
11 ports, in this exact order:

```verilog
input reset, en, in0, in1, in2, in3;
output out0, out1, out2, out3;
input clk;
```

Parameters: none.
<!-- END generated: ports -->

## Children

<!-- BEGIN generated: children -->
None. This module instantiates no other module.
<!-- END generated: children -->

Unclear in golden: `reset` is unused, so there is no reset. Nothing latch-dependent.
