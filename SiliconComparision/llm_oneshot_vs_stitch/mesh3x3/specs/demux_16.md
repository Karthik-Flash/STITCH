# demux_16

## Behaviour

Combinational 1-to-16 demultiplexer. Output op(`sel`+1) equals `ip`: `sel` = 0 drives `op1`, up to
`sel` = 15 for `op16`. All other outputs are 0.

## Reset

None. The module is combinational.

## Ports

<!-- BEGIN generated: ports -->
18 ports, in this exact order:

```verilog
input ip;
input [3:0] sel;
output op1, op2, op3, op4, op5, op6, op7, op8, op9, op10, op11, op12, op13, op14, op15, op16;
```

Parameters: none.
<!-- END generated: ports -->

## Children

<!-- BEGIN generated: children -->
None. This module instantiates no other module.
<!-- END generated: children -->

Unclear in golden: none.
