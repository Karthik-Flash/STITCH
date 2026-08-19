# analysis/

Scripts usable against this repo's current results tree. Five other
pre-migration scripts that never worked against this repo (hardcoded
paths into a folder tree that was never migrated) moved to
`../phase0/analysis/` on 2026-08-20 — see that directory's README for
what they were and why they're archived rather than fixed.

## `aggregate_results.py` — works, needs `--runs`

Walks one or more run-root folders, finds every `metrics.json`, and merges
them into one CSV/JSON. **Its default run-root is a stale pre-migration
path**, so pass `--runs` explicitly against this repo's actual results tree:

```
python aggregate_results.py --runs ..\phase0\results --out combined
```

Verified 2026-08-20: found 92 `metrics.json` files under
`phase0/results/`, produced a coherent 41-row summary matching the
pass-rate numbers already cited in `../phase0/evidence/`. The logic is
sound — only the default path is wrong.

```
python aggregate_results.py --help
```
for the full flag list (`--runs`, `--prefer`, `--out`).

## `stats.py` — not yet implemented

An 8-line placeholder — no pre-migration path dependency, nothing to
repoint, nothing to run. Per its own docstring it's for confidence-interval
and distribution reporting across N≥3 samples per cell, which is a Phase 1
need (the escalation-vs-baseline-vs-unconditional-STITCH comparison) more
than a Phase 0 one, which is why it stays here rather than moving to
`phase0/analysis/` with the genuinely broken scripts.
