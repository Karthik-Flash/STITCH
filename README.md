Detailed Overview of STITCH

STITCH adds a deterministic interpreter to a language-model repair loop for Verilog: it translates Verilator lint
and Yosys synthesis output into targeted repair directives. This repository holds the interpreter, the runners and
analyses of every study phase, the pre-registrations and evidence reports, and the paper sources.

- **Start here:** [`REPO_INDEX.md`](REPO_INDEX.md) says what lives where, which file is the evidence for each part of
  the paper, and how to regenerate every table and figure.
- **Paper (v11):** `paper/main.tex` (14 pages, no supplement) with `paper/figures/`, ready for Overleaf
  (`paper/STITCH_v11_overleaf.zip`); how to build it is in `paper/README.md`, what changed from v10 in
  `paper/V11_CHANGES.md`. Earlier drafts are in `paper/archive/` (local only).
- **The whole story, with every figure and table:** [`docs/reSTITCH.md`](docs/reSTITCH.md), including the detail
  that used to be the paper's Supplementary Material.
- **`SiliconComparision/`** holds separate silicon (PPA) studies of the NoC designs; the paper does not use them.
- **Conference version:** K. Patana et al., "STITCH: Semantic Toolchain Integration for LLM-Driven RTL Circuit and
  Hardware Design Generation," MLCAD '26, doi:10.1145/3831599.3840333.
