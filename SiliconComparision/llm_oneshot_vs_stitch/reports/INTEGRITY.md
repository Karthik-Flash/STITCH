# Integrity of the HPC results (pipeline/integrity.py)

Archive extracted into the study folder: sha256 `93c24d50a0c7aa7e8733c60dbb1096df719828933e55d5a60c5d4954c2c10ace` (excludes *.vvp/*.vcd; value as recorded at download, the archive itself is not in the repository).

## Summary

- one-shot records: 34 of 34; arm runs with metrics.json: 68 of 68
- problems: 0 (nothing missing, errored or mismatched)

| part | job | GPU | deployed commit | count |
|---|---|---|---|---|
| one-shot | 422841 | NVIDIA H200 NVL | e77bf73 | 3 |
| one-shot | 423542 | NVIDIA A100-SXM4-80GB | e77bf73 | 22 |
| one-shot | 424063 | NVIDIA H100 80GB HBM3 | 62b4131 | 9 |
| simloop | 422841 | NVIDIA H200 NVL | e77bf73 | 3 |
| simloop | 424063 | NVIDIA H100 80GB HBM3 | 62b4131 | 31 |
| stitch | 422841 | NVIDIA H200 NVL | e77bf73 | 3 |
| stitch | 424063 | NVIDIA H100 80GB HBM3 | 62b4131 | 31 |

Jobs (run manifests):

- 422841: gpunode7.sharanga.local, NVIDIA H200 NVL, commit e77bf73, GEN_TASKS ['encoder', 'register_4bit', 'allot_vc'], threads not set (before 62b4131)
- 423542: gpunode4.hpc.bits-hyderabad.ac.in, NVIDIA A100-SXM4-80GB, commit e77bf73, GEN_TASKS all, threads not set (before 62b4131)
- 424063: gpunode5.hpc.bits-hyderabad.ac.in, NVIDIA H100 80GB HBM3, commit 62b4131, GEN_TASKS all, threads {'SLURM_CPUS_PER_TASK': '4', 'LLAMA_ARG_THREADS': '4', 'LLAMA_ARG_THREADS_BATCH': '4', 'options.num_thread (p3_bridge)': 4}

Iteration testbench copies (runs/arms/results/**/iter*/tb*.v, git-ignored): 321 byte-identical to tasks/<m>/, 0 differ.

## One-shot records

| module | status | output sha256 = record | tokens out | done_reason | job | GPU | commit |
|---|---|---|---|---|---|---|---|
| allot_vc | ok (no field) | True | 1124 | stop | 422841 | NVIDIA H200 NVL | e77bf73 |
| asynch_comparator | ok (no field) | True | 732 | stop | 423542 | NVIDIA A100-SXM4-80GB | e77bf73 |
| demux_16 | ok (no field) | True | 2913 | stop | 423542 | NVIDIA A100-SXM4-80GB | e77bf73 |
| dff_asynch_clr | ok (no field) | True | 88 | stop | 423542 | NVIDIA A100-SXM4-80GB | e77bf73 |
| dff_synch_clr | ok (no field) | True | 88 | stop | 423542 | NVIDIA A100-SXM4-80GB | e77bf73 |
| dff_synch_reset | ok (no field) | True | 88 | stop | 423542 | NVIDIA A100-SXM4-80GB | e77bf73 |
| dff_synch_set | ok (no field) | True | 88 | stop | 423542 | NVIDIA A100-SXM4-80GB | e77bf73 |
| encoder | ok (no field) | True | 243 | stop | 422841 | NVIDIA H200 NVL | e77bf73 |
| falling_edge_pulse_generator | ok (no field) | True | 365 | stop | 423542 | NVIDIA A100-SXM4-80GB | e77bf73 |
| final_op_data | ok | True | 160 | stop | 424063 | NVIDIA H100 80GB HBM3 | 62b4131 |
| gray_mod6 | ok (no field) | True | 624 | stop | 423542 | NVIDIA A100-SXM4-80GB | e77bf73 |
| ip_chnl | ok (no field) | True | 1159 | stop | 423542 | NVIDIA A100-SXM4-80GB | e77bf73 |
| ip_link | ok (no field) | True | 2336 | stop | 423542 | NVIDIA A100-SXM4-80GB | e77bf73 |
| irs | ok (no field) | True | 1073 | stop | 423542 | NVIDIA A100-SXM4-80GB | e77bf73 |
| jk_ff | ok (no field) | True | 209 | stop | 423542 | NVIDIA A100-SXM4-80GB | e77bf73 |
| memory | ok (no field) | True | 206 | stop | 423542 | NVIDIA A100-SXM4-80GB | e77bf73 |
| mux | ok (no field) | True | 399 | stop | 423542 | NVIDIA A100-SXM4-80GB | e77bf73 |
| op_core | ok | True | 5432 | stop | 424063 | NVIDIA H100 80GB HBM3 | 62b4131 |
| op_data_path | ok | True | 3145 | stop | 424063 | NVIDIA H100 80GB HBM3 | 62b4131 |
| op_link1 | ok | True | 7088 | stop | 424063 | NVIDIA H100 80GB HBM3 | 62b4131 |
| op_link2 | ok | True | 6226 | stop | 424063 | NVIDIA H100 80GB HBM3 | 62b4131 |
| op_link3 | ok | True | 4992 | stop | 424063 | NVIDIA H100 80GB HBM3 | 62b4131 |
| op_link4 | ok | True | 5412 | stop | 424063 | NVIDIA H100 80GB HBM3 | 62b4131 |
| priority_encoder | ok (no field) | True | 587 | stop | 423542 | NVIDIA A100-SXM4-80GB | e77bf73 |
| register_1bit | ok (no field) | True | 104 | stop | 423542 | NVIDIA A100-SXM4-80GB | e77bf73 |
| register_32bit | ok (no field) | True | 123 | stop | 423542 | NVIDIA A100-SXM4-80GB | e77bf73 |
| register_4bit | ok (no field) | True | 114 | stop | 422841 | NVIDIA H200 NVL | e77bf73 |
| round_robin_req | ok (no field) | True | 2660 | stop | 423542 | NVIDIA A100-SXM4-80GB | e77bf73 |
| router_fifo | ok (no field) | True | 630 | stop | 423542 | NVIDIA A100-SXM4-80GB | e77bf73 |
| routing_algo_mesh | ok (no field) | True | 551 | stop | 423542 | NVIDIA A100-SXM4-80GB | e77bf73 |
| rr_arbiter | ok (no field) | True | 1230 | stop | 423542 | NVIDIA A100-SXM4-80GB | e77bf73 |
| rr_comb_new | ok (no field) | True | 1086 | stop | 423542 | NVIDIA A100-SXM4-80GB | e77bf73 |
| top_2x2_router | ok | True | 7738 | stop | 424063 | NVIDIA H100 80GB HBM3 | 62b4131 |
| top_module | ok | True | 27383 | stop | 424063 | NVIDIA H100 80GB HBM3 | 62b4131 |

## Arm runs

| module | arm | LLM calls | stop | final = outputs/<arm> | job | GPU | commit | earlier failed attempts |
|---|---|---|---|---|---|---|---|---|
| allot_vc | simloop | 6 | budget | True | 422841 | NVIDIA H200 NVL | e77bf73 | 0 |
| asynch_comparator | simloop | 6 | budget | True | 424063 | NVIDIA H100 80GB HBM3 | 62b4131 | 0 |
| demux_16 | simloop | 6 | budget | True | 424063 | NVIDIA H100 80GB HBM3 | 62b4131 | 0 |
| dff_asynch_clr | simloop | 1 | func_pass | True | 424063 | NVIDIA H100 80GB HBM3 | 62b4131 | 0 |
| dff_synch_clr | simloop | 0 | func_pass_at_input | True | 424063 | NVIDIA H100 80GB HBM3 | 62b4131 | 0 |
| dff_synch_reset | simloop | 0 | func_pass_at_input | True | 424063 | NVIDIA H100 80GB HBM3 | 62b4131 | 0 |
| dff_synch_set | simloop | 0 | func_pass_at_input | True | 424063 | NVIDIA H100 80GB HBM3 | 62b4131 | 0 |
| encoder | simloop | 1 | func_pass | True | 422841 | NVIDIA H200 NVL | e77bf73 | 0 |
| falling_edge_pulse_generator | simloop | 6 | budget | True | 424063 | NVIDIA H100 80GB HBM3 | 62b4131 | 0 |
| final_op_data | simloop | 1 | func_pass | True | 424063 | NVIDIA H100 80GB HBM3 | 62b4131 | 0 |
| gray_mod6 | simloop | 6 | budget | True | 424063 | NVIDIA H100 80GB HBM3 | 62b4131 | 0 |
| ip_chnl | simloop | 6 | budget | True | 424063 | NVIDIA H100 80GB HBM3 | 62b4131 | 0 |
| ip_link | simloop | 6 | budget | True | 424063 | NVIDIA H100 80GB HBM3 | 62b4131 | 0 |
| irs | simloop | 6 | budget | True | 424063 | NVIDIA H100 80GB HBM3 | 62b4131 | 0 |
| jk_ff | simloop | 0 | func_pass_at_input | True | 424063 | NVIDIA H100 80GB HBM3 | 62b4131 | 0 |
| memory | simloop | 0 | func_pass_at_input | True | 424063 | NVIDIA H100 80GB HBM3 | 62b4131 | 0 |
| mux | simloop | 0 | func_pass_at_input | True | 424063 | NVIDIA H100 80GB HBM3 | 62b4131 | 0 |
| op_core | simloop | 6 | budget | True | 424063 | NVIDIA H100 80GB HBM3 | 62b4131 | 0 |
| op_data_path | simloop | 6 | budget | True | 424063 | NVIDIA H100 80GB HBM3 | 62b4131 | 0 |
| op_link1 | simloop | 6 | budget | True | 424063 | NVIDIA H100 80GB HBM3 | 62b4131 | 0 |
| op_link2 | simloop | 6 | budget | True | 424063 | NVIDIA H100 80GB HBM3 | 62b4131 | 0 |
| op_link3 | simloop | 6 | budget | True | 424063 | NVIDIA H100 80GB HBM3 | 62b4131 | 0 |
| op_link4 | simloop | 6 | budget | True | 424063 | NVIDIA H100 80GB HBM3 | 62b4131 | 0 |
| priority_encoder | simloop | 0 | func_pass_at_input | True | 424063 | NVIDIA H100 80GB HBM3 | 62b4131 | 0 |
| register_1bit | simloop | 1 | func_pass | True | 424063 | NVIDIA H100 80GB HBM3 | 62b4131 | 0 |
| register_32bit | simloop | 0 | func_pass_at_input | True | 424063 | NVIDIA H100 80GB HBM3 | 62b4131 | 0 |
| register_4bit | simloop | 0 | func_pass_at_input | True | 422841 | NVIDIA H200 NVL | e77bf73 | 0 |
| round_robin_req | simloop | 6 | budget | True | 424063 | NVIDIA H100 80GB HBM3 | 62b4131 | 0 |
| router_fifo | simloop | 6 | budget | True | 424063 | NVIDIA H100 80GB HBM3 | 62b4131 | 0 |
| routing_algo_mesh | simloop | 2 | func_pass | True | 424063 | NVIDIA H100 80GB HBM3 | 62b4131 | 0 |
| rr_arbiter | simloop | 6 | budget | True | 424063 | NVIDIA H100 80GB HBM3 | 62b4131 | 0 |
| rr_comb_new | simloop | 6 | budget | True | 424063 | NVIDIA H100 80GB HBM3 | 62b4131 | 0 |
| top_2x2_router | simloop | 6 | budget | True | 424063 | NVIDIA H100 80GB HBM3 | 62b4131 | 0 |
| top_module | simloop | 6 | budget | True | 424063 | NVIDIA H100 80GB HBM3 | 62b4131 | 0 |
| allot_vc | stitch | 6 | budget | True | 422841 | NVIDIA H200 NVL | e77bf73 | 0 |
| asynch_comparator | stitch | 6 | budget | True | 424063 | NVIDIA H100 80GB HBM3 | 62b4131 | 0 |
| demux_16 | stitch | 6 | budget | True | 424063 | NVIDIA H100 80GB HBM3 | 62b4131 | 0 |
| dff_asynch_clr | stitch | 1 | clean_pass | True | 424063 | NVIDIA H100 80GB HBM3 | 62b4131 | 0 |
| dff_synch_clr | stitch | 0 | clean_pass | True | 424063 | NVIDIA H100 80GB HBM3 | 62b4131 | 0 |
| dff_synch_reset | stitch | 0 | clean_pass | True | 424063 | NVIDIA H100 80GB HBM3 | 62b4131 | 0 |
| dff_synch_set | stitch | 0 | clean_pass | True | 424063 | NVIDIA H100 80GB HBM3 | 62b4131 | 0 |
| encoder | stitch | 1 | clean_pass | True | 422841 | NVIDIA H200 NVL | e77bf73 | 0 |
| falling_edge_pulse_generator | stitch | 6 | budget | True | 424063 | NVIDIA H100 80GB HBM3 | 62b4131 | 0 |
| final_op_data | stitch | 1 | clean_pass | True | 424063 | NVIDIA H100 80GB HBM3 | 62b4131 | 0 |
| gray_mod6 | stitch | 6 | budget | True | 424063 | NVIDIA H100 80GB HBM3 | 62b4131 | 0 |
| ip_chnl | stitch | 6 | budget | True | 424063 | NVIDIA H100 80GB HBM3 | 62b4131 | 0 |
| ip_link | stitch | 6 | budget | True | 424063 | NVIDIA H100 80GB HBM3 | 62b4131 | 0 |
| irs | stitch | 6 | budget | True | 424063 | NVIDIA H100 80GB HBM3 | 62b4131 | 0 |
| jk_ff | stitch | 0 | clean_pass | True | 424063 | NVIDIA H100 80GB HBM3 | 62b4131 | 0 |
| memory | stitch | 0 | clean_pass | True | 424063 | NVIDIA H100 80GB HBM3 | 62b4131 | 0 |
| mux | stitch | 0 | clean_pass | True | 424063 | NVIDIA H100 80GB HBM3 | 62b4131 | 0 |
| op_core | stitch | 6 | budget | True | 424063 | NVIDIA H100 80GB HBM3 | 62b4131 | 0 |
| op_data_path | stitch | 6 | budget | True | 424063 | NVIDIA H100 80GB HBM3 | 62b4131 | 0 |
| op_link1 | stitch | 6 | budget | True | 424063 | NVIDIA H100 80GB HBM3 | 62b4131 | 0 |
| op_link2 | stitch | 6 | budget | True | 424063 | NVIDIA H100 80GB HBM3 | 62b4131 | 0 |
| op_link3 | stitch | 6 | budget | True | 424063 | NVIDIA H100 80GB HBM3 | 62b4131 | 0 |
| op_link4 | stitch | 6 | budget | True | 424063 | NVIDIA H100 80GB HBM3 | 62b4131 | 0 |
| priority_encoder | stitch | 0 | clean_pass | True | 424063 | NVIDIA H100 80GB HBM3 | 62b4131 | 0 |
| register_1bit | stitch | 2 | clean_pass | True | 424063 | NVIDIA H100 80GB HBM3 | 62b4131 | 0 |
| register_32bit | stitch | 0 | clean_pass | True | 424063 | NVIDIA H100 80GB HBM3 | 62b4131 | 0 |
| register_4bit | stitch | 0 | clean_pass | True | 422841 | NVIDIA H200 NVL | e77bf73 | 0 |
| round_robin_req | stitch | 6 | budget | True | 424063 | NVIDIA H100 80GB HBM3 | 62b4131 | 0 |
| router_fifo | stitch | 6 | budget | True | 424063 | NVIDIA H100 80GB HBM3 | 62b4131 | 0 |
| routing_algo_mesh | stitch | 2 | clean_pass | True | 424063 | NVIDIA H100 80GB HBM3 | 62b4131 | 0 |
| rr_arbiter | stitch | 6 | budget | True | 424063 | NVIDIA H100 80GB HBM3 | 62b4131 | 0 |
| rr_comb_new | stitch | 6 | budget | True | 424063 | NVIDIA H100 80GB HBM3 | 62b4131 | 0 |
| top_2x2_router | stitch | 6 | budget | True | 424063 | NVIDIA H100 80GB HBM3 | 62b4131 | 0 |
| top_module | stitch | 6 | budget | True | 424063 | NVIDIA H100 80GB HBM3 | 62b4131 | 0 |
