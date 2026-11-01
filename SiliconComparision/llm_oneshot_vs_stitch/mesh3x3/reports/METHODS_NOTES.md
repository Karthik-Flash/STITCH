# Methods notes (mesh3x3)

The method, model, options and arms are those of the 2x2 study (`../../reports/METHODS_NOTES.md`): qwen2.5-coder:32b,
temperature 0.1, no seed, num_ctx 32768, num_thread = the job's CPUs (4), client timeout 3600 s, one-shot then
simloop (`baseline`) and stitch (`sem_esc_restart_v3`) with a budget of 6 calls. The run manifest records the same
options for both paths (`runs/RUN_MANIFEST_426786.json`, `generation_options` and `generation_options_run_arms`).

## Run

- One job for mesh3x3 and ni: job 426786 on gpunode7 (NVIDIA H200 NVL), `STUDIES="mesh3x3 ni"`, exit 0, elapsed
  01:08:57 (sacct, reported by the user). llama-server threads 4 (`runs/RUN_MANIFEST_426786.json`).
- Generation rate of the 13 mesh3x3 calls: 61.65 tok/s pooled, 60.8 to 64.3 per call (`reports/RUN_HISTORY.md`,
  from Ollama's eval counters; the job and serve logs stayed on the cluster).
- The manifest's `git_commit` is `UNKNOWN`: preflight.py looked for DEPLOYED_COMMIT.txt in the study sub-folder
  instead of the study root. The user checked the deployed commit on the cluster (0fa68c9). preflight.py now reads
  the root file (`reports/INTEGRITY.md`).

## Reuse rule

A module of this study takes the 2x2 results (REUSED) when its golden equals the 2x2 golden after whitespace
normalisation, or is proven equivalent by Yosys (clocks=True, see below; a mutant of the study golden must be
rejected), and the prompt this study would send is byte-identical to the 2x2 prompt (`pipeline/reuse.py`,
`reports/REUSE.md`). 33 modules are REUSED; top_3x3_router is the only NEW module and the only one generated here.
The per-module reports (integrity, audit, funnel, taxonomy, STITCH vs retry) cover the NEW module; `reports/FUNNEL.md`
lists the 33 REUSED modules with their 2x2 flags, labelled "reused (2x2)".

## Assembly

`pipeline/assemble_study.py`. Each design has all 34 modules. REUSED modules come from the 2x2 final file of the
same arm, and the hybrid choices use the 2x2 re-evaluation (`../runs/analysis/<arm>/<m>/eval.json`). Golden
replacements: `tasks/top_3x3_router/golden.v` and this study's `golden/reference`. A1_style_3x3 is `golden/A1`: the
hand-written RTL with only register_1bit fixed, as in latch_study (Yosys: 6,480 latch cells, the expected value).
The top testbench is `tasks/top_3x3_router/tb_signoff.v`, cycle-exact against the golden mesh.

## Equivalence checks

For every LLM module kept by a hybrid_signoff design: a drop-in test (golden mesh with only that module from the
arm) and a Yosys equivalence check against its golden (`assemble.equiv_texts` with clocks=True: clk2fflogic, so
clock nets are modelled as logic; golden children flattened into both sides). Controls: the 2x2 one-shot encoder
(compiles, fails its tb) must not be equivalent, and every module found equivalent must be rejected once mutated
(one operator changed). Both controls hold (`reports/ASSEMBLY.md`). The 2x2 assembly used the same check without
clk2fflogic and without flattening (`pipeline/assemble.py`); with the stricter check, the same five modules are the
only drop-in failures, and all five are equivalent.
