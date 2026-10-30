# Phase 1: escalation and the in-house benchmark

Phase 1 built and measured the escalation policies, `sem_escalate` and `sem_escalate_restart`. They behave as the
baseline loop until a run fails twice with the same error signature, then switch to interpreted tool feedback. The
restart variant also issues one blank-slate restart.

Files:
- the state machine: `escalation_state.py`, unit-tested in `tests/`;
- the error signature: `error_signature.py`;
- the runners: `escalation_runner.py`, and `task3_runner.py` for the 255-run in-house benchmark;
- the RTLLM pilot and compatibility screen: `rtllm_pilot_runner.py`, `rtllm_task_a_screen.py`.

Results:
- `PHASE1_FINDINGS.md` and `PHASE1_TASK3_ANALYSIS.md`;
- the pilot's pre-registration: `RTLLM_PILOT_PREREG.md`.

The paper (v11, `../paper/main.tex`) reports Phase 1 in Section 5 (replication) and Section 3.1 with Table 3
(escalation and its cost).

See also:
- `../docs/PHASES_EXPLAINED.md` (every phase);
- `../docs/reSTITCH.md` (the whole story);
- `../REPO_INDEX.md` (where everything lives).
