# Limitations

Each item names the report or file its numbers come from.

## Testbenches

- **Coverage is partial for some parents.** The reference toggles 19 of 36 checked outputs of ip_link and 52 of 55 of
  top_module under tb_signoff.v (`reports/task_validation.json`, `ref_signoff_info`, from `pipeline/check_tasks.py`).
  An LLM module can differ on the outputs that never toggle and still pass.
- **router_fifo is reset only at the start.** After a mid-run reset the golden's wrap bits need not match, so the FIFO
  can look full; the spec leaves that undefined (`pipeline/make_tasks.py`, router_fifo stimulus rule).
- **register_1bit, register_4bit, register_32bit are judged by the spec, not by the hand-written golden.** Their
  reference is the repaired Phase 3 register; the hand-written registers do not sign off (`reports/TASK_VALIDATION.md`,
  "Hand-written Phase 3 registers").
- **The loop tb is cycle-exact even for the timing-dependent modules.** tb.v compares cycle by cycle with the golden for
  every module, while the sign-off verdict of a timing-dependent module is its property checks
  (`reports/FAILURE_AUDIT.md`). The feedback the loops see is therefore stricter than the sign-off verdict.
- **The mesh tb is cycle-exact against a golden with simulation races.** The golden mesh uses blocking-assignment flops
  (q = d). LLM modules that are formally equivalent to golden but use nonblocking assignments fail it
  (dff_synch_clr, dff_synch_reset, dff_asynch_clr, memory, routing_algo_mesh; `reports/ASSEMBLY.md`). "composes"
  therefore understates the functionally correct meshes; the diag_signoff_dropin_* designs show which modules cause it.
- **asynch_comparator (TB_ARTIFACT).** tb.v and tb_signoff.v drive random pointer pairs, including 46 that a 6-entry
  FIFO cannot reach; there the spec formula and the golden disagree (`reports/FAILURE_AUDIT.md`).

## Generation

- **No sampling seed.** Temperature 0.1, seed unset. Byte-identical first prompts gave different answers in 6 of 25
  modules (`reports/STITCH_VS_RETRY.md`, Sampling). A difference of one or two modules between the arms is within
  what sampling alone produced.
- **Outputs come from three GPUs and two deployed commits.** One-shot: 3 files from job 422841 (H200), 22 from 423542
  (A100), 9 from 424063 (H100); arms: 3 + 31 runs per arm from 422841 and 424063 (`reports/INTEGRITY.md`). The
  model, options and prompts are the same; the GPU and thread settings differ (`reports/RUN_HISTORY.md`).
- **rr_arbiter feedback was masked by a keyword.** The LLM named a net `priority`, a SystemVerilog keyword under
  `-g2012`; every loop feedback (6 iterations, both arms) showed only that syntax error (`reports/FAILURE_AUDIT.md`).
- **top_module does not fit the arms' context.** Its arms prompt leaves about 3,300 of 32,768 tokens for an answer of
  about 22,364 (`reports/METHODS_NOTES.md`). The whole-router bonus prompt was not attempted.

## Scope

- N=1: one design (2x2 mesh), one model, one run per arm. No rates or generalisation.
- PPA is pending the coworker's ORFS runs (`handoff_orfs/`). A1's ORFS config.mk and constraint.sdc are not in the
  repository; the hand-off asks for them back.
