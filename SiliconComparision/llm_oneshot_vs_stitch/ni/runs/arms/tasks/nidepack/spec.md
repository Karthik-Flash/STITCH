# nidepack

## Behaviour

Network-interface depacketiser side: depack rebuilds words from incoming flits and writes them into a FIFO;
the core reads the FIFO.

Connections (by port name of each child):

- `depack`: `flit`, `wr_clk` and `reset` are nidepack's inputs of the same name; its `data_out` is the FIFO's
  `data_in` and its `wr_en` is the FIFO's `wr_en`. Its `c_rd` is left open.
- `router_fifo` (6-entry FIFO): `reset`, `rd_clk`, `rd_en` and `wr_clk` are nidepack's inputs of the same name;
  its `data_out` is nidepack's output `data_out`. Its `rd_add`, `wr_add`, `rd_dir`, `wr_dir`, `full_ext`,
  `full_int` and `empty` are not used outside nidepack.

## Reset

`reset` (active high) goes to both children: synchronous in each, at its own clock edges.

## Ports

6 ports, in this exact order:

```verilog
input [31:0] flit;
input rd_clk, wr_clk, rd_en, reset;
output [31:0] data_out;
```

Parameters: none.

## Children

Must instantiate exactly these modules (ports listed in each child's own order):

- `depack` x 1: (flit, wr_clk, reset, data_out, wr_en, c_rd)
- `router_fifo` x 1: (reset, rd_clk, rd_en, data_in, wr_clk, wr_en, rd_add, wr_add, wr_dir, rd_dir, data_out, full_ext, full_int, empty)
