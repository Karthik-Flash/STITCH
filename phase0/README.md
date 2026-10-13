# Phase 0 — pre-Phase-1 investigation

Everything under this directory predates the Phase 1 escalation-architecture
work and is now closed. It answers one question — does semantic
interpretation of EDA tool output help a small local LLM repair Verilog? —
with two proven illustrations (`illustrations/proven/`, `decoder_3to8` and
`mux4_oe`, each replicated 3/3 at `temperature=0.1`), a documented failure
landscape of everything else tried and why it didn't hold up
(`illustrations/retired/`), and three secondary methodology findings from a
larger-module hunt that are cited in the paper's methodology section
regardless of that hunt's negative result
(`evidence/phase0_illustration_hunt_findings.md`). The interpreter and runner
this work hardened (`../src/interpreter/`, `../src/runner/`) are shared with
Phase 1 unchanged — nothing here is a dead end for the code, only for these
specific candidate modules.

Start with `evidence/phase0_illustration_hunt_findings.md` for the
consolidated, paper-ready account. `../plans/research_plan_v4.md` is the plan
of record this phase executed against. `../handoff.md` at the repo root is
the entry point for anyone picking up Phase 1.

## Layout

- `evidence/` — findings documents, replication data, and the raw aggregate
  CSV from the pre-migration sweep this phase's investigation drew on.
- `illustrations/` — `proven/` (frozen, do not edit), `retired/` (15
  candidates, one index at `retired/README.md`), `pending/` (one live
  candidate carried into Phase 1, `priority_encoder_valid`, never run).
- `results/` — raw per-run output trees. Mostly gitignored (iteration-level
  `.v`/log files); `metrics.json` and `stitch_summary.json` files survive as
  the on-disk record behind the numbers in `evidence/`.

## See also

- `../docs/PHASES_EXPLAINED.md`: every phase in one document (question, design, runs, results, paper changes,
  evidence).
- `../docs/reSTITCH.md`: the whole story, with every decision and correction.
- `../REPO_INDEX.md`: where everything lives and how to regenerate it.
