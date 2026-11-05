# flit_mux

## Behaviour

4-to-1 multiplexer of 32-bit flits with a one-hot select. Combinational.

- `sel` = 4'b0001: `out` = `in0`.
- `sel` = 4'b0010: `out` = `in1`.
- `sel` = 4'b0100: `out` = `in2`.
- `sel` = 4'b1000: `out` = `in3`.
- Any other value of `sel` (no bit set, or more than one bit set): `out` = 32'h6000_0000, the idle flit.

## Reset

None. The module is combinational.

## Ports

<!-- BEGIN generated: ports -->
6 ports, in this exact order:

```verilog
input [3:0] sel;
input [31:0] in0;
input [31:0] in1;
input [31:0] in2;
input [31:0] in3;
output [31:0] out;
```

Parameters: none.
<!-- END generated: ports -->

## Children

<!-- BEGIN generated: children -->
None. This module instantiates no other module.
<!-- END generated: children -->
