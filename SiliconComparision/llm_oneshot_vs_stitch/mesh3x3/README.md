# LLM one-shot vs STITCH on the 3x3 NoC mesh

Same method, model, options and arms as the 2x2 study (`../README.md`). The 3x3 mesh (top `top_3x3_router`,
`phase3/designs/mesh3x3_ref`) has the same 34-module set as the 2x2 mesh with a different top. Run every pipeline
script with `--study mesh3x3`.

## Status

- [x] inventory (`modules.csv`, `reports/HANDWRITTEN.md`)
- [x] reuse of 2x2 results (`reports/REUSE.md`): 33 REUSED, 1 NEW (top_3x3_router)
- [x] spec draft for the NEW module (`specs/top_3x3_router.md`); context budget (`reports/PREDEPLOY_BUDGET.md`)
- [x] task and testbenches (`tasks/top_3x3_router/`, `pipeline/make_tasks.py`; validated in
  `reports/TASK_VALIDATION.md`); HPC job `STUDIES="mesh3x3 ni"` (`../pipeline/HPC_RUN.md`, section 11;
  wall time `reports/WALLTIME.md`)
- [ ] generation on the HPC
- [ ] analysis, assembly, ORFS hand-off

## Checks

top_3x3_router is checked cycle-exact against golden/reference, like top_2x2_router: 5,000 sign-off cycles,
destinations in rows and columns 0..2. The 2x2 caveat applies: the golden's blocking-assignment flops race in
simulation, so an LLM module formally equivalent to golden can still fail the cycle-exact mesh tb
(`../README.md`, PRIMARY note).

## Golden-RTL findings

- **Edge outputs on implicit 1-bit nets.** In `mesh_router3x3.v`, nine of the twelve unconnected mesh-edge data
  outputs are wired to implicitly declared nets (r1 link2/link4, r3 link2/link3, r6 link3, r7 link1/link4,
  r9 link1/link3), so Yosys resizes those nine 32-bit cell ports to 1 bit (`reports/HANDWRITTEN.md`). Each net
  is used only once, so no output of `top_3x3_router` is driven through them and none needs a "not checked"
  entry. The golden is used as written.
- The hand-written RTL aborts Yosys (`Multiple edge sensitive events`, register_1bit) as in 2x2; the A1 copy
  synthesises with 6,480 latch cells (`reports/HANDWRITTEN.md`).

## Not in git

- `runs/inventory/a1_proc.json` and `runs/inventory/handwritten_hierarchy.json`: Yosys JSON dumps, regenerable with
  `pipeline/inventory.py --study mesh3x3`.
- `assembled/` (once Phase C runs), `runs/arms/results/**/iter*/tb*.v`, `*.vvp`, `*.vcd`, `obj_dir/`: as in the
  2x2 study (`../README.md`, "Not in git").
