# paper/archive: superseded drafts (kept for provenance)

The current paper is `../overleaf/` (v10): `main.tex`, `supplement.tex`, `figures/`, and `../STITCH_overleaf.zip`.
Its change log is `../V10_CHANGES.md`, and its figure scripts are `../figstyle.py`, `../make_v10_figures.py` and
`../../phase2/frontier/make_numbers_set4.py`.

This folder holds every earlier draft and its by-products, unchanged:

| Files | What they are |
|---|---|
| `STITCH_EXT_FINAL.pdf` | the earlier compiled draft |
| `STITCH_EXT_v7.tex`, `V7_CHANGES.md`, `ABSTRACT_INTRO_PATCH.md`, `PHASE3_MPSOC.tex` | v7 and its Phase 3 companion (v1) |
| `STITCH_EXT_v8.tex`, `V8_CHANGES.md`, `make_v8_changes.py`, `PHASE3_MPSOC_v2.tex` | v8, the first version on the sign-off oracle, with its Phase 3 companion |
| `STITCH_EXT_v9.tex`, `STITCH_EXT_supplement.tex`, `V9_CHANGES.md`, `numbers_set4.tex`, `tables_set4.tex`, `make_v9_figures.py`, `v9_number_sources.py`, `v9_number_sources.md` | v9, its supplement, its generated inputs and its number-source check |
| `figures/` | the figures those drafts used (PNG and the v9 PDFs). v10 uses none of them. |

The scripts here were written for their original locations (`paper/` and `docs/archive/paper/`) and are not
maintained. To rebuild v9, copy its files back into `paper/` first. Its generated inputs `numbers_set4.tex` and
`tables_set4.tex` are frozen copies: `make_numbers_set4.py` now writes into `../overleaf/` instead.
