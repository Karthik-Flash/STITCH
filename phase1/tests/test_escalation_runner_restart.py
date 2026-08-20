"""
tests/test_escalation_runner_restart.py — integration test for
escalation_runner.run_one_replicate's sem_escalate_restart path, using
REAL WSL tool invocations (iverilog/verilator/yosys) against a fixed,
known-broken decoder_3to8.v (phase0/illustrations/proven/decoder_3to8/
sem_adv_iter1_broken.v — the same real broken file phase0 already recorded
for this module, reused unmodified, not fabricated for this test) but a
MOCKED call_llm that always returns that same broken code regardless of
feedback. This deterministically forces a long identical-signature streak
without waiting on a real model to happen to get stuck the right way, and
without needing the mock to know anything about tool internals.

Requires WSL + iverilog/verilator/yosys installed (same requirement as
running the real runner). Skipped automatically if WSL is unavailable.

Run with:  python -m pytest phase1/tests/test_escalation_runner_restart.py -v
"""
import os
import shutil
import subprocess
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
import escalation_runner  # noqa: E402
from escalation_state import EscalationConfig  # noqa: E402

_HERE = os.path.dirname(os.path.abspath(__file__))
_REPO_ROOT = os.path.join(_HERE, "..", "..")
_BROKEN_V = os.path.join(_REPO_ROOT, "phase0", "illustrations", "proven", "decoder_3to8", "sem_adv_iter1_broken.v")
_TESTBENCH_DIR = os.path.join(_REPO_ROOT, "phase0", "illustrations", "proven")


def _wsl_available() -> bool:
    try:
        r = subprocess.run(["wsl", "echo", "ok"], capture_output=True, text=True, timeout=10)
        return r.returncode == 0
    except Exception:
        return False


@unittest.skipUnless(_wsl_available(), "WSL not available in this environment")
class TestSemEscalateRestart(unittest.TestCase):
    def setUp(self):
        with open(_BROKEN_V, encoding="utf-8") as f:
            self.broken_code = f.read()

        # Deterministic stand-in for the LLM: always returns the same
        # known-broken module, wrapped exactly as call_llm's real return
        # shape (text, prompt_tokens, completion_tokens).
        def fake_call_llm(model, messages):
            return f"```verilog\n{self.broken_code}\n```", 100, 50

        self._real_call_llm = escalation_runner.call_llm
        escalation_runner.call_llm = fake_call_llm

        self.results_dir = os.path.join(_HERE, "_tmp_restart_test_results")
        if os.path.isdir(self.results_dir):
            shutil.rmtree(self.results_dir)

    def tearDown(self):
        escalation_runner.call_llm = self._real_call_llm
        if os.path.isdir(self.results_dir):
            shutil.rmtree(self.results_dir)

    def test_restart_fires_when_model_is_stuck_every_iteration(self):
        config = EscalationConfig(
            escalate_after=2, restart_after=3, allow_restart=True,
            max_iterations=8,
        )
        result = escalation_runner.run_one_replicate(
            spec="(unused -- fake_call_llm ignores the prompt entirely)",
            module_name="decoder_3to8", model="fake-model",
            condition="sem_escalate_restart", run_replicate=1,
            config=config, testbench_dir=_TESTBENCH_DIR, results_dir=self.results_dir,
        )

        summary = result["summary"]
        self.assertFalse(summary["pass"], "the mock never produces working code -- run must exhaust max_iterations")
        self.assertEqual(summary["total_iterations"], 8)
        self.assertTrue(summary["fired_escalate"])
        self.assertEqual(summary["escalation_iteration"], 2, "2 identical baseline failures -> escalate at iter 2")

        # The err_type is identical on every iteration here (the mock never
        # changes), so the pre-existing STUCK_THRESHOLD=2 mechanism fires in
        # lockstep on iterations 2, 4, 6, 8 -- and by this runner's stated
        # precedence (STUCK_THRESHOLD checked first), it wins whenever both
        # triggers land on the same iteration. Traced by hand against
        # EscalationConfig(escalate_after=2, restart_after=3):
        #   iter1 baseline fail (streak=1)
        #   iter2 baseline fail (streak=2) -> ESCALATE; STUCK_THRESHOLD also
        #         fires here (its own independent coarse counter), no
        #         restart-eligibility yet so no collision to observe
        #   iter3 escalated fail (streak=1)
        #   iter4 escalated fail (streak=2); STUCK_THRESHOLD fires (2nd time)
        #   iter5 escalated fail (streak=3) -> restart ELIGIBLE; STUCK_THRESHOLD
        #         counter is at 1 here (reset by iter4's firing) -> restart
        #         actually injected
        #   iter6 escalated fail (streak=1, reset by the iter5 restart);
        #         STUCK_THRESHOLD fires (3rd time)
        #   iter7 escalated fail (streak=2)
        #   iter8 escalated fail (streak=3) -> restart ELIGIBLE again, but
        #         STUCK_THRESHOLD ALSO reaches 2 on this exact iteration and
        #         wins by precedence -> restart is PREEMPTED, not injected
        # This is precisely the "KNOWN INTERACTION" the runner's module
        # docstring flags -- this test exercises it concretely rather than
        # assuming it away.
        self.assertEqual(summary["restart_threshold_reached_iterations"], [5, 8])
        self.assertEqual(summary["restart_iterations"], [5], "iter 8's restart must be preempted by STUCK_THRESHOLD")
        self.assertEqual(summary["restart_preempted_by_stuck_threshold"], [8])
        self.assertTrue(summary["fired_restart"])

        iters = result["iterations"]
        self.assertEqual(len(iters), 8)
        # iterations 1-2 ran under baseline tooling
        self.assertEqual([it["escalation_state"] for it in iters[:2]], ["baseline", "baseline"])
        # iterations 3-8 ran under escalated tooling
        self.assertTrue(all(it["escalation_state"] == "escalated" for it in iters[2:]))
        # restart_injected is set on iteration 5 only (iter 8 preempted, see above)
        self.assertEqual(
            [it["iteration"] for it in iters if it["restart_injected"]],
            [5],
        )
        # every escalated iteration actually invoked verilator+yosys (real
        # tool calls, not mocked) -- this is the cost claim escalation
        # exists to bound, so it must show up as genuine invocation counts
        for it in iters[2:]:
            self.assertEqual(it["tool_invocations"]["verilator"], 1)
            self.assertEqual(it["tool_invocations"]["yosys"], 1)
        for it in iters[:2]:
            self.assertEqual(it["tool_invocations"]["verilator"], 0)
            self.assertEqual(it["tool_invocations"]["yosys"], 0)


if __name__ == "__main__":
    unittest.main()
