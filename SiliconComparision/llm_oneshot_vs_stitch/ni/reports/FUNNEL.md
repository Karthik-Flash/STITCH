# Stage funnel (pipeline/funnel.py)

Per module and arm: the first failing stage (bold), or ok. Stages: compiles -> loop tb -> sign-off tb -> synthesises -> latch/loop-free -> composes. composes = golden ni_pair design with only this module from the arm passes the top-level sign-off tb (drop-in). it = LLM calls, sf = STITCH semantic feedback fired.

## Totals: modules reaching each stage (counts of 4)

| stage | oneshot | simloop | stitch |
|---|---|---|---|
| compiles | 2 | 3 | 2 |
| loop tb | 0 | 0 | 0 |
| sign-off tb | 0 | 0 | 0 |
| synthesises | 0 | 0 | 0 |
| latch/loop-free | 0 | 0 | 0 |
| composes | 0 | 0 | 0 |

## Totals: first failing stage

| first failing stage | oneshot | simloop | stitch |
|---|---|---|---|
| compiles | 2 | 1 | 2 |
| loop tb | 2 | 3 | 2 |
| sign-off tb | 0 | 0 | 0 |
| synthesises | 0 | 0 | 0 |
| latch/loop-free | 0 | 0 | 0 |
| composes | 0 | 0 | 0 |
| passes all | 0 | 0 | 0 |

## Modules that fail only at composes

- none

## REUSED modules: 5, results of the 2x2 study (`../reports/FUNNEL.md`)

Flags of the 2x2 final file (C compile, F tb.v, S tb_signoff.v, K struct_clean); so_clean = S and K.

| module | oneshot | simloop | stitch |
|---|---|---|---|
| asynch_comparator | reused (2x2): .... | reused (2x2): C..K | reused (2x2): C..K |
| gray_mod6 | reused (2x2): .... | reused (2x2): C..K | reused (2x2): C..K |
| jk_ff | reused (2x2): CFSK **so_clean** | reused (2x2): CFSK **so_clean** | reused (2x2): CFSK **so_clean** |
| memory | reused (2x2): CFSK **so_clean** | reused (2x2): CFSK **so_clean** | reused (2x2): CFSK **so_clean** |
| router_fifo | reused (2x2): C..K | reused (2x2): C..K | reused (2x2): C..K |

## Per module

| module | oneshot | simloop | stitch |
|---|---|---|---|
| depack | **loop tb** | **loop tb** it=6 sf=0 | **loop tb** it=6 sf=1 |
| new1 | **compiles** | **loop tb** it=6 sf=0 | **compiles** it=6 sf=1 |
| nidepack | **compiles** | **compiles** it=6 sf=0 | **compiles** it=6 sf=1 |
| rp1 | **loop tb** | **loop tb** it=6 sf=0 | **loop tb** it=6 sf=1 |
