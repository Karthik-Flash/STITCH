# dff_synch_reset

## Behaviour

D flip-flop with synchronous reset. On every rising edge of `clk`: if `reset` is 1, `q` becomes 0;
otherwise `q` takes the value of `d`. `q` holds between rising edges.

## Reset

Synchronous, active-high `reset`: `q` becomes 0 at the first rising `clk` edge while `reset` is 1.
Before the first rising edge `q` is unknown.

## Ports

<!-- BEGIN generated: ports -->
4 ports, in this exact order:

```verilog
input d, reset, clk;
output q;
```

Parameters: none.
<!-- END generated: ports -->

## Children

<!-- BEGIN generated: children -->
None. This module instantiates no other module.
<!-- END generated: children -->

Unclear in golden: none.
