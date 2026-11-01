# Limitations (mesh3x3)

Each item names the report or file its numbers come from.

## Scope

- **One NEW module.** Only top_3x3_router is generated in this study; the other 33 modules are the 2x2 results
  (`reports/REUSE.md`). The per-module results of this study rest on one module and one run per arm.
- **The hybrid designs measure 2x2 modules.** top_3x3_router is not so_clean in any arm, so every hybrid_signoff
  design keeps only REUSED 2x2 modules (9 one-shot, 14 per loop arm) and the golden top (`reports/ASSEMBLY.md`).
  Their PPA is that of the 2x2 LLM modules placed in a 3x3 mesh.
- **N=1.** One design, one model, one run per arm, temperature 0.1 with no seed. No rates or generalisation.

## Testbenches

- **The mesh tb is cycle-exact against a golden with simulation races**, as in 2x2. The hybrid_signoff meshes fail it
  only through dff_asynch_clr, dff_synch_clr, dff_synch_reset, memory and routing_algo_mesh, each formally equivalent
  to its golden; with those swapped back the meshes compose (diag_signoff_dropin_*, `reports/ASSEMBLY.md`).
  "composes" understates the functionally correct meshes.
- **Formal equivalence and the tests disagree for two REUSED modules.** encoder (simloop, stitch) and jk_ff (every
  arm) pass their 2x2 tasks and the drop-in test but are not equivalent to golden under clocks=True
  (`reports/ASSEMBLY.md`). The LLM encoder returns the code of the lowest-numbered active input; the spec gives the
  OR of the codes when several inputs are active (`../tasks/encoder/spec.md`). The LLM jk_ff derives `qbar` as `~q`;
  the golden keeps `q` and `qbar` in separate registers. Neither changes the 3x3 mesh tb result.
- **A1_style_3x3 is not simulated.** Icarus does not compile it with the mesh tb (`Unable to bind wire/reg/memory
  rd_en_out`, an implicit net in the hand-written ip_chnl); it is a Yosys and PPA reference only (`reports/ASSEMBLY.md`).

## Generation and records

- **The job log stayed on the cluster.** Rates come from Ollama's eval counters, and the wall time is the user's
  sacct value (`reports/RUN_HISTORY.md`). The run manifest's commit is `UNKNOWN` (`reports/METHODS_NOTES.md`).
- **The REUSED results come from the 2x2 jobs** (three GPUs, two deployed commits; `../reports/INTEGRITY.md`), not
  from job 426786.
- **PPA is pending** the coworker's ORFS runs (`handoff_orfs/`).
