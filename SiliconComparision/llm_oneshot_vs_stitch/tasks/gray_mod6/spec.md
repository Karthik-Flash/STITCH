# gray_mod6

## Behaviour

Modulo-6 Gray-code counter with enable and a wrap flag.

- On each rising edge of `clk`, when `en` is 1, `gray_out` advances through 000, 001, 011, 010, 110,
  100 and back to 000. When `en` is 0 it holds.
- `dir` toggles each time `gray_out` leaves 100 (the wrap from 100 back to 000).

## Reset

Synchronous, active-high `reset`: `gray_out` becomes 000 at the next rising `clk` edge. `dir` is reset
to 0 only at its own toggle event (when the state leaves 100). In simulation this also happens when the
state first changes from unknown to 000 during reset.

## Ports

5 ports, in this exact order:

```verilog
input clk, reset, en;
output [2:0] gray_out;
output dir;
```

Parameters: none.

## Children

Must instantiate exactly these modules (ports listed in each child's own order):

- `jk_ff` x 4: (j, k, reset, en, clk, q, qbar)
