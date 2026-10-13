# Journal errata notes: the `comb_sensitivity` / BLKSEQ example

Working notes for editing the final draft. **Report only: no paper was edited.** Written 2026-09-24 from
`paper_112_final.pdf` (the MLCAD '26 paper), `STITCH_EXT_FINAL.pdf` and `STITCH_EXT.pdf` (the newer file, same
references), read as text, plus the saved run directories named below.

## Short version

- **The example is real.** The conference paper's harmful-regime row (`comb_sensitivity`, llama3.1, baseline passes at
  iteration 4, sem_adv fails all six) matches a saved run: `AutoChipAdvFB\AutoChipSTITCH\results_stitch\llama31`.
  Attribution to llama3.1 is supported. Two more baseline-pass / sem_adv-fail cases exist for the same module
  (qwen2.5-coder:latest in that run, qwen2.5-coder:14b in the 2026-08-14 nightly). They are extra evidence, not a
  replacement.
- **What caused the harm is now understood, and it has been fixed.** Verilator's BLKSEQ message contains no signal
  name; the interpreter of that time extracted the prose word `process` and told the model to write `process <= value`
  inside a "clocked" block. The block was combinational with an incomplete sensitivity list. A source cross-check added
  later drops such a name, so today's production interpreter emits no directive for this warning. Both runs predate that
  fix. Catching and fixing this against real tool output is part of the project's verification record.
- **Three details in the paper's text do not match the saved run** and are worth checking before the final draft
  (section 3): "syntax errors from iteration three onward", and the token and time figures.
- **The extension's harm claim does not rest on this cell.** It comes from the replicated Set 1 and Set 3 runs, which
  used the corrected interpreter (section 5).

## 1. The BLKSEQ `'process'` finding

**Mechanism.** For `always @(sel or a)` with blocking assignments, Verilator 5.020 reports the block as sequential
because its sensitivity list is incomplete:
```
%Warning-BLKSEQ: comb_sensitivity.v:13:9: Blocking assignment '=' in sequential logic process
```
The message quotes `'='`, not an identifier. The interpreter's fallback signal regex takes the last word on the line,
`process`. The directive built from it:
```
*** CRITICAL: Blocking assignment (=) in clocked always block for 'process'. ***
In clocked always @(posedge clk) blocks, ALWAYS use non-blocking: 'process <= value;'
```
It names a word that is not a signal and describes a clocked block, while the real defect is the incomplete sensitivity
list. The same finding is recorded as F5 in `phase3/evidence/PROD_V2_ON_REAL_LOGS.md`.

**Reproduction.** The runs saved no `feedback.txt`, so the directive is reproduced, not read from disk. On the saved
`sem_adv` source of each run, I ran the real Verilator 5.020 with the runner's flags
(`--lint-only -Wall --bbox-unsup -Wno-DECLFILENAME -Wno-TIMESCALEMOD -Wno-EOFNEWLINE`) and passed the trimmed output to
the production `interpret_verilator` from `src/interpreter/stitch_interpreter.py`, with and without the source path:

| saved source | Verilator | production, with source path (what `sem_adv` passes, `stitch_runner.py:658`) | without the cross-check |
|---|---|---|---|
| R1 `llama31` `sem_adv/iter_1` | BLKSEQ at 13:9 | `codes=[]`, no directive | BLKSEQ, names `'process'` |
| R1 `llama31` `sem_adv/iter_3` | BLKSEQ at 13:9 | `codes=[]`, no directive | BLKSEQ, names `'process'` |
| R1 `qwen25-coder_latest` `sem_adv/iter_1` | BLKSEQ at 13:13 | `codes=[]`, no directive | BLKSEQ, names `'process'` |
| R3 `qwen25-coder_14b` `sem_adv/iter_1` | BLKSEQ at 13:13 | `codes=[]`, no directive | BLKSEQ, names `'process'` |

Each run's `metrics.json` records BLKSEQ as fired at exactly the iterations shown in section 2. With the current code that
could not happen, which is the evidence that the runs used an earlier interpreter.

**Since-fixed status.**
- The fix is the cross-check in `interpret_verilator`, `src/interpreter/stitch_interpreter.py` lines 317-335: a signal
  name must appear in the file under repair, otherwise the directive is dropped and the raw Verilator text stands alone.
- It is in this repo's first commit (`421f8ae`, 2026-08-18). The old workspace's copy,
  `<DATA_ROOT>\STITCH_v3\interpreter\stitch_interpreter.py`, is dated
  2026-08-18 18:13 and contains it. The run files are dated 2026-05-17 (R1) and 2026-08-14 (R3), so both predate it.
- `src/interpreter/WARNING_TAXONOMY.md` and `phase3/evidence/PROD_V2_ON_REAL_LOGS.md` (F5) document the behaviour.

**Current framework, for completeness.**
- *Production (v2):* emits no directive on this code (row 1 to 4 above).
- *v3 layer:* its rule R4 names the real signal and is deliberately lowest priority. It is shown only when no hard
  directive is present, which is the case here. On the saved `llama31` source it prints
  `[STYLE] Blocking '=' inside a clocked always block (line 13: 'out'). Inside always @(posedge ...) use '<=': out <= <value>;`.
  The name is now right, but the wording still assumes a clocked block, which this one is not. None of the 11 Phase 3
  tasks produces BLKSEQ (Gate 1 output), so it does not touch the planned run. A small follow-up would be to gate that
  text on the `always` header actually containing `posedge`/`negedge`. Not changed.

## 2. Run inventory and the attribution question

All under `<DATA_ROOT>\` (outside this repo; the CSV paths in
`phase0/evidence/combined_results.csv` point at `STITCHAdv\runs\`, which does not hold them). Read read-only. Each cell is
`baseline / raw_adv / sem_adv`; `PASS@k` = first pass at iteration k; `FAIL(6)` = no pass in six iterations.

| run ID (files dated) | model dir | outcome | BLKSEQ fired under sem_adv |
|---|---|---|---|
| **R1** `AutoChipAdvFB\AutoChipSTITCH\results_stitch` (2026-05-17) | `llama31` | PASS@4 / FAIL(6) / FAIL(6) | 2 (iterations 1, 3) |
| R1 | `qwen25-coder_latest` | PASS@2 / FAIL(6) / FAIL(6) | 1 |
| R1 | `gemma3_4b` | FAIL(6) / FAIL(6) / FAIL(6) | 2 |
| R1 | `gemma3_12b` | FAIL(6) / FAIL(6) / FAIL(6) | 4 |
| R1 | `llama31_8b` | recorded FAIL in all three with 0 tokens and 0.01 s, so the model never ran; ignore | 0 |
| R2 `AutoChipAdvFB\results_stitch` | `llama31`, `qwen25-coder_latest`, `gemma3_4b` | byte-identical copies of the R1 metrics | same |
| **R3** `STITCH_v3\runs\nightly_20260814_012758\v2` (2026-08-14) | `llama31_latest` | FAIL(6) / FAIL(6) / FAIL(6) | 2 (1, 3) |
| R3 | `qwen25-coder_14b` | PASS@2 / PASS@2 / FAIL(6) | 3 (1, 3, 5) |
| R3 | `deepseek-coder_67b` | FAIL(6) / PASS@3 / PASS@4 | 2 |
| R3 | `gemma3_4b`, `gemma3_12b` | FAIL(6) in all three | 6, 4 |
| R4 `STITCH_v3\runs\resume_20260814_135236\v2` | `deepseek-coder_67b` | PASS@3 / PASS@3 / PASS@4 | 0 |

**Attribution.** A baseline-pass / sem_adv-fail pattern on this module appears for three model runs: llama3.1 (R1),
qwen2.5-coder:latest (R1) and qwen2.5-coder:14b (R3, the only one where raw_adv also passes). The paper's Table 7 row
(llama3.1, `4 Yes / 6 No`, Dec -2) is R1's `llama31` row exactly. So the paper's attribution to llama3.1 stands. If a
working note says the harmful case was "qwen2.5-coder:14b, not llama3.1", that is true only of the nightly R3, where
llama3.1 fails under every condition; it is not a correction of the paper.

Per-iteration detail for the paper's row (R1 `llama31`, from `metrics.json` and the saved `.v` files):

| iteration | baseline | sem_adv |
|---|---|---|
| 1 | FAIL, `always @(sel or a)`, blocking | FAIL, BLKSEQ fired, blocking |
| 2 | FAIL, blocking | FAIL, switched to `<=` |
| 3 | FAIL, blocking | FAIL, BLKSEQ fired, back to blocking |
| 4 | **PASS**, `always @(a or b or c or sel)` | FAIL, `<=` |
| 5-6 | (stopped) | FAIL, `<=` |

sem_adv never repaired the sensitivity list. All ten iterations (4 baseline, 6 sem_adv) compiled: `compile_errors` is 0 in both.

## 3. The paper's sentences against the saved run (`paper_112_final.pdf`, page 5)

| statement in the paper | saved data (R1 `llama31`) | status |
|---|---|---|
| "Under baseline, llama3.1 self-corrects at iteration four." | PASS at iteration 4 | supported |
| "Under semantic advanced, the interpreter fires BLKSEQ" | `semantic_fired` = 2, codes `['BLKSEQ']` | supported |
| "...issues a directive requiring non-blocking assignment restructuring." | consistent with the reproduced directive; the prompt itself was not saved | consistent, not directly readable |
| "The model attempts to follow the directive" | iterations 2, 4, 5, 6 use `<=` | supported |
| "...generates syntax errors from iteration three onward, failing all six." | 0 compile errors; all six iterations are simulation (logic) failures; iteration 3 reverted to blocking `=` | **differs**: check whether this describes a different run |
| "Though syntactically valid, the directive exceeded the model's capability floor" | the model did what the directive said; the directive named `'process'` and assumed a clocked block | interpretation; see below |
| "raw advanced consumed 22,080 tokens against 17,688 for baseline, with inference time rising from 452 seconds to 1,159 seconds" | baseline 4,152 tokens / 127 s; raw_adv 9,360 / 178 s; sem_adv 10,130 / 180 s | **not found**: no saved data I could reach has these figures |
| Table 7 row: comb_sensitivity, llama3.1:8b, 4 Yes / 6 No, Dec -2, Harmful | baseline PASS@4, sem_adv FAIL(6) | supported |

On the capability-floor reading: the paper itself labels it a hypothesis (page 6, "we treat this as a hypothesis
warranting broader validation"). The saved run adds a second candidate explanation that the paper does not mention,
namely that the directive was mis-aimed (a non-signal name, a clocked-block premise), so the model followed advice that did
not apply to its block. The two explanations are not exclusive and the data cannot separate them.

Possible sources for the two mismatches (to verify, not conclusions): the paper's artifact says
`scripts/recompute_tables.sh` recomputes Tables 2 and 7 from cached results (page 8, `github.com/aathirasun/HDLLLM`);
the figures may come from there or from another run that is no longer on this machine. The saved timings (127 to 180 s)
are also far from 452 and 1,159 s, so they were probably taken on different hardware or load.

## 4. Where each PDF describes the example

**`paper_112_final.pdf`** (names the example):

| page | location | what it says |
|---|---|---|
| 2 | contributions list | "We characterise four outcome regimes: enabling, protective, harmful, and irrelevant." (general; not this cell by name) |
| 5 | Section 5.3, Table 7 | row `comb_sensitivity, llama3.1:8b, 4 Yes / 6 No, Dec -2, Harmful` |
| 5 | Section 5.3, harmful-regime paragraph | the full account: baseline passes at 4, sem_adv fires BLKSEQ, "syntax errors from iteration three onward", capability floor, 22,080 vs 17,688 tokens, 452 s vs 1,159 s |
| 6 | end of Section 5.3 | "For complex syntactic restructuring (BLKSEQ), a sub-8B capability floor may be exceeded, meaning the interpreter should fall back to baseline feedback..."; "we treat this as a hypothesis warranting broader validation" |
| 6 | Discussion, "Interpreter scope and capability floors" | "In the harmful regime, directives requiring complex syntactic restructuring (e.g. BLKSEQ on comb_sensitivity) exceed sub-8B capability floors, causing regression absent in the baseline." |
| 6 | Limitations | "a single run per module per model ... Table 2 and Table 7 are point estimates"; "Each of the four interpreter regimes ... is illustrated by one module/model pair" |
| 6 | Future work | "capability-conditioned routing ... thereby avoiding the harmful regimes observed in our evaluation" |
| 8 | Artifact appendix | `recompute_tables.sh` recomputes Table 2 and Table 7 |

The abstract-level statements that raw tool verbosity degrades capable models read as descriptions of the protective
regime (the `decoder_3to8` / gemma3:12b row of Table 7), not of this cell.

**`STITCH_EXT_FINAL.pdf`** (and `STITCH_EXT.pdf`) do **not** name `comb_sensitivity`, llama3.1-on-this-module or BLKSEQ
anywhere. They refer to the example only as the conference paper's "single cell":

| file, page | wording |
|---|---|
| FINAL p.1, Section 1 (same in EXT p.1) | "The conference paper's table of interpreter outcomes was built on single runs: one module, one model, one draw per condition." |
| FINAL p.4, Section 4 (EXT p.3) | "The conference paper's own harmful and protective regimes point to one structural weakness in firing the interpreter on every iteration: it intervenes when intervention is not needed, and occasionally derails a run that was already converging." |
| FINAL p.10 (EXT p.9), findings list, item (1) | "(1) The harmful regime replicates at scale. On the recoverable band, sem adv drops about four points below baseline (30.7% versus 35.3%). This is the exact behaviour the conference paper's harmful regime predicted from a single cell: always-on interpretation intervenes when it should not and occasionally derails a converging run." |
| EXT p.1, abstract only (not in FINAL) | "this harmful regime, previously shown on a single cell, replicates across 17 modules and 3 models" |

## 5. What this does and does not touch in the extension

- The extension's harm result is Set 1 (about 4 points on the recoverable band, small models) and the Set 3 per-model
  table. Both ran on the Phase 2 HPC harness in late August, after the cross-check existed, so this bug cannot be the
  cause of that harm. The finding therefore does not weaken those numbers.
- The phenomenon the extension describes ("intervenes when it should not and occasionally derails a converging run")
  is exactly what R1 shows for llama3.1. What differs is the trigger: the single cell was set off by a since-fixed
  extraction fault, while the replicated harm arises on the corrected interpreter. Sentences that say "the exact
  behaviour ... predicted from a single cell" are true of the phenomenon; a draft that wants to be precise can say the
  single-cell instance was traced to a since-fixed extraction fault and the replicated effect was measured after the fix.
- Escalation is the design response to this failure mode (start as baseline, intervene only after repeated identical
  failures). In R1, baseline converged at iteration 4 while always-on interpretation derailed, which is the case
  escalation is built for.

## 6. Open items before the final draft

1. Find the source of the 22,080 / 17,688 token and 452 s / 1,159 s figures (the artifact's cached results, or another run).
2. Reconcile "syntax errors from iteration three onward" with the saved run (0 compile errors).
3. Decide how to phrase the cause in the text: capability floor (hypothesis), mis-aimed directive (traced), or both.
4. Optional, not run: re-run `comb_sensitivity` on the current interpreter, 3 models x 3 conditions x N=3 on the laptop,
   to state present-day behaviour on this module. It needs Ollama and was not part of this task.
