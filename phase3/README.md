# Phase 3: MPSoC composition + interpreter v3

Phase 3 tests STITCH on real multiprocessor hardware code. It repairs 11 defective modules: 8 taken from the group's
MPSoC and 3 seeded RISC-V/NoC modules. The repaired modules are then plugged back into the full designs and
re-synthesised, to see whether leaf-level repair restores top-level synthesis.

**New to this?** Read `docs/PHASE3_EXPLAINED.md` first; it assumes no hardware background.

## What goes where

| Path | Contents |
|---|---|
| `HANDOFF_PHASE3_CLAUDE_CODE.md` | today's integration tasks T0–T10 for Claude Code (laptop only) |
| `HPC_PHASE3_COMMANDS.md` | the user's HPC steps, Parts A–I (PowerShell + ssh), gates and failure table |
| `runner/stitch_runner_p3.py` | the runner: Ollama or mock backend, 5 conditions, equal budget, resumable, `--dry-run` |
| `runner/p3_eval.py` | the single evaluator: sim + Verilator + Yosys → `func_pass` / `struct_clean` / `clean_pass` |
| `runner/validate_tasks.py` | Gate 1: tasks are well-posed, plus the LIVE drift check on the installed tools |
| `runner/compose.py` | splices repaired leaves into `designs/` and re-synthesises (`top_level_synthesis_pass`) |
| `runner/summarize_p3.py` | paper tables T1–T7 with Wilson CIs and sf-gated attribution |
| `runner/audit_existing_runs.py` | E0: structural re-audit of Phase 1–2 recorded passes |
| `runner/check_mpsoc_identity.py` | T3: the repo MPSoC equals the analysed one |
| `tasks/<11>/` | per task: `spec.md`, `input.v` (defective), `golden.v`, `tb.v`, `meta.json` (incl. expected interpreter classes) |
| `designs/` | the real designs (`mpsoc_ref`, `mesh2x2_ref`, `mesh3x3_ref`) + `SANITISATION.md` |
| `tests/` | 44 tests on real frozen logs; `run_tests.py` needs no pytest |
| `hpc/` | slurm scripts (`gate`, `pull`, `run`, `compose`), `common_env.sh`, `models_phase3.txt`, `deploy_phase3.ps1` |
| `evidence/` | `PROD_V2_ON_REAL_LOGS.md` (findings F1–F10), `compose_bounds.jsonl`, `task_validation.json`, `deliverable2_alu/` |
| `docs/` | paper section draft, taxonomy addendum, beginner explainer |
| `../src/interpreter/stitch_interpreter_v3.py`, `_v3_parsers.py` | the v3 layer; imports production `stitch_interpreter.py` **unchanged** |

## Order of work

1. Claude Code runs `HANDOFF_PHASE3_CLAUDE_CODE.md` T0–T10 on the laptop.
2. The user runs `HPC_PHASE3_COMMANDS.md` Parts A–I:
   - **A:** preflight
   - **B:** deploy
   - **C:** gate — must print `ALL GATES PASSED`
   - **D:** pull models
   - **E:** pilot, then review
   - **F:** full 990 runs
   - **G:** monitor / resubmit
   - **H:** compose + summary
   - **I:** download

## Measured before any LLM run (reproducible)

| Measurement | Result |
|---|---|
| Production v2 on real logs | 10 findings (`evidence/PROD_V2_ON_REAL_LOGS.md`); v3 fixes F1–F9 additively; `version="v2"` reproduces production exactly |
| Interpreter on the 11 task inputs | v2 fires on 9 tasks (silent on `register_1bit`, `ni_flit_pack`; wrong advice on `register_4bit`/`register_32bit`; extra misleading directive on `Address_select`); v3 fires the intended class on all 11 |
| 2×2 mesh / 3×3 mesh | synthesis crash with 2,880 / 6,480 latch cells → with 3 leaf fixes: PASS, 0 / 0 |
| MPSoC `main` | synthesis crash, 269 latch cells → with 8 leaf fixes: PASS, 122 cells (all in 5 modules outside the task set) |
| ALU (Deliverable 2) | sim PASS with 34 latch cells → fixed: 0 |
