# top_2x2_router

## Behaviour

Flit format (32-bit word): bits [30:29] give the flit type: 01 = header, 10 = tailer, 11 = idle,
00 = body. Bits [28:27] carry the virtual-channel (VC) number, 00 = VC1 to 11 = VC4. In a header flit,
bits [7:4] are the destination row and bits [3:0] the destination column. The idle word is 32'h6000_0000.

2x2 mesh of four routers (top_module) sharing `clk` and `clr`.

- Router addresses (`current_address`, row in [7:4], column in [3:0]): r1 = 8'h00, r2 = 8'h01,
  r3 = 8'h10, r4 = 8'h11.
- Link directions: link1 = towards a higher row, link2 = lower row, link3 = higher column, link4 = lower
  column.
- Links (both directions, data and the facing VC full flags): r1 link1 to r3 link2; r1 link3 to r2 link4;
  r2 link1 to r4 link2; r3 link3 to r4 link4. A router's `full_in_<link>_vck` is the neighbour's
  `full_out` for the input facing it.
- Mesh-edge inputs receive the idle word 32'h6000_0000. Mesh-edge `full_in` flags and all `full_in_core`
  flags are 0.
- `data_in_core_rN` and `data_out_core_rN` are router N's core input and output.

## Reset

`clr` (active high) resets all four routers.

## Ports

<!-- BEGIN generated: ports -->
10 ports, in this exact order:

```verilog
input clk, clr;
input [31:0] data_in_core_r1, data_in_core_r2, data_in_core_r3, data_in_core_r4;
output [31:0] data_out_core_r1, data_out_core_r2, data_out_core_r3, data_out_core_r4;
```

Parameters: none.
<!-- END generated: ports -->

## Children

<!-- BEGIN generated: children -->
Must instantiate exactly these modules (ports listed in each child's own order):

- `top_module` x 4: (data_in_link1, data_in_link2, data_in_link3, data_in_link4, data_in_core, clr, clk, full_in_link1_vc1, full_in_link1_vc2, full_in_link1_vc3, full_in_link1_vc4, full_in_link2_vc1, full_in_link2_vc2, full_in_link2_vc3, full_in_link2_vc4, full_in_link3_vc1, full_in_link3_vc2, full_in_link3_vc3, full_in_link3_vc4, full_in_link4_vc1, full_in_link4_vc2, full_in_link4_vc3, full_in_link4_vc4, full_in_core_vc1, full_in_core_vc2, full_in_core_vc3, full_in_core_vc4, current_address, data_out_link1, data_out_link2, data_out_link3, data_out_link4, data_out_core, full_out_link1_vc1, full_out_link1_vc2, full_out_link1_vc3, full_out_link1_vc4, full_out_link2_vc1, full_out_link2_vc2, full_out_link2_vc3, full_out_link2_vc4, full_out_link3_vc1, full_out_link3_vc2, full_out_link3_vc3, full_out_link3_vc4, full_out_link4_vc1, full_out_link4_vc2, full_out_link4_vc3, full_out_link4_vc4, full_out_core_vc1, full_out_core_vc2, full_out_core_vc3, full_out_core_vc4, data_out_link1_vc1, data_out_link1_vc2, data_out_link1_vc3, data_out_link1_vc4, data_out_link2_vc1, data_out_link2_vc2, data_out_link2_vc3, data_out_link2_vc4, data_out_link3_vc1, data_out_link3_vc2, data_out_link3_vc3, data_out_link3_vc4, data_out_link4_vc1, data_out_link4_vc2, data_out_link4_vc3, data_out_link4_vc4, data_out_core_vc1, data_out_core_vc2, data_out_core_vc3, data_out_core_vc4, sel_vc_link1, sel_vc_link2, sel_vc_link3, sel_vc_link4, sel_vc_core, data_out_l1, data_out_l2, data_out_l3, data_out_l4, data_out_c)
<!-- END generated: children -->

Unclear in golden: the unused mesh-edge outputs of different routers are joined on shared nets: 20 nets (4 data, 16 full
flags) have two drivers each, for example `data_out_link2` is driven by r1 and r2. Core-side full flags
are not exported, so a core can overrun a full input VC (the word is dropped, because writes are masked
when full). Inherits the latch dependence of top_module.
