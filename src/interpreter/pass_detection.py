"""
pass_detection.py — the single source of truth for "did this simulation
pass or fail", shared verbatim between the Windows/WSL runner
(src/runner/stitch_runner.py) and the HPC port (phase2/stitch_runner_hpc.py),
the same way stitch_interpreter.py already is (see this file's sibling).

WHY THIS EXISTS (read before adding a benchmark or touching the registry):
Three silent runner defects have now corrupted real pilot data, and all
three were the same root cause: a hardcoded, format-specific assumption
about tool/testbench output baked directly into runner logic instead of
being treated as per-benchmark configuration. Bug #3 specifically: the
shared runner's pass-detection checked for the literal, case-sensitive
substring "PASS" / "ALL TESTS PASSED" (tuned for this project's own
v20/v2/phase0 testbenches) -- RTLLM's testbenches instead print
"Your Design Passed", which contains neither, so every genuine RTLLM pass
was silently recorded as a failure wherever this check ran unmodified.
The fix already existed in one runner (phase1/rtllm_pilot_runner.py,
via a monkeypatch) and simply wasn't carried into another
(phase2/twin_run_runner.py) -- proving that a per-runner patch is not a
structural fix.

THE RULE THIS MODULE ENFORCES: no runner may ever hardcode a pass/fail
string. Every runner calls detect_outcome(sim_log, benchmark) with an
EXPLICIT, mandatory benchmark identifier (there is no default -- every
caller must say which convention applies). detect_outcome raises loudly
if the identifier isn't registered in BENCHMARK_PASS_SPECS below; it never
silently falls back to some default spec. Adding support for a new
benchmark's testbench convention means adding one entry to
BENCHMARK_PASS_SPECS, nothing else.

TIE-BREAK RULE: if a fail_pattern AND a pass_pattern both appear in the
same log, FAIL wins. This replicates src/runner/stitch_runner.py's
original (pre-refactor) logic exactly -- `"FAIL" in output or (...)` was
checked before the pass condition -- so this preserves Phase 1's frozen,
paper-cited results byte-for-byte (see BENCHMARK_PASS_SPECS["phase1"]'s
patterns, copied verbatim from the original hardcoded check) while also
being the conservative default for every future benchmark: a genuine
printed failure indicator should never be overridden by an accidental
pass-substring collision.

UNKNOWN is a real, distinct outcome, returned when neither a pass nor a
fail pattern is found. It is NEVER silently treated as PASS. Callers that
need a binary success/failure (e.g. "should the repair loop keep going?")
must decide explicitly how to treat UNKNOWN (the runners in this project
treat it as "not passed" for loop-control purposes, but log it distinctly
in per-iteration metrics so it's visible in the data, not hidden inside
an ordinary FAIL count) -- see run_iverilog_sim() in stitch_runner.py /
stitch_runner_hpc.py for exactly how it's threaded into iter_detail.

Registered benchmarks, and where their patterns were verified from:
  "phase1" -- benchmarks/v20_diagnostic/*_tb.v and
              phase0/illustrations/proven/*_tb.v (surveyed directly;
              identical convention in both directories). Also the
              convention stitch_runner.py's own BENCHMARK dict / CLI runs
              against, and everything task3_runner.py and
              stuck_threshold_diagnostic.py run.
  "rtllm"   -- RTLLM v2.1's 50 testbench.v files (surveyed directly
              against a local checkout): the pass line is always exactly
              "Your Design Passed" (uniform casing across all 50), but
              fail wording varies (~25 distinct literal forms observed:
              "Failed", "Error: ...", "Test completed with N failures",
              "Test failed: ...", etc.) -- fail_patterns lists the common
              roots that cover every observed form. case_sensitive=False
              is a defensive default (all 50 observed instances already
              use identical casing; this costs nothing and guards against
              any RTLLM design outside the 44-compatible pool using
              slightly different casing).
"""

from dataclasses import dataclass, field
from typing import List, Literal

Outcome = Literal["PASS", "FAIL", "UNKNOWN"]


@dataclass(frozen=True)
class PassSpec:
    pass_patterns: List[str]
    fail_patterns: List[str] = field(default_factory=list)
    case_sensitive: bool = False


BENCHMARK_PASS_SPECS = {
    # v20_diagnostic / phase0-proven convention. Patterns are copied
    # VERBATIM from src/runner/stitch_runner.py's original hardcoded check
    # (`"FAIL" in output or ("ALL TESTS PASSED" not in output and "PASS"
    # not in output)`) -- do not "clean up" this spec without re-running
    # phase2/regression_check_twin_pilot.py-style validation against real
    # Phase 1 data first; Phase 1's results are already in the paper.
    "phase1": PassSpec(
        pass_patterns=["ALL TESTS PASSED", "PASS"],
        fail_patterns=["FAIL"],
        case_sensitive=True,
    ),
    # RTLLM v2.1 convention -- see module docstring for the survey this
    # was built from.
    "rtllm": PassSpec(
        pass_patterns=["Your Design Passed"],
        fail_patterns=["Failed", "Error", "Test completed with", "Mismatch"],
        case_sensitive=False,
    ),
}


def detect_outcome(sim_log: str, benchmark: str) -> Outcome:
    """Returns "PASS", "FAIL", or "UNKNOWN" for `sim_log` (the simulator's
    stdout+stderr -- NOT the compile log) under `benchmark`'s registered
    convention. `benchmark` is mandatory and must be a key in
    BENCHMARK_PASS_SPECS; there is no default, and an unregistered
    identifier raises ValueError immediately rather than silently
    guessing -- see the module docstring for why that boundary is the
    entire point of this module existing.
    """
    if benchmark not in BENCHMARK_PASS_SPECS:
        raise ValueError(
            f"detect_outcome: unknown benchmark {benchmark!r}. "
            f"Registered benchmarks: {sorted(BENCHMARK_PASS_SPECS)}. "
            "No silent default is provided on purpose -- register this "
            "benchmark's testbench convention in BENCHMARK_PASS_SPECS "
            "(src/interpreter/pass_detection.py) before calling "
            "detect_outcome() with it. This is exactly the class of bug "
            "this module exists to prevent (see module docstring)."
        )

    spec = BENCHMARK_PASS_SPECS[benchmark]
    if spec.case_sensitive:
        haystack = sim_log
        fail_patterns = spec.fail_patterns
        pass_patterns = spec.pass_patterns
    else:
        haystack = sim_log.lower()
        fail_patterns = [p.lower() for p in spec.fail_patterns]
        pass_patterns = [p.lower() for p in spec.pass_patterns]

    # Fail-dominant tie-break -- see module docstring.
    if any(p in haystack for p in fail_patterns):
        return "FAIL"
    if any(p in haystack for p in pass_patterns):
        return "PASS"
    return "UNKNOWN"
