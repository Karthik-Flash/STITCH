# ip_chnl

## Behaviour

Flit format (32-bit word): bits [30:29] give the flit type: 01 = header, 10 = tailer, 11 = idle,
00 = body. Bits [28:27] carry the virtual-channel (VC) number, 00 = VC1 to 11 = VC4. In a header flit,
bits [7:4] are the destination row and bits [3:0] the destination column. The idle word is 32'h6000_0000.

One input virtual channel: a 6-entry FIFO plus header tracking and the routing decision.

- Writes: on a rising edge of `wr_clk`, `data_in` is stored if `wr_en` is 1 and the FIFO is not full.
- Reads: the FIFO is read with the read enable from the irs sequencer (see irs). `fifo_out` is the FIFO's
  registered output word.
- `header` = 1 when `fifo_out` is a header flit; `tailer_org` = 1 when `fifo_out` is a tailer flit
  (both combinational). `tailer` = `tailer_org` delayed by one rising `rd_clk` edge.
- `header_flit`: a 32-bit register holding the header flit (register_32bit: din = `fifo_out`,
  ce = `header`, clr = `reset` OR `tailer`, clk = `rd_clk`). On each rising `rd_clk` edge it becomes
  32'h6000_0000 if `reset` or `tailer` is 1, else takes `fifo_out` if `header` is 1, else holds.
- `header_out` = `fifo_out` when `header` is 1, else `header_flit`. `req_l1`, `req_l2`, `req_l3`,
  `req_l4`, `req_c` are the XY routing decision for `header_out` at `current_address` (see
  routing_algo_mesh).
- `mux_data_out` = 32'h6000_0000 when `rd_en` is 0; when `rd_en` is 1 it is `header_flit` if `data_sel`
  is 1, else `fifo_out`. `data_out` = `mux_data_out`.
- `full_ext` = FIFO completely full (6 entries). `empty` = FIFO empty. `empty_synch_rdclk` = `empty`
  sampled on each rising `rd_clk` edge.
- `data_sel` comes from the irs sequencer.
- `nxt_reset` and `reg_out` are not driven in the golden: not checked.

## Reset

Active-high `reset`. The FIFO, `tailer` and the irs state reset as in their own specs.
`empty_synch_rdclk` becomes 1 at the next rising `rd_clk` edge. `header_flit` becomes 32'h6000_0000 at the
next rising `rd_clk` edge.
The routing requests are 0 while `reset` is 1.

## Ports

<!-- BEGIN generated: ports -->
26 ports, in this exact order:

```verilog
input reset, rd_clk, wr_clk, rd_en, wr_en;
input [31:0] data_in;
input [7:0] current_address;
output full_ext, empty_synch_rdclk, req_l1, req_l2, req_l3, req_l4, req_c;
output [31:0] data_out;
output tailer, tailer_org, nxt_reset, data_sel, header, empty;
output [31:0] fifo_out, header_flit, reg_out, mux_data_out, header_out;
```

Parameters: none.
<!-- END generated: ports -->

## Children

<!-- BEGIN generated: children -->
Must instantiate exactly these modules (ports listed in each child's own order):

- `dff_synch_reset` x 1: (d, reset, clk, q)
- `dff_synch_set` x 1: (d, set, clk, q)
- `irs` x 1: (reset, empty, rd_en, rd_clk, tailer, tailer_org, header, rd_en_out, data_sel, en1, en2, en4, en5, en6)
- `register_32bit` x 1: (din, clk, clr, ce, dout)
- `router_fifo` x 1: (reset, rd_clk, rd_en, data_in, wr_clk, wr_en, rd_add, wr_add, wr_dir, rd_dir, data_out, full_ext, full_int, empty)
- `routing_algo_mesh` x 1: (header_in, current_address, reset, req_link1, req_link2, req_core, req_link3, req_link4)
<!-- END generated: children -->

Unclear in golden: latch-dependent. `header_flit` is held by register_32bit, which in the golden is a level-sensitive
latch: transparent while `header` = 1, cleared asynchronously by `reset` OR `tailer`, `clk` ignored.
With a clocked register_32bit, `header_flit` updates one rising `rd_clk` edge later. That changes
`header_out` and `data_out` timing. Also: the output `full_ext` is the FIFO's `full_int` (6 entries);
the FIFO's own `full_ext` (4 or more) is left unconnected. `nxt_reset` and `reg_out` are undriven.
`rd_en_out` is an implicit wire. Read sequencing depends on irs's gated-clock flip-flops.
