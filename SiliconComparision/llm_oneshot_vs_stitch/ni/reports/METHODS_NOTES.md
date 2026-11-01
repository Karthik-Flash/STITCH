# Methods notes (ni)

The method, model, options and arms are those of the 2x2 study (`../../reports/METHODS_NOTES.md`): qwen2.5-coder:32b,
temperature 0.1, no seed, num_ctx 32768, num_thread = the job's CPUs (4), client timeout 3600 s, one-shot then
simloop (`baseline`) and stitch (`sem_esc_restart_v3`) with a budget of 6 calls. The run manifest records the same
options for both paths (`runs/RUN_MANIFEST_426786.json`).

## Run

- One job for mesh3x3 and ni: job 426786 on gpunode7 (NVIDIA H200 NVL), `STUDIES="mesh3x3 ni"`, exit 0, elapsed
  01:08:57 (sacct, reported by the user). llama-server threads 4.
- Generation rate of the 52 NI calls: 66.07 tok/s pooled, 59.0 to 68.6 per call (`reports/RUN_HISTORY.md`, from
  Ollama's eval counters; the job and serve logs stayed on the cluster).
- The manifest's `git_commit` is `UNKNOWN` (preflight.py read the study sub-folder; fixed). The user checked the
  deployed commit on the cluster (0fa68c9) (`reports/INTEGRITY.md`).

## Modules, reuse and the wrapper

- NEW (generated here): rp1, new1, depack, nidepack. REUSED (2x2 results, same rule as mesh3x3: golden equal or
  Yosys-equivalent, prompt identical; `reports/REUSE.md`): asynch_comparator, jk_ff, gray_mod6, memory, router_fifo.
- `ni_pair` (`wrapper/ni_pair.v`) is a wrapper we wrote, not golden: new1's flit output drives nidepack's flit input
  directly, with the clocks as in `phase3/designs/mpsoc_ref/main.v`. It is never generated or prompted. It is the top
  of the whole-design testbench (`wrapper/ni_pair/tb_signoff.v`) and of every NI hand-off design. In main.v a 2x2
  router sits between the halves; the direct connection makes depack sample rp1's flit on the edge rp1 updates it,
  so even the all-golden ni_pair does not pass words through intact (`reports/NI_PAIR_TRACE.md`). Its testbench
  therefore checks properties (where each 16-bit half came from), not the delivered word.

## Verdict rules (CP1)

rp1 and depack: cycle-exact against golden. new1, nidepack and ni_pair: property checks are the verdict; the
cycle-exact comparison is logged as secondary (`README.md`, Checks).

## Port-shift check (GOLDEN_DEFECT)

The golden new1 and nidepack connect router_fifo by position with its last outputs shifted. A new1 or nidepack final
that compiles and fails is re-simulated with `tasks/<m>/tb_signoff.v` whose reference copy is a scratch golden with
the shift corrected (`, data_out, , full_int, empty)`), and checked for Yosys equivalence with it (clocks=True). It
is GOLDEN_DEFECT only if it then matches cycle-exact or is equivalent. Controls: the corrected copy gives 0
mismatches against itself, the original golden more than 0 (`pipeline/audit.py`, shift_check). One file qualified
for the check (new1, simloop); it is not GOLDEN_DEFECT (`reports/FAILURE_AUDIT.md`).

## Assembly and equivalence

As mesh3x3 (`../mesh3x3/reports/METHODS_NOTES.md`): `pipeline/assemble_study.py`, REUSED modules from the 2x2 final
file of the same arm, golden replacements from `tasks/<m>/golden.v` and `golden/reference`, ni_pair in every design.
A1_style_ni (`golden/A1`) is byte-identical to control_all_golden: the hand-written NI RTL synthesises without
latches, so nothing is fixed; it is kept once, as C0, with the alias recorded. Equivalence: clocks=True, golden
children flattened, encoder and mutant controls.

## SDC

ni_pair has two clock ports, `rd_clk` and `wr_clk`, on the two sides of asynchronous FIFOs. The hand-off ships
`handoff_orfs/constraint.sdc`: A1's 10 ns clock on each port and `set_clock_groups -asynchronous` between them. This
is the only SDC change versus A1 (`pipeline/handoff_study.py`).
