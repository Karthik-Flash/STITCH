# asynch_comparator

## Behaviour

Combinational full/empty detector for a 6-entry FIFO. `rd_ptr` and `wr_ptr` step through the 6-state
Gray sequence 000, 001, 011, 010, 110, 100 (positions 0 to 5) and then wrap to 000. `rd_dir` and `wr_dir`
toggle on each wrap.

- `empty` = 1 when `rd_ptr` equals `wr_ptr` and `rd_dir` equals `wr_dir`; else 0.
- `full_int` = 1 when `rd_ptr` equals `wr_ptr` and `rd_dir` differs from `wr_dir`; else 0.
- `full_ext` = 1 when the FIFO holds 4 or more entries; else 0. The occupancy is
  pos(`wr_ptr`) - pos(`rd_ptr`) when the dir bits are equal, and pos(`wr_ptr`) - pos(`rd_ptr`) + 6 when
  they differ. For `full_ext`, the codes 101 and 111 (not in the sequence) count as position 5 (100).

## Reset

None. The module is combinational.

## Ports

<!-- BEGIN generated: ports -->
7 ports, in this exact order:

```verilog
input [2:0] rd_ptr, wr_ptr;
input rd_dir, wr_dir;
output full_ext, full_int, empty;
```

Parameters: none.
<!-- END generated: ports -->

## Children

<!-- BEGIN generated: children -->
None. This module instantiates no other module.
<!-- END generated: children -->

Unclear in golden: none. Codes 101 and 111 never occur from the counter; `empty` and `full_int` compare the raw codes,
`full_ext` treats them as 100.
