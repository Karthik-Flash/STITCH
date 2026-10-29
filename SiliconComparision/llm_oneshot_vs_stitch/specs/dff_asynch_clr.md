# dff_asynch_clr

## Behaviour

D flip-flop with asynchronous clear. On every rising edge of `clk`, `q` takes the value of `d`.
While `clr` is 1, `q` is 0 regardless of `clk`.

## Reset

Asynchronous, active-high `clr`: `q` goes to 0 as soon as `clr` rises and stays 0 while `clr` is 1.

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

Unclear in golden: none in this module. Its parents drive `clk` from data or control signals (grants, header/tailer
flags), not only from the system clock.
