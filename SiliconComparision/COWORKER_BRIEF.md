---
# Brief: latch vs no-latch silicon comparison
Goal: measure the area, power, timing and parasitic cost or benefit of removing the inferred latches STITCH
repaired. This is NOT a claim that STITCH improves PPA; STITCH targets sign-off correctness.

Variants: A = original as written (register_1bit aborts Yosys). A1 = control: A with only register_1bit
fixed, all latches kept. B = repaired (golden leaves). C = an actual STITCH repair (optional). PRIMARY PAIR:
A1 vs B. B vs C should be nearly identical (the repairs were formally checked against golden).

Primer: a latch is level-sensitive (transparent while enabled); a flip-flop samples at a clock edge (two
latches back to back). Inferred latches come from incomplete if/case assignments or level-sensitive
registers; they have no clock, so timing sign-off cannot check them properly.

Scaling check: 36 latched bits x 20 instances per router = 720 latch cells per router, so 2,880 (4 routers)
and 6,480 (9 routers). MPSoC top: 269 -> 122 after repair; the 122 are in 5 modules outside the repair set.

Metrics (state tools, versions, library, seeds):
1. Yosys: cells by type, latch/flop/mux counts, area via a liberty file (sky130_fd_sc_hd or Nangate45; pick
   one and keep it).
2. OpenSTA/OpenROAD: WNS/TNS, unconstrained endpoints, latch time-borrowing paths, power with identical
   activity (same VCD from the same stimulus, or the same vectorless defaults).
3. OpenROAD place and route: identical floorplan, utilisation and seeds (at least 3); core area, wirelength,
   SPEF total capacitance, clock-net capacitance.
4. Optional: ngspice on sky130 cells (dlxtp vs dfxtp vs a mux) for switching energy and glitch
   propagation. Optional: Vivado (LUT/FF/LATCH counts, power with SAIF, WNS); A as written may be
   accepted by Vivado.

Rules: same top, constraints, library, tool versions and seeds for every variant. The MPSoC top-level
testbench is weak (2 instructions, no network traffic), so do not use it for power; use leaf testbenches
or seeded random vectors. The repaired leaves differ from the latch versions only where the latch held an
old value (equivalent on legal inputs), so say so in the results. Report per leaf and per level.

Hypotheses to confirm or refute: (a) mux-type leaves lose their storage cell, so area drops slightly;
(b) register_32bit/4bit change from latches to flip-flops, so area and power per bit probably rise while
timing becomes analysable; (c) OpenSTA reports unconstrained or clockless endpoints for the inferred
latch enables in A1 but not in B. The net PPA sign is an open question.

Report back: a table, variant x design x (cells, latches, flops, area, WNS, power, wirelength, total
capacitance), plus a short note on anything surprising.
---