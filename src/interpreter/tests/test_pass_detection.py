"""
tests/test_pass_detection.py — unit tests for detect_outcome() / the
BENCHMARK_PASS_SPECS registry (pass_detection.py), the shared module that
replaced Bug #3's hardcoded, benchmark-specific pass/fail substring checks
(see pass_detection.py's module docstring for the full history).

Real per-benchmark pass/fail cases use REAL CAPTURED sim-log fragments
(the "--- SIMULATION ---" section of an actual sim_log.txt, exactly what
run_iverilog_sim() passes to detect_outcome()), stored as fixture files
under tests/fixtures/pass_detection/{phase1,rtllm}/ -- pulled directly
from real HPC/laptop run output:
  - phase1/alu_8bit_pass_real.txt   <- phase1/results/stuck_threshold_diag/
    off/replicate_1/deepseek-coder_67b/sem_adv/alu_8bit/iter_1/sim_log.txt
  - phase1/pwm_generator_fail_real.txt <- .../pwm_generator/iter_2/sim_log.txt
  - rtllm/counter_12_pass_real.txt  <- phase2/results/twin_run_pilot/native/
    replicate_1/rtlcoder-deepseek-v11/baseline/counter_12/iter_1/sim_log.txt
    (this exact file is the one TWIN_PILOT_ANALYSIS.md's preamble names as
    the smoking-gun example of Bug #3: recorded "pass": false despite this
    literal content)
  - rtllm/accu_fail_real.txt         <- .../accu/iter_2/sim_log.txt (a real
    "===========Error===========" verdict, not a synthesized string)
  - rtllm/barrel_shifter_fail_real.txt <- .../barrel_shifter/iter_5/sim_log.txt
    (a real "Test completed with N failures" verdict -- a different fail
    wording than accu's, confirming fail_patterns covers more than one
    literal form)

Edge cases (empty log, warnings-only, case-sensitivity guard, pass-string-
inside-other-text, both-markers tie-break, unregistered benchmark) are
deliberately CONSTRUCTED, not captured -- adversarial inputs like these
are rare or absent in real logs by construction (a testbench's own
$display calls don't accidentally collide with its own pass/fail verdict
line), so they're built by hand to pin down the documented rule, and
clearly labeled as such below.

Run with:  python -m pytest src/interpreter/tests/test_pass_detection.py -v
"""
import os
import sys

import pytest

_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(_HERE, ".."))  # src/interpreter/
from pass_detection import detect_outcome, BENCHMARK_PASS_SPECS  # noqa: E402

FIXTURES = os.path.join(_HERE, "fixtures", "pass_detection")


def _load(*parts):
    with open(os.path.join(FIXTURES, *parts), encoding="utf-8") as f:
        return f.read()


# ── registry sanity ─────────────────────────────────────────────────────────
def test_registry_has_phase1_and_rtllm():
    assert set(BENCHMARK_PASS_SPECS) >= {"phase1", "rtllm"}


def test_unregistered_benchmark_raises_loudly():
    """No silent default -- this is the entire point of the module. See
    its docstring: a silent default here is exactly the Bug #3 shape."""
    with pytest.raises(ValueError, match="unknown benchmark"):
        detect_outcome("whatever", "some_benchmark_nobody_registered")


# ── real captured fragments, one PASS + one FAIL per registered benchmark ──
def test_phase1_real_pass():
    log = _load("phase1", "alu_8bit_pass_real.txt")
    assert detect_outcome(log, "phase1") == "PASS"


def test_phase1_real_fail():
    log = _load("phase1", "pwm_generator_fail_real.txt")
    assert detect_outcome(log, "phase1") == "FAIL"


def test_rtllm_real_pass():
    """This exact fixture is the counter_12 log TWIN_PILOT_ANALYSIS.md's
    preamble names as the concrete example of Bug #3 in action: real
    twin-pilot output, literally "Your Design Passed", that the old
    hardcoded check recorded as a failure. This test is the regression
    guard for that specific finding."""
    log = _load("rtllm", "counter_12_pass_real.txt")
    assert detect_outcome(log, "rtllm") == "PASS"


def test_rtllm_real_fail_error_form():
    """Real "===========Error===========" verdict (accu)."""
    log = _load("rtllm", "accu_fail_real.txt")
    assert detect_outcome(log, "rtllm") == "FAIL"


def test_rtllm_real_fail_test_completed_form():
    """Real "Test completed with N failures" verdict (barrel_shifter) --
    a different literal fail form than accu's, confirming fail_patterns
    isn't tuned to just one observed wording."""
    log = _load("rtllm", "barrel_shifter_fail_real.txt")
    assert detect_outcome(log, "rtllm") == "FAIL"


# ── edge cases (deliberately constructed, see module docstring) ────────────
def test_empty_log_is_unknown():
    assert detect_outcome("", "phase1") == "UNKNOWN"
    assert detect_outcome("", "rtllm") == "UNKNOWN"


def test_warnings_only_log_is_unknown():
    """A log with only Icarus/vvp warnings and no verdict line at all --
    e.g. a testbench whose $finish fires before either branch runs."""
    log = (
        "VCD info: dumpfile wave.vcd opened for output.\n"
        "WARNING: sim.v:12: $readmemh: not enough words in the file\n"
        "counter_12_tb.v:49: $finish called at 430000 (1ps)\n"
    )
    assert detect_outcome(log, "phase1") == "UNKNOWN"
    assert detect_outcome(log, "rtllm") == "UNKNOWN"


def test_phase1_case_sensitivity_guards_against_false_positive():
    """phase1's spec is case_sensitive=True on purpose (preserves
    stitch_runner.py's original behavior exactly -- see pass_detection.py).
    Lower-case "passed" must NOT satisfy the upper-case "PASS" pattern --
    this is the literal Bug #3 mechanism (RTLLM's "Your Design Passed"
    never matched the original case-sensitive "PASS" check either), run
    here as a guard so a future edit can't silently reintroduce
    case-insensitivity for this benchmark and change Phase 1's frozen
    results."""
    log = "the design passed its own internal self-check routine\n"
    assert detect_outcome(log, "phase1") == "UNKNOWN"


def test_pass_word_inside_unrelated_text_does_not_false_positive_rtllm():
    """"Passed" appearing as part of ordinary diagnostic narration, not
    the registered exact pass line, must not be mistaken for a real
    pass -- rtllm's pass_patterns requires the full literal
    "Your Design Passed", not just the word "Passed" in isolation."""
    log = "Note: 3 of 5 assertions in the warm-up phase were skipped.\n"
    assert detect_outcome(log, "rtllm") == "UNKNOWN"


def test_tie_break_fail_wins_phase1():
    """Constructed: both a fail pattern and a pass pattern present in the
    same log (e.g. a per-vector FAIL line printed before a stale/unrelated
    PASS-looking substring elsewhere in the buffer). FAIL must win --
    this replicates stitch_runner.py's original `"FAIL" in output or
    (...)` precedence exactly, so Phase 1's already-published results
    stay reproducible. See pass_detection.py's module docstring."""
    log = "FAIL: a=1 b=0  expected sum=1  got sum=0\nALL TESTS PASSED\n"
    assert detect_outcome(log, "phase1") == "FAIL"


def test_tie_break_fail_wins_rtllm():
    """Constructed: an intermediate debug line loosely mentions "passed"
    while the actual final verdict is a real failure -- the kind of thing
    a testbench's own diagnostic $display could produce ahead of its real
    verdict line. FAIL must win over any pass-shaped substring appearing
    earlier in the same buffer."""
    log = (
        "// stage 1 debug: your design passed the warm-up vector\n"
        "=========== Test completed with 2 failures ===========\n"
    )
    assert detect_outcome(log, "rtllm") == "FAIL"


if __name__ == "__main__":
    sys.exit(pytest.main([__file__, "-v"]))
