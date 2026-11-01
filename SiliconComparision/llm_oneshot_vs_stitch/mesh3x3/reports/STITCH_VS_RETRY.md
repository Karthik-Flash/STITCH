# STITCH vs simulation-only retry (pipeline/stitch_vs_retry.py)

Flags: C compile, F tb.v, S tb_signoff.v, K struct_clean (local re-evaluation of the final files). it = LLM calls, sf = STITCH semantic feedback fired. Directive codes: `iteration:codes` fed back after that iteration (stitch arm).

## Outcome classes

| class | count | modules |
|---|---|---|
| already_clean | 0 | - |
| both_fixed | 0 | - |
| stitch_only | 0 | - |
| retry_only | 0 | - |
| neither | 1 | top_3x3_router |

## Prompt equivalence (stitch runs with sf=0 and at least one call in both arms)

0 of 0 such modules got byte-identical prompts in both arms: -. These modules cannot distinguish the arms.


## Sampling

The first LLM call of the two arms gets the same prompt (feedback-first protocol). In 1 modules both arms made that call with a byte-identical prompt; in 0 of them the two answers differ (). Generation used temperature 0.1 with no seed, so a difference between the arms can come from sampling alone. Below, each gain or regression names the first iteration where the arms' RTL differs and whether the prompts differed there.

## Gains (stitch has the flag, simloop does not)


## Regressions (simloop has the flag, stitch does not)

- top_3x3_router: compile per iteration (0 = one-shot): simloop `C..C..C`, stitch `C..C.C.`; arms first produce different RTL at iteration 4: different prompt; stitch carried: directives UNUSEDSIGNAL, WIDTHEXPAND; escalated
- top_3x3_router: struct_clean (K) per iteration (0 = one-shot): simloop `K..K..K`, stitch `K..K.K.`; arms first produce different RTL at iteration 4: different prompt; stitch carried: directives UNUSEDSIGNAL, WIDTHEXPAND; escalated

## STITCH fired (sf=1) and the final still fails: 1 modules

Audit class (reports/FAILURE_AUDIT.md): LLM_BUG 1

top_3x3_router (LLM_BUG)

## Where STITCH helped

Final flag better than the simulation-only loop: none. Of these, the arms diverged after a different (STITCH) prompt in: none; after an identical prompt (sampling) in: none. No module reached so_clean under STITCH only (0).

## Where it did not

STITCH fired but the final still fails (1): top_3x3_router. Never fired and failed in both arms: -.

## Where it hurt

Final flag worse than the simulation-only loop: top_3x3_router. Arms diverged after a different (STITCH) prompt in: top_3x3_router; after an identical prompt (sampling) in: none.

## Per module

| module | one-shot | simloop final | stitch final | stitch directive codes per iteration | outcome |
|---|---|---|---|---|---|
| top_3x3_router | C..K | C..K it=6 | .... it=6 sf=1 | 3:UNUSEDSIGNAL,WIDTHEXPAND / 5:UNUSEDSIGNAL | neither |
