# Runner Hardening Report — Bug #3 class, structural fix

**Date**: 2026-08-24
**Scope**: pre-HPC-full-run hardening of every pass/fail decision point in the repo, per the runner-hardening brief. Full run not yet submitted — this is the pre-flight gate.

---

## TL;DR

- Built one shared `detect_outcome()` function + `BENCHMARK_PASS_SPECS` registry (`src/interpreter/pass_detection.py`), and made `benchmark` a **required, keyword-only, no-default** argument on every runner entry point that decides pass/fail. Calling any of them without it raises `TypeError` immediately — this is what makes Bug #3's failure mode (a benchmark-specific check silently reused against the wrong benchmark) structurally impossible now, not just patched.
- The actual live bug (`phase2/twin_run_runner.py` carrying **no** RTLLM-aware pass-detection override at all) is fixed. Confirmed by replaying all 445 real sim logs from the 64-run twin pilot through the new detector: **64/64 cells reproduce `corrected_pass.json`'s ground truth exactly**, and the aggregated grid matches the brief's stated numbers exactly.
- Golden-reference check: **44/44 compatible RTLLM designs' golden references are correctly detected as PASS.** The broken-reference half of the check is 36/44 clean, with the remaining 8 individually root-caused (see §4) — none of them are `detect_outcome()` defects.
- **This was run locally only** (Windows/WSL, local `D:\Projects\RTLLM` clone). Per the brief, that does not satisfy the pre-sbatch gate — the HPC-run gate is still outstanding (see §6).

---

## 1. Inventory — every pass/fail decision point found

| # | File | What it did before this fix | Fix applied |
|---|---|---|---|
| 1 | `src/runner/stitch_runner.py` `run_iverilog_sim()` | Hardcoded, case-sensitive: `"FAIL" in output or ("ALL TESTS PASSED" not in output and "PASS" not in output)` | Routes through `detect_outcome(output, benchmark)`. `benchmark` is now a required kwarg on `run_iverilog_sim()`/`run_one_condition()`. |
| 2 | `phase2/stitch_runner_hpc.py` `run_iverilog_sim()` | Byte-identical hardcoded check to #1 — confirmed via direct diff. **This was the live bug**: nothing overrode it for RTLLM runs launched through this file. | Same fix as #1, mirrored. |
| 3 | `phase1/escalation_runner.py` `run_one_replicate()` | Called `run_iverilog_sim` (imported via `from stitch_runner import run_iverilog_sim` — a separate name binding from `stitch_runner.run_iverilog_sim`) | `run_one_replicate()` now also takes a required `benchmark` kwarg, threaded straight through. |
| 4 | `phase1/rtllm_pilot_runner.py` | Had its own fix already — but as a **monkeypatch** (`_rtllm_aware_run_iverilog_sim`, rebinding `stitch_runner.run_iverilog_sim` *and* `escalation_runner.run_iverilog_sim` separately). This is exactly the pattern that let Bug #3 ship unpatched elsewhere: a fix that has to be remembered and reapplied per file. | **Deleted the monkeypatch entirely.** Now just passes `benchmark="rtllm"` explicitly at its two call sites (`_run_classic`, `_run_escalation`). |
| 5 | `phase2/twin_run_runner.py` `_run_one_cell()` | Called `sr.run_one_condition(...)` with **no pass-detection override of any kind.** This is the actual, live, unpatched Bug #3 — every RTLLM pass in the twin pilot was silently recorded as a failure. | Passes `benchmark="rtllm"` explicitly. |
| 6 | `phase1/rtllm_task_a_screen.py` `screen_one()` | Its own **third, independent** hardcoded check: `passed = "Your Design Passed" in sim_out`. Correct for RTLLM (unlike #1/#2's original check), but a second implementation that could silently drift from the shared one. | Routed through `detect_outcome(sim_out, "rtllm")`. |
| 7 | `phase1/task3_runner.py`, `phase1/stuck_threshold_diagnostic.py` | Called `stitch_runner.run_one_condition()` unmodified — always against `benchmarks/v20_diagnostic` or `phase0/illustrations/proven` testbenches. | Pass `benchmark="phase1"` explicitly. |
| 8 | `phase1/smoke_test.py` | Called `escalation_runner.run_one_replicate()` for `decoder_3to8` (a `phase0/illustrations/proven` testbench). | Passes `benchmark="phase1"`. |
| 9 | `phase2/rtlcoder_adapter.py` | **Confirmed to have no pass/fail logic at all.** `generate()`/`postprocess()` only produce code text (stub-rejoin + `endmodule`-cut extraction); pass/fail happens downstream in `run_iverilog_sim()`, reached via `twin_run_runner.py`'s `call_llm` monkeypatch. | No change needed — RTLCoder's output already converges on the same `detect_outcome()` call as every other model, since it flows through the same `run_iverilog_sim()`. |
| 10 | `phase2/smoke_test.py` `check_compile()` | Deliberately does **not** judge pass/fail — prints the sim tail for human inspection only, by explicit design ("pass/fail on THIS specific generation is a separate question from this smoke test"). | Left alone. |
| 11 | `phase1/tests/test_escalation_runner_restart.py` | Pre-existing integration test calling `escalation_runner.run_one_replicate()` directly (real WSL tool invocations against `decoder_3to8`). Broke once `benchmark` became required. | Updated call site: `benchmark="phase1"`. Test still passes end-to-end (real WSL run, not mocked). |

**Files inventoried and found to need no change**: `phase1/error_signature.py`, `phase1/escalation_state.py`, `phase1/demo_error_signature.py`, `phase1/rtllm_alu_refix2_launch.py`, `phase0/analysis/*.py` — none contain pass/fail string logic (checked by grep + read).

---

## 2. `detect_outcome` + registry

New module: `src/interpreter/pass_detection.py` (co-located with `stitch_interpreter.py`, following that file's existing precedent for logic shared verbatim between the Windows/WSL and HPC runners).

```python
def detect_outcome(sim_log: str, benchmark: str) -> Literal["PASS", "FAIL", "UNKNOWN"]:
    ...
```

**Registry** (`BENCHMARK_PASS_SPECS`):

| benchmark | pass_patterns | fail_patterns | case_sensitive | built from |
|---|---|---|---|---|
| `"phase1"` | `["ALL TESTS PASSED", "PASS"]` | `["FAIL"]` | `True` | copied **verbatim** from `stitch_runner.py`'s original hardcoded check, to guarantee byte-for-byte Phase 1 reproducibility |
| `"rtllm"` | `["Your Design Passed"]` | `["Failed", "Error", "Test completed with", "Mismatch"]` | `False` | direct survey of all 50 RTLLM v2.1 `testbench.v` files (see §3) |

**Rules enforced**:
- No default `benchmark` anywhere — every call site is explicit (see §1's inventory).
- Unregistered benchmark → `ValueError`, immediately, no silent fallback.
- Tie-break: **fail-dominant** — if a fail pattern and a pass pattern both appear in the same log, `FAIL` wins. This replicates `stitch_runner.py`'s original `"FAIL" in output or (...)` precedence exactly (Phase 1 regression safety), and is applied as the general rule for every benchmark, not special-cased.
- `UNKNOWN` (neither pattern found) is a real, distinct outcome. Callers treat it as "not a pass" for loop-control purposes but log it separately: `run_iverilog_sim()` returns a 3-tuple `(success, feedback, outcome)`, and `run_one_condition()`/`run_one_replicate()` record it in `metrics["unknown_outcomes"]` / `iter_detail["sim_outcome"]` / `IterationRecord.sim_outcome`, and print a loud `** UNKNOWN OUTCOME **` line when it happens. It is never silently coerced to PASS.

### Testbench convention survey (RTLLM)

Direct grep across all 50 `testbench.v` files under `D:\Projects\RTLLM`:
- **Pass line is uniform**: exactly `"Your Design Passed"` in all 50 (confirmed casing-identical, not assumed).
- **Fail wording is not uniform** — ~25 distinct literal forms surveyed, e.g. `"=========== Failed ==========="`, `"Test completed with N failures"`, `"===========Error==========="`, `"Test failed: A = ..., B = ..."`. `fail_patterns` covers the common roots of all observed forms.
- No collision found between any fail form and the pass line.

---

## 3. Unit tests

`src/interpreter/tests/test_pass_detection.py` — 13 tests, all passing:

- One real-pass + real-fail test per registered benchmark, using **actual captured `sim_log.txt` fragments** (not synthetic strings), stored as fixtures under `src/interpreter/tests/fixtures/pass_detection/{phase1,rtllm}/`:
  - `rtllm/counter_12_pass_real.txt` — this is the *exact* file `TWIN_PILOT_ANALYSIS.md`'s preamble names as the smoking-gun example of the live bug (recorded `"pass": false` despite this literal content). This test is the regression guard for that specific finding.
  - `rtllm/accu_fail_real.txt`, `rtllm/barrel_shifter_fail_real.txt` — two different real fail wordings (`"===========Error==========="` vs `"Test completed with N failures"`), confirming `fail_patterns` isn't tuned to one observed form.
  - `phase1/alu_8bit_pass_real.txt`, `phase1/pwm_generator_fail_real.txt` — real Phase-1-convention captures.
- Edge cases (deliberately constructed, documented as such in the file): empty log, warnings-only log, phase1's case-sensitivity guard (lower-case `"passed"` must NOT satisfy the upper-case `"PASS"` pattern — this is literally the Bug #3 mechanism run as a regression guard), pass-word-in-unrelated-text false-positive guard, fail-dominant tie-break for both benchmarks, unregistered-benchmark raise.

Full existing suite (`src/interpreter/tests/` + `phase1/tests/`) re-run after the refactor: **76/76 passed**, including a real end-to-end WSL integration test (`test_escalation_runner_restart.py`) exercising real `iverilog`/`verilator`/`yosys` calls against `decoder_3to8` under the new required `benchmark` kwarg.

---

## 4. Golden-reference verification (`phase2/verify_pass_detection.py`)

For every one of the 44 compatible RTLLM designs (`phase1/results/rtllm_pilot/task_a_screen.json`, `status=="pass"`):
1. Compile + simulate the **golden reference** (renamed the same way `rtllm_task_a_screen.py` already does) → confirm `detect_outcome() == "PASS"`.
2. Compile + simulate a **deliberately broken** version — same port signature (copied verbatim from the golden reference's own header, ANSI or non-ANSI, including any `#(parameters)` block) but every output forced to the constant `0` → confirm `detect_outcome() == "FAIL"`.

**Result (local run, Windows/WSL, `D:\Projects\RTLLM`)**:

- **Golden side: 44/44 PASS.** Every real RTLLM pass string in the entire compatible pool is correctly recognized — this is the direct, exhaustive regression guard for Bug #3.
- **Broken side: 36/44 FAIL as expected.** The remaining 8 were individually investigated (not glossed over):

| Design(s) | Outcome | Root cause (confirmed by direct inspection) |
|---|---|---|
| `adder_pipe_64bit`, `multi_16bit`, `multi_booth_8bit`, `multi_pipe_8bit`, `parallel2serial` | `UNKNOWN` | All are handshake-protocol designs (`done`/`rdy`/`valid` output gates a testbench wait loop). Forcing that signal to a constant `0` means the wait never resolves; the testbench reaches its own `$finish` without ever printing a pass/fail verdict at all. Confirmed directly for `multi_16bit`: raw sim output is just `testbench.v:72: $finish called at 50000 (1s)` — nothing else. This is a limitation of "force every output to 0" as a generic corruption for handshake designs, not a `detect_outcome()` defect — there was genuinely no pass/fail text for it to classify. |
| `freq_divbyeven` | `COMPILE_ERROR` | Its testbench instantiates a `generate`-array of DUTs with a `parameter NUM_DIV` override per instance; the golden reference declares that parameter in a shape this script's generic header-copy doesn't preserve. A structural incompatibility with this one design's parameterization style, not a pass-detection issue (compile never reaches the point where `detect_outcome()` would run). |
| `edge_detect` | `PASS` (false pass) | **Confirmed a genuine weak-oracle bug in RTLLM's own testbench**, not a detection defect: `edge_detect/testbench.v` only flags an error when `rise != expected && down != expected` are **both** simultaneously wrong (`&&`, not `||`). Forcing both outputs to `0` never satisfies that AND-condition for any of its 4 test vectors, so the testbench's own check formula genuinely never fires, and it genuinely prints `"Your Design Passed"`. `detect_outcome()` correctly reported what was actually printed. |
| `square_wave` | `PASS` (false pass) | **Also a confirmed weak-oracle bug**: `square_wave/testbench.v` only checks for ">8 consecutive `wave_out==1`" — it never checks that the output actually toggles at all. A constant-`0` output trivially satisfies "never more than 8 consecutive ones." Same conclusion: the testbench genuinely passes a stuck-at-0 output; `detect_outcome()` reported it accurately. |

**None of the 8 non-green broken rows are `detect_outcome()` defects.** Every one was traced to either (a) this verification script's generic "force outputs to 0" corruption strategy being unsound for handshake-protocol or heavily-parameterized designs, or (b) a pre-existing weak-oracle bug in two of RTLLM's own testbenches (independently confirmed by reading their check logic directly — not assumed). The 44/44 golden-side result is the number that actually matters for Bug #3's regression guard: it proves every genuine pass string in the whole compatible pool is recognized.

**Full per-design results**: `phase2/results/verify_pass_detection/results.json` (gitignored, local).

### ⚠️ This does NOT satisfy the pre-sbatch gate

Per the brief: *"Do not accept a local-only green from `verify_pass_detection.py`. Local proves the code compiles; HPC proves the deployed harness works."* This run was executed locally (Windows/WSL, local `D:\Projects\RTLLM` clone, local Icarus build) for iteration and debugging, which the brief explicitly permits. **It has NOT been run on HPC.** I have no cluster access from this session. `verify_pass_detection.py` is written to run unmodified on either platform (dual-mode: WSL wrapper on Windows, native `subprocess` on Linux, auto-selected via `platform.system()`) — the outstanding step is:

```
python phase2/verify_pass_detection.py --rtllm-root $RTLLM_ROOT
```

run on an HPC compute node, against the deployed RTLLM checkout and the same Icarus binaries the full run will use, before `sbatch` goes out.

---

## 5. Twin-pilot regression check (`phase2/regression_check_twin_pilot.py`)

Replays all 445 real, on-disk `sim_log.txt` files from the 64-run twin pilot (`phase2/results/twin_run_pilot/`, gitignored but present locally) through the new `detect_outcome()`, re-deriving each cell's pass/fail the same way the harness does (first iteration whose simulation reaches PASS), and diffs against `corrected_pass.json` — the manually-verified ground truth `TWIN_PILOT_ANALYSIS.md` built before this fix existed.

**Result: 64/64 cells match exactly.** The aggregated grid also reproduces the brief's stated numbers exactly:

```
accu            — 0/3 every model-condition
counter_12      — 3/3 every model-condition
barrel_shifter  — 1/3 deepseek-coder:6.7b/shared only, 0/3 elsewhere
alu             — 0/3 every model-condition
calendar        — 3/3 RTLCoder/native, 1/1 (partial) RTLCoder/shared, no data elsewhere
```

No deviation found — the fix is correct and the original manual analysis was correct.

---

## 6. Open items before `sbatch`

1. **Run `verify_pass_detection.py` on HPC** against the deployed `$RTLLM_ROOT` and the real Icarus build — this is the actual gate, not the local run reported in §4. Everything needed is in the script; it needs no code changes to run there (dual-mode already handles native Linux).
2. **8 non-green rows in the local golden/broken check are explained but not eliminated** (§4). None indicate a `detect_outcome()` defect, but they mean `verify_pass_detection.py` itself won't print a clean "ALL GREEN" even on HPC for these 8 designs' *broken* half — the HPC runner should expect and cross-check against this same explained set, not treat non-green broken-rows as an automatic abort signal without reading why.
3. Re-deploy `phase2/stitch_runner_hpc.py` to HPC (it changed in this fix — new `benchmark` kwarg, `detect_outcome()` import) and re-confirm both prior fix signatures (Bug #1, Bug #2) are still present, per this project's existing deploy-verification discipline (`HPC_RTLCODER_COMMANDS.md`).
4. Also deploy the new `src/interpreter/pass_detection.py` alongside `stitch_interpreter.py` (same directory, same import pattern) — `stitch_runner_hpc.py` now imports it.

---

## 7. Broader audit (Bug #4 hunt) — reported, not fixed

Per the brief's explicit instruction to report rather than silently fix anything outside pass-detection's scope:

- **Fence-extraction regex mishandles ` ```systemverilog ` and ` ```sv ` language tags.** Confirmed empirically (not assumed): the regex `` r"```(?:verilog)?(.*?)```" `` used identically in `stitch_runner.py`, `stitch_runner_hpc.py`, and `escalation_runner.py`'s `_extract_code()` correctly strips ` ```verilog ` and bare ` ``` ` fences, but for ` ```systemverilog ` or ` ```sv `, the optional `(?:verilog)?` group matches zero characters (since the text doesn't start with the literal word "verilog"), so the literal tag word (`"systemverilog"` or `"sv"`) is captured as part of the "code" and would corrupt compilation — the exact same class of defect as the already-fixed Bug #1 (unclosed-fence corruption). `SYSTEM_PROMPT` instructs models to use ` ```verilog ` specifically, so exposure is likely low, but not proven zero (nothing in the prompt forbids a model habitually tagging `sv`). **Not fixed here** — out of this task's scope (pass-detection), flagged for a follow-up.
- **The fence-extraction regex is duplicated verbatim in three places** (`stitch_runner.py`, `stitch_runner_hpc.py`, `escalation_runner.py`) — currently byte-identical (confirmed by direct comparison), but `escalation_runner.py`'s own docstring already flags this as "keep both in sync if either changes." This is a live divergence risk of the exact Bug #3 shape (a fix applied to one copy and not the others) — same pattern this whole task exists to eliminate for pass-detection, just not yet applied to extraction.
- **`classify_error()` is duplicated verbatim** between `stitch_runner.py` and `stitch_runner_hpc.py` — confirmed byte-identical today by direct diff, same structural risk as the fence regex above (hardcoded substring matching: `"compilation error" in fb`, `"already declared" in fb`, etc.) — same class of fragility as Bug #3, unaudited beyond confirming current parity.
- **RTLCoder adapter vs. shared extraction — confirmed non-overlapping, not a live risk.** `rtlcoder_adapter.py`'s `postprocess()` never sees fence markers at all (RTLCoder is a raw completion model, not a chat model — no ` ```verilog ` wrapper is ever produced or expected). Its extraction (stub-rejoin + first-`endmodule` cut) is a completely separate mechanism from the fence-strip regex, confirmed by reading both paths — there is no shared code between them to drift, and (per §1, item 9) both converge on the same downstream `detect_outcome()` regardless.
- **cwd/path assumptions in simulator invocation**: `run_iverilog_sim()` in both runners already handles per-iteration cwd correctly for every benchmark (Bug #2's fix — `cd`'d via WSL bash on Windows, `subprocess.run(cwd=...)` on Linux) — this was re-confirmed as part of building `verify_pass_detection.py`'s own dual-mode compile/sim helper, which had to replicate the same pattern and worked identically for both `phase1`- and `rtllm`-convention testbenches, including RTLLM's `$readmemh`-using designs (`alu`, `calendar`). No new cwd fragility found.
- **`classify_error()`'s output feeds `_BASE_HINTS`/feedback text but never gates pass/fail** — confirmed it's downstream of the pass/fail decision (called only after `run_iverilog_sim()` already returned), so it's not a Bug #3-shaped risk for *this* task's scope, just noted above as its own separate fragility.

---

## Deliverables checklist

| # | Deliverable | Status |
|---|---|---|
| 1 | `detect_outcome` + `BENCHMARK_PASS_SPECS` registry | ✅ `src/interpreter/pass_detection.py` |
| 2 | All runners refactored to use it, incl. RTLCoder adapter path | ✅ (adapter needed no change — confirmed architecturally clean; see §1 item 9) |
| 3 | `verify_pass_detection.py` + green output | ⚠️ Script done, **local** run reported (§4); **HPC run still outstanding** (§6) |
| 4 | Unit tests + fixtures | ✅ 13/13 new, 76/76 full suite |
| 5 | Twin-pilot regression check + green output | ✅ 64/64 exact match, grid matches brief |
| 6 | This report | ✅ |

**Not cleared for `sbatch` yet** — per the brief's own acceptance criteria, the HPC-run gate (§6, item 1) is the one remaining step.
