# LLM one-shot vs STITCH on the 2x2 NoC mesh

## Studies

| study | folder | status |
|---|---|---|
| 2x2 mesh (top_2x2_router) | this folder | done: results below, ORFS hand-off in `handoff_orfs/` |
| 3x3 mesh (top_3x3_router) | [mesh3x3/](mesh3x3/README.md) | tasks ready; HPC generation pending |
| network interface (new1, nidepack; ORFS top ni_pair) | [ni/](ni/README.md) | tasks ready; HPC generation pending |

qwen2.5-coder:32b writes each of the 34 modules of the hand-written 2x2 mesh (top `top_2x2_router`) from a
behavioural spec. Three arms: one-shot (one call), simloop (the Phase 3 simulation-only retry loop, `baseline`) and
stitch (`sem_esc_restart_v3`, STITCH semantic feedback). Each final file is checked against its task (compile, loop
tb, sign-off tb, Yosys, Verilator); then whole meshes are assembled and handed to ORFS for PPA against A1 and B
(`../latch_study`). Folder layout and the golden references: `../README.md`, section `llm_oneshot_vs_stitch/`.

This is an N=1 case study: one design, one model, one run per arm.

## Status

- [x] specs, tasks, testbenches (34 modules)
- [x] generation (34 one-shot, 68 arm runs)
- [x] failure audit, funnel, taxonomy
- [x] STITCH vs sim-only retry
- [x] assembly (pure / hybrid_compile / hybrid_signoff)
- [x] ORFS hand-off prepared (`handoff_orfs/`)
- [ ] coworker: ORFS run per design (`handoff_orfs/PPA_TABLE.md`)
- [ ] coworker: A1 config.mk + constraint.sdc returned (to be stored in `../latch_study/orfs_A1/`)
- [ ] PPA comparison vs A1 (primary) and B (like-for-like)
- [ ] out of scope here: 3x3 mesh, NI, RV32

## Results (2x2)

Every number below comes from a report written by a script in `pipeline/`:

| report | script | content |
|---|---|---|
| `reports/INTEGRITY.md` | integrity.py | records, hashes, job / GPU / commit per output |
| `reports/FAILURE_AUDIT.md` | audit.py | class of every failing final file, audit findings |
| `reports/FUNNEL.md` | funnel.py | stage reached per module and arm |
| `reports/TAXONOMY.md` | taxonomy.py | failure categories, per file and per iteration |
| `reports/STITCH_VS_RETRY.md` | stitch_vs_retry.py | outcome classes, prompt equivalence, sampling |
| `reports/ASSEMBLY.md` | assemble.py | whole-mesh designs and their checks |
| `reports/RUN_HISTORY.md` | run_history.py | jobs, GPUs, speeds |
| `handoff_orfs/` | handoff.py | ORFS hand-off, PPA_TABLE.md |

so_clean = passes the sign-off tb and is structurally clean (no latch, no logic loop, no hard Verilator warning).

| | oneshot | simloop | stitch |
|---|---|---|---|
| so_clean modules (of 34) | 9 | 14 | 14 |
| first failing stage = compiles | 21 | 13 | 13 |
| first failing stage = loop tb | 4 | 7 | 7 |
| first failing stage = composes (mesh drop-in) | 3 | 5 | 5 |
| passes every stage | 6 | 9 | 9 |

Whole meshes (Yosys cells / latch cells; composes = passes the mesh tb):

| design | composes | Yosys cells | latch cells | hand-off |
|---|---|---|---|---|
| control_all_golden | yes | 119720 | 0 | C0 (setup check) |
| hybrid_signoff_oneshot | no (race modules, see below) | 118840 | 0 | P1 PRIMARY |
| hybrid_signoff_simloop = hybrid_signoff_stitch | no (race modules, see below) | 119280 | 0 | P2 PRIMARY |
| hybrid_compile_oneshot | no | 120220 | 0 | O1 optional |
| hybrid_compile_stitch | no | 119260 | 0 | O2 optional |
| pure_oneshot, pure_simloop, pure_stitch | no: the mesh does not compile | - | - | not shipped |
| hybrid_compile_simloop | no | does not synthesise (irs: `Multiple edge sensitive events`) | - | not shipped |
| diag_signoff_dropin_oneshot / _simloop (= _stitch) | yes | 118840 / 119200 | 0 | not shipped (diagnostic) |
| A1 (sanity, same Yosys script) | - | 119720 | 2880 | reference |

PRIMARY note (hybrid_signoff): fails the cycle-exact mesh tb only through dff_synch_clr, dff_synch_reset,
dff_asynch_clr, memory, routing_algo_mesh (P1 contains only dff_synch_clr, dff_synch_reset and memory of these). Each is formally
equivalent to its golden module (Yosys equivalence check; a negative control fails). The mismatch comes from the
golden's blocking-assignment flops (q = d) racing in simulation; the LLM modules use nonblocking (<=)
(routing_algo_mesh is combinational: the golden uses nonblocking assignments in an explicit-list always block, the
LLM module `always @(*)`). With those five swapped back to golden the mesh composes (diag_signoff_dropin_*).

## Findings

**Q1. Can the LLM generate the 2x2 mesh from specs?** Leaf modules, yes; hierarchy and control, no. Of the 16 leaf
modules, 9 are so_clean as one-shot and 14 after either retry loop. Of the 18 modules with children, none is
so_clean in any arm. No pure mesh compiles: in each arm at least one module stops Icarus (pure_simloop and
pure_stitch: demux_16, `'op1' has already been declared`).

**Q2. How does its RTL fail?** Mostly before simulation: compiling is the first failing stage for 21 one-shot
modules and 13 in each loop arm. The dominant primary categories are syntax (11 / 4 / 4: one-shot / simloop /
stitch) and ports (9 / 6 / 7), then function (3 / 4 / 4), timing (1 / 3 / 3) and width (1 / 2 / 2). The audit
classes every failing final file as LLM_BUG (25 one-shot, 19 per loop arm) except asynch_comparator in the two
loop arms (TB_ARTIFACT); no case is SPEC_AMBIGUITY.

**Q3. Does STITCH repair failures?** Retrying does: so_clean rises from 9 (one-shot) to 14 in both loop arms, the
same 14 modules. STITCH adds no so_clean module of its own: 5 modules are fixed by both loops, 0 by STITCH only,
0 by the simulation-only retry only. The attributable structural gains of STITCH over retry are
falling_edge_pulse_generator and top_2x2_router, where the arms diverged after a different (STITCH) prompt;
neither reaches so_clean. The ip_link and irs regressions and the rr_comb_new gain are sampling: the two arms got
identical prompts and still diverged (temperature 0.1, no seed; identical first prompts gave different answers in
6 of 25 modules). STITCH fired on 14 modules, and all 14 finals are still LLM_BUG. In 4 of the 11 runs where it
never fired, the prompts were byte-identical to simloop's throughout, so those runs cannot tell the arms apart.

**Q4. PPA.** Pending the coworker's ORFS runs (`handoff_orfs/`). C0 must reproduce B (setup check). P1 and P2
measure the area, fmax and power of the LLM-written modules that pass their own sign-off checks, inside the
otherwise golden mesh, against A1 (primary) and B (like-for-like). O1 and O2 are functionally incorrect meshes;
their PPA is indicative only.

### Audit findings

- **Golden RTL races.** The mesh tb compares cycle-exact against a golden that uses blocking-assignment flops
  (q = d); the hybrid_signoff meshes fail only through LLM modules formally equivalent to golden (PRIMARY note
  above; `reports/ASSEMBLY.md`, `reports/FAILURE_AUDIT.md`).
- **asynch_comparator is TB_ARTIFACT.** All 46 mismatching input combinations are pointer pairs a 6-entry FIFO
  cannot reach; there the spec formula and the golden disagree (golden = spec in 32, LLM = spec in 14). The tb
  drives random pointer pairs.
- **rr_arbiter uses `priority` as a net name.** It is a SystemVerilog keyword under `-g2012`, so every loop
  feedback shows only that syntax error (6 iterations, both arms). With it renamed, real errors remain (LLM_BUG).

## What this does not show

- N=1: one design, one model (qwen2.5-coder:32b), one run per arm, one temperature (0.1, no seed). No rate,
  percentage or generalisation follows from it.
- Prompts are written from behavioural specs, not from the original designer's intent; testbenches compare
  against golden RTL (cycle-exact) plus spec properties, so a different but valid design can fail.
- STITCH vs retry differences of one or two modules are within what sampling alone produced here.
- No PPA yet; no 3x3 mesh, NI or RV32.

## Not in git

- `runs/arms/results/**/iter*/tb*.v`: the runner's per-iteration copies of the task testbenches. All 321 are
  byte-identical to `tasks/<m>/` (`pipeline/integrity.py`, `reports/INTEGRITY.md`).
- `assembled/`: the assembled meshes and their check logs, regenerable with `pipeline/assemble.py` (the hand-off
  designs are copied into `handoff_orfs/`).
- `runs/inventory/a1_proc.json` and `runs/inventory/handwritten_hierarchy.json` (over 1 MB each): Yosys JSON dumps,
  regenerable with `pipeline/inventory.py`.
- `*.vvp`, `*.vcd`, `obj_dir/` (simulation build output) and `hpc_logs/` (cluster job logs).

Method details: `reports/METHODS_NOTES.md`. Limitations: `reports/LIMITATIONS.md`. Cluster runs:
`pipeline/HPC_RUN.md`.
