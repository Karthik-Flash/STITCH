# LLM one-shot vs STITCH on the network interface

Same method, model, options and arms as the 2x2 study (`../README.md`). The network interface of the MPSoC
(`phase3/designs/mpsoc_ref/main.v`) has two halves with no common wrapper in the golden: the packetiser `new1`
(router_fifo + rp1) and the depacketiser `nidepack` (depack + router_fifo). Run every pipeline script with
`--study ni`.

`ni_pair` is a wrapper, not golden: it connects new1's output to nidepack's input for the NI testbench and is the
ORFS top of every NI hand-off design. It is never generated and never prompted.

This is an N=1 case study: four NEW modules, one model, one run per arm.

## Status

- [x] inventory (`modules.csv`, `reports/HANDWRITTEN.md`)
- [x] reuse of 2x2 results (`reports/REUSE.md`): 5 REUSED (router_fifo subtree), 4 NEW (new1, rp1, nidepack, depack)
- [x] specs, tasks and testbenches for the NEW modules; ni_pair wrapper and its testbench (`wrapper/`;
  `reports/TASK_VALIDATION.md`)
- [x] generation on the HPC (job 426786, H200; `reports/RUN_HISTORY.md`)
- [x] integrity, failure audit (with the port-shift check), funnel, taxonomy, STITCH vs retry
- [x] assembly (pure / hybrid_compile / hybrid_signoff, control, A1-style)
- [x] ORFS hand-off prepared (`handoff_orfs/`, with `constraint.sdc`)
- [ ] coworker: ORFS run per design (`handoff_orfs/PPA_TABLE.md`)
- [ ] PPA comparison

## Results

Every number below comes from a report written by a script in `../pipeline/` (run with `--study ni`); the reports
are those listed in `../mesh3x3/README.md`, plus `reports/NI_PAIR_TRACE.md` (ni_pair_trace.py).

| module (NEW) | oneshot | simloop | stitch | first failing stage (oneshot / simloop / stitch) | audit |
|---|---|---|---|---|---|
| rp1 | C... | C... | C... | loop tb / loop tb / loop tb | LLM_BUG (3) |
| depack | C..K | C..K | C..K | loop tb / loop tb / loop tb | LLM_BUG (3) |
| new1 | .... | C..K | .... | compiles / loop tb / compiles | LLM_BUG (3) |
| nidepack | .... | .... | .... | compiles / compiles / compiles | LLM_BUG (3) |
| so_clean | 0 of 4 | 0 of 4 | 0 of 4 | | |

Flags: C compile, F tb.v, S tb_signoff.v, K struct_clean. Each loop arm made 6 calls per module; STITCH fired on all
four modules.

Whole designs (top ni_pair, 9 modules + the wrapper; composes = passes the ni_pair property checks):

| design | LLM modules NEW / REUSED | composes | Yosys cells | latch cells | hand-off |
|---|---|---|---|---|---|
| control_all_golden = A1_style_ni | 0 / 0 | yes | 1799 | 0 | C0 (optional; also the A1-style reference) |
| hybrid_signoff_oneshot = _simloop = _stitch | 0 / 2 (jk_ff, memory) | yes | 1767 | 0 | P1 (optional) |
| hybrid_compile_oneshot | 2 / 3 | no | 1580 | 0 | O1 optional |
| hybrid_compile_simloop | 3 / 5 | no | 1578 | 0 | O2 optional |
| hybrid_compile_stitch | 2 / 5 | no | 1587 | 0 | O3 optional |
| pure_oneshot, pure_simloop, pure_stitch | 4 / 5 | no: the design does not compile | - | - | not shipped |

A1_style_ni is byte-identical to control_all_golden: the hand-written NI RTL synthesises without latches, so the
A1 method fixes nothing (`reports/ASSEMBLY.md`). P1 differs from C0 only in the two REUSED 2x2 modules jk_ff and
memory: no NEW NI module is so_clean, so P1 has no NEW LLM module to measure.

## Findings

**Q1. Can the LLM generate the NI modules from their specs?** No. None of the four NEW modules is so_clean in any
arm. nidepack never compiles; new1 compiles only in simloop and then fails its properties; rp1 and depack compile in
every arm and fail the cycle-exact loop tb. The two leaf modules, rp1 and depack, are state machines written from
state tables; in 2x2 the leaf modules were the ones that reached so_clean. No pure ni_pair compiles.

**Q2. How does its RTL fail?** Two ways (`reports/FAILURE_AUDIT.md`, `reports/TAXONOMY.md`):
- At the hierarchy: 5 of the 6 new1 and nidepack finals tie a constant to a child output port (router_fifo's
  `rd_add`, `wr_add`, `rd_dir`, `wr_dir`; depack's `c_rd`), which Icarus rejects. The spec calls these ports
  "not used" or "left open" and lists child ports without directions; the files' own comments read "left open" as
  "can be tied to a constant". The simloop new1 compiles but drives `empty` from the FIFO's `empty` instead of its
  `full_int` and gives rp1's `rd_en` a second driver.
- In the state machines: rp1 writes the header flit one edge early and keeps 3-bit state codes in a 2-bit register;
  depack does not clear `wr_en` when a body flit arrives in state header.
Primary labels: ports 2 / 1 / 2, function 2 / 2 / 2, timing 0 / 1 / 0 (oneshot / simloop / stitch). Every failing
final is LLM_BUG; none is SPEC_AMBIGUITY or GOLDEN_DEFECT.

**Q3. Does STITCH repair failures?** No. STITCH fired on all four modules and every stitch final still fails. The
only difference between the arms is new1, which compiles in simloop and not in stitch; the arms got a byte-identical
first prompt and the answers already differ there, so the difference is sampling, not STITCH
(`reports/STITCH_VS_RETRY.md`). Retrying did not repair any NEW module either: so_clean is 0 in all three arms.

**Q4. PPA.** No ORFS run is required (`handoff_orfs/`, all optional): no NEW NI module signed off, so no NI design
measures LLM output. P1 measures two REUSED 2x2 modules inside the NI. O1 to O3 contain NEW LLM modules that compile but fail
the ni_pair properties; their PPA is indicative only.

### Audit findings

- **Port-shift check.** The one file that could have failed only through the golden's port shift (new1, simloop)
  gives 18806 cycle-exact mismatches against a scratch golden with the shift corrected (controls: 0 for the
  corrected golden, 5643 for the original) and is not equivalent to it: LLM_BUG, not GOLDEN_DEFECT.
- **Child-port directions.** The spec lists each child's ports in order without direction; adding the directions
  would remove the reading behind the five compile failures above.
- **jk_ff (REUSED) is not proven equivalent** to golden, though it passes its 2x2 task and the drop-in test
  (`reports/ASSEMBLY.md`).

## Golden-RTL findings

- **Port shift (phase3/designs/SANITISATION.md, item 3).** new1 and nidepack instantiate router_fifo by position
  with one connection fewer than its 14 ports, so the connections after `data_out` land one port early. In new1
  this is observable: output `full_int` is the FIFO's `full_ext` (4 or more entries) and output `empty` is the
  FIFO's `full_int` (full). In nidepack none of the shifted nets leaves the module. The golden is used as written;
  no failure is caused by the shift alone (Audit findings).
- **rp1 sends one packet per power-up.** Its body counter `j` is initialised to 0 at declaration and is not cleared
  by reset. After any reset that follows the first packet, `j` != N in payload2, so rp1 alternates payload1 and
  payload2 for ever and never sends another tailer. The golden is used as written and the spec states this.
- **rp1's `j` is undefined in silicon.** ASIC synthesis ignores the declaration initial value, so in a synthesised
  netlist `j` has no defined value at power-up; even the first packet is not guaranteed there.
- **depack holds `wr_en`.** After a completed word, `wr_en` stays 1 until the next body flit, so the FIFO rewrites
  the same word on every `wr_clk` edge in between. On the rp1 stream (tailer, then 32'h7FFF_FFFF for ever) no body
  flit follows, so the FIFO fills with copies of the last word. The golden is used as written and the spec states
  this.
- **The golden halves misread each other in ni_pair.** In `main.v` a 2x2 router sits between the halves; ni_pair
  connects them directly. rp1 samples the FIFO output, router_fifo samples depack's output, and in ni_pair depack
  samples rp1's flit, each on the edge where the other side updates it (blocking assignments). One packet for the
  written word 32'h1234_ABCD (all golden modules) reaches the depacketiser FIFO as 32'h1234_1234, and the FIFO is
  full 6 cycles after the tailer flit, with `wr_en` still held (`reports/NI_PAIR_TRACE.md`).

## Checks

| module | sign-off verdict | properties (tb_signoff.v) |
|---|---|---|
| rp1, depack | cycle-exact against golden/reference | - |
| new1 | properties; cycle-exact logged as secondary | reset values of niout and wr_o; every new flit is a legal flit; a header carries {source, dest}; a body flit is a half of a written word; wr_o rises only with a body flit; FIFO-flag outputs rise only on a write, and the full output implies the 4-entry output |
| nidepack | properties; cycle-exact logged as secondary | data_out reset value; data_out changes only on rd_en; each word read is one depack assembled from the input flits (testbench model of depack's states) |
| ni_pair | properties; cycle-exact logged as secondary | the new1 properties, plus: data_out reset value, changes only on rd_en, both 16-bit halves come from written words (or from a header, idle or last flit) |

Inputs of rp1, new1 and ni_pair change 1 ns after the falling clock edge, because rp1 updates `rd_en` on that
edge. depack's `c_rd` is not checked (nidepack leaves it open).

## What this does not show

- N=1: four NEW modules, one model (qwen2.5-coder:32b), one run per arm, temperature 0.1 with no seed. No rate,
  percentage or generalisation follows from it.
- ni_pair is our wrapper, not the MPSoC network interface; its testbench and PPA describe the halves joined
  directly.
- P1 holds no NEW module, so the NI hand-off does not measure the PPA of NI modules written by the LLM.
- No PPA yet. Method details: `reports/METHODS_NOTES.md`. Limitations: `reports/LIMITATIONS.md`.

## Not in git

- `runs/arms/results/**/iter*/tb*.v`: the runner's per-iteration testbench copies; all 56 are byte-identical to
  `tasks/<m>/` (`reports/INTEGRITY.md`).
- `assembled/`: regenerable with `pipeline/assemble_study.py --study ni` (the hand-off designs are copied into
  `handoff_orfs/`).
- `runs/inventory/a1_proc.json` and `runs/inventory/handwritten_hierarchy.json`: Yosys JSON dumps, regenerable with
  `pipeline/inventory.py --study ni`.
- `*.vvp`, `*.vcd`, `obj_dir/`: as in the 2x2 study (`../README.md`, "Not in git").
