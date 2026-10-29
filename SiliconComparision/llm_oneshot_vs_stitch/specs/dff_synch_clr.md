# dff_synch_clr

## Behaviour

D flip-flop with synchronous clear. On every rising edge of `clk`: if `clr` is 1, `q` becomes 0;
otherwise `q` takes the value of `d`. `q` holds between rising edges.

## Reset

Synchronous, active-high `clr`: `q` becomes 0 at the first rising `clk` edge while `clr` is 1.

## Ports

<!-- BEGIN generated: ports -->
4 ports, in this exact order:

```verilog
input d, clr, clk;
output q;
```

Parameters: none.
<!-- END generated: ports -->

## Children

<!-- BEGIN generated: children -->
None. This module instantiates no other module.
<!-- END generated: children -->

Unclear in golden: none.
