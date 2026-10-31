# ip_link

## Behaviour

Flit format (32-bit word): bits [30:29] give the flit type: 01 = header, 10 = tailer, 11 = idle,
00 = body. Bits [28:27] carry the virtual-channel (VC) number, 00 = VC1 to 11 = VC4. In a header flit,
bits [7:4] are the destination row and bits [3:0] the destination column. The idle word is 32'h6000_0000.

One router input port with four virtual channels.

- Each `data_in` word that is not idle (bits [30:29] not equal to 11) is written into the VC chosen by
  `data_in[28:27]` (00 = VC1, 01 = VC2, 10 = VC3, 11 = VC4). The write happens on each rising `wr_clk`
  edge while the word is present.
- The read enable of VC k is the OR of `rd_en(16(k-1)+1)` to `rd_en(16k)`: VC1 uses `rd_en1` to
  `rd_en16`, and so on to VC4 with `rd_en49` to `rd_en64`.
- `rok_vck` = NOT (VC k's `empty_synch_rdclk`): VC k holds data, registered on `rd_clk`.
- `data_out_vck`, `full_vck`, `req_l1_vck` to `req_l4_vck`, `req_c_vck` and `tailer_vck` are VC k's
  `data_out`, `full_ext`, routing requests and `tailer` (see ip_chnl).

## Reset

Active-high `reset`, passed to all four channels (see ip_chnl).

## Ports

<!-- BEGIN generated: ports -->
105 ports, in this exact order:

```verilog
input reset, rd_clk, wr_clk;
input [31:0] data_in;
input [7:0] current_address;
output [31:0] data_out_vc1, data_out_vc2, data_out_vc3, data_out_vc4;
output full_vc1, full_vc2, full_vc3, full_vc4, req_l1_vc1, req_l1_vc2, req_l1_vc3, req_l1_vc4, req_l2_vc1,
       req_l2_vc2, req_l2_vc3, req_l2_vc4, req_l3_vc1, req_l3_vc2, req_l3_vc3, req_l3_vc4, req_l4_vc1,
       req_l4_vc2, req_l4_vc3, req_l4_vc4, req_c_vc1, req_c_vc2, req_c_vc3, req_c_vc4;
input rd_en1, rd_en2, rd_en3, rd_en4, rd_en5, rd_en6, rd_en7, rd_en8, rd_en9, rd_en10, rd_en11, rd_en12,
      rd_en13, rd_en14, rd_en15, rd_en16, rd_en17, rd_en18, rd_en19, rd_en20, rd_en21, rd_en22, rd_en23,
      rd_en24, rd_en25, rd_en26, rd_en27, rd_en28, rd_en29, rd_en30, rd_en31, rd_en32, rd_en33, rd_en34,
      rd_en35, rd_en36, rd_en37, rd_en38, rd_en39, rd_en40, rd_en41, rd_en42, rd_en43, rd_en44, rd_en45,
      rd_en46, rd_en47, rd_en48, rd_en49, rd_en50, rd_en51, rd_en52, rd_en53, rd_en54, rd_en55, rd_en56,
      rd_en57, rd_en58, rd_en59, rd_en60, rd_en61, rd_en62, rd_en63, rd_en64;
output tailer_vc1, tailer_vc2, tailer_vc3, tailer_vc4, rok_vc1, rok_vc2, rok_vc3, rok_vc4;
```

Parameters: none.
<!-- END generated: ports -->

## Children

<!-- BEGIN generated: children -->
Must instantiate exactly these modules (ports listed in each child's own order):

- `ip_chnl` x 4: (reset, rd_clk, wr_clk, rd_en, wr_en, data_in, current_address, full_ext, empty_synch_rdclk, req_l1, req_l2, req_l3, req_l4, req_c, data_out, tailer, tailer_org, nxt_reset, data_sel, header, empty, fifo_out, header_flit, reg_out, mux_data_out, header_out)
<!-- END generated: children -->

Unclear in golden: inherits ip_chnl's latch-dependent `header_flit`. There is no valid/handshake signal: a non-idle word
held on `data_in` for N `wr_clk` edges is written N times.
