# router_fifo

## Behaviour

6-entry FIFO of 32-bit words with separate write and read clocks.

- Write: on a rising edge of `wr_clk`, if `wr_en` is 1 and the FIFO is not full (`full_int` = 0),
  `data_in` is stored and the write pointer advances.
- Read: on a rising edge of `rd_clk`, if `rd_en` is 1 and the FIFO is not empty (`empty` = 0),
  `data_out` (registered) takes the oldest entry and the read pointer advances. Otherwise `data_out` holds.
- `wr_add` and `rd_add` are the current write and read pointers. Both step through the Gray sequence 000,
  001, 011, 010, 110, 100. `wr_dir` and `rd_dir` toggle each time the matching pointer wraps.
- `empty` = no entries; `full_int` = 6 entries; `full_ext` = 4 or more entries. All three are
  combinational in the pointers.

## Reset

Synchronous, active-high `reset`: both pointers return to 000 at their clock's next rising edge, and
`data_out` becomes 32'h6000_0000 at the next rising `rd_clk` edge. Stored words are not cleared. Each dir
bit inherits gray_mod6's caveat.

## Ports

<!-- BEGIN generated: ports -->
14 ports, in this exact order:

```verilog
input reset, rd_clk, rd_en;
input [31:0] data_in;
input wr_clk, wr_en;
output [2:0] rd_add, wr_add;
output wr_dir, rd_dir;
output [31:0] data_out;
output full_ext, full_int, empty;
```

Parameters: none.
<!-- END generated: ports -->

## Children

<!-- BEGIN generated: children -->
Must instantiate exactly these modules (ports listed in each child's own order):

- `asynch_comparator` x 1: (rd_ptr, wr_ptr, rd_dir, wr_dir, full_ext, full_int, empty)
- `gray_mod6` x 2: (clk, reset, en, gray_out, dir)
- `memory` x 1: (reset, rd_clk, rd_add, wr_clk, wr_add, data_in, wr_en, rd_en, data_out)
<!-- END generated: children -->

Unclear in golden: inherits gray_mod6's dir-reset caveat and memory's same-edge read/write ordering. In the golden,
`wen_int` and `ren_int` are implicit (undeclared) wires. Nothing latch-dependent.
