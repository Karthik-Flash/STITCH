# analysis/

Scripts that produced the aggregate figures and regime breakdowns cited in
`evidence/`. They are migrated here as the provenance for those numbers.

## Status: these scripts require path updates before they will run

**Every script in this directory resolves its data root against the
pre-migration folder layout**, either through a hardcoded absolute path or a
relative parent-walk that assumed the old tree. None of them will run
unmodified in this repository.

| Script | Problem |
|---|---|
| `hpc_checkpoint.py` | Hardcoded absolute path to the HPC pull directory, which was not migrated (it is conference-paper territory — see the archived HDLLLM repository) |
| `phase_d_delta.py` | Hardcoded absolute repository root |
| `phase_e_replay.py` | Hardcoded absolute repository root |
| `phase1_verify.py` | `Path(__file__).resolve().parents[3]` — assumed the old nesting depth |
| `phase2_reconstruct.py` | `Path(__file__).resolve().parents[3]`, plus a reference to a runner that has since been retired |
| `aggregate_results.py` | Default run-root is resolved relative to the old layout; pass `--runs` explicitly |
| `stats.py` | Placeholder — confidence-interval and distribution reporting, not yet implemented |

They were deliberately **not** rewritten during migration. Each one is tied to
a specific historical run tree, and silently repointing them at new paths would
produce numbers that look valid but no longer correspond to the data the
`evidence/` documents cite. Repoint them consciously, against the run tree you
actually mean, when you next need to regenerate a figure.

## Note on the data they consumed

The raw per-iteration run trees these scripts read (`nightly_*`, `resume_*`,
`hpc_pull`) were **not migrated** — they belong to the conference-paper work.
`evidence/combined_results.csv` is the aggregated output that survived, and its
last two columns retain absolute paths into that original tree as provenance.
Treat those columns as historical annotation, not as resolvable paths.
