"""
tests/test_escalation_state.py — unit tests for escalation_state.py's
EscalationState, run without any subprocess, WSL, or LLM call.

Run with:  python -m pytest phase1/tests/test_escalation_state.py -v
       or: python -m unittest phase1.tests.test_escalation_state -v
"""
import os
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
from escalation_state import EscalationConfig, EscalationState  # noqa: E402


class TestBaselineToEscalated(unittest.TestCase):
    def test_escalates_after_N_identical_failures(self):
        st = EscalationState(EscalationConfig(escalate_after=2))
        e1 = st.observe_failure("sigA", iteration=1)
        self.assertFalse(e1.escalated_now)
        self.assertEqual(st.state, "baseline")

        e2 = st.observe_failure("sigA", iteration=2)
        self.assertTrue(e2.escalated_now)
        self.assertEqual(st.state, "escalated")
        self.assertEqual(st.escalation_iteration, 2)

    def test_distinct_signatures_reset_the_streak(self):
        st = EscalationState(EscalationConfig(escalate_after=2))
        st.observe_failure("sigA", iteration=1)
        e2 = st.observe_failure("sigB", iteration=2)  # different -> streak resets to 1
        self.assertFalse(e2.escalated_now)
        self.assertEqual(e2.streak_len, 1)
        self.assertEqual(st.state, "baseline")

        e3 = st.observe_failure("sigB", iteration=3)  # now 2 identical in a row
        self.assertTrue(e3.escalated_now)

    def test_threshold_is_config_driven_not_hardcoded(self):
        st = EscalationState(EscalationConfig(escalate_after=4))
        for i in range(1, 4):
            e = st.observe_failure("sigA", iteration=i)
            self.assertFalse(e.escalated_now, f"should not escalate before N=4 (iter {i})")
        e4 = st.observe_failure("sigA", iteration=4)
        self.assertTrue(e4.escalated_now)

    def test_never_escalates_below_threshold_across_a_full_run(self):
        st = EscalationState(EscalationConfig(escalate_after=3))
        for i, sig in enumerate(["sigA", "sigB", "sigA", "sigB"], start=1):
            e = st.observe_failure(sig, iteration=i)
            self.assertFalse(e.escalated_now)
        self.assertEqual(st.state, "baseline")


class TestMonotonicity(unittest.TestCase):
    def test_stays_escalated_even_after_a_distinct_signature(self):
        st = EscalationState(EscalationConfig(escalate_after=2))
        st.observe_failure("sigA", iteration=1)
        st.observe_failure("sigA", iteration=2)  # escalates
        self.assertEqual(st.state, "escalated")

        st.observe_failure("sigZ", iteration=3)  # totally different failure
        self.assertEqual(st.state, "escalated", "escalation must be monotonic")

    def test_never_returns_to_baseline(self):
        st = EscalationState(EscalationConfig(escalate_after=2))
        st.observe_failure("sigA", iteration=1)
        st.observe_failure("sigA", iteration=2)
        self.assertEqual(st.state, "escalated")
        for i in range(3, 9):
            st.observe_failure(f"sig{i}", iteration=i)  # every failure a new signature
            self.assertEqual(st.state, "escalated")


class TestIterationTiming(unittest.TestCase):
    """The exact scenario documented in escalation_state.py's module
    docstring: escalation is detected by iteration 2's classification, but
    escalated tooling only applies starting iteration 3, whose streak count
    must start fresh at 1, not continue at 3."""

    def test_escalated_phase_streak_starts_fresh(self):
        st = EscalationState(EscalationConfig(escalate_after=2, restart_after=3, allow_restart=True))
        e1 = st.observe_failure("sigA", iteration=1)   # baseline-tooled
        self.assertEqual(e1.streak_len, 1)
        self.assertEqual(st.state, "baseline")

        e2 = st.observe_failure("sigA", iteration=2)   # baseline-tooled, triggers escalation
        self.assertTrue(e2.escalated_now)
        self.assertEqual(st.state, "escalated")

        e3 = st.observe_failure("sigA", iteration=3)   # first ESCALATED-tooled iteration
        self.assertEqual(
            e3.streak_len, 1,
            "escalated-phase streak must start at 1, not continue the pre-escalation count of 2",
        )
        self.assertFalse(e3.restart_now, "restart_after=3 not yet reached in the escalated phase")


class TestRestartSemEscalateRestart(unittest.TestCase):
    def test_restart_fires_after_M_identical_failures_while_escalated(self):
        st = EscalationState(EscalationConfig(escalate_after=2, restart_after=3, allow_restart=True))
        st.observe_failure("sigA", iteration=1)
        st.observe_failure("sigA", iteration=2)   # escalate
        st.observe_failure("sigA", iteration=3)   # escalated streak=1
        st.observe_failure("sigA", iteration=4)   # escalated streak=2
        e5 = st.observe_failure("sigA", iteration=5)  # escalated streak=3 -> restart
        self.assertTrue(e5.restart_now)
        self.assertEqual(st.restart_iterations, [5])
        self.assertEqual(st.state, "escalated", "restart must not de-escalate")

    def test_restart_resets_streak_and_can_fire_again(self):
        st = EscalationState(EscalationConfig(escalate_after=2, restart_after=2, allow_restart=True))
        st.observe_failure("sigA", iteration=1)
        st.observe_failure("sigA", iteration=2)   # escalate
        st.observe_failure("sigA", iteration=3)
        e4 = st.observe_failure("sigA", iteration=4)  # restart_after=2 reached
        self.assertTrue(e4.restart_now)

        # after reset, two more identical failures should fire a second restart
        st.observe_failure("sigA", iteration=5)
        e6 = st.observe_failure("sigA", iteration=6)
        self.assertTrue(e6.restart_now)
        self.assertEqual(st.restart_iterations, [4, 6])

    def test_restart_does_not_fire_before_escalation(self):
        # Even with a pathologically low restart_after, restart can only be
        # evaluated in the "escalated" state.
        st = EscalationState(EscalationConfig(escalate_after=5, restart_after=1, allow_restart=True))
        for i in range(1, 4):
            e = st.observe_failure("sigA", iteration=i)
            self.assertFalse(e.restart_now)
            self.assertEqual(st.state, "baseline")


class TestSemEscalateNeverRestarts(unittest.TestCase):
    """sem_escalate (allow_restart=False) must never inject a restart, even
    when the escalated-phase streak reaches restart_after -- its effect must
    stay isolable from sem_escalate_restart's, per the Task 1 spec."""

    def test_plain_escalate_never_sets_restart_now(self):
        st = EscalationState(EscalationConfig(escalate_after=2, restart_after=3, allow_restart=False))
        st.observe_failure("sigA", iteration=1)
        st.observe_failure("sigA", iteration=2)   # escalate
        st.observe_failure("sigA", iteration=3)
        st.observe_failure("sigA", iteration=4)
        e5 = st.observe_failure("sigA", iteration=5)  # would be the 3rd escalated-phase failure
        self.assertFalse(e5.restart_now)
        self.assertEqual(st.restart_iterations, [])
        self.assertEqual(st.state, "escalated")


class TestObservePass(unittest.TestCase):
    def test_pass_resets_streak(self):
        st = EscalationState(EscalationConfig(escalate_after=2))
        st.observe_failure("sigA", iteration=1)
        st.observe_pass()
        # a fresh failure after a pass should not be treated as a continuation
        e = st.observe_failure("sigA", iteration=3)
        self.assertEqual(e.streak_len, 1)


if __name__ == "__main__":
    unittest.main()
