# STITCH vs simulation-only retry (pipeline/stitch_vs_retry.py)

Flags: C compile, F tb.v, S tb_signoff.v, K struct_clean (local re-evaluation of the final files). it = LLM calls, sf = STITCH semantic feedback fired. Directive codes: `iteration:codes` fed back after that iteration (stitch arm).

## Outcome classes

| class | count | modules |
|---|---|---|
| already_clean | 9 | dff_synch_clr, dff_synch_reset, dff_synch_set, jk_ff, memory, mux, priority_encoder, register_32bit, register_4bit |
| both_fixed | 5 | dff_asynch_clr, encoder, final_op_data, register_1bit, routing_algo_mesh |
| stitch_only | 0 | - |
| retry_only | 0 | - |
| neither | 20 | allot_vc, asynch_comparator, demux_16, falling_edge_pulse_generator, gray_mod6, ip_chnl, ip_link, irs, op_core, op_data_path, op_link1, op_link2, op_link3, op_link4, round_robin_req, router_fifo, rr_arbiter, rr_comb_new, top_2x2_router, top_module |

## Prompt equivalence (stitch runs with sf=0 and at least one call in both arms)

4 of 11 such modules got byte-identical prompts in both arms: dff_asynch_clr, encoder, final_op_data, routing_algo_mesh. These modules cannot distinguish the arms.

- asynch_comparator: first differing prompt: iteration 2
- demux_16: first differing prompt: iteration 2
- op_data_path: first differing prompt: iteration 2
- op_link4: first differing prompt: iteration 3
- register_1bit: identical while both ran; calls differ (1 vs 2)
- router_fifo: first differing prompt: iteration 2
- rr_arbiter: first differing prompt: iteration 2

## Sampling

The first LLM call of the two arms gets the same prompt (feedback-first protocol). In 25 modules both arms made that call with a byte-identical prompt; in 6 of them the two answers differ (ip_link, irs, op_link1, register_1bit, router_fifo, top_module). Generation used temperature 0.1 with no seed, so a difference between the arms can come from sampling alone. Below, each gain or regression names the first iteration where the arms' RTL differs and whether the prompts differed there.

## Gains (stitch has the flag, simloop does not)

- falling_edge_pulse_generator: compile per iteration (0 = one-shot): simloop `.CCCCC.`, stitch `.CCCCCC`; arms first produce different RTL at iteration 6: different prompt; stitch carried: directives UNUSEDSIGNAL; escalated
- falling_edge_pulse_generator: struct_clean (K) per iteration (0 = one-shot): simloop `.KKKKK.`, stitch `.KKKKKK`; arms first produce different RTL at iteration 6: different prompt; stitch carried: directives UNUSEDSIGNAL; escalated
- rr_comb_new: compile per iteration (0 = one-shot): simloop `.CC....`, stitch `.C....C`; arms first produce different RTL at iteration 2: identical prompt, different sample (not attributable to STITCH)
- top_2x2_router: struct_clean (K) per iteration (0 = one-shot): simloop `.......`, stitch `..KKKKK`; arms first produce different RTL at iteration 2: different prompt; stitch carried: directives PINMISSING, WIDTHEXPAND, WIDTHTRUNC; escalated

## Regressions (simloop has the flag, stitch does not)

- ip_link: compile per iteration (0 = one-shot): simloop `CCCCCCC`, stitch `CCC....`; arms first produce different RTL at iteration 1: identical prompt, different sample (not attributable to STITCH)
- irs: compile per iteration (0 = one-shot): simloop `.....CC`, stitch `.......`; arms first produce different RTL at iteration 1: identical prompt, different sample (not attributable to STITCH)

## STITCH fired (sf=1) and the final still fails: 14 modules

Audit class (reports/FAILURE_AUDIT.md): LLM_BUG 14

allot_vc (LLM_BUG), falling_edge_pulse_generator (LLM_BUG), gray_mod6 (LLM_BUG), ip_chnl (LLM_BUG), ip_link (LLM_BUG), irs (LLM_BUG), op_core (LLM_BUG), op_link1 (LLM_BUG), op_link2 (LLM_BUG), op_link3 (LLM_BUG), round_robin_req (LLM_BUG), rr_comb_new (LLM_BUG), top_2x2_router (LLM_BUG), top_module (LLM_BUG)

## Where STITCH helped

Final flag better than the simulation-only loop: falling_edge_pulse_generator, rr_comb_new, top_2x2_router. Of these, the arms diverged after a different (STITCH) prompt in: falling_edge_pulse_generator, top_2x2_router; after an identical prompt (sampling) in: rr_comb_new. No module reached so_clean under STITCH only (0).

## Where it did not

STITCH fired but the final still fails (14): allot_vc, falling_edge_pulse_generator, gray_mod6, ip_chnl, ip_link, irs, op_core, op_link1, op_link2, op_link3, round_robin_req, rr_comb_new, top_2x2_router, top_module. Never fired and failed in both arms: asynch_comparator, demux_16, op_data_path, op_link4, router_fifo, rr_arbiter.

## Where it hurt

Final flag worse than the simulation-only loop: ip_link, irs. Arms diverged after a different (STITCH) prompt in: none; after an identical prompt (sampling) in: ip_link, irs.

## Per module

| module | one-shot | simloop final | stitch final | stitch directive codes per iteration | outcome |
|---|---|---|---|---|---|
| allot_vc | .... | C... it=6 | C... it=6 sf=1 | 3:WIDTHEXPAND,WIDTHTRUNC | neither |
| asynch_comparator | .... | C..K it=6 | C..K it=6 sf=0 | - | neither |
| demux_16 | .... | .... it=6 | .... it=6 sf=0 | - | neither |
| dff_asynch_clr | .... | CFSK it=1 | CFSK it=1 sf=0 | - | both_fixed |
| dff_synch_clr | CFSK | CFSK it=0 | CFSK it=0 sf=0 | - | already_clean |
| dff_synch_reset | CFSK | CFSK it=0 | CFSK it=0 sf=0 | - | already_clean |
| dff_synch_set | CFSK | CFSK it=0 | CFSK it=0 sf=0 | - | already_clean |
| encoder | C..K | CFSK it=1 | CFSK it=1 sf=0 | - | both_fixed |
| falling_edge_pulse_generator | .... | .... it=6 | C..K it=6 sf=1 | 2:UNUSEDSIGNAL / 3:UNUSEDSIGNAL / 4:UNUSEDSIGNAL / 5:UNUSEDSIGNAL | neither |
| final_op_data | .... | CFSK it=1 | CFSK it=1 sf=0 | - | both_fixed |
| gray_mod6 | .... | C..K it=6 | C..K it=6 sf=1 | 3:UNUSEDSIGNAL / 5:UNUSEDSIGNAL | neither |
| ip_chnl | .... | .... it=6 | .... it=6 sf=1 | 1:PINMISSING,UNDRIVEN,WIDTHTRUNC / 2:PINMISSING,UNUSEDSIGNAL / 3:PINMISSING,UNUSEDSIGNAL / 4:MULTIDRIVEN,PINMISSING,UNUSEDSIGNAL / 5:PINMISSING,WIDTHEXPAND,WIDTHTRUNC | neither |
| ip_link | C... | C... it=6 | .... it=6 sf=1 | 2:PINMISSING,WIDTHEXPAND,WIDTHTRUNC / 3:PINMISSING,UNUSEDSIGNAL / 4:PINMISSING,WIDTHEXPAND,WIDTHTRUNC / 5:PINMISSING,UNUSEDSIGNAL | neither |
| irs | .... | C... it=6 | .... it=6 sf=1 | 3:UNUSEDSIGNAL / 4:UNUSEDSIGNAL | neither |
| jk_ff | CFSK | CFSK it=0 | CFSK it=0 sf=0 | - | already_clean |
| memory | CFSK | CFSK it=0 | CFSK it=0 sf=0 | - | already_clean |
| mux | CFSK | CFSK it=0 | CFSK it=0 sf=0 | - | already_clean |
| op_core | .... | .... it=6 | .... it=6 sf=1 | 5:UNUSEDSIGNAL,WIDTHTRUNC | neither |
| op_data_path | .... | .... it=6 | .... it=6 sf=0 | - | neither |
| op_link1 | .... | .... it=6 | .... it=6 sf=1 | 3:PINMISSING,WIDTHEXPAND,WIDTHTRUNC / 4:PINMISSING / 5:PINMISSING,WIDTHTRUNC | neither |
| op_link2 | .... | .... it=6 | .... it=6 sf=1 | 1:PINMISSING / 2:PINMISSING,WIDTHEXPAND / 3:PINMISSING / 4:PINMISSING,WIDTHEXPAND / 5:PINMISSING | neither |
| op_link3 | .... | .... it=6 | .... it=6 sf=1 | 1:PINMISSING / 2:PINMISSING / 3:PINMISSING / 4:PINMISSING / 5:PINMISSING | neither |
| op_link4 | .... | .... it=6 | .... it=6 sf=0 | - | neither |
| priority_encoder | CFSK | CFSK it=0 | CFSK it=0 sf=0 | - | already_clean |
| register_1bit | .... | CFSK it=1 | CFSK it=2 sf=0 | - | both_fixed |
| register_32bit | CFSK | CFSK it=0 | CFSK it=0 sf=0 | - | already_clean |
| register_4bit | CFSK | CFSK it=0 | CFSK it=0 sf=0 | - | already_clean |
| round_robin_req | .... | .... it=6 | .... it=6 sf=1 | 2:COMB_LOOP,UNDRIVEN,WIDTHTRUNC / 3:COMB_LOOP,UNDRIVEN,WIDTHTRUNC / 4:UNDRIVEN,UNUSEDSIGNAL,WIDTHTRUNC / 5:WIDTHTRUNC | neither |
| router_fifo | C..K | C..K it=6 | C..K it=6 sf=0 | - | neither |
| routing_algo_mesh | .... | CFSK it=2 | CFSK it=2 sf=0 | - | both_fixed |
| rr_arbiter | .... | .... it=6 | .... it=6 sf=0 | - | neither |
| rr_comb_new | .... | .... it=6 | C... it=6 sf=1 | 3:UNDRIVEN | neither |
| top_2x2_router | C... | C... it=6 | C..K it=6 sf=1 | 1:PINMISSING,WIDTHEXPAND,WIDTHTRUNC / 2:PINMISSING,UNUSEDSIGNAL / 3:PINMISSING,WIDTHEXPAND,WIDTHTRUNC / 4:PINMISSING,UNUSEDSIGNAL / 5:PINMISSING,UNUSEDSIGNAL | neither |
| top_module | .... | .... it=6 | .... it=6 sf=1 | 5:PINMISSING | neither |
