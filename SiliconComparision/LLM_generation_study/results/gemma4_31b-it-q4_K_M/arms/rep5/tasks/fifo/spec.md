# fifo

## Behaviour

Input buffer of one router port: a first-in first-out queue of up to 4 words of 32 bits.

- On a rising `clk` edge with `wr_en` = 1, `din` is stored behind the words already held. If 4 words are
  already held before that edge, the write is ignored, even when `rd_en` = 1 at the same edge.
- On a rising `clk` edge with `rd_en` = 1, the oldest stored word is removed. If no word is held before that
  edge, the read is ignored.
- A write and a read at the same edge both take effect (when allowed by the two rules above): the oldest word
  leaves and `din` is stored, so the number of stored words does not change.
- `dout` always shows the oldest stored word, with no clock edge needed: after the edge that stores a word
  into an empty buffer, `dout` already shows that word; after the edge that removes the oldest word, `dout`
  shows the next one. While the buffer is empty, the value of `dout` does not matter.
- `empty` = 1 when 0 words are stored.
- `almost_full` = 1 when 3 or 4 words are stored.

## Reset

Synchronous, active-high `reset`: at a rising `clk` edge with `reset` = 1 the buffer becomes empty, and
`wr_en` and `rd_en` at that edge are ignored. The stored data values do not need to be cleared.

## Ports

8 ports, in this exact order:

```verilog
input clk;
input reset;
input wr_en;
input [31:0] din;
input rd_en;
output [31:0] dout;
output empty;
output almost_full;
```

Parameters: none.

## Children

None. This module instantiates no other module.
