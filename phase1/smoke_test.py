"""
smoke_test.py — Task 1 validation, per plan v2's "Immediate next actions" #3
("Smoke-test on decoder_3to8/gemma3:4b ... before scaling. If it does not
[work], debug before scaling."). Runs escalation_runner.run_one_replicate
for real (real WSL Verilator/Yosys/Icarus, real Ollama gemma3:4b), on a
small hand-picked set, BEFORE Task 3's full 255-run sweep. This is not
Task 3 -- it is the harness sanity check Task 3 is gated behind.

Output goes to phase1/results/smoke/ (kept separate from the eventual
Task 3 output directory so it's never mistaken for a real evaluation
result).

Requires: WSL (Verilator/Yosys/Icarus) + Ollama serving gemma3:4b.
Produced: caught a real bug on first run — the escalation_state log
field was reading post-mutation state; fixed in escalation_runner.py
before Task 3 (see that file's IterationRecord append comments).

Usage: python phase1/smoke_test.py
"""
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from escalation_runner import run_one_replicate  # noqa: E402
from escalation_state import EscalationConfig  # noqa: E402

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "src", "runner"))
from stitch_runner import BENCHMARK  # noqa: E402  -- decoder_3to8's spec text, reused unmodified

RESULTS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "results", "smoke")
TESTBENCH_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "phase0", "illustrations", "proven")


def main():
    spec = BENCHMARK["decoder_3to8"]["spec"]
    config = EscalationConfig(escalate_after=2, restart_after=3, allow_restart=False)

    print(f"Running sem_escalate smoke test: decoder_3to8 / gemma3:4b / replicate 1")
    print(f"  results -> {RESULTS_DIR}")
    result = run_one_replicate(
        spec=spec, module_name="decoder_3to8", model="gemma3:4b",
        condition="sem_escalate", run_replicate=1, config=config,
        testbench_dir=TESTBENCH_DIR, results_dir=RESULTS_DIR,
    )

    print("\n=== SUMMARY ===")
    print(json.dumps(result["summary"], indent=2))
    print("\n=== PER-ITERATION ===")
    for it in result["iterations"]:
        print(f"  iter {it['iteration']}: state={it['escalation_state']:<10} "
              f"result={it['result']:<4} err_type={it['err_type']} "
              f"sig={it['error_signature']}")


if __name__ == "__main__":
    main()
