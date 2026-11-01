# LLM one-shot vs STITCH on the 3x3 NoC mesh

Same method, model, options and arms as the 2x2 study (`../README.md`). The 3x3 mesh (top `top_3x3_router`,
`phase3/designs/mesh3x3_ref`) has the same 34-module set as the 2x2 mesh with a different top. Run every pipeline
script with `--study mesh3x3`.

This is an N=1 case study: one NEW module, one model, one run per arm.

## Status

- [x] inventory (`modules.csv`, `reports/HANDWRITTEN.md`)
- [x] reuse of 2x2 results (`reports/REUSE.md`): 33 REUSED, 1 NEW (top_3x3_router)
- [x] spec, task and testbenches for the NEW module (`specs/`, `tasks/top_3x3_router/`, `reports/TASK_VALIDATION.md`)
- [x] generation on the HPC (job 426786, H200; `reports/RUN_HISTORY.md`)
- [x] integrity, failure audit, funnel, taxonomy, STITCH vs retry
- [x] assembly (pure / hybrid_compile / hybrid_signoff, control, A1-style)
- [x] ORFS hand-off prepared (`handoff_orfs/`)
- [ ] coworker: ORFS run per design (`handoff_orfs/PPA_TABLE.md`)
- [ ] PPA comparison

## Results

Every number below comes from a report written by a script in `../pipeline/` (run with `--study mesh3x3`):

| report | script | content |
|---|---|---|
| `reports/INTEGRITY.md` | integrity.py | records, hashes, job / GPU per output |
| `reports/FAILURE_AUDIT.md` | audit.py | class of every failing final file |
| `reports/FUNNEL.md` | funnel.py | stage reached per arm; REUSED modules with their 2x2 flags |
| `reports/TAXONOMY.md` | taxonomy.py | failure categories, per file and per iteration |
| `reports/STITCH_VS_RETRY.md` | stitch_vs_retry.py | outcome, gains and regressions, sampling |
| `reports/ASSEMBLY.md` | assemble_study.py | whole-mesh designs, drop-in and equivalence checks |
| `reports/RUN_HISTORY.md` | run_history.py | job, GPU, speeds |
| `handoff_orfs/` | handoff_study.py | ORFS hand-off, PPA_TABLE.md |

| top_3x3_router | oneshot | simloop | stitch |
|---|---|---|---|
| flags (C compile, F tb.v, S tb_signoff.v, K struct_clean) | C..K | C..K (6 calls) | .... (6 calls, STITCH fired) |
| first failing stage | loop tb | loop tb | compiles |
| audit class | LLM_BUG | LLM_BUG | LLM_BUG |

Whole meshes (34 modules; composes = passes the cycle-exact mesh tb):

| design | LLM modules NEW / REUSED | composes | Yosys cells | latch cells | hand-off |
|---|---|---|---|---|---|
| A1_style_3x3 | - (hand-written) | not simulated (Icarus error) | 269370 | 6480 | A1_style_3x3 (optional; A1 / 3x3 already measured) |
| control_all_golden | 0 / 0 | yes | 269370 | 0 | C0 (reference) |
| hybrid_signoff_oneshot | 0 / 9 | no (race modules, see below) | 267390 | 0 | P1 PRIMARY |
| hybrid_signoff_simloop = hybrid_signoff_stitch | 0 / 14 | no (race modules, see below) | 268380 | 0 | P2 PRIMARY |
| hybrid_compile_oneshot | 1 / 12 | no | 270495 | 0 | O1 optional |
| hybrid_compile_stitch | 0 / 20 | no | 268335 | 0 | O2 optional |
| hybrid_compile_simloop | 1 / 20 | no | does not synthesise (irs: `Multiple edge sensitive events`) | - | not shipped |
| pure_oneshot, pure_simloop, pure_stitch | 1 / 33 | no: the mesh does not compile | - | - | not shipped |
| diag_signoff_dropin_oneshot / _simloop (= _stitch) | 0 / 6, 0 / 9 | yes | 267390 / 268200 | 0 | not shipped (diagnostic) |

PRIMARY note (hybrid_signoff): top_3x3_router is so_clean in no arm, so the PRIMARY designs hold only REUSED 2x2
modules and the golden top. They fail the cycle-exact mesh tb only through dff_asynch_clr, dff_synch_clr,
dff_synch_reset, memory and routing_algo_mesh (P1 holds dff_synch_clr, dff_synch_reset and memory of these), the
same modules as in 2x2. Each is formally equivalent to its golden (clocks=True; the encoder and mutant controls are
rejected), and with them swapped back the meshes compose (diag_signoff_dropin_*).

## Findings

**Q1. Can the LLM generate the 3x3 top from its spec?** No. top_3x3_router is so_clean in no arm. The one-shot file
compiles and is structurally clean but fails the loop tb; the simloop final is byte-identical to it after 6 calls;
the stitch final does not compile. No pure 3x3 mesh compiles: pure_oneshot stops at a REUSED module (`'gnt_or' has
already been declared`), pure_simloop and pure_stitch at demux_16 (`'op1' has already been declared`), as in 2x2.

**Q2. How does its RTL fail?** The one-shot and simloop top drive each router's core output `data_out_core_rN`
from two router outputs (`data_out_core` and `data_out_c`) and tie the four VC data outputs of each link to one net:
every core output is X from cycle 0 (`reports/FAILURE_AUDIT.md`). The stitch final redeclares a net
(`'full_out_link4_vc4_r8' has already been declared`). Primary labels: function (one-shot, simloop), ports (stitch)
(`reports/TAXONOMY.md`).

**Q3. Does STITCH repair the failure?** No. STITCH fired (directives UNUSEDSIGNAL, WIDTHEXPAND) and the final still
fails. The arms first produce different RTL at iteration 4, after a different prompt (STITCH directives, escalated);
the stitch final then loses compile and struct_clean, which the simloop final keeps. This regression is attributable
to the STITCH prompt, not to sampling (`reports/STITCH_VS_RETRY.md`).

**Q4. PPA.** Pending the coworker's ORFS runs (`handoff_orfs/`): C0 (must reproduce B / 3x3), P1 and P2 required;
A1_style_3x3, O1 and O2 optional. A1 / 3x3 and B / 3x3 are already measured (`../../latch_study/PPA_SUMMARY.md`,
copied into `handoff_orfs/PPA_TABLE.md`). P1 and P2 measure the REUSED 2x2 LLM modules that pass their own sign-off checks, inside an otherwise
golden 3x3 mesh. O1 and O2 are functionally incorrect meshes; their PPA is indicative only.

### Audit findings

- **The 2x2 golden race carries over.** The same five REUSED modules fail the cycle-exact 3x3 mesh tb and are
  formally equivalent to golden (PRIMARY note; `reports/ASSEMBLY.md`).
- **Two REUSED modules pass their tests but are not equivalent.** encoder (simloop, stitch) gives the code of the
  lowest-numbered active input where its spec gives the OR of the codes; jk_ff (every arm) is not proven
  equivalent. Both pass their 2x2 task and the drop-in test (`reports/ASSEMBLY.md`, `reports/LIMITATIONS.md`).

## Golden-RTL findings

- **Edge outputs on implicit 1-bit nets.** In `mesh_router3x3.v`, nine of the twelve unconnected mesh-edge data
  outputs are wired to implicitly declared nets (r1 link2/link4, r3 link2/link3, r6 link3, r7 link1/link4,
  r9 link1/link3), so Yosys resizes those nine 32-bit cell ports to 1 bit (`reports/HANDWRITTEN.md`). Each net
  is used only once, so no output of `top_3x3_router` is driven through them and none needs a "not checked"
  entry. The golden is used as written.
- **Blocking-assignment flops race in the cycle-exact mesh tb**, as in 2x2 (Audit findings above).
- The hand-written RTL aborts Yosys (`Multiple edge sensitive events`, register_1bit) as in 2x2; the A1-style copy
  synthesises with 6,480 latch cells (`reports/HANDWRITTEN.md`, `reports/ASSEMBLY.md`).

## Checks

top_3x3_router is checked cycle-exact against golden/reference, like top_2x2_router: 5,000 sign-off cycles,
destinations in rows and columns 0..2.

## What this does not show

- N=1: one NEW module, one model (qwen2.5-coder:32b), one run per arm, temperature 0.1 with no seed. No rate,
  percentage or generalisation follows from it.
- The 33 REUSED modules were not generated again; their results are the 2x2 ones. The PRIMARY designs therefore
  measure 2x2 LLM modules in a 3x3 mesh, not new 3x3 generation.
- One STITCH regression on one module is a single event, not a tendency.
- No PPA yet. Method details: `reports/METHODS_NOTES.md`. Limitations: `reports/LIMITATIONS.md`.

## Not in git

- `runs/arms/results/**/iter*/tb*.v`: the runner's per-iteration testbench copies; all 14 are byte-identical to
  `tasks/top_3x3_router/` (`reports/INTEGRITY.md`).
- `assembled/`: regenerable with `pipeline/assemble_study.py --study mesh3x3` (the hand-off designs are copied into
  `handoff_orfs/`).
- `runs/inventory/a1_proc.json` and `runs/inventory/handwritten_hierarchy.json`: Yosys JSON dumps, regenerable with
  `pipeline/inventory.py --study mesh3x3`.
- `*.vvp`, `*.vcd`, `obj_dir/`: as in the 2x2 study (`../README.md`, "Not in git").
