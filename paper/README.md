# paper/: the journal paper (v11)

reSTITCHing: Replicated, Cost-Controlled, and Sign-off-Aware Repair of LLM-Generated RTL.

| Path | What it is |
|---|---|
| `main.tex` | the paper, the single working copy (14 pages including references, no supplement) |
| `figures/` | every figure `main.tex` uses, as vector PDF |
| `STITCH_v11_overleaf.zip` | `main.tex`, `figures/` and this README, ready to upload to Overleaf |
| `V11_CHANGES.md` | how the v11 narrative was drafted and what changed from v10 |
| `make_figures.py`, `figstyle.py` | the figure generator and the shared style (one colour and one name per condition) |
| `archive/` | earlier drafts v7 to v10, the v10 supplement and zip (local only, gitignored) |
| `paper_112_final.pdf` | the conference paper (local only, gitignored) |

The detail behind the paper (every former supplement table and figure) is in `../docs/reSTITCH.md`.

## Compile

On Overleaf: New Project > Upload Project, choose `STITCH_v11_overleaf.zip`; compiler pdfLaTeX (the default); main
document `main.tex`.

Locally, from this folder:

    latexmk -pdf main.tex

pdfLaTeX only, no BibTeX step (the bibliography is inline). Every package is in TeX Live 2023 or later and MiKTeX.

## Regenerate the figures

From the repository root:

    python -B paper/make_figures.py

It writes `paper/figures/*.pdf` (the paper's figures) and `docs/figures/*.png` (the same figures plus the former
supplement figures, for `docs/reSTITCH.md`). Every value is read from an evidence file; the inputs are listed at the
top of the script.

## Re-zip for Overleaf

From this folder (Python, so the zip uses forward slashes; PowerShell 5.1's `Compress-Archive` writes backslashes,
which Overleaf can misread):

    python -c "import zipfile,glob; z=zipfile.ZipFile('STITCH_v11_overleaf.zip','w',zipfile.ZIP_DEFLATED); [z.write(f, f.replace(chr(92),'/')) for f in ['main.tex','README.md']+sorted(glob.glob('figures/*.pdf'))]; z.close()"

The zip was checked by extracting it into an empty folder and building it there: 14 pages, no warnings, all fonts
embedded.

## Names

The paper uses readable condition names; the repository keeps the code names: Baseline (`baseline`), Alarm
(`baseline_gate`), Raw (`raw_adv`), Interpret v2/v3 (`sem_adv`, `sem_adv_v2`, `sem_adv_v3`), Escalate
(`sem_escalate`), Escalate-R (`sem_escalate_restart`, `sem_esc_restart_v3`). Studies: tiering and fine-tuning (Set 2),
small open models (Set 1), larger open models (Set 3), commercial models (Sets 4 and 4b), MPSoC case study (Phase 3).
