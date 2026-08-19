# Proven illustration results

Summary metrics only. Per-iteration run data — generated `.v` files, model
responses, simulation logs, feedback text — is deliberately excluded from this
repository (see `.gitignore`). Each `metrics.json` carries the per-iteration
record needed to reconstruct a run's outcome: verdict, iteration count,
`semantic_fired`, Verilator codes seen, token counts, and per-iteration error
classification.

## Layout

```
decoder_3to8/<model>/<condition>/metrics.json
mux4_oe/<model>/<condition>/metrics.json
n3_replication/<model>/<module>/<condition>/sample_N/metrics.json
n3_replication_post_parameterisation/<module>/sample_N/metrics.json
```

## What each set establishes

**`decoder_3to8/`** — single-run three-condition verification on `gemma3:4b`
against the current pipeline. Reproduces the pattern the MLCAD paper reports
for this module.

**`mux4_oe/`** — three-condition results on `gemma3:4b` (enabling regime) and
`llama3.1:latest` (efficiency regime). The second module to reproduce the
mechanism end to end.

**`n3_replication/`** — the full replication: 2 models x 2 modules x 3
conditions x 3 samples = 36 cells, all at `temperature=0.1`.

> **Read this before citing the replication.** The three samples per cell are
> *not* three independent draws. At `temperature=0.1` the output distribution
> is near-degenerate: iteration-1 generated Verilog was byte-identical across
> all three samples in 6 of 12 cells, and where it varied the verdict and
> iteration count did not. These results establish **reproducibility, not a
> variance bound**. See `plans/research_plan_v4.md` §2 for the methodology
> decision that follows.

**`n3_replication_post_parameterisation/`** — the `sem_adv` condition re-run
after the UNUSEDSIGNAL directive template was parameterised, confirming the
result is unaffected by that change. 3/3 PASS in 2 iterations for both modules.

## Headline figures

| Model | Module | baseline | raw_adv | sem_adv |
|---|---|---|---|---|
| gemma3:4b | `decoder_3to8` | 0/3 pass | 0/3 pass | **3/3 pass, 2 iters** |
| gemma3:4b | `mux4_oe` | 0/3 pass | 0/3 pass | **3/3 pass, 2 iters** |
| llama3.1 | `decoder_3to8` | 3/3, 2 iters | 3/3, 2 iters | 3/3, 2 iters |
| llama3.1 | `mux4_oe` | 3/3, 4 iters | 3/3, 4 iters | **3/3, 2 iters** |

In every cell `raw_adv` matches `baseline` exactly. That is the control which
isolates the effect to interpretation rather than to tool presence.
