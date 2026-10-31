# LLM one-shot vs STITCH on the network interface

Same method, model, options and arms as the 2x2 study (`../README.md`). The network interface of the MPSoC
(`phase3/designs/mpsoc_ref/main.v`) has two halves with no common wrapper in the golden: the packetiser `new1`
(router_fifo + rp1) and the depacketiser `nidepack` (depack + router_fifo). Run every pipeline script with
`--study ni`.

`ni_pair` is a wrapper, not golden: it connects new1's output to nidepack's input for the NI testbench and is the
ORFS top of every NI hand-off design. It is never generated and never prompted.

## Status

- [x] inventory (`modules.csv`, `reports/HANDWRITTEN.md`)
- [x] reuse of 2x2 results (`reports/REUSE.md`): 5 REUSED (router_fifo subtree), 4 NEW (new1, rp1, nidepack, depack)
- [x] spec drafts for the NEW modules (`specs/`); context budget (`reports/PREDEPLOY_BUDGET.md`)
- [x] ni_pair wrapper (`wrapper/ni_pair.v`) and its whole-design testbench (`wrapper/ni_pair/`); tasks and
  testbenches for the 4 NEW modules (`tasks/`, `pipeline/make_tasks.py`; validated in
  `reports/TASK_VALIDATION.md`); HPC job `STUDIES="mesh3x3 ni"` (`../pipeline/HPC_RUN.md`, section 11; wall
  time `reports/WALLTIME.md`)
- [ ] generation on the HPC
- [ ] analysis, assembly, ORFS hand-off

## Checks

| module | sign-off verdict | properties (tb_signoff.v) |
|---|---|---|
| rp1, depack | cycle-exact against golden/reference | - |
| new1 | properties; cycle-exact logged as secondary | reset values of niout and wr_o; every new flit is a legal flit; a header carries {source, dest}; a body flit is a half of a written word; wr_o rises only with a body flit; FIFO-flag outputs rise only on a write, and the full output implies the 4-entry output |
| nidepack | properties; cycle-exact logged as secondary | data_out reset value; data_out changes only on rd_en; each word read is one depack assembled from the input flits (testbench model of depack's states) |
| ni_pair | properties; cycle-exact logged as secondary | the new1 properties, plus: data_out reset value, changes only on rd_en, both 16-bit halves come from written words (or from a header, idle or last flit) |

Inputs of rp1, new1 and ni_pair change 1 ns after the falling clock edge, because rp1 updates `rd_en` on that
edge. depack's `c_rd` is not checked (nidepack leaves it open).

## Golden-RTL findings

- **Port shift (phase3/designs/SANITISATION.md, item 3).** new1 and nidepack instantiate router_fifo by position
  with one connection fewer than its 14 ports, so the connections after `data_out` land one port early. In new1
  this is observable: output `full_int` is the FIFO's `full_ext` (4 or more entries) and output `empty` is the
  FIFO's `full_int` (full). In nidepack none of the shifted nets leaves the module. The golden is used as written;
  a failure caused only by the shift is classed GOLDEN_DEFECT in the audit.
- **rp1 sends one packet per power-up.** Its body counter `j` is initialised to 0 at declaration and is not cleared
  by reset. After any reset that follows the first packet, `j` != N in payload2, so rp1 alternates payload1 and
  payload2 for ever and never sends another tailer. The golden is used as written and the spec states this.
- **rp1's `j` is undefined in silicon.** ASIC synthesis ignores the declaration initial value, so in a synthesised
  netlist `j` has no defined value at power-up; even the first packet is not guaranteed there.
- **depack holds `wr_en`.** After a completed word, `wr_en` stays 1 until the next body flit, so the FIFO rewrites
  the same word on every `wr_clk` edge in between. On the rp1 stream (tailer, then 32'h7FFF_FFFF for ever) no body
  flit follows, so the FIFO fills with copies of the last word. The golden is used as written and the spec states
  this.
- **Same-edge hand-offs.** rp1 samples the FIFO output, and router_fifo samples depack's output, on the same clock
  edge on which the other side updates it, both with blocking assignments. In ni_pair, depack also samples rp1's
  flit on the edge rp1 updates it. new1, nidepack and ni_pair are therefore timing-dependent: their sign-off verdict
  is the property check, and the cycle-exact comparison with golden is logged as secondary. rp1 and depack are
  checked cycle-exact.
- **The golden halves misread each other in ni_pair.** In `main.v` a 2x2 router sits between the halves; ni_pair
  connects them directly. One packet for the written word 32'h1234_ABCD (Icarus, all golden modules) reaches the
  depacketiser FIFO as 32'h1234_1234, and the FIFO is full 6 cycles after the tailer flit, with `wr_en` still held
  (`reports/NI_PAIR_TRACE.md`, `pipeline/ni_pair_trace.py`). This is the same-edge hand-off between rp1 and depack
  plus the held `wr_en`; the ni_pair properties therefore check where each 16-bit half came from, not which word
  arrives.

## Not in git

- `runs/inventory/a1_proc.json` and `runs/inventory/handwritten_hierarchy.json`: Yosys JSON dumps, regenerable with
  `pipeline/inventory.py --study ni`.
- `assembled/` (once Phase C runs), `runs/arms/results/**/iter*/tb*.v`, `*.vvp`, `*.vcd`, `obj_dir/`: as in the
  2x2 study (`../README.md`, "Not in git").
