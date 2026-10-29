# dff_asynch_clr

## Behaviour

D flip-flop with asynchronous clear. On every rising edge of `clk`, `q` takes the value of `d`.
While `clr` is 1, `q` is 0 regardless of `clk`.

## Reset

Asynchronous, active-high `clr`: `q` goes to 0 as soon as `clr` rises and stays 0 while `clr` is 1.

## Ports

4 ports, in this exact order:

```verilog
input d, clr, clk;
output q;
```

Parameters: none.

## Children

None. This module instantiates no other module.
