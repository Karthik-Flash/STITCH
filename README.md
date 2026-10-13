Detailed Overview of STITCH

STITCH adds a deterministic interpreter to a language-model repair loop for Verilog: it translates Verilator lint
and Yosys synthesis output into targeted repair directives. This repository holds the interpreter, the runners and
analyses of every study phase, the pre-registrations and evidence reports, and the paper sources.

- **Start here:** [`REPO_INDEX.md`](REPO_INDEX.md) says what lives where, which file is the evidence for each part of
  the paper, and how to regenerate every table and figure.
- **Paper (v10):** `paper/overleaf/main.tex` and `paper/overleaf/supplement.tex`, self-contained and ready for
  Overleaf (`paper/STITCH_overleaf.zip`); change log `paper/V10_CHANGES.md`. v9 is kept in `paper/`.
- **Conference version:** K. Patana et al., "STITCH: Semantic Toolchain Integration for LLM-Driven RTL Circuit and
  Hardware Design Generation," MLCAD '26, doi:10.1145/3831599.3840333.
