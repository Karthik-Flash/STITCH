# STITCH — Handoff (Phase 2 complete, Phase 3 not yet scoped)

Supersedes the previous version of this file (Phase 1→2 handoff, resolved —
see git history, commit `eee7a28` and earlier, if you need that
archaeology). Written 2026-09-23 for a fresh Claude Code chat picking this
up to start Phase 3. There is also a parallel chat (same user) that carries
the full Phase 2 conversational history and may still be used for Phase 2
final touches/doubts — if something here looks unresolved and isn't in this
file or `reSTITCH.md`, it may only exist in that chat's memory, not on disk.

## Orientation — read this paragraph first

Phase 0 proved the interpreter mechanism on 2 illustrations. Phase 1 built
`sem_escalate` (conditional escalation) and ran an in-house 255-run
benchmark — cost story, not a pass-rate win. Phase 2 is **done**: three
confirmatory HPC runs at N=3, all analyzed, all findings reconciled and
written into `reSTITCH.md` (the master narrative document — read that
first for the science, this file is operational/orientation only). Phase 2
also closed out a live reviewer-critique pass on the interpreter's
regex/message-matching (see "Most recent work" below) — nothing open
remains from that. **Phase 3 has not been scoped yet.** `reSTITCH.md` Part
11 ("Directions for the Next Paper") and `note.txt`'s `EXTENSION` block at
the repo root are the two existing seeds for it — treat both as candidate
directions to discuss with the user, not a committed plan.

---

## Key locations

**Canonical harness (still the source of truth for fixes):**
- `src/runner/stitch_runner.py` — shared Windows/WSL runner.
- `src/interpreter/stitch_interpreter.py` — the semantic interpreter,
  platform-agnostic, imported unchanged by every runner (Windows and both
  HPC ports). `src/interpreter/WARNING_TAXONOMY.md` is the up-to-date
  ledger of which warning classes are verified against real tool output —
  **read this before trusting or extending any interpreter claim**, it was
  just re-verified end to end (2026-09-23) against a reviewer critique and
  is current as of today, not stale.
- `src/interpreter/pass_detection.py` — the `detect_outcome()` registry
  (Bug #3 class fix, Phase 2). Every runner calls this explicitly with a
  required `benchmark` kwarg (`"phase1"` or `"rtllm"`) — no silent default
  exists, by design.

**Phase 2** (`phase2/`, fully committed, `results/` gitignored):
- `SET1_ANALYSIS.md` — Set 1 (STITCH conditions on 3 small models).
- `TWIN_RUN_ANALYSIS.md` (+ `TWIN_PILOT_ANALYSIS.md` for the earlier
  pilot) — Set 2 (fine-tuning comparison).
- `SET3_ANALYSIS.md` — Set 3 (STITCH conditions on 3 large models),
  including the just-added gemma3:27b mechanism trace.
- `set1_runner.py`, `twin_run_runner.py`, `set3_runner.py` — the three
  HPC run harnesses; `*.slurm` — matching sbatch scripts.
- `set1_analysis/`, `twin_analysis_SET2/`, `set3_analysis/` — the actual
  figure/table generation scripts behind each `*_ANALYSIS.md`. Note:
  `set3_analysis/_data.py` and `fig_capability_ladder_full.py` both work
  around a real Python gotcha — a module named `_data.py` cannot
  `import _data` to reach a differently-located same-named module
  (`sys.modules` collides on the bare name). One reimplements the needed
  function directly, the other uses
  `importlib.util.spec_from_file_location`. If you add a fourth `_data.py`
  anywhere, expect this again.
- `HPC_RTLCODER_COMMANDS.md` — the HPC runbook (deploy/monitor/collect
  command reference, still accurate).
- `rtlcoder_adapter.py` / `stitch_runner_hpc.py` — Linux-native HPC ports,
  validated end-to-end on H100.

**`reSTITCH.md`** (repo root, **gitignored** — never staged/committed,
disk-only, always fetch it fresh from this machine, not from git):
the single master narrative. Parts 1-5 are Phase 0/1 background, Part 6
onward is Phase 2's confirmatory study (Set 2 in Part 7, Set 1 in Part 8,
Set 3 in Part 9), Part 10 is the whole-study "Five claims" + explicit
non-claims section, Part 11 is next-paper directions, Appendix B is the
run inventory table. **This is the document to read start-to-finish before
touching Phase 3** — it is the only place the full, reconciled, currently-
true version of every finding lives; individual `*_ANALYSIS.md` files are
detail views that feed into it, not always kept in perfect lockstep on
every micro-edit.

---

## HPC cluster and models (get this right — it's asked about often)

**Cluster**: BITS Hyderabad, `soumyaj@hpc.bits-hyderabad.ac.in`. Project
root `/scratch/soumyaj/RTLCoderHPC/` (40GB home quota). `oss-cad-suite`
(iverilog/verilator/yosys) at `/scratch/soumyaj/oss-cad-suite/bin`. `ollama`
binary at `/scratch/soumyaj/AutoChipHPC/bin/ollama` (reused from an earlier
project, not reinstalled — not on PATH by default, must be exported).
GPU nodes: `gpunode4` (A100 80GB, `gpu_a100_8`), `gpunode6` (H100 80GB
HBM3, `gpu_h100_4` — the one actually used for every real Phase 2 run).
`gpunode5` drains intermittently, avoid it. Full copy-paste command
sequences live in `phase2/HPC_RTLCODER_COMMANDS.md` — don't reconstruct
from memory.

**Models, exactly as used per run** (do not blur these three sets together):
- **Set 1** (small-model ladder, 4B–8B, STITCH conditions):
  `gemma3:4b`, `llama3.1:latest`, `deepseek-coder:6.7b` — all via Ollama.
  4 conditions (baseline / sem_adv / sem_escalate / sem_escalate_restart),
  42 RTLLM modules, N=3, T=0.1, 1512 runs.
- **Set 2 / Twin** (fine-tuning comparison, isolates fine-tuning as the
  only variable): `rtlcoder-deepseek-v1.1` (HuggingFace `transformers`,
  fine-tuned, native + shared prompt = 2 conditions) vs. its base model
  `deepseek-coder:6.7b` plus `gemma3:4b` and `llama3.1:latest` (Ollama,
  shared-prompt only) — 5 model-conditions total, **condition fixed at
  `baseline` throughout** (interpreter never runs in this design — never
  frame a Set 2 result as a STITCH validation). 42 modules, N=3, T=0.5,
  630 runs.
- **Set 3** (large-model ladder, 14B–32B, STITCH conditions, mirrors Set 1
  exactly): `qwen2.5-coder:14b`, `qwen2.5-coder:32b`, `gemma3:27b` — all
  via Ollama. Same 4 conditions, same 42-module pool, N=3, T=0.1.

If Phase 3 adds a new model tier or a new benchmark, follow this pattern —
new `MODELS` list in a new/copied runner, explicit `benchmark=` kwarg for
pass detection, N=3 minimum, same 42-module RTLLM pool unless there's a
specific reason to diverge (and if so, say why in the analysis doc, the
way Set 3 explicitly reused Set 1's difficulty tiers rather than
recomputing them).

---

## Key findings (Phase 2, condensed — `reSTITCH.md` Part 10 has the full version)

1. The interpreter mechanism generalizes as a **per-tier prediction**: it
   helps only where a real reachable defect exists (the "recoverable
   band"), and is silent elsewhere — this held across all three
   confirmatory runs.
2. **The harmful regime is real**: always-on interpretation (`sem_adv`)
   measurably lowers pass rate vs. baseline on small models (~4 points).
3. **Escalation (`sem_escalate`) avoids that harm** on small models by
   construction (starts every run in baseline mode, only diverges after 2
   observed failures) — a structural guarantee, not a statistical one.
4. **On large models, escalation matches baseline and never shows the
   harmful regime** — but traced to the individual replicate level, the
   pooled numeric edge is **not mechanism-backed** (zero winning
   replicates had `semantic_fired=1`) and is reported as noise-consistent,
   not a win. This was a real overclaim caught and corrected this phase —
   see `reSTITCH.md` §9.2-9.4 for the full honest reframe and the
   gemma3:27b exception (one model where sem_adv *does* help, traced to a
   recurring ANSI-port-declaration bug — hypothesis-flagged, not proven).
5. **Cost result strengthens with scale**: ~75% tool-call reduction on
   ceiling-tier modules; recoverable-band reduction rises from 16.6%
   (small models) to 27.6% (large models).
6. **Set 2 negative result**: RTLCoder-Deepseek-v1.1 fine-tuning shows no
   measurable advantage over its own base model on RTLLM's recoverable
   band — traced to 4 concrete losing-module root causes (missing
   submodule definition, SystemVerilog construct rejected by plain
   iverilog, unresolved parameter binding, a folder-name-vs-spec-name
   memorization artifact). RTLCoder's one clear strength: signal_processing
   modules under its native prompt format (9/9 = 100%).
7. **Methodological finding, not a science finding**: a silent
   case-sensitive pass-string bug (`"PASS"` vs. RTLLM's actual `"Your
   Design Passed"`) misclassified 31% of the Set 2 pilot's completed runs
   before being caught and fixed with a structural registry
   (`pass_detection.py`) instead of another one-off patch.

## Most recent work (2026-09-23, this session, now closed out)

A reviewer-style critique claimed the interpreter's regex/message-matching
was stale relative to real Verilator/Yosys output, specifically for
`UNUSEDSIGNAL` quoting and latch/loop message wording. Investigation found
both were **already fixed in Phase 0** (2026-08-17/18, documented in
`WARNING_TAXONOMY.md`'s "Known false-NEGATIVE/POSITIVE history" sections)
— confirmed by direct code read plus a live regex test, not just trusting
the docs. While checking, a genuinely stale claim was caught along the way:
`WARNING_TAXONOMY.md` said `MULTIDRIVEN` had "no real trigger found," but a
corpus grep turned up 32 real firings across two structurally different
Verilator message formats, both confirmed handled by the current
`_extract_signal_name()` regex. `WARNING_TAXONOMY.md` was updated with this
evidence and is staged (not committed — standing rule, see below).

---

## Standing conventions (violate these and expect a correction)

- **RTLLM is never copied into this repo** — read live from
  `D:\Projects\RTLLM` locally / `$RTLLM_ROOT` on HPC.
- **N≥3 before any cell result is trusted** — proven twice (Phase 0, then
  Phase 1 Task 3's N=1→N=3 replication collapse).
- **`semantic_fired`-gate every mechanism claim.** A pooled pass-rate edge
  is not evidence the interpreter caused it — check the replicate-level
  trace before calling anything a "win." This exact discipline caught the
  Set 3 escalation-at-scale overclaim this phase; keep applying it in
  Phase 3.
- **No `Co-Authored-By: Claude` trailer** in any commit message in this
  repo (explicit project rule, stated 2026-08-22, reconfirmed multiple
  times since — this overrides any generic attribution default).
- **Stage and propose; the user runs `git commit`/`git push`** — never
  commit or push autonomously unless explicitly told to for that specific
  batch.
- **`reSTITCH.md` is gitignored on purpose** — edit it on disk freely, but
  never try to `git add` it; it's the user's own working narrative
  document, not a repo artifact.
- **Verify every "fix" against real captured data before calling it
  fixed** — golden references, real HPC logs, real sim/run output. Every
  bug found this phase was caught this way.
- **Never frame a Set 2 (Twin) result as a STITCH validation** — its
  `condition` is fixed at `baseline` throughout; the interpreter never
  runs in that design.

---

## Phase 3 — not yet scoped, candidate directions only

Two sources, neither yet a decision:

1. **`reSTITCH.md` Part 11** ("Directions for the Next Paper"):
   (a) defect-class expansion — mine the 19 floor-tier (always-fail)
   modules for defect classes the interpreter has no vocabulary for yet,
   extend `_VERILATOR_INTERP`/Yosys detection, re-measure; (b) robustness
   under imperfect specs — inject spec-level ambiguity/defects, separate
   model-defect from spec-defect behavior; (c) frontier/closed-source
   models via API — a further capability-ladder point, and a targeted
   follow-up on whether gemma3:27b's non-monotonicity is post-training-
   alignment-driven (currently just a hypothesis).
2. **`note.txt`'s `EXTENSION` block** (repo root, informal, pre-Phase-2
   notes, not reconciled with `reSTITCH.md` yet): ideas around latch
   inference visibility (show how many latches are inferred vs. not,
   attributable to STITCH), and an MPSoC/RISC/router/network-interface
   angle — "prove on a basic element," leverage multi-processor designs as
   a harder benchmark class, possibly aimed at an ISCAS-venue framing
   ("STITCH the HierRTL"). This predates the Set 1/2/3 confirmatory runs
   and hasn't been checked against what those runs actually established —
   treat as raw brainstorm, not a spec.

Two commitments carry forward unconditionally regardless of which
direction Phase 3 takes (`reSTITCH.md`'s own closing line): every
interpreter claim stays N≥3-replicated and `semantic_fired`-gated, and
every pass-rate figure is reported against the difficulty tier that
determines whether the mechanism could even have been measured.

**First actual step for a Phase 3 session**: read `reSTITCH.md` in full,
then take the two candidate directions above to the user and scope
Phase 3 with them explicitly — do not start building against either
direction unprompted, since neither is committed yet.

## Origin (condensed, for archaeology)

Phase 0 proved the interpreter on 2 illustrations, 50 interpreter tests.
Phase 1 built `sem_escalate` and ran a 255-run in-house benchmark — cost
story, not pass-rate win; also fixed 2 harness bugs
(`stitch_runner.py`, commit `a047d78`). Phase 2 built the HPC
infrastructure, fixed the pass-detection Bug #3 class structurally
(`pass_detection.py`), and ran three N=3 confirmatory studies (Set 1/2/3)
totaling 1512+630+~1512 runs, fully reconciled into `reSTITCH.md`. Earlier
handoff versions (Phase 0→1, Phase 1→2) are in git history if the detailed
reasoning is ever needed — this file only carries forward what's still
load-bearing.
