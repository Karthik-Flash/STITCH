# rp1

## Behaviour

Network-interface packetiser: turns one 32-bit word from the core-side FIFO into a packet of flits.

Flit format (32-bit word): bits [30:29] give the flit type: 01 = header, 10 = tailer, 11 = idle,
00 = body. Bits [28:27] carry the virtual-channel (VC) number, 00 = VC1. The idle word is 32'h6000_0000.

A state machine advances on each rising edge of `rd_clk` (when `reset` is 0). `niout`, `wr_o` and the state
are registered; `wr_clk` is not used. Two internal counters, `i` (packet words sent) and `j` (body pairs sent),
are compared with parameter `N` (= 1).

| state | `niout` written on this edge | next state |
|---|---|---|
| idle | unchanged | header if `wr_en` = 1, else idle |
| header | `{1'b0, 2'b01, 2'b00, 11'd0, source, dest}` (header flit, VC1) | payload1 |
| payload1 | `{1'b0, 2'b00, 2'b00, 11'd0, data_in[15:0]}` (body flit); `j` increments | payload2 |
| payload2 | `{1'b0, 2'b00, 2'b00, 11'd0, data_in[31:16]}` (body flit); `i` increments | see below |
| tailer | `{1'b0, 2'b10, 29'd0}` = 32'h4000_0000 (tailer flit) | last |
| last | 32'h7FFF_FFFF | last |

In payload2, after `i` increments: if `i` = N the next state is tailer. Then, if `j` = N, `wr_o` becomes 1 and
the next state stays as just set (tailer if `i` = N, otherwise payload2); if `j` != N the next state is
payload1, overriding tailer.

`rd_en` (the FIFO read enable) is updated on each falling edge of `rd_clk`: 1 when the state is header or
payload2, otherwise 0.

## Reset

Synchronous, active-high `reset`. On a rising `rd_clk` edge with `reset` = 1: `niout` = 32'h6000_0000, state
idle, `i` = 0, `wr_o` = 0. On a falling `rd_clk` edge with `reset` = 1: `rd_en` = 0. `j` is initialised to 0 at
declaration and is not cleared by reset: it keeps counting across resets.

## Ports

<!-- BEGIN generated: ports -->
10 ports, in this exact order:

```verilog
input [31:0] data_in;
input [7:0] dest, source;
input rd_clk, wr_clk, wr_en, reset;
output [31:0] niout;
output rd_en, wr_o;
```

Parameters: N=1;header=1;idle=0;last=5;payload1=2;payload2=3;tailer=4.
<!-- END generated: ports -->

## Children

<!-- BEGIN generated: children -->
None. This module instantiates no other module.
<!-- END generated: children -->

Unclear in golden: `j` has only a declaration initial value (`integer j = 0`), no reset. The first packet after
power-up ends with tailer and last; after any later reset, `j` != N in payload2, so the machine alternates
payload1 and payload2 for ever (one packet per power-up). A synthesised netlist has no initial value for `j`.
The `else` in payload2 binds to `if (j == N)`, not to `if (i == N)`. All assignments are blocking.
