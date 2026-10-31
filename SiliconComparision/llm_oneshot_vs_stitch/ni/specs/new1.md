# new1

## Behaviour

Network-interface packetiser side: the core writes 32-bit words into a FIFO, and the packetiser reads them and
sends each as a packet of flits on `niout`.

Connections (by port name of each child):

- `router_fifo` (6-entry FIFO): `reset`, `rd_clk`, `data_in`, `wr_clk` and `wr_en` are new1's inputs of the same
  name; its `rd_en` is rp1's `rd_en`; its `data_out` feeds rp1's `data_in`. Its `full_ext` (4 or more entries)
  drives new1's output `full_int`, and its `full_int` (6 entries, full) drives new1's output `empty`. Its
  `empty`, `rd_add`, `wr_add`, `rd_dir` and `wr_dir` are not used.
- `rp1` (packetiser): `dest`, `source`, `rd_clk`, `wr_clk`, `wr_en` and `reset` are new1's inputs of the same
  name; its `niout` and `wr_o` are new1's outputs of the same name.

So `wr_en` both writes `data_in` into the FIFO (rising `wr_clk`) and starts a packet in rp1 (sampled on rising
`rd_clk`). rp1 pops the FIFO through `rd_en` while it sends the packet.

## Reset

`reset` (active high) goes to both children: synchronous in each, at its own clock edges.

## Ports

<!-- BEGIN generated: ports -->
11 ports, in this exact order:

```verilog
input rd_clk, wr_clk;
input [31:0] data_in;
input reset, wr_en;
input [7:0] dest, source;
output empty, full_int;
output [31:0] niout;
output wr_o;
```

Parameters: none.
<!-- END generated: ports -->

## Children

<!-- BEGIN generated: children -->
Must instantiate exactly these modules (ports listed in each child's own order):

- `router_fifo` x 1: (reset, rd_clk, rd_en, data_in, wr_clk, wr_en, rd_add, wr_add, wr_dir, rd_dir, data_out, full_ext, full_int, empty)
- `rp1` x 1: (data_in, dest, source, rd_clk, wr_clk, wr_en, reset, niout, rd_en, wr_o)
<!-- END generated: children -->

Unclear in golden: router_fifo is instantiated by position with one connection fewer than its 14 ports, so every
connection after `data_out` lands one port early: new1's `full_int` is the FIFO's `full_ext` and new1's `empty` is
the FIFO's `full_int`; the FIFO's `empty` is left open (phase3/designs/SANITISATION.md, item 3). The names of the two
outputs therefore do not match their meaning. rp1 samples the FIFO's `data_out` on the same rising `rd_clk` edge on
which the FIFO updates it (both use blocking assignments), so which word rp1 sends depends on simulator
scheduling. Inherits rp1's one-packet-per-power-up behaviour and router_fifo's caveats.
