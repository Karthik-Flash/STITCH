# rr_arbiter

## Behaviour

Round-robin arbiter for four requesters with registered grants.

- At most one of `gnt1` to `gnt4` is 1. All grants are 0 while `reset` is 1.
- A grant is issued on a rising `clk` edge and is held while its request stays 1.
- When the granted request drops, the grant drops at the next rising `clk` edge. The arbiter then
  rotates priority so the requester after the one just served is first (after requester i: i+1, i+2,
  i+3, i, wrapping 4 to 1). The next grant is issued at the following rising `clk` edge, which leaves one
  idle cycle between grants.
- After reset the priority order is 1, 2, 3, 4. The first grant can take two rising `clk` edges after
  `reset` falls.
- Simulation check (all four requesting, each grant released after two cycles): grants go 1, 2, 3, 4, 1,
  ... with one idle cycle between them.

## Reset

Active-high `reset`: grants forced to 0 combinationally. All internal priority state clears
asynchronously.

## Ports

<!-- BEGIN generated: ports -->
10 ports, in this exact order:

```verilog
input req1, req2, req3, req4, reset;
output gnt1, gnt2, gnt3, gnt4;
input clk;
```

Parameters: none.
<!-- END generated: ports -->

## Children

<!-- BEGIN generated: children -->
Must instantiate exactly these modules (ports listed in each child's own order):

- `dff_asynch_clr` x 5: (d, clr, clk, q)
- `falling_edge_pulse_generator` x 4: (reset, gnt, clk, q0)
- `priority_encoder` x 4: (reset, en, in0, in1, in2, in3, out0, out1, out2, out3, clk)
<!-- END generated: children -->

Unclear in golden: the rotation state is held in flip-flops clocked by grant-derived pulses (falling_edge_pulse_generator)
and cleared asynchronously by other pulses. The exact moment the priority rotates depends on gate
delays, not on `clk` alone. Each priority_encoder's `reset` pin is unused. Nothing latch-dependent.
