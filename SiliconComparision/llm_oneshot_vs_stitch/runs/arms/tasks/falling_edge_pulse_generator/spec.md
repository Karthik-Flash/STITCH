# falling_edge_pulse_generator

## Behaviour

Turns a falling edge of `gnt` into a pulse on `q0` that lasts until the next rising `clk` edge.

- `q0` becomes 1 on each falling edge of `gnt`.
- An internal flag F takes the value of `q0` on each rising `clk` edge. While F is 1, `q0` is held at 0.
  So `q0` ends shortly after the first rising `clk` edge that follows its rise, and F returns to 0 at
  the next `clk` edge.

## Reset

Asynchronous, active-high `reset`: `q0` and F go to 0 and stay 0 while `reset` is 1.

## Ports

4 ports, in this exact order:

```verilog
input reset, gnt, clk;
output q0;
```

Parameters: none.

## Children

Must instantiate exactly these modules (ports listed in each child's own order):

- `dff_asynch_clr` x 2: (d, clr, clk, q)
