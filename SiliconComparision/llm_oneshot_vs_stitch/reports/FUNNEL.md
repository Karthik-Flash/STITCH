# Stage funnel (pipeline/funnel.py)

Per module and arm: the first failing stage (bold), or ok. Stages: compiles -> loop tb -> sign-off tb -> synthesises -> latch/loop-free -> composes. composes = golden 2x2 mesh with only this module from the arm passes the top-level sign-off tb (drop-in). it = LLM calls, sf = STITCH semantic feedback fired.

## Totals: modules reaching each stage (counts of 34)

| stage | oneshot | simloop | stitch |
|---|---|---|---|
| compiles | 13 | 21 | 21 |
| loop tb | 9 | 14 | 14 |
| sign-off tb | 9 | 14 | 14 |
| synthesises | 9 | 14 | 14 |
| latch/loop-free | 9 | 14 | 14 |
| composes | 6 | 9 | 9 |

## Totals: first failing stage

| first failing stage | oneshot | simloop | stitch |
|---|---|---|---|
| compiles | 21 | 13 | 13 |
| loop tb | 4 | 7 | 7 |
| sign-off tb | 0 | 0 | 0 |
| synthesises | 0 | 0 | 0 |
| latch/loop-free | 0 | 0 | 0 |
| composes | 3 | 5 | 5 |
| passes all | 6 | 9 | 9 |

Bonus whole-router row: not attempted: prompt alone 32,290 of 32,768 tokens (budget.py).

## Modules that fail only at composes

- dff_asynch_clr (simloop): passes every module stage but fails in the mesh; Yosys formal equivalence with golden: True
- dff_asynch_clr (stitch): passes every module stage but fails in the mesh; Yosys formal equivalence with golden: True
- dff_synch_clr (oneshot): passes every module stage but fails in the mesh; Yosys formal equivalence with golden: True
- dff_synch_clr (simloop): passes every module stage but fails in the mesh; Yosys formal equivalence with golden: True
- dff_synch_clr (stitch): passes every module stage but fails in the mesh; Yosys formal equivalence with golden: True
- dff_synch_reset (oneshot): passes every module stage but fails in the mesh; Yosys formal equivalence with golden: True
- dff_synch_reset (simloop): passes every module stage but fails in the mesh; Yosys formal equivalence with golden: True
- dff_synch_reset (stitch): passes every module stage but fails in the mesh; Yosys formal equivalence with golden: True
- memory (oneshot): passes every module stage but fails in the mesh; Yosys formal equivalence with golden: True
- memory (simloop): passes every module stage but fails in the mesh; Yosys formal equivalence with golden: True
- memory (stitch): passes every module stage but fails in the mesh; Yosys formal equivalence with golden: True
- routing_algo_mesh (simloop): passes every module stage but fails in the mesh; Yosys formal equivalence with golden: True
- routing_algo_mesh (stitch): passes every module stage but fails in the mesh; Yosys formal equivalence with golden: True

## Per module

| module | oneshot | simloop | stitch |
|---|---|---|---|
| allot_vc | **compiles** | **loop tb** it=6 sf=0 | **loop tb** it=6 sf=1 |
| asynch_comparator | **compiles** | **loop tb** it=6 sf=0 | **loop tb** it=6 sf=0 |
| demux_16 | **compiles** | **compiles** it=6 sf=0 | **compiles** it=6 sf=0 |
| dff_asynch_clr | **compiles** | **composes** it=1 sf=0 | **composes** it=1 sf=0 |
| dff_synch_clr | **composes** | **composes** it=0 sf=0 | **composes** it=0 sf=0 |
| dff_synch_reset | **composes** | **composes** it=0 sf=0 | **composes** it=0 sf=0 |
| dff_synch_set | ok | ok it=0 sf=0 | ok it=0 sf=0 |
| encoder | **loop tb** | ok it=1 sf=0 | ok it=1 sf=0 |
| falling_edge_pulse_generator | **compiles** | **compiles** it=6 sf=0 | **loop tb** it=6 sf=1 |
| final_op_data | **compiles** | ok it=1 sf=0 | ok it=1 sf=0 |
| gray_mod6 | **compiles** | **loop tb** it=6 sf=0 | **loop tb** it=6 sf=1 |
| ip_chnl | **compiles** | **compiles** it=6 sf=0 | **compiles** it=6 sf=1 |
| ip_link | **loop tb** | **loop tb** it=6 sf=0 | **compiles** it=6 sf=1 |
| irs | **compiles** | **loop tb** it=6 sf=0 | **compiles** it=6 sf=1 |
| jk_ff | ok | ok it=0 sf=0 | ok it=0 sf=0 |
| memory | **composes** | **composes** it=0 sf=0 | **composes** it=0 sf=0 |
| mux | ok | ok it=0 sf=0 | ok it=0 sf=0 |
| op_core | **compiles** | **compiles** it=6 sf=0 | **compiles** it=6 sf=1 |
| op_data_path | **compiles** | **compiles** it=6 sf=0 | **compiles** it=6 sf=0 |
| op_link1 | **compiles** | **compiles** it=6 sf=0 | **compiles** it=6 sf=1 |
| op_link2 | **compiles** | **compiles** it=6 sf=0 | **compiles** it=6 sf=1 |
| op_link3 | **compiles** | **compiles** it=6 sf=0 | **compiles** it=6 sf=1 |
| op_link4 | **compiles** | **compiles** it=6 sf=0 | **compiles** it=6 sf=0 |
| priority_encoder | ok | ok it=0 sf=0 | ok it=0 sf=0 |
| register_1bit | **compiles** | ok it=1 sf=0 | ok it=2 sf=0 |
| register_32bit | ok | ok it=0 sf=0 | ok it=0 sf=0 |
| register_4bit | ok | ok it=0 sf=0 | ok it=0 sf=0 |
| round_robin_req | **compiles** | **compiles** it=6 sf=0 | **compiles** it=6 sf=1 |
| router_fifo | **loop tb** | **loop tb** it=6 sf=0 | **loop tb** it=6 sf=0 |
| routing_algo_mesh | **compiles** | **composes** it=2 sf=0 | **composes** it=2 sf=0 |
| rr_arbiter | **compiles** | **compiles** it=6 sf=0 | **compiles** it=6 sf=0 |
| rr_comb_new | **compiles** | **compiles** it=6 sf=0 | **loop tb** it=6 sf=1 |
| top_2x2_router | **loop tb** | **loop tb** it=6 sf=0 | **loop tb** it=6 sf=1 |
| top_module | **compiles** | **compiles** it=6 sf=0 | **compiles** it=6 sf=1 |
