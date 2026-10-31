# depack

## Behaviour

Network-interface depacketiser: rebuilds 32-bit words from the body flits of incoming packets.

Flit format (32-bit word): bits [30:29] give the flit type: 01 = header, 10 = tailer, 11 = idle,
00 = body.

A state machine advances on each rising edge of `wr_clk` (when `reset` is 0). All outputs are registered.

| state | condition on `flit[30:29]` | action | next state |
|---|---|---|---|
| state0 | 01 (header) | `wr_en` = 0 | header |
| state0 | otherwise | `wr_en` = 0 | state0 |
| header | 00 (body) | `wr_en` = 0; store `flit[15:0]` as the low half | firsthalf |
| header | otherwise | none (`wr_en` holds its value) | header |
| firsthalf | 10 (tailer) | `wr_en` = 0 | state0 |
| firsthalf | otherwise | `wr_en` = 1, `c_rd` = 1, `data_out` = `{flit[15:0], low half}` | header |

`data_out` changes only in the last row. `c_rd` is only ever set to 1.

`wr_en` is held: after a completed word (firsthalf to header with `wr_en` = 1) it stays 1 while the machine waits in
header, and is cleared only by the next body flit or by reset. While it is held, `data_out` keeps the completed word.

- `c_rd` is not used by the parent (nidepack leaves it open): not checked.

## Reset

Synchronous, active-high `reset`: on a rising `wr_clk` edge with `reset` = 1, state0 and `wr_en` = 0.
`data_out`, `c_rd` and the stored low half are not reset (unknown until first written).

## Ports

6 ports, in this exact order:

```verilog
input [31:0] flit;
input wr_clk, reset;
output [31:0] data_out;
output wr_en, c_rd;
```

Parameters: firsthalf=2;header=1;nextstate=4;secondhalf=3;state0=0.

## Children

None. This module instantiates no other module.
