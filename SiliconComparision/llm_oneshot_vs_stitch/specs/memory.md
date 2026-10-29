# memory

## Behaviour

8-word by 32-bit storage with separate write and read clocks.

- Write: on a rising edge of `wr_clk`, if `wr_en` is 1, the word at address `wr_add` takes `data_in`.
- Read (registered): on a rising edge of `rd_clk`: if `reset` is 1, `data_out` becomes 32'h6000_0000;
  else if `rd_en` is 1, `data_out` becomes the word at `rd_add`; otherwise `data_out` holds.

## Reset

Synchronous, active-high `reset` on the read side only: `data_out` becomes 32'h6000_0000 at the next
rising `rd_clk` edge. The stored words are not reset.

## Ports

<!-- BEGIN generated: ports -->
9 ports, in this exact order:

```verilog
input reset, rd_clk;
input [2:0] rd_add;
input wr_clk;
input [2:0] wr_add;
input [31:0] data_in;
input wr_en, rd_en;
output [31:0] data_out;
```

Parameters: none.
<!-- END generated: ports -->

## Children

<!-- BEGIN generated: children -->
None. This module instantiates no other module.
<!-- END generated: children -->

Unclear in golden: reading a word never written returns unknown. In the router, `rd_clk` and `wr_clk` are the same
clock. The golden uses blocking assignments in two separate always blocks, so a read and a write of the
same address on one edge can return the old or the new word, depending on simulator scheduling.
Nothing latch-dependent.
