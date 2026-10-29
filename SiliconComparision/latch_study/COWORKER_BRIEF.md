---
# Brief: latch vs no-latch silicon comparison
Goal: measure what repairing unintended latches costs and buys. The claim is sign-off correctness, not improved
PPA. A latch is level-sensitive storage; a flip-flop samples at a clock edge.

An inferred latch is storage the designer never asked for. It appears when combinational code leaves an output
unassigned on some path (for example, a missing `else`), or when a register is coded level-sensitive instead of
edge-triggered. Both occur here. This is hazardous because:
- the enable is not a clean clock, so timing tools may skip or mis-time the path;
- a glitch on the enable can corrupt stored data;
- scan and test insertion can break;
- behavior can differ between tools.

STITCH detects these defects from lint and synthesis output and repairs the RTL. The study measures what repair
costs and buys; PPA may change only slightly or even get slightly worse.

Variants: A = original as written (register_1bit aborts Yosys); A1 = A with only register_1bit fixed, all
latches retained; B = golden repairs; C = actual STITCH repair. Primary comparison: 2x2 mesh A1 vs B vs C.
B and C should be nearly identical. A is the expected-failure baseline, not a PPA result.

The mesh's 2,880 (2x2) and 6,480 (3x3) latches come only from `register_32bit` and `register_4bit`.
Repair changes these to flip-flops. SKY130HD flip-flops are larger than latches and add clock load; expect a
small area and clock-power increase, not a reduction. Latches are about 3% of mesh cells, so the delta may be
only a few percent and within placement noise. The benefit under study is timing analysability and sign-off
correctness. The MPSoC top drops from 269 to 122 latches; the remaining 122 are outside the repair set.

Work completed: `PPA_SUMMARY.md` records the supplied one-run A1/B results for both mesh sizes, their derived
area/power deltas, and the limits of the unmatched activity and single-seed comparison. The analysis bundle is
local-only. The key check still left out is whether A1 has untimed or clockless endpoints that B does not; endpoint
and clock-sink counts have not been measured.

Run priorities:
1. Primary: 2x2 mesh, A1 vs B vs C, with at least 3 placement seeds.
2. Optional scaling check: 3x3 mesh, A1 vs B; latch count should scale by about 9/4.
3. Skip the MPSoC top unless time allows; its 2-instruction, no-network-traffic testbench is weak.
4. Cheap leaf check: Yosys plus the same liberty file on each task's `defective.v` and `golden.v` (all 11 leaves).

Use the existing ORFS open flow, SKY130HD library and 10 ns clock. Keep top, constraints, tool versions, activity,
die dimensions and other settings identical. Use a fixed die size, not a utilization target, and report the spread
across seeds. For A1 and B, run OpenSTA `check_setup` and `report_checks -unconstrained`; count endpoints that are
not timed.

### The extra metric: unconstrained or clockless endpoints

Static timing analysis checks paths from launching registers to capturing registers. If a path starts or ends at a
latch whose enable cannot be traced to a clock, the tool may skip it silently. No reported violation does not mean
the path was checked.

For A1 and B, run `check_setup -verbose` and `report_checks -unconstrained` in OpenSTA. Count endpoints that were
not timed, and count the clock sinks reached by the clock. These values are not measured in the supplied run.

**HYPOTHESIS: to confirm.** Expected outcomes to test, not results:

| Metric | A1 (latches) | B (repaired) |
|---|---|---|
| Clock sinks | Fewer | About 2,880 more on 2x2 |
| Unconstrained endpoints | Some or many, possibly around latch enables | Few or none |
| Reported slack | May be flattering; prior 2x2 report noted +0.64 ns | Timed result may be lower |

If A1 has untimed endpoints and B does not, that supports timing analysability as a benefit. If A1 has none, report
that result plainly; do not claim that its slack was optimistic.

Report one compact table per variant (A1, B, C) and one delta table, not a separate report per design. Summarize
the primary 2x2 across seeds and include the optional 3x3 result in the same tables if run. Use these metrics:
- latch cells / flop cells;
- final standard-cell instance area (not synthesis area or fill-cell area);
- WNS / TNS (ns) and unconstrained endpoint count;
- total power split into sequential / clock / combinational (mW), with identical activity;
- one consistently defined total wire-capacitance measure (not raw SPEF ground/coupling sums);
- max-slew and max-cap violations.

**A1**

| Metric | 2x2 primary (median [range]) | 3x3 optional |
|---|---|---|---|
| Latch cells / flop cells | TBD | TBD |
| Std-cell instance area, final (um^2) | TBD | TBD |
| WNS / TNS (ns) | TBD | TBD |
| Unconstrained endpoints | TBD | TBD |
| Total power: sequential / clock / combinational (mW) | TBD | TBD |
| Total wire capacitance (pF; same method) | TBD | TBD |
| Max-slew / max-cap violations | TBD | TBD |

**B**

| Metric | 2x2 primary (median [range]) | 3x3 optional |
|---|---|---|
| Latch cells / flop cells | TBD | TBD |
| Std-cell instance area, final (um^2) | TBD | TBD |
| WNS / TNS (ns) | TBD | TBD |
| Unconstrained endpoints | TBD | TBD |
| Total power: sequential / clock / combinational (mW) | TBD | TBD |
| Total wire capacitance (pF; same method) | TBD | TBD |
| Max-slew / max-cap violations | TBD | TBD |

**C**

| Metric | 2x2 primary (median [range]) | 3x3 optional |
|---|---|---|
| Latch cells / flop cells | TBD | TBD |
| Std-cell instance area, final (um^2) | TBD | TBD |
| WNS / TNS (ns) | TBD | TBD |
| Unconstrained endpoints | TBD | TBD |
| Total power: sequential / clock / combinational (mW) | TBD | TBD |
| Total wire capacitance (pF; same method) | TBD | TBD |
| Max-slew / max-cap violations | TBD | TBD |

**Delta and leaf area**

| Metric / leaf | B-A1 (%) | C-B (%) | Defective-to-golden leaf area (%) | STITCH-to-golden leaf area (%) |
|---|---|---|---|---|
| Latch cells / flop cells | TBD | TBD | n/a | n/a |
| Final standard-cell instance area | TBD | TBD | n/a | n/a |
| WNS / TNS | TBD | TBD | n/a | n/a |
| Unconstrained endpoints (absolute count delta) | TBD | TBD | n/a | n/a |
| Total power by component | TBD | TBD | n/a | n/a |
| Total wire capacitance | TBD | TBD | n/a | n/a |
| Max-slew / max-cap violations (absolute count delta) | TBD | TBD | n/a | n/a |
| Address_select | n/a | n/a | TBD | TBD |
| execute_mux | n/a | n/a | TBD | TBD |
| mem_wb_mux | n/a | n/a | TBD | TBD |
| mux3 | n/a | n/a | TBD | TBD |
| MuxPC | n/a | n/a | TBD | TBD |
| ni_flit_pack | n/a | n/a | TBD | TBD |
| noc_xbar4 | n/a | n/a | TBD | TBD |
| register_1bit | n/a | n/a | TBD | TBD |
| register_32bit | n/a | n/a | TBD | TBD |
| register_4bit | n/a | n/a | TBD | TBD |
| riscv_alu_flags | n/a | n/a | TBD | TBD |

Keep detailed file listings, GDS/congestion notes and recommended actions in private notes, not the report.
End with exactly three short lines: tool versions; placement seeds; anything surprising.
---