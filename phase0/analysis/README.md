# phase0/analysis/

Scripts that produced the aggregate figures and regime breakdowns cited in
`../evidence/`. Moved here from `analysis/` on 2026-08-20, alongside the
`illustrations/`, `evidence/`, and `results/` reorganization — they are
phase-0-specific pre-migration artifacts, not general tooling, and per the
verification below none of them run against this repo without a rewrite.

## Status: verified broken against this repo, 2026-08-20

Each script's default path resolution was checked directly (`python
<script>.py`, no args) before moving anything. All five error out or —
for `hpc_checkpoint.py` — only "work" against a directory that exists on
one specific machine outside this repository entirely, not against
anything this repo actually contains.

| Script | Result | Exact error |
|---|---|---|
| `phase_d_delta.py` | Exit 1 | `FileNotFoundError: ...AutoChipAdvFB\STITCHAdv\res\phase1_consolidated.json` — hardcoded absolute path into the pre-migration tree |
| `phase_e_replay.py` | Exit 1 | `FileNotFoundError: ...AutoChipAdvFB\stitch_interpreter.py` — loads the interpreter from its old pre-restructure location, which no longer exists |
| `phase1_verify.py` | Exit 1 | Runs partway (prints "0 metrics.json under STITCHAdv/runs", since that tree isn't found either), then `FileNotFoundError: <REPO_ROOT>\res\phase1_consolidated.json` — a *second*, differently-broken path, this one repo-relative but still pointing nowhere real |
| `phase2_reconstruct.py` | Exit 1 | `FileNotFoundError: D:\AutoChipAdvFB\AutoChipSTITCH\autochip_stitch_runner.py` — imports the retired runner from its pre-restructure path |
| `hpc_checkpoint.py` | **Exit 0, but not portable** | Runs and prints real numbers (150 `metrics.json`, per-hardware pass rates) — but only because `HPC_PULL = Path(r"<DATA_ROOT>\AutoChipAdvFB\STITCHAdv\runs\hpc_pull")` happens to still exist on the machine this was checked on. That directory is outside this git repository entirely (never migrated, never committed — see `.gitignore`'s `runs/hpc_pull/` entry) and will not exist for a fresh clone or a coauthor. Classified broken for repo-portability purposes, not because it crashes here. |

None were rewritten during migration or since. Each is tied to a specific
historical run tree, and silently repointing them at new paths would
produce numbers that look valid but no longer correspond to the data
`../evidence/` actually cites. Repoint consciously, against the run tree
you actually mean, if you need to regenerate one of these figures.

`aggregate_results.py` and `stats.py` are the exceptions — the former
genuinely works against this repo's current results tree (needs `--runs`
explicitly, its logic is otherwise sound), the latter is an unimplemented
placeholder with no path dependency to break. Both stay at `../../analysis/`;
see that directory's README.

## Note on the data they consumed

The raw per-iteration run trees these scripts read (`nightly_*`, `resume_*`,
`hpc_pull`) were **not migrated** — they belong to the conference-paper work.
`../evidence/combined_results.csv` is the aggregated output that survived,
and its last two columns retain absolute paths into that original tree as
provenance. Treat those columns as historical annotation, not as resolvable
paths.
