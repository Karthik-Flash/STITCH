# irs

## Behaviour

Read sequencer for one input virtual channel. It decides when the channel's FIFO is read and when the
stored header flit is sent instead of the FIFO output.

- `en1` = NOT `empty`. `en2` = `rd_en`.
- `en4` (packet in progress): becomes 1 on a rising edge of `header`; it is cleared, and held at 0, while
  `reset` or `en5` is 1.
- `en5`: on a rising edge of `tailer` it takes the value of `en4`; it is held at 0 while `reset` or `en6` is 1.
- `en6`: on a rising edge of `rd_clk` it takes the value of `en5`; it is held at 0 while `reset` is 1.
- `rd_en_out` = `en1` when `en4` is 0 (before a header has been seen, read whenever the FIFO is not empty,
  so the next flit is pre-fetched to the FIFO output), and `en2` when `en4` is 1 (inside a packet, read
  only when the output side grants a read).
- `data_sel` (send the stored header): becomes 1 on a rising edge of `rd_en`. It is held at 0 while
  `reset` is 1, while an internal flag A is 1, or while an internal flag B is 1. A takes the value of
  `data_sel` on each rising edge of `rd_clk` (A is 0 while `reset` is 1). B becomes 1 on each falling edge
  of `data_sel` and is held at 0 while `reset` or `tailer` is 1. Net effect: after reset or a tailer,
  the first rising edge of `rd_en` gives a `data_sel` pulse that ends at the next rising `rd_clk` edge,
  and no further pulse occurs until `tailer` is 1 again.
- `tailer_org` is an input with no effect on any output.

## Reset

Asynchronous, active-high `reset`: `en4`, `en5`, `en6`, `data_sel` and both internal flags go to 0
immediately and stay 0 while `reset` is 1.

## Ports

14 ports, in this exact order:

```verilog
input reset, empty, rd_en, rd_clk, tailer, tailer_org, header;
output rd_en_out, data_sel, en1, en2, en4, en5, en6;
```

Parameters: none.

## Children

Must instantiate exactly these modules (ports listed in each child's own order):

- `dff_asynch_clr` x 6: (d, clr, clk, q)
