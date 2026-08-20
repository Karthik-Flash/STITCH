"""
escalation_state.py — TASK 1 deliverable: the sem_escalate / sem_escalate_restart
state machine, as a pure, subprocess-free, LLM-free class.

Deliberately factored out of the runner loop (escalation_runner.py) so the
state-transition logic — the actual thing Task 1 asked to be "implemented",
and the thing a bug in would silently invalidate every downstream number —
can be unit-tested without WSL, Ollama, or any real tool invocation. See
phase1/tests/test_escalation_state.py.

STATES
  "baseline"  — iverilog+vvp only. Every condition (including the plain
                baseline/raw_adv/sem_adv conditions) starts here; for
                sem_escalate/sem_escalate_restart it's also where every RUN
                starts (per-module-run instance, not shared across runs).
  "escalated" — Verilator+Yosys+interpreter fire exactly as in sem_adv,
                unchanged (stitch_runner.py's own functions, called by
                escalation_runner.py — this class only tracks WHICH state
                a given iteration should run tools under, it does not run
                any tool itself).

TRANSITIONS (see EscalationConfig for the two thresholds)
  baseline -> escalated:
    N (config.escalate_after) consecutive FAILED iterations with the SAME
    error_signature. Distinct signatures reset the streak (this is
    error_signature.py's job upstream; this class just compares strings).
    Monotonic: once escalated, this instance never returns to baseline for
    the rest of the run (see observe_failure — there is no transition out
    of "escalated" anywhere in this class).

  escalated -> restart injected (sem_escalate_restart only; config.allow_restart):
    M (config.restart_after) consecutive FAILED iterations with the SAME
    error_signature, counted from the point escalation began — NOT
    including the failure that triggered escalation itself (that failure
    happened under baseline tooling and is what caused the transition; the
    escalated-phase streak starts counting fresh from the first iteration
    that actually ran WITH escalated tooling). After a restart fires, the
    streak resets to 0 and the state stays "escalated" — restart breaks
    the degenerate loop, it does not de-escalate.
    For plain sem_escalate (allow_restart=False), this streak is still
    tracked and returned (restart_fireable=True on the calling iterations)
    so the runner can log "would this cell have triggered restart" even
    though sem_escalate itself never injects anything — this is what
    keeps the two conditions' effects isolable per the Task 1 spec: same
    counting machinery, restart injection is the only behavioral delta.

ITERATION-TIMING NOTE (the part most likely to be gotten wrong):
  observe_failure() is called AFTER an iteration's outcome is known, to
  decide what state the *next* iteration should run tools under. It does
  not retroactively change what tools ran on the iteration just observed.
  Concretely, in a 3-consecutive-same-signature run with escalate_after=2:
    iter 1 FAILS (sig A)                    -> streak=1, still baseline
    iter 2 FAILS (sig A) [ran under baseline]-> streak=2 -> ESCALATE now
    iter 3 [runs under escalated tooling] FAILS (sig A) -> escalated-phase
                                                streak=1 (fresh, not 3)
  Iteration 2 is the last baseline-tooled iteration even though it is the
  one whose classification triggered the transition — the transition
  takes effect starting the NEXT iteration, because tool usage for
  iteration i is decided from iterations 1..i-1's outcomes only (the
  runner has not generated iteration i's code yet when the decision is
  made).

Requires: nothing external — pure class, no WSL, no Ollama, no
subprocess. Unit-tested in isolation in phase1/tests/test_escalation_state.py.
"""
from dataclasses import dataclass


@dataclass
class EscalationConfig:
    """
    All thresholds config-driven, nothing hardcoded in escalation_state.py
    or escalation_runner.py — per the Task 1 requirement.
    """
    escalate_after: int = 2      # N: consecutive identical-signature baseline failures -> escalate
    restart_after: int = 3       # M: consecutive identical-signature escalated failures -> restart injection
    allow_restart: bool = False  # False = sem_escalate, True = sem_escalate_restart
    signature_window: int = 5    # lines error_signature() keys on (see error_signature.DEFAULT_WINDOW)
    max_iterations: int = 8      # Pass@8, per the Task 1 metric


@dataclass
class FailureEvent:
    """Returned by EscalationState.observe_failure() for one FAILED iteration."""
    escalated_now: bool = False    # True only on the iteration whose classification caused baseline->escalated
    restart_now: bool = False      # True only on the iteration whose classification caused a restart injection
    streak_len: int = 0            # length of the current same-signature streak, in the CURRENT phase
    state_before: str = "baseline"
    state_after: str = "baseline"


class EscalationState:
    """One instance per (module, model, condition, run_replicate) — this is
    per-run state, never shared across runs or modules."""

    def __init__(self, config: EscalationConfig):
        self.config = config
        self.state = "baseline"          # "baseline" | "escalated"
        self._last_sig = None
        self._streak = 0                 # consecutive-same-signature count, scoped to the current phase
        self.escalation_iteration = None # 1-indexed iteration where baseline->escalated happened, or None
        self.restart_iterations = []     # 1-indexed iterations where a restart was injected

    def observe_failure(self, signature: str, iteration: int) -> FailureEvent:
        """
        Call once per FAILED iteration, after its error_signature is known.
        iteration: 1-indexed iteration number, used only to record
        escalation_iteration / restart_iterations for logging — the state
        machine itself does not need absolute iteration numbers to decide
        transitions, only the streak.
        """
        state_before = self.state

        if signature == self._last_sig:
            self._streak += 1
        else:
            self._last_sig = signature
            self._streak = 1

        event = FailureEvent(streak_len=self._streak, state_before=state_before)

        if self.state == "baseline" and self._streak >= self.config.escalate_after:
            self.state = "escalated"
            self.escalation_iteration = iteration
            event.escalated_now = True
            # Escalated-phase streak starts fresh on the NEXT observed
            # failure (the first one to actually run under escalated
            # tooling) — see the module docstring's timing note.
            self._last_sig = None
            self._streak = 0
        elif self.state == "escalated" and self._streak >= self.config.restart_after:
            if self.config.allow_restart:
                self.restart_iterations.append(iteration)
                event.restart_now = True
            # Reset the streak whether or not this condition actually
            # injects the restart prompt — sem_escalate (allow_restart=False)
            # still resets so its "would-restart" signal in the log means
            # "reached M consecutive failures", once per M, not "every
            # iteration after the Mth".
            self._last_sig = None
            self._streak = 0

        event.state_after = self.state
        return event

    def observe_pass(self) -> None:
        """A PASS ends the run; nothing downstream reads state after this,
        but reset defensively so a misused instance can't report a stale
        streak."""
        self._last_sig = None
        self._streak = 0
