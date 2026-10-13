# Pending work (state as of 2026-10-13)

**Only one item is pending, and it is optional: Haiku's 85 Set 4b runs (section 1).** Everything else is done.
Money: INR = USD × 96 × 1.18.

## Wrap-up status (final clean-up brief, 2026-10-14; resume here)

| Step | Status |
|---|---|
| Enforce LF line endings (`.gitattributes`) | done, commit `d6d10c2` |
| Archive superseded paper drafts into `paper/archive/` | done (this commit) |
| Consolidate docs: `docs/PHASES_EXPLAINED.md`, `docs/HPC_GUIDE.md`, `docs/reSTITCH.md`; old docs to `docs/archive/`; private originals to `private/` (gitignored) | in progress |
| `docs/reSTITCH_REVISITED_QA.md` | to do |
| Update `REPO_INDEX.md` and `handoff.md`; tests; push `main`; final leak audit | to do |

To resume: run `git log --oneline -6` and continue with the first row that is not done.

Done:
- **2026-10-12:**
  - Gemini 2.5 Flash Set 4b (228/228) and the Gemini Phase 3 ladder row (198/198).
  - Set 4c, closed (section 1b).
- **2026-10-13:**
  - Paper v9 (`paper/STITCH_EXT_v9.tex`, 16 pages, with the Gemini column) and its supplement.
  - The repository clean-up and `REPO_INDEX.md`.
  - Staged commits on `phase3-setup`. Push and merge wait for the user's "PUSH".
  - Paper v10, the Overleaf-ready build: `paper/overleaf/`, `paper/STITCH_overleaf.zip`, `paper/V10_CHANGES.md`.
    Haiku's missing floor-tier cells are projected in two marked places only.
  - Personal paths and cluster identifiers replaced by placeholders.

## 1. Claude Haiku 4.5, Set 4b: 85 runs to finish (optional, later; when Anthropic credit is added)

Haiku is at 143/228 valid runs. The other 85 errored on 2026-09-29 with HTTP 400 "credit balance is too
low". They cost $0. They are recorded as errored in
`phase2/results/set4_api/floor_full/anthropic/master_log.json`.

| Module | Missing (condition, rep) | Runs |
|---|---|---|
| float_multi | sem_escalate_restart rep3 | 1 |
| traffic_light | all 4 conditions × rep1–3 | 12 |
| barrel_shifter | all 4 conditions × rep1–3 | 12 |
| pulse_detect | all 4 conditions × rep1–3 | 12 |
| LIFObuffer | all 4 conditions × rep1–3 | 12 |
| fsm | all 4 conditions × rep1–3 | 12 |
| serial2parallel | all 4 conditions × rep1–3 | 12 |
| counter_12 | all 4 conditions × rep1–3 | 12 |
| **Total** | | **85** |

"All 4 conditions" = baseline, sem_adv, sem_escalate, sem_escalate_restart.

**Before running:**
1. Add credit in the Anthropic console.
2. Write a short pre-registration amendment (Amendment 4 in `SET4_PREREG.md`): scope = these 85 runs,
   protocol unchanged, the cap below.
3. Confirm the toolchain: `wsl -e bash -lc 'bash $REPO_ROOT/phase2/frontier/osscad_versions.sh 20260917'`
   must print Yosys 0.69+71 (150c32b03), Verilator 5.053, Icarus 14.0.
4. Do a smoke call: `run_set4.sh ... --smoke-call` with the same ledger and cap.

**Resume command** (WSL; `--retry-errored` drops the 85 errored entries from the master log, so they run
once more; completed runs are never re-run):

```
wsl -e bash -lc 'bash $REPO_ROOT/phase2/frontier/run_set4.sh --backend anthropic \
  --model claude-haiku-4-5-20251001 --tag floor_full --budget-usd 15 --provider-cap-usd 9.50 \
  --ledger-dir $REPO_ROOT/phase2/results/p3_api/ledgers --planned 228 \
  --modules traffic_light,barrel_shifter,pulse_detect,LIFObuffer,fsm,serial2parallel,counter_12,float_multi \
  --retry-errored'
```

**Suggested cap.** The projection for the 85 runs is $4.56 (INR 517). It comes from the Part B plan
(`phase2/results/p3_api/b_plan.json`, scaled to the missing runs). A cap of 1.5× is $6.84 of new spend
(INR 775). The runner cap applies to the cumulative ledger `phase2/results/p3_api/ledgers/anthropic_ledger.jsonl`,
which is at $2.6568 now. So `--provider-cap-usd 9.50`. Haiku's alu cost about 1.3× its projection.
If credit is tight, run the modules in the order above and stop at a module boundary.

`backends.py` now stops the provider on the first HTTP 400/402 or a 429 that outlasts its retries
(Amendment 3). An empty Anthropic account therefore stops at the first call, not after 85 errored runs.

**After the run:** `analysis_set4b.py`, `oracle_audit.py alu freq_divbyfrac`, `spend_summary.py`,
`scan_secrets.py`, `leak_audit.py`, then append the results to `SET4_REPORT.md`.

## 1b. Set 4c (Gemini 2.5 Pro, reasoning, residual floor): CLOSED, not pending

Closed on 2026-10-12 (`SET4_PREREG.md` Amendment 5):
- **Why:** the pre-registered stop rule fired on run 1 (10,237 thinking tokens against a 2,048 budget; the answer
  was cut off).
- **Outcome:** 0 of 18 runs completed and no results are reported. Cost USD 0.1723 (INR 19.5).
- **Q7:** answered by the free shifted-trace analysis of the Set 4b runs (in the `SET4_REPORT.md` oracle audit).
- **Code:** the Set 4c code stays; `set4c_launch.sh` refuses to run without `--reopen`.

**The only pending paid work is section 1: Haiku's 85 Set 4b runs, which are optional and for later.**

Remaining Gemini prepaid credit: about INR 423, unused.

## 2. Closure steps (done 2026-10-13, except the push)

1. Paper condensed: v9 is 16 pages including references; detail is in `paper/STITCH_EXT_supplement.tex`. Done.
   v10 (`paper/overleaf/`, Overleaf-ready) is 15 pages. Done.
2. Repository cleaned up, with `REPO_INDEX.md`. Done.
3. Staged, human-readable commits on `phase3-setup`. Done.
4. Merge `phase3-setup` into `main` and push. **Waiting for the user's "PUSH".**
5. Keep API keys out of every commit. `scan_secrets.py` and `leak_audit.py` run before each commit and push. The
   keys live only in `%USERPROFILE%\.stitch\api_keys.env`, outside the repo; `phase2/results/` is gitignored.

If Haiku's 85 runs are ever completed, finish the paper:
1. Run `python -B phase2/frontier/make_numbers_set4.py`. It replaces every projected Haiku value in
   `paper/overleaf/` with the measured one and removes the daggers, the notes and the heat-map hatching.
2. Set `\finaltrue` in `paper/overleaf/main.tex`, rebuild both files and re-zip the folder.

The text needs no edit.

**If Haiku's Set 4b cannot be completed**, keep its 143 measured runs and remove only the projections:
1. Run `python -B phase2/frontier/make_numbers_set4.py --no-projection`. This keeps every measured value, and
   Haiku's missing cells then read "not run":
   - in the heat map, as a "–";
   - in the Q1 count, which is limited to the 12 modules all three models ran;
   - in the supplement's coverage note.

   The daggers, the projected count and the projection table disappear.
2. Set `\finaltrue` in both `paper/overleaf/main.tex` and `supplement.tex`. Rebuild both with `latexmk -pdf` and
   confirm they compile with no "Projected Haiku values remain" error. Then re-zip the folder.

Tested on 2026-10-13: both files compile under `\finaltrue` with 0 errors and 0 warnings (15 and 14 pages).
Re-running without the flag restores the projected version byte for byte.
