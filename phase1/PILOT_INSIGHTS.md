# RTLLM pilot — consolidated insights (original pilot + diagnostic + refix re-run)

**Status: diagnostic and harness-hardening work, not a confirmatory result
either way.** Everything below is labeled for what it actually
establishes. Nothing here should be cited as "STITCH does/doesn't work
on RTLLM" — see §B and §C for exactly why.

Sources: `phase1/results/rtllm_pilot/master_log.json` (original pilot,
288/375, stopped by decision), `phase1/results/rtllm_pilot_refix/master_log.json`
(bug-fix validation re-run, 38/150, stopped — machine thermal), plus the
read-only diagnostic performed on the original data. All gitignored; this
document plus `phase1/task3_summary.json`-style artifacts are the
reproducible record.

---

## A. Harness bugs found and fixed — the pilot's main concrete output

Two real, silent correctness bugs in the shared runner were found and
fixed during this work, both verified before/after on golden references
(see the two proposed commits, still staged, not committed pending your
review). **This — not any pass-rate number — is the most valuable thing
the pilot produced.**

### Bug #2 — `run_iverilog_sim()` never set a working directory for `vvp`

**Disqualifying for every RTLLM design that does relative-path file I/O.**
`$readmemh("reference.dat", ...)` (or any bare-filename read) could never
resolve, because `vvp` ran from wherever the WSL launcher's default
directory was, not `iter_dir` where the staged data file actually lives.
100% reproducible whenever a design compiled — a model's logic was never
even evaluated. Confirmed present in the original pilot: this is why
`alu`'s "logic_error" bucket (7/63 terminal cases, pre-fix) was actually
**100% this bug in disguise**, not genuine wrong-answer mismatches
(`classify_error()` buckets it as `logic_error` because the
`"SIMULATION FAILED"` prefix itself contains the substring "fail").

**Zeroed out 4-5 of the 50 RTLLM designs by construction**: `alu`,
`calendar`, `signal_generator`, `multi_booth_8bit` all use this pattern
(confirmed in Task A's compatibility screen); `asyn_fifo` has a separate,
unrelated blocking issue (`break` statement unsupported).

**Checked against v20: does NOT affect it.** Grepped every
`benchmarks/v20_diagnostic/*.v` testbench for `$readmemh`/`$fopen` —
zero hits. This bug could not have altered any v20 number, historical or
in Task 3's 255-run benchmark. It is RTLLM-specific in actual impact,
even though it was latent in `stitch_runner.py` regardless of benchmark.

**Fixed and verified**: golden-reference `alu` + `reference.dat` now
reaches a real pass/fail instead of the open error; golden-reference
`accu` (non-file-I/O) produces byte-identical output before/after — no
regression on the existing v20/Task 3 result set.

### Bug #1 — code-extraction fallback didn't strip an unclosed fence marker

A response that opens ` ```verilog ` but never closes it falls through
the extraction regex to a raw-text fallback that used to keep the
opening marker attached — iverilog's preprocessor then reads the leading
`` `verilog `` as a malformed macro reference ("macro verilog undefined
... I give up"), corrupting what may otherwise be compilable code.

**Confirmed recurring in v20 too, not RTLLM-specific**: the identical
signature was already visible in `datapath_mux_alu`/gemma3:4b (found
earlier this session, before RTLLM work started). **Checked its actual
impact on Task 3's 255-run benchmark, not just v20 in the abstract**:
grepped every generated `.v` file under `phase1/results/task3/` for the
stray-fence signature — **58 of 659 (8.8%) of Task 3's generated files
were corrupted by this bug.** That means some fraction of Task 3's
reported `syntax_error` terminal states, `STUCK_THRESHOLD` fires, and
the three flip-cell findings in `PHASE1_TASK3_ANALYSIS.md` may be
partly attributable to this extraction artifact rather than genuine
model behavior. **This is not re-litigated here** — re-auditing Task 3
against the fix is separate scope — but it should be flagged
prominently before anyone treats `PHASE1_TASK3_ANALYSIS.md` as final.

On RTLLM specifically, the rate was higher and varied sharply by module
(9-11% on the simple modules, 34.6% on `alu`'s longer spec) — see the
original diagnostic for the full per-module table.

**Fixed in both places the identical pattern exists** — `stitch_runner.py`'s
inline extraction (classic conditions) and `escalation_runner.py`'s
separate `_extract_code()` (escalation conditions; not shared code,
needed its own fix). Verified: the real captured unclosed-fence response
now extracts cleanly; a real properly-fenced response produces
byte-identical output old vs new.

**Framing, stated once, plainly:** the pilot's headline contribution so
far is a more-correct harness with two silent bugs closed, one of which
had already contaminated a small but real fraction of the Task 3
benchmark this phase already reported on.

---

## B. What the pilot did and didn't measure — precisely

### The 3 complete modules (`accu`, `counter_12`, `barrel_shifter`)

No condition differentiation. `counter_12` is a ceiling (~100% regardless
of condition), `accu` is a floor (~0-7%), `barrel_shifter` sits at a
flat, identical 20% across every single condition. STITCH's mechanism
fired for real — 51 genuine chances across `accu`/`barrel_shifter` (0 on
`counter_12`, correctly, since it almost never fails) — and among those
51: **0 rescues, 1 loss (replicated across 3 conditions on one cell), 48
no-change.**

**Read this as inconclusive-to-unfavorable on this specific 3-module
set, not a clean negative.** Three modules, chosen by an alphabetical
rule rather than by difficulty, is not enough diversity to say anything
general about the mechanism — see §C for why that's structural, not bad
luck.

### `alu`, post-fix (bug #2 and bug #1 both fixed)

**Baseline reported first, as required: baseline `alu` is still 0/9**
across the 3 models that completed a full baseline sample in the refix
run (`gemma3:4b`, `llama3.1`, `deepseek-coder:6.7b`) — every one of
those 9 baseline runs burned the full 6-iteration cap. **`gemma3:12b`
and `qwen2.5-coder:14b` never reached baseline in the refix run before
it was stopped** — this matters specifically because in the *pre-fix*
diagnostic, `qwen2.5-coder:14b` was the only model showing genuine
`logic_error` (compiled, wrong answer) rather than compile failures on
`alu` — the model closest to a working solution never got retested
post-fix.

**With baseline still at 0 for the 3 models tested, `alu` reads as
genuinely hard for those 3 models even with both bugs fixed** — the
harness is no longer the story for them; the model's actual capability
is. Post-fix failure-class breakdown across all 38 completed runs
(all conditions, all 3 models): **36/38 (95%) still COMPILE-class**,
only 2/38 genuine `logic_error` — confirming the pre-fix "logic_error"
bucket really was almost entirely the bug, not masked model capability,
for the 3 models actually tested.

STITCH's interpreter fired substantially here too (16 fires across 8
`sem_adv` runs, 6 across 6 `sem_escalate`, 8 across 6
`sem_escalate_restart`) — real engagement, still 0 passes anywhere.

### CRITICAL HONESTY POINT — `calendar` was never reached

The refix run only got through `alu` (38/75) before the machine
overheated and the run was stopped. **`calendar` — the other file-I/O
module bug #2 was supposed to unblock — was never retested. 0/75.**

**"File-I/O modules still fail post-fix" is not an established
conclusion. Only `alu` was retested, and only 3 of 5 models on it.** Do
not generalize from `alu` to `calendar`, `signal_generator`, or
`multi_booth_8bit`. This is a real, named gap, not an oversight to gloss
over.

---

## C. The real lesson for the full study

STITCH's effect — on every piece of evidence this project has produced,
going back to phase 0's two proven illustrations — is only observable on
modules in a specific difficulty band: **baseline sometimes fails but is
recoverable with the right feedback.** Too easy (`counter_12`) and there's
a ceiling with no room to differentiate. Too hard (`accu`, and now `alu`
even post-fix) and there's a floor with no room either. The pilot's
alphabetical-first-per-category selection rule was explicitly designed
to avoid cherry-picking a favorable sample — and it did that — but a side
effect of avoiding difficulty-based selection is that it also didn't
control for landing in the band where the mechanism is even measurable.
That's not a flaw in the rule; it's a real, structural fact about what
this method can and can't show, worth carrying into how the full study
is designed and read.

**The full-50 run self-corrects on coverage** (it runs everything, no
selection question) **but only if per-module difficulty is reported
alongside the aggregate.** A pooled pass rate across 50 modules with a
mix of ceilings, floors, and recoverable-band modules will hide exactly
the structure this pilot's 3-module pooled number hid — a flat 40%
looked like "no effect" until the per-module breakdown showed it was
actually three completely different stories glued together. Report per
module, not just pooled, in the full study.

**Do not claim STITCH's RTLLM value is established, positively or
negatively.** The pilot was diagnostic and harness-validation work. It
found two real bugs, clarified what conditions the mechanism needs to be
measurable at all, and left the actual RTLLM question open.

---

## Graphs (rough, from complete data only — `phase1/results/`, gitignored)

Every image is watermarked "PILOT / TRIAL — NOT A RESULT" directly on
the figure, not just in this doc.

- `phase1/results/pilot_graph1_pass_rate.png` — pass rate per condition,
  3 complete modules, grouped by module (the demo graph).
- `phase1/results/pilot_graph2_failure_class.png` — COMPILE vs LOGIC
  failure-class breakdown per module.
- `phase1/results/pilot_graph3_fire_rate.png` — interpreter fire rate
  (% of runs with ≥1 `semantic_fired`) per STITCH-involving condition,
  pooled across the 3 complete modules.

---

## D. HPC readiness notes (not a run — what the full study needs)

**Confirmed compatible pool: 44/50.** 6 excluded, each for a distinct,
already-diagnosed reason (full table in `phase1/RTLLM_PILOT_PREREG.md`):

| design | reason |
|---|---|
| `radix2_div` | the RTLLM golden reference itself fails its own testbench (3/8 vectors) — not fixable by us |
| `multi_8bit` | `Incomplete for loop` — non-Verilog-2001 syntax in the testbench, this iverilog build rejects it |
| `ring_counter` | testbench does an array-slice assignment requiring SystemVerilog |
| `asyn_fifo` | testbench uses a `break` statement, unsupported by this iverilog build |
| `freq_divbyodd` | `reg` driven by continuous assignment in the testbench |
| `clkgenerator` | same reg/continuous-assignment issue, in the testbench's own clock generation |

**Both harness fixes (bug #1, bug #2) must be in the HPC build.** Bug #2
alone currently zeroes 4 of the 44 compatible designs (`alu`, `calendar`,
`signal_generator`, `multi_booth_8bit`) unconditionally, regardless of
model quality.

**Cost reality, from real pilot data**: a module that never exits early
(`alu`-class) costs its full iteration cap on every replicate, every
condition, every model — no early stopping to average the cost down.
**Budget HPC time off the observed worst-case module, not the mean of
easy modules** — extrapolating from `accu`/`counter_12`/`barrel_shifter`'s
mostly-short runs would understate wall-clock/compute cost by however
many of the 44 turn out `alu`-shaped.

**Planned HPC scope — to design next, not decided here:**

| axis | scope | phase |
|---|---|---|
| Modules | full 44-compatible pool, pass@5 | Phase 1 |
| Model ladder | 4B → 32B open-weight | Phase 1 |
| Fine-tuning comparison | RTLCoder vs. deepseek-coder twin (same base weights, controlled natural experiment already identified in `plans/research_plan_v2.md` §3.1) | Phase 1 (RTLCoder), cheap to add |
| Frontier APIs | separate axis, own budget check | Phase 2 |
| STITCH conditions | needs a decision: same 5-condition design as Task 3, or trimmed given what this pilot showed about escalation only being measurable in a specific difficulty band | to decide together, not defaulted |
