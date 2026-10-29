# mux

## Behaviour

Registered 16-to-1 selector. On every rising edge of `clk`, `m_out` takes input t(`sel`+1): `sel` = 0
selects `t1`, and so on to `sel` = 15, which selects `t16`.

## Reset

None. `m_out` is unknown until the first rising `clk` edge.

## Ports

<!-- BEGIN generated: ports -->
19 ports, in this exact order:

```verilog
input t1, t2, t3, t4, t5, t6, t7, t8, t9, t10, t11, t12, t13, t14, t15, t16;
input [3:0] sel;
output m_out;
input clk;
```

Parameters: none.
<!-- END generated: ports -->

## Children

<!-- BEGIN generated: children -->
None. This module instantiates no other module.
<!-- END generated: children -->

Unclear in golden: no reset.
