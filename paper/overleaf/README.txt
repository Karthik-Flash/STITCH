reSTITCHing: Replicated, Cost-Controlled, and Sign-off-Aware Repair of LLM-Generated RTL
Paper v10, Overleaf bundle
=========================================================================================

Contents
  main.tex        the paper (limit 17 pages including references)
  supplement.tex  Supplementary Material S1 to S9
  figures/        every figure the two files use, as vector PDF

Compile on Overleaf
  1. New Project > Upload Project, and choose STITCH_overleaf.zip.
  2. Menu > Compiler: pdfLaTeX (the default). Menu > Main document: main.tex.
  3. Recompile. To build the supplement, set Main document to supplement.tex.

Compile locally
  latexmk -pdf main.tex
  latexmk -pdf supplement.tex
  pdflatex only. There is no BibTeX step: the bibliography is inline. Every package
  is in TeX Live (2023 or later) and MiKTeX.

Projected values (remove before submission)
  Claude Haiku 4.5 is incomplete on the RTLLM floor tier (12 of 19 modules measured).
  Projected values appear only in the floor heat map (figures/fig_floor_heatmap.pdf) and
  in one count in Section 8.3. They are typeset with \proj{} (italic, with a dagger), and
  every place that uses them says so. In main.tex, \finaltrue (near the top) turns any
  remaining projection into a compile error, so a final build cannot ship one.
  When Haiku's runs are completed, re-run the generators below: the projections are
  replaced by measured values and the daggers and notes disappear.

Regenerating (from the repository root)
  python -B phase2/frontier/make_numbers_set4.py   NUMBERS and TABLES blocks, heat map
  python -B paper/make_v10_figures.py              every other figure
  Do not edit the blocks between "% BEGIN GENERATED" and "% END GENERATED" by hand.
