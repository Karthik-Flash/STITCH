# Limitations (ni)

Each item names the report or file its numbers come from.

## Scope

- **The top is our wrapper.** ni_pair joins the two NI halves directly; in the MPSoC a router sits between them. Its
  testbench result and its PPA describe this wrapper, not the MPSoC network interface (`reports/METHODS_NOTES.md`,
  `reports/NI_PAIR_TRACE.md`).
- **The PRIMARY design has no NEW module.** No NEW module is so_clean in any arm, so hybrid_signoff (byte-identical
  in all three arms) keeps only the REUSED 2x2 modules jk_ff and memory (`reports/ASSEMBLY.md`). Its PPA measures
  those two 2x2 modules inside the NI, not the NI modules generated here.
- **N=1.** Four NEW modules, one model, one run per arm, temperature 0.1 with no seed. No rates or generalisation.

## Testbenches

- **Property verdicts for new1, nidepack and ni_pair.** These are timing-dependent (same-edge hand-offs with blocking
  assignments in the golden), so their verdict is the property check; a design can pass the properties and still
  differ cycle by cycle from golden (`README.md`, Checks).
- **depack `c_rd` is not checked** (nidepack leaves it open).
- **The loop tb (tb.v) is cycle-exact for every module**, as in 2x2, so the feedback the loops see is stricter than
  the sign-off verdict for new1 and nidepack.
- **jk_ff is not proven equivalent.** The REUSED jk_ff kept by hybrid_signoff passes its 2x2 task and the drop-in
  test, but Yosys does not prove it equivalent to golden under clocks=True (`reports/ASSEMBLY.md`).

## Generation and records

- **The job log stayed on the cluster.** Rates come from Ollama's eval counters and the wall time is the user's
  sacct value (`reports/RUN_HISTORY.md`); the run manifest's commit is `UNKNOWN` (`reports/INTEGRITY.md`).
- **Sampling.** In 4 modules both arms sent a byte-identical first prompt; the answers differ in 1 (new1), and the
  new1 regression of STITCH against retry follows from that (`reports/STITCH_VS_RETRY.md`).
- **PPA is pending** the coworker's ORFS runs (`handoff_orfs/`).
