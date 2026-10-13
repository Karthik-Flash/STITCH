# Phase 3 integration report (Claude Code, laptop)

Date 2026-09-24. Branch `phase3-setup`, cut from `main` at `61535aa`. First pass: nothing pushed. Second pass (E0
extended to all four conditions, raw-feedback decision, journal errata notes): the branch is pushed to
`origin/phase3-setup` as a backup and is not merged into `main`. No ssh/scp/sbatch was run, and
`src/interpreter/stitch_interpreter.py` was not touched (T0 hash below).

## Outcome per step

| Step | Result | One line |
|---|---|---|
| M.1-M.2 merge the drop | PASS | 318 files into `phase3\`, 2 v3 files into `src\interpreter\`; no target existed; production interpreter diff empty; empty drop folder deleted |
| M.3 root duplicates | PASS | deleted `HANDOFF_PHASE3_CLAUDE_CODE.md` and `PROD_V2_ON_REAL_LOGS.md` (see M.3); kept `reSTITCH_PHASE3_EXPLAINED.md` |
| T0 no overwrite | PASS | sha256 matches `42f61a49...2abff`; only the 2 v3 files are new under `src/interpreter` |
| T1 superseded drop | PASS | nothing left at root; every successor exists in `phase3\` |
| T2 line endings | PASS + 2 FINDINGS | 0 CR bytes in 321 files; `git add --renormalize` does not stage new files; global `*.log` ignore would have dropped 49 fixture logs |
| T3 MPSoC identity | PASS | output exactly as expected |
| T4 runner integration | 2 FINDINGS | T4.1 clean; T4.2 the BLKSEQ `'process'` directive is a since-fixed extraction bug, and three baseline-pass / sem_adv-fail cases exist for the example module (section 2, corrected); T4.3 clean; T4.4 prompts not comparable to Set 1/3 (decision recorded) |
| T5 system prompt | PASS | production prompt written verbatim, 972 bytes, from `phase2/stitch_runner_hpc.py:126` |
| T6 E0 audit | PASS (second pass) | `final_rtl()` picked testbenches in 48% of passes (fixed); all four conditions audited: 773 passes, 60 structurally dirty (7.8%); see `E0_AUDIT_RESULTS.md` |
| T7 local verification | PASS | 44 passed; Gate 1 PASS (11 OK); 990-run plan; mock smoke 55 runs; summarize OK |
| T8 doc pointers | PASS | append-only: 22 insertions, 0 deletions in `docs/`; `handoff.md` section added |
| T9 commit | DONE | branch `phase3-setup`; first pass `dc5e11b` and `93b23ed`, second pass in `git log`; pushed as a backup, not merged |

## Findings that may change how the runs are read (need your decision)

### 1. Phase 3 prompts are not the Set 1/3 prompts (T4.3, T4.4)

- **Raw text is included next to directives in production.** Every branch of production's `_build_sem_adv_feedback`
  (`src/runner/stitch_runner.py:446-509`) prints the raw Verilator text and the raw (trimmed) Yosys text and then the
  directive. So Phase 3's default `--sem-include-raw 1` matches production. No change needed.
- **The raw trimming differs a lot.** Production keeps every Yosys line matching `_YOSYS_KEEP` (`stitch_runner.py:223`),
  with no cap. Phase 3's `raw_tool_text()` keeps only `Latch inferred` lines, `ERROR` lines and `Warning:` lines, capped
  at 40, and shows the gates of a logic loop. Measured on the frozen real logs:

  | fixture | Yosys log lines | production keeps | Phase 3 keeps |
  |---|---|---|---|
  | `probe_latch` | 594 | 98 | 2 |
  | `mpsoc_register_4bit` | 453 | 6 | 1 |
  | `mpsoc_Decoder` | 6,114 | 5,239 (mostly `No latch inferred`) | 40 |
  | `probe_loop` | 444 | 7 (loop as one line) | 6 (loop plus its gates) |

  Consequence: Phase 3 `raw_adv` shows the model far less noise than production's raw feedback (whether that makes it a
  stronger baseline is untested), and Phase 3 `sem_adv_v2` is not byte-comparable to Set 1/3 `sem_adv`. Other differences: Phase 3 labels directives
  `SEMANTIC ANALYSIS (fix these):` and omits production's "Read the SEMANTIC DIRECTIVES carefully" header, and the task
  is repair-with-code-in-the-prompt, not generation from a spec. The system prompt gap is closed by T5. Cross-phase
  comparisons should be described as "same models, temperature and iteration budget", not "same prompt".
- **Decision (2026-09-24): keep `raw_tool_text()` as is.** Phase 3 raw feedback stays filtered to Verilator
  warning/error lines and Yosys latch, error and logic-loop lines, at most 40 lines per tool. The line counts above are the
  record of what that choice changes: on `probe_latch` production would show 98 Yosys lines against Phase 3's 2, and on the
  real `mpsoc_Decoder` 5,239 against 40 (mostly `No latch inferred`, which alone would exceed the runner's 8,192-token
  context). The filter is one function applied to every condition that shows raw text (raw tools, v2, v3, and escalation
  once it escalates; baseline shows none), so comparisons within Phase 3 are like for like. This is stated in the paper
  draft, `phase3/docs/PAPER_SECTION_compositional_integrity.md` section X.6. Cross-phase comparisons should say "same models,
  temperature and iteration budget", not "same prompt".
- **T4.1 is clean.** Every production runner (`src/runner/stitch_runner.py:276`, `phase2/stitch_runner_hpc.py:269`, and
  the escalation runners that call `run_yosys_check`) builds `latch_lines` from raw Yosys lines, at most 5, each line
  filtered by `detect_yosys_latches`. Nobody passes bare names, so evidence F8 never affected a published condition.

### 2. The harmful-regime example (T4.2), corrected on the second pass

**Correction to my first pass.** I first looked only at `nightly_20260814_012758`, the run the handoff named, and wrote
that llama3.1 was not a harm case and qwen2.5-coder:14b was. That is true of that one run only. The conference paper's
llama3.1 example (Table 7, `comb_sensitivity llama3.1:8b  4 Yes / 6 No`, page 5) comes from an earlier run in which
llama3.1 is a genuine baseline-pass / sem_adv-fail case, so the paper's attribution is backed by data. The full record,
with run IDs, per-condition outcomes and the sentences of each PDF that describe the example, is in
`phase3/docs/JOURNAL_ERRATA_NOTES.md`.

The runs live outside this repo, in the older workspace under `D:\BITS Files\Year 3\3-2\LLM_Verilog Project\AgenticAI\`
(the CSV paths point at `STITCHAdv`, which does not hold them). They were read read-only. Cells are
baseline / raw_adv / sem_adv; `PASS@k` is the iteration of the first pass.

| run (files dated) | llama3.1 | qwen2.5-coder |
|---|---|---|
| `AutoChipAdvFB\AutoChipSTITCH\results_stitch` (2026-05-17; the paper's row; a byte-identical copy is `AutoChipAdvFB\results_stitch`) | `llama31`: PASS@4 / FAIL / FAIL, BLKSEQ at iterations 1, 3 | `qwen25-coder_latest`: PASS@2 / FAIL / FAIL, BLKSEQ at 1 |
| `STITCH_v3\runs\nightly_20260814_012758` (2026-08-14) | `llama31_latest`: FAIL / FAIL / FAIL, BLKSEQ at 1, 3 | `qwen25-coder_14b`: PASS@2 / PASS@2 / FAIL, BLKSEQ at 1, 3, 5 |

So for this module there are three baseline-pass / sem_adv-fail cases, not one: llama3.1 and qwen2.5-coder:latest in the
paper's run, and qwen2.5-coder:14b in the nightly. The nightly's llama3.1 row is the only llama3.1 row that fails
everywhere.

- **The directive text is not saved anywhere.** Neither run kept `feedback.txt`, so it cannot be quoted from disk. I
  reproduced it by running the real Verilator 5.020 with the runner's flags on the saved `iter_1` source and feeding
  production `interpret_verilator` without the source path:
  ```
  *** CRITICAL: Blocking assignment (=) in clocked always block for 'process'. ***
  In clocked always @(posedge clk) blocks, ALWAYS use non-blocking: 'process <= value;'
  ```
  It names `'process'` (a word from Verilator's message, not a signal), and the block is not clocked; the real defect is
  the incomplete sensitivity list `@(sel or a)`.
- **Today's production emits nothing for this case.** With the source path (which `sem_adv` passes,
  `stitch_runner.py:658`) the cross-check drops `'process'` because it is not in the file, and the result is `codes=[]`.
  Both runs nevertheless recorded BLKSEQ as fired, so they ran an older interpreter. The run files are dated 2026-05-17
  and 2026-08-14; the only interpreter copy I found with the cross-check (`STITCH_v3\interpreter\stitch_interpreter.py`)
  is dated 2026-08-18, the same day as this repo's first commit, so both runs predate it.
- **What the saved runs support, and what they do not.** In the paper's run, sem_adv followed the directive (iterations
  2, 4, 5, 6 switch `=` to `<=`) and never fixed the sensitivity list, while baseline fixed it at iteration 4. All six
  sem_adv iterations compiled (0 compile errors); every failure is a simulation logic error. The paper's text says
  "generates syntax errors from iteration three onward", and its token and time figures (22,080 vs 17,688 tokens,
  452 s vs 1,159 s) are not in any saved data I could reach; the saved run shows 4,152 / 9,360 / 10,130 tokens and
  127 / 178 / 180 s. Those two points need a check against the paper's artifact (`scripts/recompute_tables.sh`).
- **Independence of Set 1 and Set 3.** The extension's harm claim (sem_adv about 4 points below baseline on the small
  models, 30.7% versus 35.3%) comes from the Phase 2 HPC runs on RTLLM, which ran late August with the cross-check
  already in place, and does not rest on this single cell.

### 3. E0 retro-audit (T6): all four conditions

Extended on the second pass (your decision 1): `audit_existing_runs.py` now also reads `run_log.json`, whose fields sit
under a `summary` key, so `sem_escalate` and `sem_escalate_restart` are covered. Results, tables, cause and model
breakdowns and reading notes are in `phase3/evidence/E0_AUDIT_RESULTS.md`; tables are generated by
`phase3/runner/e0_breakdown.py`.

| condition | passes audited | structurally dirty | rate (Wilson 95% CI) |
|---|---|---|---|
| baseline | 195 | 15 | 7.7% (4.7-12.3) |
| sem_adv | 188 | 13 | 6.9% (4.1-11.5) |
| sem_escalate | 194 | 13 | 6.7% (4.0-11.1) |
| sem_escalate_restart | 196 | 19 | 9.7% (6.3-14.6) |
| all four | 773 | 60 | 7.8% (6.1-9.9) |

- The rates overlap across conditions and no significance test was run. 35 of the 60 dirty passes were first-draft passes,
  so no feedback round happened; the Set 1/3 pass criterion is the testbench, which is why every condition can pass with
  a defect it cannot see. This does not change any Set 1/3 pass-rate result.
- **Bug fixed in `audit_existing_runs.py`.** Each `iter_N/` holds `<module>.v` and a testbench copy `<module>_tb.v`. The
  original `final_rtl()` filter excluded only names starting with `tb`/`test`, so the mtime tie-break picked the
  testbench in **278 of 576** baseline/sem_adv/Twin passes. After the fix, all 773 audited files are `<module>.v` in the
  iteration equal to `iterations_to_pass`. The audit script also gained the `summary` unwrapping (decision 1).
- **Reproducibility.** The earlier 383-run audit was re-run inside the four-condition one and reproduced record for
  record (383 of 383 identical). The one exception to "highest `iter_N` is the final iteration" in the data is a Set 2 run
  (`twin_run/.../rtlcoder-deepseek-v11/baseline/calendar`, stale `iter_2..5` dirs beside a 1-iteration pass), which is
  outside E0's scope.
- **Spot-check by hand (3 records):** `set1_run/adder_16bit/deepseek-coder_67b/sem_adv/rep1` clean;
  `set3_run/fixed_point_substractor/qwen25-coder_32b/baseline/rep3` sim PASS at iteration 1 with 1 Yosys latch event and
  1 loop; `set1_run/instr_reg/deepseek-coder_67b/baseline/rep1` passed at iteration 2 and the audited file is
  `iter_2/instr_reg.v` (Yosys `Async reset \rst yields non-constant value`).
- **Cosmetic:** `p3_eval.synth()` captures `yosys_error` only from lines starting `ERROR`, so errors printed as
  `file.v:17: ERROR: ...` leave `yosys_error` empty (14 of the 30 Yosys failures) while `yosys_ok` is correctly `False`.
  Scoring is unaffected; not changed.

## Lower-impact findings

- **T2, `git add --renormalize` stages nothing for new files** (it implies `-u`). I used a plain `git add` on the same
  paths; the index then reported 0 CRLF except `deploy_phase3.ps1`, which is `eol=crlf` by design.
- **T2, `.gitignore` interactions.** The global `*.log` rule would have silently dropped all 49 real-log fixtures and
  evidence logs that the 44 tests and `validate_tasks.py` read. Added `!phase3/**/*.log`; 49 are staged.
  `handoff*.md` also matches `phase3/HANDOFF_PHASE3_CLAUDE_CODE.md`, so it stays untracked, which follows the repo's
  local-only convention for handoff files. Also ignored from the drop: `phase3/results/` (T2), `STITCH_phase3_drop.zip`
  and `STITCH_phase3_drop/`, and the consumed `phase3/GITATTRIBUTES_ADDITIONS.txt`. All stay on disk.
- **`deploy_phase3.ps1` ships more than its comment says.** It says `results/` is never shipped, but `scp -r phase3`
  copies a local `phase3\results\` too (the E0 output, and any downloaded pilot on a redeploy) and `__pycache__` dirs.
  This is clutter, not a clobber (the run writes to `$B/results`). Not changed.
- **M.3:** the root `PROD_V2_ON_REAL_LOGS.md` was not identical to its `phase3\evidence\` copy. The only differences
  were un-prefixed `tests/...` paths and an older test command, so the `phase3\` copy supersedes it. The other root
  duplicate was byte-identical. `STITCH_phase3_drop.zip` matches `*PHASE3*` but has no copy in `phase3\`, so I left it
  (it is now ignored, not deleted).

## Details

### M / T0 / T1
```
git status --porcelain src/interpreter   ->  ?? src/interpreter/_v3_parsers.py
                                             ?? src/interpreter/stitch_interpreter_v3.py
git diff --stat -- src/interpreter/stitch_interpreter.py   ->  (empty)
sha256(LF) 42f61a493e4544e027b880ba5ae16ef1677c52f9b328cce2e13c25028fb2abff   (expected value)
```

### T2
`.gitattributes` got the 5 lines of `GITATTRIBUTES_ADDITIONS.txt`; `.gitignore` kept your `reSTITCH_PHASE3_EXPLAINED.md`
line and got a Phase 3 block. After the plain `git add` of `phase3` and the two v3 files: 318 files staged, 316 from
the drop plus the 2 v3 files (2 drop files are ignored), and `git ls-files --eol` gives 287 `i/lf w/lf eol=lf`, 30
`i/none` (empty or newline-free files), and 1 `w/lf eol=crlf` (`deploy_phase3.ps1`). A byte scan of all 321 files
under `phase3\` and the v3 files found 0 CR bytes.

### T3
```
source: D:\Projects\STITCH\MPSoC\MPSoC Source Codes | modules repo/ref: 72 71
only in repo: ['test']
only in ref: []
differing bodies: ['main', 'new1', 'nidepack']
T3: PASS
```

### T5
`phase3/runner/system_prompt.txt`: 972 bytes, LF, no trailing newline (the runner reads it with a bare `.read()`), sha256
`886bb444f1cf7585fd4c9587c6b527a8e1beebc72d6926231869c277808cf847`. Source: `phase2/stitch_runner_hpc.py`, the
`SYSTEM_PROMPT` literal at line 126, which Set 1 and Set 3 reach through `escalation_runner_hpc.py`
(`from stitch_runner_hpc import SYSTEM_PROMPT`). It is byte-identical to `src/runner/stitch_runner.py:103`. The runner's
`open().read()` returns exactly the production string.

### T7
```
Yosys 0.33 (git sha1 2584903a060) | Verilator 5.020 2024-01-01 rev (Debian 5.020-1) | Icarus Verilog version 12.0
run_tests.py            44 passed, 0 failed
validate_tasks.py       11 OK lines, GATE 1: PASS   (production sha256 verified inside the tool)
dry-run                 plan: 11 tasks x 5 conditions x 3 reps = 165 runs/model; x 6 model(s) = 990 runs
mock smoke (fix_on_2)   done: 55 new runs
summarize_p3.py         runs: 55 errors: 0; baseline silent structural pass 6/11
```
The local toolchain is exactly the one the fixtures were captured with, so Part C's drift check is the first place a
different tool version can show up.

### T8
`docs/HPC_COMMANDS.md`: one "planned" row in the Part 8 table plus a new Part 9 (14 lines added).
`docs/FULL_RUN_RUNBOOK.md`: new section 9 pointing at `phase3/HPC_PHASE3_COMMANDS.md` Parts A-I and the gate rule (8
lines added). No existing line changed. `handoff.md`: new "Phase 3 status" section at the end.

## Files created or changed
First pass. New: everything under `phase3\` (318 files from the drop), `src/interpreter/stitch_interpreter_v3.py`,
`src/interpreter/_v3_parsers.py`, `phase3/runner/system_prompt.txt`, this report. Edited: `.gitattributes`,
`.gitignore`, `docs/HPC_COMMANDS.md`, `docs/FULL_RUN_RUNBOOK.md`, `handoff.md`. Deleted: root
`HANDOFF_PHASE3_CLAUDE_CODE.md`, root `PROD_V2_ON_REAL_LOGS.md`, `STITCH_phase3_drop\`.

Second pass. New: `phase3/evidence/E0_AUDIT_RESULTS.md`, `phase3/runner/e0_breakdown.py`,
`phase3/docs/JOURNAL_ERRATA_NOTES.md`. Edited: `phase3/runner/audit_existing_runs.py` (`final_rtl()` in the first pass;
`run_log.json` `summary` unwrapping and the usage note in the second), `phase3/docs/PAPER_SECTION_compositional_integrity.md`
(one sentence in X.6), this report (decision, corrected section 2, section 3). The PDFs in the repo root were only read.

Local only, not committed: `note.txt` (git workflow section appended), `phase3/results/e0_audit_phase2.jsonl` (383
records, superseded) and `phase3/results/e0_audit_phase2_all4conditions.jsonl` (773 records).
