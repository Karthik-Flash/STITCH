# routing_algo_mesh

## Behaviour

Combinational XY routing decision for one flit.

- The flit is a header when `header_in[29]` = 1 and `header_in[30]` = 0.
- If `reset` is 1, or the flit is not a header, all five request outputs are 0.
- Otherwise exactly one output is 1. Compare the destination row `header_in[7:4]` with the current row
  `current_address[7:4]`: greater gives `req_link1`, smaller gives `req_link2`. If the rows are equal,
  compare the destination column `header_in[3:0]` with `current_address[3:0]`: greater gives `req_link3`,
  smaller gives `req_link4`, equal gives `req_core`. All comparisons are unsigned.

## Reset

`reset` = 1 forces all outputs to 0 (combinational).

## Ports

8 ports, in this exact order:

```verilog
input [31:0] header_in;
input [7:0] current_address;
input reset;
output req_link1, req_link2, req_core, req_link3, req_link4;
```

Parameters: none.

## Children

None. This module instantiates no other module.
