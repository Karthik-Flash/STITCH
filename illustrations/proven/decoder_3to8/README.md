# `decoder_3to8` — proven illustration (real run, real evidence)

**Source:** `runs/nightly_20260814_012758/v2/gemma3_4b/{baseline,raw_adv,sem_adv}/decoder_3to8/`
— the exact case cited in the MLCAD paper's §5 / Table 7
(`decoder_3to8 | gemma3:4b | baseline FAIL|6 | raw_adv FAIL|6 | sem_adv PASS|2`).
Confirmed by `metrics_*.json` in this folder: `baseline` and `raw_adv` both
run the full 6 iterations and never pass; `sem_adv` passes on iteration 2.

Unlike the `pending/` modules, nothing here is reconstructed or guessed —
every file is a direct copy of what the real pipeline actually produced.

## The bug

`enable` is read nowhere in the combinational `case` block. With `enable=0`,
the model's decoder still outputs the one-hot pattern for whatever `in` is,
instead of `8'b0`.

## What each condition saw and did

| Condition | Iterations | Result | File here |
|---|---|---|---|
| `baseline` | 6 | FAIL (never fixed) | `baseline_iter6_final.v` |
| `raw_adv` | 6 | FAIL (never fixed) | `raw_adv_iter6_final.v` |
| `sem_adv` iter 1 | 1 | FAIL (same bug as above) | `sem_adv_iter1_broken.v`, `sem_adv_iter1_sim_log.txt` |
| `sem_adv` iter 2 | 2 | **PASS** | `sem_adv_iter2_fixed.v`, `sem_adv_iter2_sim_log.txt` |

The testbench is at `../decoder_3to8_tb.v` (flat, runner-readable) — it is the
shared testbench, identical across all three conditions/iterations. A
byte-identical nested copy used to sit here as `tb.v`; it was removed
2026-08-19 so the flat file the runner actually reads is the single source
of truth and the two cannot drift apart.

## What actually fired (from `metrics_sem_adv.json`)

```json
"verilator_codes_seen": ["UNUSEDSIGNAL"],
"semantic_fired": 1,
```

Verilator's `UNUSEDSIGNAL` fired on the `enable` port on iteration 1 (`enable`
is declared but never read in the combinational logic). `stitch_interpreter.py`'s
`UNUSEDSIGNAL` template converted that into an actionable directive; iteration
2's fix (comparing `sem_adv_iter1_broken.v` → `sem_adv_iter2_fixed.v`) is
exactly "wrap the case in `if (enable) ... else out = 0;`" — i.e. the model
acted on the directive, not a coincidental resample.

**Caveat inherited from the project's own findings:** the exact directive text
sent to the model on iteration 1 was never persisted to disk (`STITCH_PROGRESS_AND_FINDINGS.md`
§7 finding 1 — a known, already-documented gap). What's provable from these
files is the *outcome* (UNUSEDSIGNAL fired, model changed exactly the right
thing, passed next iteration) — not a byte-for-byte capture of the prompt
text itself. If a paper listing needs the literal directive text, reconstruct
it the same way `analysis/phase2_reconstruct.py` did (re-run `interpret_verilator`
on `sem_adv_iter1_broken.v` — the `UNUSEDSIGNAL` template is deterministic, so
this reconstruction is exact, not an approximation).

## Testbench comment note

`../decoder_3to8_tb.v`'s header comment says *"Yosys: Inferred latch for signal `\out`"* as
the expected mechanism — that turned out not to be what actually fired for
this model/run (it was Verilator's `UNUSEDSIGNAL` on `enable`, per the metrics
above, not a Yosys latch warning). Left as-is since it's the original
testbench file, unedited per the "frozen evidence" rule — just don't let the
comment's framing override what `metrics_sem_adv.json` actually recorded.

## Boundary rule

Do not edit anything in this folder. It is frozen evidence, same status as
`benchmark/v20_baseline/` and the `runs/` trees it was copied from.
