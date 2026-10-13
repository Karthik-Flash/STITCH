# STITCH: Handoff (final state, 2026-10-14)

For a new contributor, a fresh Claude Code chat or a planner agent. All study phases are done. The journal paper is
final (v10). The documentation is consolidated. Earlier versions of this file are in git history.

---

## 0. Final state

- **Paper (v10, final).**
  - **Sources:** `paper/overleaf/main.tex` (15 pages including references) and `paper/overleaf/supplement.tex` (S1 to
    S9, 14 pages), with `figures/` beside them.
  - **Build:** a clean-room `latexmk -pdf` gives 0 errors and 0 warnings for both. `paper/STITCH_overleaf.zip` is
    ready for Overleaf.
  - **Change log:** `paper/V10_CHANGES.md`.
  - **Earlier drafts:** v7, v8 and v9, with their by-products, are in `paper/archive/`.
- **Docs (consolidated).**
  - `docs/PHASES_EXPLAINED.md`: every phase;
  - `docs/HPC_GUIDE.md`: the cluster procedure;
  - `docs/reSTITCH.md`: the whole story;
  - `docs/reSTITCH_REVISITED_QA.md`: 93 questions in paper order.

  The documents they replaced are in `docs/archive/`. The private notes are in `private/` (gitignored, local only).
- **Phase 3 (MPSoC).** Complete: 990 runs, plus the pre-registered final batch (the control arm and
  qwen2.5-coder:32b, 396 runs), plus three API ladder rows.
- **API study (`phase2/frontier/`).** Complete except one optional item.
  - Set 4: 612 runs. Set 4b: GPT-4.1 mini and Gemini 2.5 Flash 228/228 each; Claude Haiku 4.5 143/228.
  - Set 4c closed by its stop rule.
  - Spend: $13.70 (INR 1,552).
- **Repository hygiene.**
  - Personal paths and cluster identifiers are placeholders; evidence, pre-registrations and hash-frozen scripts are
    unchanged.
  - `.gitattributes` keeps LF for shell and Slurm scripts.
  - All-history leak audit: clean.
- **Open items** (`phase2/frontier/PENDING.md`):
  1. **Optional:** Haiku's 85 Set 4b runs. The paper marks their projected values and can drop them with
     `make_numbers_set4.py --no-projection`.
  2. **Make the repository public before submission.** The paper's Availability section points to it.

## 1. What STITCH is, in one paragraph

A language model repairs Verilog in a loop: generate, simulate, feed the result back, retry. STITCH adds Verilator
lint and Yosys synthesis to the loop, and a deterministic interpreter (no model) that turns their output into short
repair directives.

The project measures when that helps, how much, at what cost, and for which models.

Conditions:
- `baseline`: simulation only, AutoChip style;
- `raw_adv`: plus raw tool text;
- `sem_adv`: plus directives on every iteration;
- `sem_escalate` and `sem_escalate_restart`: baseline until two identical failure signatures, then directives; the
  restart variant adds one blank-slate retry;
- `baseline_gate` (Phase 3 control): simulation plus a bare "fails sign-off" alarm.

## 2. What each phase established (final numbers, paper v10)

| Phase | Established | Main write-up |
|---|---|---|
| 0 | Two replicated illustrations (`decoder_3to8`, `mux4_oe`, 3/3); the input/output reachability asymmetry; three larger candidates retired | `phase0/evidence/phase0_illustration_hunt_findings.md` |
| 1 | Escalation cuts Verilator and Yosys calls 35 to 45% at an equal or better pass rate; single-run benchmark labels collapse at N=3 | `phase1/PHASE1_FINDINGS.md` |
| 2 (RTLLM) | Tiers (ceiling 6, recoverable 17, floor 19). Always-on interpretation trails baseline by about 4 points on small models, not significant. Escalation with restart matches baseline (0.0, CI -4.6 to +4.6), and its guarantee holds only before the trigger. The tool-call cut grows 16.6, 27.6, 88.6% up the ladder. Fine-tuning (RTLCoder) shows no net gain. The floor is mostly beyond small models. | `phase2/SET1_ANALYSIS.md`, `SET3_ANALYSIS.md`, `TWIN_RUN_ANALYSIS.md`, `phase2/frontier/SET4_REPORT.md` |
| 3 (MPSoC) | Simulation-only repair signs off 63% of runs as defective (all 108 sim-silent runs). Latch-free clean synthesis rises 24% to 88%. Escalation beats the alarm-only control by +19.7 (pre-registered; survives Holm), and v3 beats it by +14.6. Interpretation beats raw text by +14.1 with 23% fewer calls. Escalation is sign-off clean in 72% of runs. Repaired leaves restore synthesis of both meshes. | `phase3/evidence/phase3_final/PHASE3_FINAL.md` |

Every correction made along the way, with its before and after numbers, is in `docs/reSTITCH.md`, Parts 7 to 11.

## 3. Which runner and interpreter ran where (exact)

The interpreter:
- `src/interpreter/stitch_interpreter.py`: the production interpreter, "v2". It has never been edited since Phase 2.
  The SHA-256 of the LF-normalised file is `42f61a493e4544e027b880ba5ae16ef1677c52f9b328cce2e13c25028fb2abff`,
  recorded in every Phase 3 run.
- `stitch_interpreter_v3.py` and `_v3_parsers.py`: the v3 layer, version 3.0.1. It imports v2 unchanged, and
  `version="v2"` reproduces v2 byte for byte.
- `pass_detection.py`: the `detect_outcome(..., benchmark=)` registry (Phases 1 and 2).

| Run | Runner | Interpreter | Models | Budget |
|---|---|---|---|---|
| Phase 0 | `src/runner/stitch_runner.py` | production | gemma3:4b, llama3.1 | 6 |
| Phase 1, 255 runs | `phase1/task3_runner.py` with `escalation_runner.py` | production | gemma3:4b, llama3.1, deepseek-coder:6.7b | 6, escalation 8 |
| Set 2, Twin (630) | `phase2/twin_run_runner.py` with `stitch_runner_hpc.py` and `rtlcoder_adapter.py` | none (`baseline`) | RTLCoder (2 prompts), deepseek-coder:6.7b, gemma3:4b, llama3.1; T=0.5 | 8 |
| Set 1 (1,512) and Set 3 (612) | `phase2/set1_runner.py`, `set3_runner.py` | production | small: gemma3:4b, llama3.1:8b, deepseek-coder:6.7b; large: qwen2.5-coder 14b and 32b, gemma3:27b; T=0.1 | 6, escalation 8 |
| Sets 4, 4b, 4c | `phase2/frontier/set4_runner.py` (Set 3 engine, API model call) | production | GPT-4.1 mini, Gemini 2.5 Flash, Claude Haiku 4.5; Gemini 2.5 Pro (4c) | 6, escalation 8 |
| Phase 3 (1,386 plus 3 x 198 API) | `phase3/runner/stitch_runner_p3.py` with `p3_eval.py` | v2 via `version="v2"`; v3 | 7 local models (3B to 32B); 3 API models | 6 calls, every condition |

## 4. Where things are

See `REPO_INDEX.md`. It covers the top-level map, every phase, the canonical evidence for each paper section, the
command for every rebuild, and the archive, private and gitignore policy.

RTLLM is never copied into the repository: it is read from `$RTLLM_ROOT`.

## 5. Cluster

All cluster commands, pitfalls and the run inventory are in `docs/HPC_GUIDE.md`. Claude Code never runs ssh, scp or
sbatch; the user does.

## 6. Standing conventions

- **Commits:**
  - before every commit, `scan_secrets.py` must report 0 matches, and the staged diff must contain no key prefix;
  - commit with explicit paths;
  - no `Co-Authored-By: Claude` trailer;
  - never force-push.
- **Never edit `src/interpreter/stitch_interpreter.py`.** Extend through the v3 layer.
- **Never move or edit** evidence, pre-registrations, freeze records, task files, fixtures or `phase3/hpc/`. Archive
  superseded material with `git mv`.
- **Claims:**
  - N of at least 3 before a cell is trusted;
  - gate every interpreter claim on `semantic_fired`;
  - report pass rates by difficulty tier (RTLLM) or by sim-silent and sim-visible stratum (Phase 3).
- **Numbers:** every number in a document comes from a generated evidence file, not from memory.
- **Twin:** never frame Set 2 as a STITCH result; its condition is fixed at `baseline`.
- **Private notes:** the notes in `private/` are the user's. Leave them as they are, and never commit them.

---

## Message to the next Claude Code chat

You are picking up STITCH after every study phase and the final journal paper (v10, `paper/overleaf/`).
1. Read this file.
2. Read `REPO_INDEX.md`.
3. Read `docs/reSTITCH_REVISITED_QA.md` for the paper and `docs/reSTITCH.md` for the story.
4. For Phase 3 numbers, read `phase3/evidence/phase3_final/PHASE3_FINAL.md`. For the API study, read
   `phase2/frontier/SET4_REPORT.md`.

The open items are in `phase2/frontier/PENDING.md`.

Take direction from the user. Check plans against the data, point out problems, and propose better options. If a
request would overstate a result or mix protocols, say so before acting, then follow the decision. Do not commit, push
or run anything on the cluster unless asked.
