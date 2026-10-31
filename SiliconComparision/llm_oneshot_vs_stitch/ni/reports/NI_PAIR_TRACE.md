# One packet through the all-golden ni_pair (pipeline/ni_pair_trace.py)

Core word 32'h1234_abcd written once after reset; Icarus; samples 4 ns after each rising clock edge (cycle 0 = the edge after the write). depack wr_en / data_out and FIFO full are nidepack's internal nets (D1.wr_en, D1.depack_out, D1.full_int, D1.empty). The shifted connection (phase3/designs/SANITISATION.md item 3) puts router_fifo's full_ext (4 or more entries) on the net named full_int and its full_int (6 entries) on the net named empty.

| cycle | niout | depack wr_en | depack data_out | net full_int = FIFO 4+ entries | net empty = FIFO full |
|---|---|---|---|---|---|
| 0 | 20000011 | 0 | xxxxxxxx | 0 | 0 |
| 1 | 0000abcd | 0 | xxxxxxxx | 0 | 0 |
| 2 | 00001234 | 0 | xxxxxxxx | 0 | 0 |
| 3 | 40000000 | 1 | 12341234 | 0 | 0 |
| 4 | 7fffffff | 1 | 12341234 | 0 | 0 |
| 5 | 7fffffff | 1 | 12341234 | 0 | 0 |
| 6 | 7fffffff | 1 | 12341234 | 0 | 0 |
| 7 | 7fffffff | 1 | 12341234 | 1 | 0 |
| 8 | 7fffffff | 1 | 12341234 | 1 | 0 |
| 9 | 7fffffff | 1 | 12341234 | 1 | 1 |
| 10 | 7fffffff | 1 | 12341234 | 1 | 1 |
| 11 | 7fffffff | 1 | 12341234 | 1 | 1 |
| 12 | 7fffffff | 1 | 12341234 | 1 | 1 |
| 13 | 7fffffff | 1 | 12341234 | 1 | 1 |
| 14 | 7fffffff | 1 | 12341234 | 1 | 1 |
| 15 | 7fffffff | 1 | 12341234 | 1 | 1 |
| 16 | 7fffffff | 1 | 12341234 | 1 | 1 |
| 17 | 7fffffff | 1 | 12341234 | 1 | 1 |
| 18 | 7fffffff | 1 | 12341234 | 1 | 1 |
| 19 | 7fffffff | 1 | 12341234 | 1 | 1 |
| 20 | 7fffffff | 1 | 12341234 | 1 | 1 |
| 21 | 7fffffff | 1 | 12341234 | 1 | 1 |
| 22 | 7fffffff | 1 | 12341234 | 1 | 1 |
| 23 | 7fffffff | 1 | 12341234 | 1 | 1 |
| 24 | 7fffffff | 1 | 12341234 | 1 | 1 |
| 25 | 7fffffff | 1 | 12341234 | 1 | 1 |
| 26 | 7fffffff | 1 | 12341234 | 1 | 1 |
| 27 | 7fffffff | 1 | 12341234 | 1 | 1 |
| 28 | 7fffffff | 1 | 12341234 | 1 | 1 |
| 29 | 7fffffff | 1 | 12341234 | 1 | 1 |
