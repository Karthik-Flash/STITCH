# Phase D — honest delta report (interpreter fixes, v2_fixes_20260816_030703)

**Direct answer to "are the results better?": the fixes are verified correct and working exactly as designed — but the Phase C regime-bucket delta table, read at face value, overstates that by a lot. Read this whole thing before quoting the headline number anywhere.**

## The headline, and why it's misleading

Naive regime-bucket delta across the 18 Phase C cells:

| bucket | old | new | delta |
|---|---|---|---|
| harmful | 7 | 1 | **-6** |
| enabling | 0 | 0 | +0 |
| unexplained_variance | 6 | 4 | -2 |
| fired_no_effect | 5 | 3 | -2 |
| no_change_pass | 0 | 6 | +6 |
| no_change_fail | 0 | 4 | +4 |

"Harmful dropped from 7 to 1" looks like a strong result. **It mostly isn't evidence the fixes worked.** Here's the problem: Phase C re-ran all three conditions completely fresh (`--conditions all`), and `temperature=0.1` with no fixed seed means iteration-1 of every condition is an independent LLM sample — the same structural issue already found and documented for the original llama3.1 investigation (§5 of the handoff doc: `sem_adv` iteration 1 has no code lineage from `raw_adv` iteration 1). The same thing applies here between the *old* sweep and *this* re-run: baseline and sem_adv's first generation are freshly resampled, not held constant while only the interpreter changes.

**Checked every one of the 18 cells for whether the interpreter actually engaged (`semantic_fired > 0`) in the new run — the only condition under which a fix could possibly be responsible for anything:**

| category | count | what it means |
|---|---|---|
| `pure_resampling_noise` | 5 | Interpreter never fired in **either** old or new run (`semantic_fired=0` both times). Regime bucket may have moved, but it has **nothing to do with any of the 5 fixes** — pure independent-sample variance. |
| `confounded` | 6 | Interpreter fired in the **old** run but not the new one, and the outcome also changed. Can't cleanly attribute — could be "the fix's absence of a bad directive helped," could just as easily be "this resample would have passed anyway." Not usable as evidence either way. |
| `clean_definitional_fix` | 3 | Interpreter fired the same in both, old fabricated a name and new correctly declined, **outcome unchanged** (no pass/fail flip). This is the clean, controlled evidence: same underlying situation, only the directive changed, nothing else moved. |
| `partial_cleanup` | 1 | Interpreter still fires in both, but on fewer (more trustworthy) codes now; regime bucket unchanged. |
| `interpreter_engaged_in_new_run` | 3 | Interpreter didn't fire in the old run, does now — genuinely new interpreter involvement, attributable to the fix reaching a code path it didn't before. |

**Of the 6 cells that moved out of "harmful," 5 belong to `confounded` or `pure_resampling_noise`** — meaning the honest read is: *we can't credit the fixes for most of that -6*. Only `sync_fifo_8`/llama3.1 (the one `clean_definitional_fix` that started in the harmful bucket) is solid, attributable evidence, and even that one didn't flip to passing — it just stopped emitting a fabricated directive while still failing.

## What Phase C *does* solidly demonstrate

- **`clean_definitional_fix` (3 cells: `sync_fifo_8`/llama3.1, `lfsr_8bit`/gemma3:4b, `fsm_seq_detector`/deepseek):** interpreter fired identically, old fabricated a signal name, new correctly declined, nothing else about the outcome changed. This is a clean, controlled before/after on the same underlying situation — the strongest evidence in this whole Phase C run, and it confirms the extraction fixes behave exactly as intended.
- **`interpreter_engaged_in_new_run` (3 cells):** the ANSI port-list fix and the general robustness of the rewritten interpreter mean it's now firing (correctly) in situations where it previously never engaged at all — `gemma3:4b/spi_master_8bit` is the clearest example, and it didn't cause any harm (stayed `fired_no_effect`, not `harmful`).
- **No case regressed a `clean_definitional_fix` or `interpreter_engaged_in_new_run` cell into something worse.** Nothing in the attributable evidence points to the fixes causing new harm.

## What Phase C does *not* demonstrate

It does not demonstrate that the fixes changed the aggregate pass rate, because 11 of 18 cells (`pure_resampling_noise` + `confounded`) are contaminated by independent resampling and can't be attributed either way. **The actually clean evidence that the fixes work is what Phase B already produced** — the direct old-vs-new directive text diffs on the *exact same saved `.v` files* (§ Phase B report: `simple_cpu_alu`, `sync_fifo_8`, plus the 20-module llama3.1 sweep and the `full_adder`/`alu_8bit` cases found along the way). That comparison holds everything constant except the interpreter, which is the only way to get a truly controlled answer. Phase C adds breadth but reintroduces the sampling confound Phase B was specifically designed to avoid.

## If this needs to go further

The only way to get a clean, non-confounded large-sample answer to "did the fixes improve the aggregate numbers" is to **not resample** — reuse the exact `.v` files already on disk from the *old* sweep for every iteration, re-run only `run_verilator_lint`/`interpret_verilator` (old vs new) against them, and diff directive text the way Phase B did, at scale, instead of re-running the LLM loop end-to-end. That removes the resampling confound entirely, at the cost of not measuring whether a *different* directive changes what the model generates next (which does require a real LLM call). Worth deciding which question actually matters for the paper before running anything further.

## Bucket table, for the record, with the caveat attached

Use this table only with the categorization above attached — presenting "-6 harmful" on its own in the paper would be a real overstatement of what was actually shown, not a rounding error.

Full per-cell data: `phase_d_delta.json` in this folder.
