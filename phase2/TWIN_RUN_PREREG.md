# Phase 2 RTLCoder twin-comparison run — pre-registration

Written BEFORE the run, per the 2026-08-22 design instruction, revised
2026-08-23 (see **Revision history** at the end). **Not launched yet** —
this is the design + build for review; the user launches after reading
this doc, the confirmed run count, the wall-clock estimate, and the
correctness-check confirmations below.

---

## What this run is, and isn't

**Is**: a MODEL comparison. Does RTLCoder-Deepseek-v1.1's fine-tuning
(on deepseek-coder:6.7b's own base weights) produce a measurably
different repair-loop pass rate than the unmodified twin, and how do
both compare against a small ladder of other open-weight models
(gemma3:4b, llama3.1) — with prompt format itself reported as a
measured variable rather than left as a confound.

**Is NOT**: a test of STITCH's semantic interpreter. The `condition`
parameter passed to `stitch_runner_hpc.run_one_condition()` is fixed at
`"baseline"` (iverilog-only feedback loop) for every single cell in this
run — no Verilator, no Yosys, no interpreter, in any cell, under any
model or prompt condition. This is deliberate, not an oversight: mixing
a model-comparison question with an interpreter-effect question in the
same run would make neither answer clean. Any future run that wants to
cross RTLCoder against STITCH's tool conditions is separate scope, not
this one.

---

## Design

**Not a full model × prompt-condition cross.** "Native" and "shared" are
procedurally identical for the 3 Ollama models (both are the harness
`SYSTEM_PROMPT` — there is no other native convention for them), so
running both would have been 60 redundant replicates, not a second
condition, for those 3 models. Only RTLCoder has a real native-vs-shared
contrast. Five model-conditions, not eight:

| model | prompt condition | why |
|---|---|---|
| `rtlcoder-deepseek-v1.1` | `native` | RTLCoder's own stub-completion prompt |
| `rtlcoder-deepseek-v1.1` | `shared` | harness `SYSTEM_PROMPT`, reformatted for a completion model |
| `deepseek-coder:6.7b` | `shared` | its only condition — harness `SYSTEM_PROMPT` is its one convention |
| `gemma3:4b` | `shared` | same |
| `llama3.1:latest` | `shared` | same |

| axis | values | count |
|---|---|---|
| Model-conditions | the 5 above | 5 |
| Modules | `accu`, `counter_12`, `barrel_shifter`, `alu`, `calendar` — identical set to the phase1 laptop pilot, for direct comparability | 5 |
| Replicates | N=3, same discipline as the pilot (N=1 is resampling noise, not a result — phase-0 lesson) | 3 |
| STITCH condition | `baseline` only, fixed — see above | 1 |
| Iteration cap | Pass@8 (`MAX_RETRIES=8`), uniform across all cells | — |
| Sampling | **T=0.5, top_p=0.9 for ALL FIVE model-conditions** — see the temperature section below | — |

**Total: 5 × 5 × 3 = 75 runs, all distinct** (no procedurally-duplicate
cells). Confirmed by direct computation in `phase2/twin_run_runner.py`
and cross-checked against a dry-run staging pass against the real local
RTLLM checkout, plus a mocked-dispatch check confirming the temperature
override actually reaches the Ollama call path (see chat log).

### The two readable comparisons this design answers

- **(a) The pure fine-tuning twin comparison**: `rtlcoder-deepseek-v1.1`
  / `shared` vs. `deepseek-coder:6.7b` / `shared` — same prompt, same
  temperature, same everything else; the only thing that differs is the
  fine-tuning. This is the headline comparison the whole run exists for.
- **(b) The prompt-format effect, isolated**: `rtlcoder-deepseek-v1.1` /
  `native` vs. `rtlcoder-deepseek-v1.1` / `shared` — same model, same
  temperature; only the prompt convention differs. Report both cells
  side by side, and don't fold this into (a) or vice versa.

`gemma3:4b` and `llama3.1:latest` / `shared` provide ladder context
around (a) and (b) — not a third axis of their own in this design.

### Repair-iteration behavior for RTLCoder (a design decision, not previously specified)

RTLCoder is a completion model, not a chat model — it has no native
multi-turn repair convention. For iterations 2+ (after a failure), this
run keeps every RTLCoder call in the SAME completion-shaped form its
training data and the smoke test validated, rather than switching to a
foreign turn-taking format:

- **native**: `{spec}\n\nA previous attempt failed. Here is what went
  wrong:\n{feedback}\n\nGive me the complete corrected code.\n\nmodule
  {name}(\n` — or, if STUCK_THRESHOLD's rewrite prompt fired that
  iteration, just the rewrite prompt (which already embeds the spec)
  plus the trailing stub, not double-embedding the spec.
- **shared**: the full chat history flattened into text (the same
  `[USER]`/`[ASSISTANT]` linearization `stitch_runner_hpc.call_llm()`'s
  own Gemini branch already uses), plus the trailing stub.

Both keep RTLCoder's completion-model contract intact (always ends on
an open stub it completes) rather than asking it to behave like a chat
model mid-run. Flagged here so it's visible to review, not buried in
code.

### Token/cost reporting note

RTLCoder's `(prompt_tokens, completion_tokens)` are computed via its own
tokenizer on `(prompt, postprocessed code)` — real counts, not stubbed
to zero — but this measures something subtly different from Ollama's
`usage.completion_tokens`, which counts the full RAW generation
including whatever the model generated past the intended module before
`postprocess()` cut it off. Report RTLCoder's token cost with this
caveat attached; don't pool it silently against the Ollama models' token
counts as if directly comparable.

---

## Temperature — matched at T=0.5 across every model-condition

**Revised 2026-08-23. All five model-conditions use T=0.5, top_p=0.9** —
RTLCoder's own native setting, and a deliberate override of
`stitch_runner_hpc.py`'s hardcoded T=0.1 for the 3 Ollama models (see
`twin_run_runner.py`'s `_call_ollama()`, which routes around that
file's own Ollama branch for exactly this reason, without editing the
verified port).

**Why**: matching temperature removes it as a confound in the twin
comparison — a difference in pass rate between RTLCoder and
deepseek-coder:6.7b should be attributable to fine-tuning, not to one
side sampling at a different temperature than the other. T=0.5 (not
0.1) was chosen specifically because phase0's own finding was that
**T=0.1 is near-deterministic** — N=3 samples at T=0.1 barely spread,
which is exactly why phase0 already had to treat single-sample results
as unfalsifiable. A comparison that depends on N=3 actually sampling
real variation needs a temperature warm enough to produce it.

**This is a deliberate deviation from the project's usual T=0.1**,
stated explicitly, not silently changed: every prior run in this
project (Task 3, the RTLLM pilot, the phase0 illustrations) used T=0.1.
**This run's iteration counts and pass rates are NOT directly comparable
to those T=0.1 results** — a module that passed on iteration 2 at T=0.1
in the pilot is not the same measurement as the same module at T=0.5
here. This run is a **model comparison**, run entirely at its own
matched temperature; it is not, and should not be read as, a
re-measurement of the phase0/pilot T=0.1 illustrations at a different
setting.

---

## Reporting plan (decomposed, never pooled)

- A **model-condition × module grid**: pass rate (x/3) and mean
  iterations-to-pass (or cap, if failed), with comparisons (a) and (b)
  above called out explicitly, not left for the reader to reconstruct
  from a flat table.
- **Ceiling/floor flagging per module**, same lesson as the pilot's
  flat-40% decomposition: if a module is at or near 3/3 for every
  model-condition, or 0/3 for every model-condition, say so explicitly
  and don't read anything into its cell-to-cell variation. Only modules
  in the recoverable middle band carry real signal.
- **Baseline-honest framing, stated once and held to**: this is a model/
  fine-tuning comparison. Nothing here is evidence for or against
  STITCH's interpreter, because the interpreter never runs in this
  design. Do not frame an RTLCoder result — good or bad — as validating
  or invalidating STITCH.

---

## Correctness checks (confirmed before this doc was written — see chat log for the full verification detail)

1. **Both harness fixes present on the code that will actually run.**
   `phase2/stitch_runner_hpc.py` is a from-scratch Linux-native port
   built directly from the current local, git-committed
   `src/runner/stitch_runner.py` (commit `a047d78`, both fixes already
   pushed). This sidesteps "is the HPC copy stale?" entirely rather than
   trying to inspect a filesystem this session has no access to: it
   doesn't reuse whatever, if anything, already exists on HPC — the
   deploy step in `docs/HPC_COMMANDS.md` overwrites it fresh. A
   mechanical diff against the real source file (not just a visual
   read) confirmed every function outside the three WSL-specific tool
   invocations is logically byte-identical (only comments/docstrings
   trimmed), both `FIX 2026-08-2{1,2}` markers are present, and zero
   WSL/`wsl.exe` invocations remain in the ported file. Both fix
   signatures (`cwd=iter_dir` for bug #2, the fence-stripping `re.sub`
   for bug #1) are grep-verifiable in the shipped file, and
   `docs/HPC_COMMANDS.md` has the user run the same grep after
   deploying, as an independent second confirmation on the actual node
   — **still step 1 before launch, unchanged by this revision.**
2. **oss-cad-suite on PATH.** Baked directly into `twin_run.slurm`
   (`PATH=/scratch/soumyaj/oss-cad-suite/bin:$PATH`) — the same fix the
   smoke test needed, confirmed answer, not a placeholder.
3. **RTLLM read live, not vendored.** `twin_run_runner.py`'s
   `RTLLM_ROOT` is env-configurable (`$RTLLM_ROOT`, same variable the
   smoke test already uses), defaults to
   `/scratch/soumyaj/RTLCoderHPC/RTLLM` — nothing under RTLLM is copied
   into this repo; confirmed by the same policy already enforced
   throughout phase1/phase2.

---

## Wall-clock estimate — confirm before launching, not after

**Revised for 75 runs.** No real HPC timing data exists for RTLCoder
generation yet (the smoke test confirmed correctness, not speed) — that
side of the estimate still carries real uncertainty, flagged not hidden:

| component | iterations (worst case, Pass@8) | basis | estimate |
|---|---|---|---|
| 3 Ollama models, 1 condition each | 360 (120 each) | Observed local-laptop pace from the phase1 `alu`/`calendar` refix run: 13.4–32.7 s/iteration (GPU-dependent; T=0.1 there vs. T=0.5 here — pace shouldn't meaningfully differ, sampling temperature doesn't change per-token generation cost). HPC GPU pace itself is unvalidated but plausibly comparable or faster. | ~1.3–3.3h |
| RTLCoder, 2 conditions | 240 (120 each) | **No real observation.** Estimated from generic 7B-fp16-on-H100, unoptimized HF `generate()`, `max_new_tokens=1024`: ~20–50 tok/s single-sequence is a common range, so ~20–50s/iteration. | ~1.3–3.3h |
| **Worst case total** (every cell burns the full 8-iteration cap, zero early passes) | 600 | sum of the above | **~2.7–6.5h** |

**Realistic expectation is lower than the worst case** — historical data
(Task 3, the pilot) shows many cells converge well under cap — but
budget the sbatch wall-clock limit off the worst case, not the mean,
same lesson as the phase1 pilot's HPC-readiness note. **Recommend
`--time=08:00:00`** (down from the original 120-run design's
recommended 12h, reflecting the real ~40% iteration-count cut).

---

## Revision history

- **2026-08-22**: original design, 120 runs (4 models × 2 prompt
  conditions × 5 modules × N=3), T=0.1 for Ollama models / T=0.5 for
  RTLCoder.
- **2026-08-23**: cut to 75 runs (5 model-conditions × 5 modules × N=3)
  — dropped the 60 procedurally-identical Ollama "native" runs, kept
  only `shared` for the 3 Ollama models. Matched temperature to T=0.5
  across all five model-conditions, overriding the harness's usual T=0.1
  for the Ollama side — removes temperature as a confound in the twin
  comparison, at the cost of not being directly iteration-comparable to
  this project's other (T=0.1) results. Both changes were flagged as
  open items in the 2026-08-22 version of this doc and resolved by
  explicit user decision, not defaulted.
