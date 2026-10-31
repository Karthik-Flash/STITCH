# Hand-written RTL tool pass (ni; pipeline/handwritten_check.py)

golden/handwritten = the hand-written RTL as received (sanitised copy); golden/A1 = its synthesisable copy (latch_study A1: only Yosys-aborting modules fixed).

## Per root

| root | handwritten: Yosys | A1: Yosys cells | A1 latch cells | A1 check problems | A1 logic loops | Verilator errors / hard (handwritten) | hard codes |
|---|---|---|---|---|---|---|---|
| new1 | ok | 1052 | 0 | 0 | 0 | 0 / 0 | - |
| nidepack | ok | 747 | 0 | 0 | 0 | 0 / 0 | - |

## Yosys front-end warnings (handwritten)

- new1: 2 implicitly declared nets: router_fifo.v: ren_int; router_fifo.v: wen_int
- new1: 0 cell ports resized
- nidepack: 2 implicitly declared nets: router_fifo.v: ren_int; router_fifo.v: wen_int
- nidepack: 0 cell ports resized

## Per module

Latch cells per module: modules.csv own_storage (`$dlatch`), golden/A1 after proc.

| module | file | children | kind | own storage | clock ports | reset ports | latch-enable ports | clocking | clock sources |
|---|---|---|---|---|---|---|---|---|---|
| asynch_comparator | asynch_comparator.v | - | combinational | - | - | - | - | none (combinational) | - |
| jk_ff | jk_ff.v | - | sequential | $sdffx4 | clk | reset | - | system clock | clk |
| gray_mod6 | gray_mod6.v | jk_ffx4 | sequential | - | clk | reset | - | gated | clk, internal net |
| memory | memory.v | - | sequential | $memrdx1, $memwr_v2x1, $sdffx1 | rd_clk;wr_clk | reset | - | system clock | rd_clk, wr_clk |
| router_fifo | router_fifo.v | asynch_comparatorx1, gray_mod6x2, memoryx1 | sequential | - | rd_clk;wr_clk | reset | - | system clock | child gray_mod6, rd_clk, wr_clk |
| rp1 | rp1.v | - | sequential | $dffx1, $sdffx5 | rd_clk | reset | - | system clock | rd_clk |
| new1 | new.v | router_fifox1, rp1x1 | sequential | - | rd_clk;wr_clk | reset | - | system clock | rd_clk, wr_clk |
| depack | depack.v | - | sequential | $dffx3, $sdffx2 | wr_clk | reset | - | system clock | wr_clk |
| nidepack | nidepack.v | depackx1, router_fifox1 | sequential | - | rd_clk;wr_clk | reset | - | system clock | rd_clk, wr_clk |
