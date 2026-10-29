# op_data_path

## Behaviour

Flit format (32-bit word): bits [30:29] give the flit type: 01 = header, 10 = tailer, 11 = idle,
00 = body. Bits [28:27] carry the virtual-channel (VC) number, 00 = VC1 to 11 = VC4. In a header flit,
bits [7:4] are the destination row and bits [3:0] the destination column. The idle word is 32'h6000_0000.

Combinational output crossbar for the five output ports of one router.

- For each output port P, 16 candidate words are the per-VC data outputs of the four other input ports,
  in slot order 4 x (source position) + (VC - 1), with source positions:
  - link1: link2, link3, link4, core
  - link2: link1, link3, link4, core
  - link3: link1, link2, link4, core
  - link4: link1, link2, link3, core
  - core: link1, link2, link3, link4
  (`data_from_<src>_ch<k>` is source <src> VC k.)
- `data_out_l1` to `data_out_l4` and `data_out_c` = the candidate selected by `sel_vc_<P>` (4-bit slot
  index).
- `data_out_<P>` = that word formatted by final_op_data, with `gnt_or` = OR of `gnt_vc_<P>_ch1` to `_ch4`
  and `vc_id` = number of the granted output VC (ch1 = 00, ch2 = 01, ch3 = 10, ch4 = 11). In code:
  `vc_id[1]` = ch3 OR ch4, `vc_id[0]` = ch2 OR ch4.
- `rd_clk1` to `rd_clk4` and `rd_clk_core` have no effect.

## Reset

None. The module is combinational.

## Ports

<!-- BEGIN generated: ports -->
60 ports, in this exact order:

```verilog
input [31:0] data_from_link1_ch1, data_from_link1_ch2, data_from_link1_ch3, data_from_link1_ch4,
             data_from_link2_ch1, data_from_link2_ch2, data_from_link2_ch3, data_from_link2_ch4,
             data_from_link3_ch1, data_from_link3_ch2, data_from_link3_ch3, data_from_link3_ch4,
             data_from_link4_ch1, data_from_link4_ch2, data_from_link4_ch3, data_from_link4_ch4,
             data_from_core_ch1, data_from_core_ch2, data_from_core_ch3, data_from_core_ch4;
input [3:0] sel_vc_link1, sel_vc_link2, sel_vc_link3, sel_vc_link4, sel_vc_core;
input gnt_vc_link1_ch1, gnt_vc_link1_ch2, gnt_vc_link1_ch3, gnt_vc_link1_ch4, gnt_vc_link2_ch1,
      gnt_vc_link2_ch2, gnt_vc_link2_ch3, gnt_vc_link2_ch4, gnt_vc_link3_ch1, gnt_vc_link3_ch2,
      gnt_vc_link3_ch3, gnt_vc_link3_ch4, gnt_vc_link4_ch1, gnt_vc_link4_ch2, gnt_vc_link4_ch3,
      gnt_vc_link4_ch4, gnt_vc_core_ch1, gnt_vc_core_ch2, gnt_vc_core_ch3, gnt_vc_core_ch4;
output [31:0] data_out_link1, data_out_link2, data_out_link3, data_out_link4, data_out_core, data_out_l1,
              data_out_l2, data_out_l3, data_out_l4, data_out_c;
input rd_clk1, rd_clk2, rd_clk3, rd_clk4, rd_clk_core;
```

Parameters: none.
<!-- END generated: ports -->

## Children

<!-- BEGIN generated: children -->
Must instantiate exactly these modules (ports listed in each child's own order):

- `final_op_data` x 5: (data_in, vc_id, gnt_or, data_out)
<!-- END generated: children -->

Unclear in golden: `rd_clk1` to `rd_clk4` and `rd_clk_core` are unused. Nothing latch-dependent.
