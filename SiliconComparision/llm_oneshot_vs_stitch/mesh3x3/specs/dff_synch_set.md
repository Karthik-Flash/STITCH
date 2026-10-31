# dff_synch_set

## Behaviour

D flip-flop with synchronous set. On every rising edge of `clk`: if `set` is 1, `q` becomes 1;
otherwise `q` takes the value of `d`. `q` holds between rising edges.

## Reset

Synchronous, active-high `set`: `q` becomes 1 at the first rising `clk` edge while `set` is 1.
Before the first rising edge `q` is unknown.

## Ports

<!-- BEGIN generated: ports -->
4 ports, in this exact order:

```verilog
input d, set, clk;
output q;
```

Parameters: none.
<!-- END generated: ports -->

## Children

<!-- BEGIN generated: children -->
None. This module instantiates no other module.
<!-- END generated: children -->

Unclear in golden: none.
