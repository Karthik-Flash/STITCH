# rr_arbiter

## Behaviour

Round-robin arbiter for 4 requesters, numbered 0 to 3. Requester i asks for a grant when `req[i]` = 1.

The arbiter remembers the number of the requester it granted last (the "last" requester). The grant is
combinational, from `req` and the last requester:

- `gnt` is one-hot: `gnt[i]` = 1 means requester i is granted. `gnt` = 0 when no requester asks.
- Priority starts at the requester after the last one and goes round: if the last requester is L, the order
  is L+1, L+2, L+3, L (numbers taken modulo 4). The first requester in this order with `req` = 1 is granted.

The last requester changes only at a rising `clk` edge where `advance` = 1 and `gnt` is not 0: it becomes
the requester granted at that edge. Otherwise it keeps its value. `advance` = 1 with `gnt` = 0 changes nothing.

So a requester that keeps asking is granted within 4 edges with `advance` = 1 and a grant.

## Reset

Synchronous, active-high `reset`: at a rising `clk` edge with `reset` = 1 the last requester becomes 3, so
the priority order after reset is 0, 1, 2, 3. `advance` at that edge is ignored.

## Ports

<!-- BEGIN generated: ports -->
5 ports, in this exact order:

```verilog
input clk;
input reset;
input [3:0] req;
input advance;
output [3:0] gnt;
```

Parameters: none.
<!-- END generated: ports -->

## Children

<!-- BEGIN generated: children -->
None. This module instantiates no other module.
<!-- END generated: children -->
