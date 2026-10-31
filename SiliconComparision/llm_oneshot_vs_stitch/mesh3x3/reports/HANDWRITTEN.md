# Hand-written RTL tool pass (mesh3x3; pipeline/handwritten_check.py)

golden/handwritten = the hand-written RTL as received (sanitised copy); golden/A1 = its synthesisable copy (latch_study A1: only Yosys-aborting modules fixed).

## Per root

| root | handwritten: Yosys | A1: Yosys cells | A1 latch cells | A1 check problems | A1 logic loops | Verilator errors / hard (handwritten) | hard codes |
|---|---|---|---|---|---|---|---|
| top_3x3_router | aborts: `ERROR: Multiple edge sensitive events found for this signal!` | 269370 | 6480 | 0 | 0 | 0 / 0 | - |

## Yosys front-end warnings (handwritten)

- top_3x3_router: 18 implicitly declared nets: allot_vc.v: mux_out3; ip_chnl.v: rd_en_out; mesh_router3x3.v: data_out_link1_r7; mesh_router3x3.v: data_out_link1_r9; mesh_router3x3.v: data_out_link2_r1; mesh_router3x3.v: data_out_link2_r3; mesh_router3x3.v: data_out_link3_r3; mesh_router3x3.v: data_out_link3_r6; mesh_router3x3.v: data_out_link3_r9; mesh_router3x3.v: data_out_link4_r1; mesh_router3x3.v: data_out_link4_r7; op_data_path.v: gnt_or_c; op_data_path.v: gnt_or_l1; op_data_path.v: gnt_or_l2; op_data_path.v: gnt_or_l3; op_data_path.v: gnt_or_l4; router_fifo.v: ren_int; router_fifo.v: wen_int
- top_3x3_router: 9 cell ports resized: top_3x3_router.r1.data_out_link2 1->32; top_3x3_router.r1.data_out_link4 1->32; top_3x3_router.r3.data_out_link2 1->32; top_3x3_router.r3.data_out_link3 1->32; top_3x3_router.r6.data_out_link3 1->32; top_3x3_router.r7.data_out_link1 1->32; top_3x3_router.r7.data_out_link4 1->32; top_3x3_router.r9.data_out_link1 1->32; top_3x3_router.r9.data_out_link3 1->32

## Per module

Latch cells per module: modules.csv own_storage (`$dlatch`), golden/A1 after proc.

| module | file | children | kind | own storage | clock ports | reset ports | latch-enable ports | clocking | clock sources |
|---|---|---|---|---|---|---|---|---|---|
| dff_synch_reset | dff_synch_reset.v | - | sequential | $sdffx1 | clk | reset | - | system clock | clk |
| dff_synch_set | dff_synch_set.v | - | sequential | $sdffx1 | clk | set | - | system clock | clk |
| dff_asynch_clr | dff_asynch_clr.v | - | sequential | $adffx1 | clk | clr | - | system clock | clk |
| irs | IRS.v | dff_asynch_clrx6 | sequential | - | rd_en;rd_clk;tailer;header;en2 | reset | - | gated | en2, header, internal net, rd_clk, tailer |
| register_32bit | register_32bit.v | - | sequential | $adlatchx3 | - | clr | ce | data-clocked | ce |
| asynch_comparator | asynch_comparator.v | - | combinational | - | - | - | - | none (combinational) | - |
| jk_ff | jk_ff.v | - | sequential | $sdffx4 | clk | reset | - | system clock | clk |
| gray_mod6 | gray_mod6.v | jk_ffx4 | sequential | - | clk | reset | - | gated | clk, internal net |
| memory | memory.v | - | sequential | $memrdx1, $memwr_v2x1, $sdffx1 | rd_clk;wr_clk | reset | - | system clock | rd_clk, wr_clk |
| router_fifo | router_fifo.v | asynch_comparatorx1, gray_mod6x2, memoryx1 | sequential | - | rd_clk;wr_clk | reset | - | system clock | child gray_mod6, rd_clk, wr_clk |
| routing_algo_mesh | routing_algo_mesh.v | - | combinational | - | - | - | - | none (combinational) | - |
| ip_chnl | ip_chnl.v | dff_synch_resetx1, dff_synch_setx1, irsx1, register_32bitx1, router_fifox1, routing_algo_meshx1 | sequential | - | rd_clk;wr_clk;rd_en;tailer;header | reset | header | data-clocked | header, rd_clk, rd_en, tailer, wr_clk |
| ip_link | ip_link.v | ip_chnlx4 | sequential | - | rd_clk;wr_clk;tailer_vc1;tailer_vc2;tailer_vc3;tailer_vc4 | reset | - | gated | internal net, rd_clk, tailer_vc1, tailer_vc2, tailer_vc3, tailer_vc4, wr_clk |
| mux | mux.v | - | sequential | $dffx1 | clk | - | - | system clock | clk |
| register_1bit | register_1bit.v | - | sequential | $adffx1 | clk | reset | - | system clock | clk |
| register_4bit | register_4bit.v | - | sequential | $adlatchx1 | - | clr | ce | data-clocked | ce |
| allot_vc | allot_vc.v | muxx4, register_1bitx4, register_4bitx4 | sequential | - | rd_clk | reset | ce_b1;ce_b2;ce_b3;ce_b4 | data-clocked | ce_b1, ce_b2, ce_b3, ce_b4, rd_clk |
| demux_16 | demux_16.v | - | combinational | - | - | - | - | none (combinational) | - |
| encoder | encoder.v | - | combinational | - | - | - | - | none (combinational) | - |
| falling_edge_pulse_generator | falling_edge_pulse_generator.v | dff_asynch_clrx2 | sequential | - | clk | reset | - | gated | clk, internal net |
| priority_encoder | priority_encoder.v | - | sequential | $dffx4 | clk | - | - | system clock | clk |
| rr_arbiter | rr_arbiter.v | dff_asynch_clrx5, falling_edge_pulse_generatorx4, priority_encoderx4 | sequential | - | clk | reset | - | gated | clk, internal net |
| round_robin_req | round_robin_req.v | dff_asynch_clrx16, dff_synch_resetx16, rr_arbiterx5 | sequential | - | rd_clk;g1_int;g2_int;g3_int;g4_int;g5_int;g6_int;g7_int;g8_int;g9_int;g10_int;g11_int;g12_int;g13_int;g14_int;g15_int;g16_int | reset;nreq_1;nreq_2;nreq_3;nreq_4;nreq_5;nreq_6;nreq_7;nreq_8;nreq_9;nreq_10;nreq_11;nreq_12;nreq_13;nreq_14;nreq_15;nreq_16 | - | data-clocked | g10_int, g11_int, g12_int, g13_int, g14_int, g15_int, g16_int, g1_int, g2_int, g3_int, g4_int, g5_int, g6_int, g7_int, g8_int, g9_int, rd_clk |
| dff_synch_clr | dff_synch_clr.v | - | sequential | $sdffx1 | clk | clr | - | system clock | clk |
| rr_comb_new | rr_comb_new.v | dff_synch_clrx4 | sequential | - | clk | reset | - | system clock | clk |
| op_core | op_core.v | allot_vcx1, demux_16x4, encoderx1, round_robin_reqx1, rr_comb_newx1 | sequential | - | rd_clk | reset | - | gated | internal net, rd_clk |
| final_op_data | fop.v | - | combinational | - | - | - | - | none (combinational) | - |
| op_data_path | op_data_path.v | final_op_datax5 | combinational | - | - | - | - | none (combinational) | - |
| op_link1 | op_link1.v | allot_vcx1, demux_16x4, encoderx1, round_robin_reqx1, rr_comb_newx1 | sequential | - | rd_clk | reset | - | gated | internal net, rd_clk |
| op_link2 | op_link2.v | allot_vcx1, demux_16x4, encoderx1, round_robin_reqx1, rr_comb_newx1 | sequential | - | rd_clk | reset | - | gated | internal net, rd_clk |
| op_link3 | op_link3.v | allot_vcx1, demux_16x4, encoderx1, round_robin_reqx1, rr_comb_newx1 | sequential | - | rd_clk | reset | - | gated | internal net, rd_clk |
| op_link4 | op_link4.v | allot_vcx1, demux_16x4, encoderx1, round_robin_reqx1, rr_comb_newx1 | sequential | - | rd_clk | reset | - | gated | internal net, rd_clk |
| top_module | top_module.v | ip_linkx5, op_corex1, op_data_pathx1, op_link1x1, op_link2x1, op_link3x1, op_link4x1 | sequential | - | clk | clr | - | gated | clk, internal net |
| top_3x3_router | mesh_router3x3.v | top_modulex9 | sequential | - | clk | clr | - | system clock | child top_module, clk |
