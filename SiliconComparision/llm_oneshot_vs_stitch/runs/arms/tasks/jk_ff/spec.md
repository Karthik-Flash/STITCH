# jk_ff

## Behaviour

JK flip-flop with enable and synchronous reset. On every rising edge of `clk`:
- if `reset` is 1: `q` = 0 and `qbar` = 1;
- else if `en` is 1: j,k = 00 holds, 01 gives `q` = 0, 10 gives `q` = 1, 11 toggles `q`;
- else hold.
`qbar` is always the complement of `q` after the first rising edge.

## Reset

Synchronous, active-high `reset` (`q` = 0, `qbar` = 1). Before the first rising edge both outputs are
unknown.

## Ports

7 ports, in this exact order:

```verilog
input j, k, reset, en, clk;
output q, qbar;
```

Parameters: none.

## Children

None. This module instantiates no other module.
