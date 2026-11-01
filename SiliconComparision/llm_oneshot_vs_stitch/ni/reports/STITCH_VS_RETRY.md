# STITCH vs simulation-only retry (pipeline/stitch_vs_retry.py)

Flags: C compile, F tb.v, S tb_signoff.v, K struct_clean (local re-evaluation of the final files). it = LLM calls, sf = STITCH semantic feedback fired. Directive codes: `iteration:codes` fed back after that iteration (stitch arm).

## Outcome classes

| class | count | modules |
|---|---|---|
| already_clean | 0 | - |
| both_fixed | 0 | - |
| stitch_only | 0 | - |
| retry_only | 0 | - |
| neither | 4 | depack, new1, nidepack, rp1 |

## Prompt equivalence (stitch runs with sf=0 and at least one call in both arms)

0 of 0 such modules got byte-identical prompts in both arms: -. These modules cannot distinguish the arms.


## Sampling

The first LLM call of the two arms gets the same prompt (feedback-first protocol). In 4 modules both arms made that call with a byte-identical prompt; in 1 of them the two answers differ (new1). Generation used temperature 0.1 with no seed, so a difference between the arms can come from sampling alone. Below, each gain or regression names the first iteration where the arms' RTL differs and whether the prompts differed there.

## Gains (stitch has the flag, simloop does not)


## Regressions (simloop has the flag, stitch does not)

- new1: compile per iteration (0 = one-shot): simloop `..CCCCC`, stitch `...CC..`; arms first produce different RTL at iteration 1: identical prompt, different sample (not attributable to STITCH)
- new1: struct_clean (K) per iteration (0 = one-shot): simloop `..KKKKK`, stitch `...KK..`; arms first produce different RTL at iteration 1: identical prompt, different sample (not attributable to STITCH)

## STITCH fired (sf=1) and the final still fails: 4 modules

Audit class (reports/FAILURE_AUDIT.md): LLM_BUG 4

depack (LLM_BUG), new1 (LLM_BUG), nidepack (LLM_BUG), rp1 (LLM_BUG)

## Where STITCH helped

Final flag better than the simulation-only loop: none. Of these, the arms diverged after a different (STITCH) prompt in: none; after an identical prompt (sampling) in: none. No module reached so_clean under STITCH only (0).

## Where it did not

STITCH fired but the final still fails (4): depack, new1, nidepack, rp1. Never fired and failed in both arms: -.

## Where it hurt

Final flag worse than the simulation-only loop: new1. Arms diverged after a different (STITCH) prompt in: none; after an identical prompt (sampling) in: new1.

## Per module

| module | one-shot | simloop final | stitch final | stitch directive codes per iteration | outcome |
|---|---|---|---|---|---|
| depack | C..K | C..K it=6 | C..K it=6 sf=1 | 2:MULTIDRIVEN / 3:MULTIDRIVEN / 4:MULTIDRIVEN / 5:MULTIDRIVEN | neither |
| new1 | .... | C..K it=6 | .... it=6 sf=1 | 4:UNUSEDSIGNAL | neither |
| nidepack | .... | .... it=6 | .... it=6 sf=1 | 1:PINMISSING / 2:UNUSEDSIGNAL / 3:PINMISSING / 4:UNUSEDSIGNAL / 5:PINMISSING,UNUSEDSIGNAL | neither |
| rp1 | C... | C... it=6 | C... it=6 sf=1 | 1:CLOCK_UNUSED,WIDTHEXPAND,WIDTHTRUNC / 2:CLOCK_UNUSED,WIDTHEXPAND,WIDTHTRUNC / 4:CLOCK_UNUSED / 5:CLOCK_UNUSED,WIDTHEXPAND,WIDTHTRUNC | neither |
