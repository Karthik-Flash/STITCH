# Phase 3 integration report (Claude Code, laptop)

Date 2026-09-24. Branch `phase3-setup`, cut from `main` at `672573d`. Nothing was pushed, no ssh/scp/sbatch was run,
and `src/interpreter/stitch_interpreter.py` was not touched (T0 hash below).

## Outcome per step

| Step | Result | One line |
|---|---|---|
| M.1-M.2 merge the drop | PASS | 318 files into `phase3\`, 2 v3 files into `src\interpreter\`; no target existed; production interpreter diff empty; empty drop folder deleted |
| M.3 root duplicates | PASS | deleted `HANDOFF_PHASE3_CLAUDE_CODE.md` and `PROD_V2_ON_REAL_LOGS.md` (see M.3); kept `reSTITCH_PHASE3_EXPLAINED.md` |
| T0 no overwrite | PASS | sha256 matches `42f61a49...2abff`; only the 2 v3 files are new under `src/interpreter` |
| T1 superseded drop | PASS | nothing left at root; every successor exists in `phase3\` |
| T2 line endings | PASS + 2 FINDINGS | 0 CR bytes in 321 files; `git add --renormalize` does not stage new files; global `*.log` ignore would have dropped 49 fixture logs |
| T3 MPSoC identity | PASS | output exactly as expected |
| T4 runner integration | 2 FINDINGS | T4.1 clean; T4.2 harmful-regime example is a since-fixed bug and the harm case is a different model; T4.3 clean; T4.4 prompts not comparable to Set 1/3 |
| T5 system prompt | PASS | production prompt written verbatim, 972 bytes, from `phase2/stitch_runner_hpc.py:126` |
| T6 E0 audit | FINDING | `final_rtl()` picked testbenches in 48% of passes (fixed); 383 passes audited; escalation conditions not covered |
| T7 local verification | PASS | 44 passed; Gate 1 PASS (11 OK); 990-run plan; mock smoke 55 runs; summarize OK |
| T8 doc pointers | PASS | append-only: 22 insertions, 0 deletions in `docs/`; `handoff.md` section added |
| T9 commit | see final message | branch `phase3-setup`, not pushed |

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
  I did not change the runner; if you want production-style raw text, that is a one-function change in `raw_tool_text()`.
- **T4.1 is clean.** Every production runner (`src/runner/stitch_runner.py:276`, `phase2/stitch_runner_hpc.py:269`, and
  the escalation runners that call `run_yosys_check`) builds `latch_lines` from raw Yosys lines, at most 5, each line
  filtered by `detect_yosys_latches`. Nobody passes bare names, so evidence F8 never affected a published condition.

### 2. The harmful-regime example (T4.2)

`runs/nightly_20260814_012758/` is not in this repo. It is at
`D:\BITS Files\Year 3\3-2\LLM_Verilog Project\AgenticAI\STITCH_v3\runs\nightly_20260814_012758\` (the CSV path pointed
at `STITCHAdv`, which holds a different nightly). I read it read-only. Its per-iteration `feedback.txt` prompts were
never saved, so the directive cannot be quoted from disk. `metrics.json` records what fired.

- **llama3.1 `sem_adv` (the run named in the handoff):** BLKSEQ fired at iterations 1 and 3. But baseline and raw_adv
  also fail for llama3.1 on this module, so this row does not show sem_adv causing a failure.
- **The row that does show harm is qwen2.5-coder:14b:** baseline PASS and raw_adv PASS (2 iterations each), sem_adv FAIL
  (6 iterations, BLKSEQ fired at 1, 3 and 5). Under baseline the model rewrote the block as
  `always @(sel or a or b or c)`. Under sem_adv it changed `=` to `<=` and kept the incomplete `@(sel or a)`.
- **The directive text, reproduced** by running the real Verilator 5.020 with the runner's flags on the saved
  `iter_1` source and feeding production `interpret_verilator` without the source path:
  ```
  *** CRITICAL: Blocking assignment (=) in clocked always block for 'process'. ***
  In clocked always @(posedge clk) blocks, ALWAYS use non-blocking: 'process <= value;'
  ```
  It names `'process'` (a word from Verilator's message, not a signal), and the block is not clocked. The real defect
  is the incomplete sensitivity list.
- **Today's production emits nothing for this case.** With the source path (which `sem_adv` passes,
  `stitch_runner.py:658`) the cross-check drops `'process'` because it is not in the file, and the result is
  `codes=[]`. The nightly nevertheless recorded `semantic_fired` with BLKSEQ, so it ran an older interpreter. Git
  cannot date the change (the repo's first commit is 2026-08-18, after the nightly).
- **Implication for the paper:** as an illustration it shows a wrong directive from a since-fixed extraction bug
  harming a model, not correct advice harming a model. Set 1's roughly 4-point harm comes from the Phase 2 HPC run (late
  August, after the repo's first commit that already contains the cross-check), so this finding does not by itself
  affect it.

### 3. E0 retro-audit (T6): results, and one coverage gap

- **Bug fixed in `audit_existing_runs.py`, `final_rtl()` only.** Each `iter_N/` holds `<module>.v` and a testbench copy
  `<module>_tb.v`. The original filter excluded only names starting with `tb`/`test`, so the mtime tie-break picked the
  testbench in **278 of 576** passing runs. After the fix it picks `<module>.v` from the highest iteration in
  **576 of 576**. The "highest `iter_N` is the final iteration" rule held for all 383 Set 1/3 passes; the only exception
  in the data is one Set 2 run (`twin_run/.../rtlcoder-deepseek-v11/baseline/calendar`, stale `iter_2..5` dirs beside a
  1-iteration pass), which is outside E0's scope.
- **Command run** (WSL, results local and gitignored):
  `audit_existing_runs.py --metrics-glob 'phase2/results/set[13]_run/**/metrics.json' --pass-field pass
  --condition-field condition --model-field model --module-field module --out phase3/results/e0_audit_phase2.jsonl`.
  1,062 metrics files, 383 passing runs audited.
- **Result: structurally dirty passes**

  | set | condition | passes | dirty | rate |
  |---|---|---|---|---|
  | Set 1 (4B-8B) | baseline | 109 | 11 | 10.1% |
  | Set 1 | sem_adv | 103 | 10 | 9.7% |
  | Set 3 (14B-32B) | baseline | 86 | 4 | 4.7% |
  | Set 3 | sem_adv | 85 | 3 | 3.5% |
  | pooled | baseline | 195 | 15 | 7.7% |
  | pooled | sem_adv | 188 | 13 | 6.9% |

  By model: deepseek-coder:6.7b 16/111 (14.4%), qwen2.5-coder:14b 6/52 (11.5%), llama3.1 5/63 (7.9%),
  qwen2.5-coder:32b 1/77 (1.3%), gemma3:4b 0/38, gemma3:27b 0/42. I did not test any of these differences for
  significance; baseline versus sem_adv is 15/195 against 13/188.
- **Why runs are dirty** (a run can have several reasons): Yosys hard failure 13 (5 `Async reset ... non-constant`,
  2 `Multiple edge sensitive events`, 6 SystemVerilog `for (integer i...)` in one RAM module), Yosys latch 5, Verilator
  `WIDTHTRUNC` 8, `UNOPTFLAT` 6, `LATCH` 3, Yosys loop 1. The async-reset errors are the same class as the
  `register_1bit` task.
- **Spot-check by hand (3 records):** `set1_run/adder_16bit/deepseek-coder_67b/sem_adv/rep1` clean;
  `set3_run/fixed_point_substractor/qwen25-coder_32b/baseline/rep3` sim PASS at iteration 1 with 1 Yosys latch event and
  1 loop; `set1_run/instr_reg/deepseek-coder_67b/baseline/rep1` passed at iteration 2 and the audited file is
  `iter_2/instr_reg.v` (Yosys `Async reset \rst yields non-constant value`). All three audited files are the last
  iteration's design, not a testbench.
- **Coverage gap.** `sem_escalate` and `sem_escalate_restart` runs have no `metrics.json`; they write `run_log.json`
  with `pass`/`condition`/`model`/`module` nested under a `summary` key (1,054 files, the 8 missing are the documented
  6 + 2 transient errors). The audit script reads top-level fields only, so **E0 covers baseline and sem_adv but not the
  two escalation conditions**. The handoff limits the T6 adaptation to `final_rtl()`, so I stopped there. Covering them
  is a small change (read `m["summary"]` when present) and needs your go-ahead.
- **Cosmetic:** `p3_eval.synth()` captures `yosys_error` only from lines starting `ERROR`, so errors printed as
  `file.v:17: ERROR: ...` leave `yosys_error` empty while `yosys_ok` is correctly `False`. Scoring is unaffected.

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
New: everything under `phase3\` (318 files from the drop), `src/interpreter/stitch_interpreter_v3.py`,
`src/interpreter/_v3_parsers.py`, `phase3/runner/system_prompt.txt`, this report.
Edited: `phase3/runner/audit_existing_runs.py` (`final_rtl()` only), `.gitattributes`, `.gitignore`,
`docs/HPC_COMMANDS.md`, `docs/FULL_RUN_RUNBOOK.md`, `handoff.md`.
Local only, not committed: `note.txt` (git workflow section appended), `phase3/results/e0_audit_phase2.jsonl`.
Deleted: root `HANDOFF_PHASE3_CLAUDE_CODE.md`, root `PROD_V2_ON_REAL_LOGS.md`, `STITCH_phase3_drop\`.
