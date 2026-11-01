# Stage funnel (pipeline/funnel.py)

Per module and arm: the first failing stage (bold), or ok. Stages: compiles -> loop tb -> sign-off tb -> synthesises -> latch/loop-free -> composes. composes = golden top_3x3_router design with only this module from the arm passes the top-level sign-off tb (drop-in). it = LLM calls, sf = STITCH semantic feedback fired.

## Totals: modules reaching each stage (counts of 1)

| stage | oneshot | simloop | stitch |
|---|---|---|---|
| compiles | 1 | 1 | 0 |
| loop tb | 0 | 0 | 0 |
| sign-off tb | 0 | 0 | 0 |
| synthesises | 0 | 0 | 0 |
| latch/loop-free | 0 | 0 | 0 |
| composes | 0 | 0 | 0 |

## Totals: first failing stage

| first failing stage | oneshot | simloop | stitch |
|---|---|---|---|
| compiles | 0 | 0 | 1 |
| loop tb | 1 | 1 | 0 |
| sign-off tb | 0 | 0 | 0 |
| synthesises | 0 | 0 | 0 |
| latch/loop-free | 0 | 0 | 0 |
| composes | 0 | 0 | 0 |
| passes all | 0 | 0 | 0 |

## Modules that fail only at composes

- none

## REUSED modules: 33, results of the 2x2 study (`../reports/FUNNEL.md`)

Flags of the 2x2 final file (C compile, F tb.v, S tb_signoff.v, K struct_clean); so_clean = S and K.

| module | oneshot | simloop | stitch |
|---|---|---|---|
| allot_vc | reused (2x2): .... | reused (2x2): C... | reused (2x2): C... |
| asynch_comparator | reused (2x2): .... | reused (2x2): C..K | reused (2x2): C..K |
| demux_16 | reused (2x2): .... | reused (2x2): .... | reused (2x2): .... |
| dff_asynch_clr | reused (2x2): .... | reused (2x2): CFSK **so_clean** | reused (2x2): CFSK **so_clean** |
| dff_synch_clr | reused (2x2): CFSK **so_clean** | reused (2x2): CFSK **so_clean** | reused (2x2): CFSK **so_clean** |
| dff_synch_reset | reused (2x2): CFSK **so_clean** | reused (2x2): CFSK **so_clean** | reused (2x2): CFSK **so_clean** |
| dff_synch_set | reused (2x2): CFSK **so_clean** | reused (2x2): CFSK **so_clean** | reused (2x2): CFSK **so_clean** |
| encoder | reused (2x2): C..K | reused (2x2): CFSK **so_clean** | reused (2x2): CFSK **so_clean** |
| falling_edge_pulse_generator | reused (2x2): .... | reused (2x2): .... | reused (2x2): C..K |
| final_op_data | reused (2x2): .... | reused (2x2): CFSK **so_clean** | reused (2x2): CFSK **so_clean** |
| gray_mod6 | reused (2x2): .... | reused (2x2): C..K | reused (2x2): C..K |
| ip_chnl | reused (2x2): .... | reused (2x2): .... | reused (2x2): .... |
| ip_link | reused (2x2): C... | reused (2x2): C... | reused (2x2): .... |
| irs | reused (2x2): .... | reused (2x2): C... | reused (2x2): .... |
| jk_ff | reused (2x2): CFSK **so_clean** | reused (2x2): CFSK **so_clean** | reused (2x2): CFSK **so_clean** |
| memory | reused (2x2): CFSK **so_clean** | reused (2x2): CFSK **so_clean** | reused (2x2): CFSK **so_clean** |
| mux | reused (2x2): CFSK **so_clean** | reused (2x2): CFSK **so_clean** | reused (2x2): CFSK **so_clean** |
| op_core | reused (2x2): .... | reused (2x2): .... | reused (2x2): .... |
| op_data_path | reused (2x2): .... | reused (2x2): .... | reused (2x2): .... |
| op_link1 | reused (2x2): .... | reused (2x2): .... | reused (2x2): .... |
| op_link2 | reused (2x2): .... | reused (2x2): .... | reused (2x2): .... |
| op_link3 | reused (2x2): .... | reused (2x2): .... | reused (2x2): .... |
| op_link4 | reused (2x2): .... | reused (2x2): .... | reused (2x2): .... |
| priority_encoder | reused (2x2): CFSK **so_clean** | reused (2x2): CFSK **so_clean** | reused (2x2): CFSK **so_clean** |
| register_1bit | reused (2x2): .... | reused (2x2): CFSK **so_clean** | reused (2x2): CFSK **so_clean** |
| register_32bit | reused (2x2): CFSK **so_clean** | reused (2x2): CFSK **so_clean** | reused (2x2): CFSK **so_clean** |
| register_4bit | reused (2x2): CFSK **so_clean** | reused (2x2): CFSK **so_clean** | reused (2x2): CFSK **so_clean** |
| round_robin_req | reused (2x2): .... | reused (2x2): .... | reused (2x2): .... |
| router_fifo | reused (2x2): C..K | reused (2x2): C..K | reused (2x2): C..K |
| routing_algo_mesh | reused (2x2): .... | reused (2x2): CFSK **so_clean** | reused (2x2): CFSK **so_clean** |
| rr_arbiter | reused (2x2): .... | reused (2x2): .... | reused (2x2): .... |
| rr_comb_new | reused (2x2): .... | reused (2x2): .... | reused (2x2): C... |
| top_module | reused (2x2): .... | reused (2x2): .... | reused (2x2): .... |

## Per module

| module | oneshot | simloop | stitch |
|---|---|---|---|
| top_3x3_router | **loop tb** | **loop tb** it=6 sf=0 | **compiles** it=6 sf=1 |
