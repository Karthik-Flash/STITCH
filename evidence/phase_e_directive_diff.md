# Phase E — interpreter-only replay against the old sweep's saved `.v` files

**No LLM calls. No iverilog/vvp re-runs.** Every saved `sem_adv` iteration `.v` file from the pre-fix sweep (`nightly_20260814_012758`, `resume_20260814_135236`, `smoke_now`) was re-linted with the same deterministic `run_verilator_lint`, and the resulting warning text was fed through both the true pre-fix interpreter (hand-reproduced from the diff taken when Fix 1/2 were applied — not imported from any current file, since the deprecated subfolder copy was already patched before the two-file duplication was discovered) and the current fixed `stitch_interpreter.interpret_verilator`. Since the `.v` file, the Verilator invocation, and the warning text are all held bit-for-bit identical between "old" and "new," **any difference in directive text is attributable only to the interpreter fix — there is no resampling confound here**, unlike Phase C.

## Totals

- **100** (model, module) cells replayed — all 5 complete local v20 models × 20 modules, `sem_adv` condition
- **317** total `.v` files examined across all iterations present on disk
- **120** iterations had a clean Verilator lint (no warnings at all) — skipped, not categorized, nothing for any interpreter version to act on
- **197** iterations had at least one Verilator warning and were actually compared

## Bucket counts

| bucket | count | meaning |
|---|---|---|
| `identical_directive` | 173 | Old and new produced the same directive text (or a purely cosmetic wording difference — see below). No fix applies. |
| `fix_declined_junk` | **14** | Old emitted a directive naming a fabricated/placeholder signal; new correctly emits nothing for that code. |
| `fix_reclassified` | **10** | Old gave the wrong UNDRIVEN template (blanket "add an assignment," assuming a declared output); new correctly gives source-grounded guidance instead. |
| `fix_newly_extracted` | 0 | Old used the `"the_signal"` placeholder for a code; new extracted a real signal for that *same* code. Structurally near-impossible under how the fixes work — see note below. |
| `fix_now_declines_where_old_extracted` (regressions) | **0** | Old extracted a verified-real signal; new declined it anyway. **Zero found.** |

`120 (no warnings) + 173 + 14 + 10 + 0 + 0 = 317`. Every file accounted for.

### Why `fix_newly_extracted` is legitimately zero, not a bug

This bucket requires old to hit the `"the_signal"` placeholder default for a code, and new to find a *real* signal for that *same* code. Structurally that can't happen: new's extraction uses the same underlying regex-matching as old, with only a validation *layer* added on top that can reject matches, never manufacture ones old couldn't find. If old found nothing at all, new — using the same base patterns — finds nothing either, and correctly declines (landing in `fix_declined_junk`, not this bucket). Confirmed against the raw data: every placeholder case that changed landed in `fix_declined_junk` as expected.

### 6 cosmetic-only cases folded into `identical_directive`

Six iterations had `old_text != new_text` purely because a *genuine* Path-A UNDRIVEN case got reworded (old: `"is never assigned"`; new: `"is declared but never assigned"`) with no change in classification or advice. These were explicitly flagged by the replay script (`QA FLAG` in the notes) rather than silently binned, and manually confirmed as cosmetic: `deepseek/ripple_carry_adder` (iters 2, 4, 6), `deepseek/uart_tx` (iter 4), `llama3.1/alu_accumulator_top` (iter 4), `llama3.1/ripple_carry_adder` (iter 6). Not counted as a fix in any evidence bucket — the advice itself didn't change.

## A correction worth being precise about

While building this replay, I found that the `sync_fifo_8`/llama3.1 `iter_6` "process" false-positive documented in the Phase B report was **not actually inherited from the old interpreter**. The *true* old fallback regex (`r":\s*([A-Za-z_]\w*)\s*$"`) requires a colon immediately before the identifier and correctly finds nothing on Verilator's `"...in combinational logic process"` line — old correctly fell back to the `"the_signal"` placeholder here, same as many other cases in this bucket. It was my **own first draft of Fix 1** that loosened the fallback to "last word before end of line" (dropping the colon requirement), which is what let `"process"` through — a regression I introduced and then caught via the separate source-crosscheck safeguard, not a second pre-existing bug in the old system. Correcting the record here rather than letting the earlier framing stand uncorrected.

## Connecting back to Phase D

Phase D flagged `sync_fifo_8`/llama3.1 as its one `clean_definitional_fix` case — the single cell in the "harmful → something" movement that could be cleanly attributed to the fixes rather than resampling noise. This replay confirms the mechanism directly: `sync_fifo_8`/llama3.1 shows up in **`fix_declined_junk` twice** (iter_3: `WIDTHEXPAND` on fabricated `'h0'`; iter_6: `COMBDLY` on the `"the_signal"` placeholder). Phase D's one clean movement now has a fully mechanistic, non-confounded explanation: the old interpreter was feeding this module two separate fabricated/placeholder directives across its 6 iterations, and the new one correctly says nothing for either.

## What this data answers

- **"How often was the old interpreter actively misleading the model?"** — `fix_declined_junk` (14) + `fix_reclassified` (10) = **24 of 197 warned iterations (12.2%)** where the old interpreter's directive was either naming a fabricated signal or confidently asserting the wrong category of bug. That's a real, countable, non-confounded number for the paper.
- **"How often was it silently doing nothing when it could have helped?"** — `fix_newly_extracted` = 0. No bounded-upside cases found in this replay; the fixes' value here is entirely in *removing bad advice*, not adding previously-missed good advice.
- **Zero regressions** (`fix_now_declines_where_old_extracted` = 0) — the stricter validation never rejected a signal name that was actually real and present in the source, across all 197 compared iterations.

---

## Full evidence

### Bucket 2 — `fix_declined_junk` (14 cases)

**By model:** deepseek-coder:6.7b (8), gemma3:4b (1), llama3.1:latest (5)
**By module:** counter_4bit (2), fsm_seq_detector (1), full_adder (2), gray_counter_4bit (3), lfsr_8bit (3), sync_fifo_8 (3)

**deepseek-coder:6.7b / counter_4bit / iter_4** — code `COMBDLY`, signal `the_signal`
- OLD: `*** WARNING: Delay (#) in combinational block near 'the_signal'. ***`
- NEW: *(interpreter declined to fire on `COMBDLY` — no directive emitted; other codes in this iteration unaffected)*

**deepseek-coder:6.7b / counter_4bit / iter_5** — code `COMBDLY`, signal `the_signal`
- OLD: `*** WARNING: Delay (#) in combinational block near 'the_signal'. ***`
- NEW: *(declined)*

**deepseek-coder:6.7b / fsm_seq_detector / iter_6** — code `WIDTHTRUNC`, signal `the_signal`
- OLD: `*** WARNING: Bit-width truncation on 'the_signal'. ***`
- NEW: *(declined)*

**deepseek-coder:6.7b / gray_counter_4bit / iter_4** — code `COMBDLY`, signal `the_signal`
- OLD: `*** WARNING: Delay (#) in combinational block near 'the_signal'. ***`
- NEW: *(declined)*

**deepseek-coder:6.7b / gray_counter_4bit / iter_5** — code `COMBDLY`, signal `the_signal`
- OLD: `*** WARNING: Delay (#) in combinational block near 'the_signal'. ***`
- NEW: *(declined)*

**deepseek-coder:6.7b / gray_counter_4bit / iter_6** — code `COMBDLY`, signal `the_signal`
- OLD: `*** WARNING: Delay (#) in combinational block near 'the_signal'. ***`
- NEW: *(declined)*

**deepseek-coder:6.7b / lfsr_8bit / iter_3** — code `WIDTHEXPAND`, signal `the_signal`
- OLD: `*** WARNING: Width expansion on 'the_signal' — value is zero-extended. ***`
- NEW: *(declined)*

**deepseek-coder:6.7b / sync_fifo_8 / iter_2** — code `WIDTHTRUNC`, signal `h0` (fabricated from `8'h00`-style literal)
- Also in this iteration: `BLKSEQ` went from placeholder `'the_signal'` to a real extraction (`'process'` — itself a fabricated match from the pre-source-crosscheck extraction path; both old and new here predate that specific safeguard being exercised in this exact spot, included as-is since the bucket assignment is driven by the WIDTHTRUNC decline)
- OLD: `*** WARNING: Bit-width truncation on 'h0'. ***`
- NEW: *(declined)*

**gemma3:4b / lfsr_8bit / iter_3** — code `WIDTHEXPAND`, signal `the_signal`
- OLD: `*** WARNING: Width expansion on 'the_signal' — value is zero-extended. ***`
- NEW: *(declined)*

**llama3.1:latest / full_adder / iter_2** — code `WIDTHTRUNC`, signal `the_signal`
- OLD: `*** WARNING: Bit-width truncation on 'the_signal'. ***`
- NEW: *(declined — `WIDTHEXPAND` on the real signal `cin` is untouched in the same iteration)*

**llama3.1:latest / full_adder / iter_3** — code `WIDTHTRUNC`, signal `the_signal`
- OLD: `*** WARNING: Bit-width truncation on 'the_signal'. ***`
- NEW: *(declined)*

**llama3.1:latest / lfsr_8bit / iter_3** — code `BLKSEQ`, signal `the_signal`
- OLD: `*** CRITICAL: Blocking assignment (=) in clocked always block for 'the_signal'. ***`
- NEW: *(declined)*

**llama3.1:latest / sync_fifo_8 / iter_3** — code `WIDTHEXPAND`, signal `h0` (fabricated)
- OLD: `*** WARNING: Width expansion on 'h0' — value is zero-extended. ***`
- NEW: *(declined)* — **this is one of Phase D's `sync_fifo_8` mechanism cases, see above**

**llama3.1:latest / sync_fifo_8 / iter_6** — code `COMBDLY`, signal `the_signal`
- OLD: `*** WARNING: Delay (#) in combinational block near 'the_signal'. ***`
- NEW: *(declined)* — **the other Phase D `sync_fifo_8` mechanism case**

### Bucket 3 — `fix_reclassified` (10 cases)

**By model:** deepseek-coder:6.7b (5), llama3.1:latest (5)
**By module:** alu_8bit (2), fsm_seq_detector (1), simple_cpu_alu (3), spi_master_8bit (4)

All 10 cases follow the identical pattern — old gives the same blanket "declared output, add an assignment" advice regardless of what's actually wrong; new correctly determines the signal's real declaration status and gives different guidance. Full text shown for the two distinct signals involved:

**`simple_cpu_alu` / `alu_8bit` — signal `B`** (llama3.1:latest, iters 2, 4, 5 of `simple_cpu_alu`; iters 2, 6 of `alu_8bit`)
- OLD: `*** CRITICAL: Output 'B' is never assigned. ***`<br>`Add an assignment: 'B = <value>;' in your always block or use assign.`
- NEW: `*** CRITICAL: 'B' is flagged as undriven; its declaration is ambiguous from source. ***`<br>`Check BOTH possibilities:`<br>`  A) If 'B' is a declared output that's never assigned: add 'B = <value>;'`<br>`     in your always block or use assign.`<br>`  B) If 'B' is used but never declared at all: add it to the port list`<br>`     (input <width> B) or declare it internally (wire B; / reg B;).`
- (`alu_8bit` iter_6 also independently shows `WIDTHEXPAND` on fabricated `'h7f'` declined in the same iteration — doesn't change the bucket assignment, driven by the UNDRIVEN reclassification.)

**`fsm_seq_detector` / `spi_master_8bit` — signals `clk` / `shift_in`** (deepseek-coder:6.7b, `fsm_seq_detector` iter_4; `spi_master_8bit` iters 2, 3, 4, 5)
- OLD (`clk`): `*** CRITICAL: Output 'clk' is never assigned. ***`<br>`Add an assignment: 'clk = <value>;' in your always block or use assign.`
- NEW (`clk`): `*** CRITICAL: 'clk' is flagged as undriven; its declaration is ambiguous from source. ***`<br>`Check BOTH possibilities: ...`
- OLD (`shift_in`): `*** CRITICAL: Output 'shift_in' is never assigned. ***`<br>`Add an assignment: 'shift_in = <value>;' in your always block or use assign.`
- NEW (`shift_in`): `*** CRITICAL: 'shift_in' is flagged as undriven; its declaration is ambiguous from source. ***`<br>`Check BOTH possibilities: ...`
- (`spi_master_8bit` iter_5 also independently shows `COMBDLY` on placeholder `'the_signal'` declined in the same iteration.)

Every one of these 10 cases resolves to the `"ambiguous"` classification rather than a clean Path B — meaning the flagged signal, while genuinely misdiagnosed by the old blanket template, wasn't cleanly resolvable to "definitely an undeclared identifier" by the source-parsing heuristic either (`B` and `shift_in`/`clk` end up declared as internal `wire`s by later iterations in several of these traces, which is exactly the "declared internally but never driven" third case discussed when Phase B first found this pattern on `simple_cpu_alu`). The ambiguous fallback is still strictly more honest than old's confident wrong answer — it never asserts a fix that isn't grounded in what's actually in the file — but it's also not yet a clean Path A/B resolution in these particular traces. Worth remembering as a real, current limitation of the disambiguation logic when framing this bucket's claim in the paper: "old was wrong" is fully supported; "new is precisely right" is only partially supported — "new no longer asserts something false" is the accurate claim.

### Bucket 4 — `fix_newly_extracted` (0 cases)

Zero, and expected to be zero — see the structural explanation above.

### Bucket 5 — `fix_now_declines_where_old_extracted` / regressions (0 cases)

**Zero cases found across all 197 compared iterations.** No instance of the new, stricter validation rejecting a signal name that was independently verified to actually appear in the source file being checked. This is the strongest single number in this report: it means the fixes' entire effect in this replay is confined to removing bad advice, never accidentally removing good advice.
