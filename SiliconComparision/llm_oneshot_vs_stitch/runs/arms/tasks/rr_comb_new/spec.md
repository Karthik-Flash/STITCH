# rr_comb_new

## Behaviour

Fixed-priority grant selector, priority 2 > 3 > 4 > 1, with grant hold. It chooses which of the four
output VCs of one output port sends on the physical link. `r1` to `r4` are the VC ready signals. A grant
is held while its VC stays ready. When no grant is held, the next grant goes to `r2` if ready, else
`r3`, else `r4`, else `r1`. It is not round-robin. The exact equations follow.

- State: four grant bits G1 to G4, updated on each rising `clk` edge.
- `gi` = Gi AND `ri` (combinational).
- `and_outi` = 1 when `gi` is the only active `g` (for example `and_out1` = `g1` AND NOT `g2` AND NOT
  `g3` AND NOT `g4`). `or_out` = `g1` OR `g2` OR `g3` OR `g4`.
- `b1`,`b0` = code of the single active grant: only `g1` gives 00, only `g2` 01, only `g3` 10, only
  `g4` 11; no grant or several grants give 00.
- Next-grant candidates (combinational):
  - `l1` = `r1` & !`g2` & !`g3` & !`g4` & ((!`r3` & !`r4` & (`b0` | (!`b1` & !`r2`))) | (`b1` & (`b0` | !`r4`)))
  - `l2` = `r2` & !`g1` & !`g3` & !`g4` & ((!`b0` & !`r1` & !`r4`) | (!`r1` & !`r3` & !`r4`) | (`b1` & `b0` & !`r1`) | (!`b1` & !`b0`))
  - `l3` = `r3` & !`g2` & !`g1` & !`g4` & ((!`r1` & !`r2` & !`r4`) | (`b0` & !`r1` & !`r2`) | (!`b1` & !`r2`) | (!`b1` & `b0`))
  - `l4` = `r4` & !`g2` & !`g3` & !`g1` & ((!`b1` & !`r2` & !`r3`) | (!`r1` & !`r2` & !`r3`) | (!`b1` & `b0` & !`r3`) | (`b1` & !`b0`))
- `mux_outi` = `ri` when `and_outi` is 1, else `li`. On each rising `clk` edge, Gi takes `mux_outi`.
- These equations give exactly the fixed-priority rule above (checked in simulation).
- `b1_logic` and `b0_logic` are not driven in the golden: not checked.

## Reset

Synchronous, active-high `reset`: G1 to G4 become 0 at the next rising `clk` edge.

## Ports

27 ports, in this exact order:

```verilog
input reset, clk, r1, r2, r3, r4;
output g1, g2, g3, g4, l1, l2, l3, l4, mux_out1, mux_out2, mux_out3, mux_out4, and_out1, and_out2, and_out3,
       and_out4, or_out, b1, b0, b1_logic, b0_logic;
```

Parameters: none.

## Children

Must instantiate exactly these modules (ports listed in each child's own order):

- `dff_synch_clr` x 4: (d, clr, clk, q)
