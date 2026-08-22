"""
escalation_runner.py — TASK 1 deliverable: the sem_escalate / sem_escalate_restart
runner. Harness/orchestration only — every tool-invocation and directive-
generation function is imported UNMODIFIED from src/runner/stitch_runner.py
and src/interpreter/stitch_interpreter.py (via stitch_runner's re-export).
Nothing under phase0/ or src/ is edited by this file.

CONDITIONS IMPLEMENTED
  sem_escalate          — baseline (iverilog only) until EscalationConfig
                           .escalate_after consecutive identical-signature
                           failures, then escalated (Verilator+Yosys+
                           interpreter, exactly stitch_runner's sem_adv
                           feedback builder). Monotonic once escalated.
  sem_escalate_restart  — identical, PLUS: after .restart_after consecutive
                           identical-signature failures WHILE escalated,
                           inject stitch_runner._REWRITE_PROMPT (the SAME
                           blank-slate template already used by the
                           pre-existing STUCK_THRESHOLD mechanism, reused
                           rather than reinvented) and reset the streak.
                           Stays escalated.

The actual state-transition logic lives in escalation_state.py
(EscalationState) and is unit-tested there without any subprocess/LLM
dependency — this file is the thin integration layer that calls tools,
calls the LLM, and drives that state machine from real outcomes.

KNOWN INTERACTION, DELIBERATELY NOT SILENTLY RESOLVED — FLAGGED TO THE USER:
stitch_runner.py already has an unrelated, pre-existing "stuck" mechanism
(STUCK_THRESHOLD=2 consecutive failures of the same COARSE classify_error()
err_type -> inject _REWRITE_PROMPT), active in baseline/raw_adv/sem_adv
today. This runner reuses that mechanism completely unmodified, and it can
fire in sem_escalate/sem_escalate_restart too, using the same coarse
counter, independent of the new fine-signature streak in EscalationState.
Precedence when both would fire on the same iteration: the pre-existing
STUCK_THRESHOLD check runs first (exactly where it already sits in the
loop); the new restart-injection check is skipped for that iteration if
STUCK_THRESHOLD already fired (see the two-branch precedence block inside
run_one_replicate() below). This avoids ever sending two blank-slate
rewrites stacked on one iteration, but
it does mean sem_escalate_restart's OWN restart trigger can be preempted
by the older, coarser mechanism before it ever gets to fire — expected to
happen more on models/modules with noisy err_type but low error_signature
resolution. Both counters are logged every iteration (see IterationRecord)
specifically so this interaction is visible in the data, not hidden by it.

RESULT LAYOUT
  <results_dir>/<safe_model>/<condition>/<module>/replicate_<r>/iter_<i>/
    feedback.txt, llm_response.txt, <module>.v, sim_log.txt   (same as
    stitch_runner.py's per-iteration files, for auditability)
  <results_dir>/<safe_model>/<condition>/<module>/replicate_<r>/run_log.json
    {"iterations": [ <IterationRecord as dict>, ... ], "summary": {...}}
    — the raw JSON array of NAMED objects Task 2 requires. No positional
    tuples anywhere in this file.

Requires: WSL (Verilator/Yosys/Icarus, via stitch_runner.py's subprocess
calls) and Ollama serving the target model. Validated end-to-end against
both by phase1/smoke_test.py before Task 3 ran on it.
"""
import json
import os
import re
import shutil
import sys
import time
from dataclasses import asdict, dataclass
from typing import Optional

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "src", "runner"))
from stitch_runner import (  # noqa: E402  — every one of these reused unmodified
    SYSTEM_PROMPT, call_llm, sanitize_ascii,
    run_verilator_lint, run_yosys_check, run_iverilog_sim,
    classify_error, _build_baseline_feedback, _build_sem_adv_feedback,
    _REWRITE_PROMPT, STUCK_THRESHOLD,
    interpret_verilator, interpret_yosys_latches, interpret_comb_loop,
)

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from error_signature import error_signature  # noqa: E402
from escalation_state import EscalationConfig, EscalationState  # noqa: E402


@dataclass
class IterationRecord:
    """Task 2 schema, verbatim field names, one object per iteration.
    Positional tuples are banned -- this IS the enforcement of that."""
    module: str
    model: str
    condition: str
    run_replicate: int
    iteration: int
    escalation_state: str          # "baseline" | "escalated" -- state DURING this iteration's tool run
    error_signature: Optional[str] # None on a PASS iteration
    raw_error: Optional[str]       # unnormalized iverilog feedback; None on PASS
    tool_invocations: dict         # {"iverilog": 1, "vvp": 0/1, "verilator": 0/1, "yosys": 0/1, "count": int}
    interpreter_invoked: bool
    restart_injected: bool
    tokens_used: int
    result: str                    # "pass" | "fail"
    # extra fields kept alongside the required schema, not replacing it:
    err_type: Optional[str] = None
    prompt_tokens: int = 0
    completion_tokens: int = 0
    escalated_now: bool = False    # True iff THIS iteration's failure triggered the escalation transition
    streak_len: int = 0


def _extract_code(llm_out: str) -> str:
    """Mirrors stitch_runner.py's run_one_condition() extraction exactly,
    including its 2026-08-21 fix: a response with an unclosed ```verilog
    fence falls through the regex match and used to carry the opening
    marker itself into the "code", which iverilog's preprocessor then
    misreads as a macro reference. Duplicated here rather than imported
    because stitch_runner's version is inline in run_one_condition(), not
    a standalone function -- keep both in sync if either changes."""
    match = re.search(r"```(?:verilog)?(.*?)```", llm_out, re.DOTALL)
    if match:
        code = match.group(1).strip()
    else:
        code = re.sub(r"^```(?:verilog)?\s*\n?", "", llm_out.strip())
    return sanitize_ascii(code)


def run_one_replicate(
    spec: str,
    module_name: str,
    model: str,
    condition: str,          # "sem_escalate" | "sem_escalate_restart"
    run_replicate: int,
    config: EscalationConfig,
    testbench_dir: str,
    results_dir: str,
    dependencies=None,
) -> dict:
    if condition not in ("sem_escalate", "sem_escalate_restart"):
        raise ValueError(f"escalation_runner only implements sem_escalate/sem_escalate_restart, got {condition!r}")
    assert config.allow_restart == (condition == "sem_escalate_restart"), (
        "EscalationConfig.allow_restart must match the condition being run "
        "(False for sem_escalate, True for sem_escalate_restart) -- caller bug, not a data problem"
    )

    dependencies = dependencies or []
    tb_path = os.path.join(testbench_dir, f"{module_name}_tb.v")
    if not os.path.exists(tb_path):
        raise FileNotFoundError(f"testbench not found: {tb_path}")

    safe_model = model.replace(":", "_").replace(".", "")
    run_dir = os.path.join(results_dir, safe_model, condition, module_name, f"replicate_{run_replicate}")
    os.makedirs(run_dir, exist_ok=True)

    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": spec},
    ]

    escalation = EscalationState(config)
    iteration_log = []
    total_tokens = 0
    t_start = time.time()

    # Coarse STUCK_THRESHOLD mechanism, reused unmodified from stitch_runner.py
    # -- see the module docstring's "KNOWN INTERACTION" note.
    stuck_consecutive = 0
    stuck_last_err = None

    passed = False
    iterations_to_pass = None

    for i in range(config.max_iterations):
        iter_num = i + 1
        iter_dir = os.path.join(run_dir, f"iter_{iter_num}")
        os.makedirs(iter_dir, exist_ok=True)

        with open(os.path.join(iter_dir, "feedback.txt"), "w", encoding="utf-8") as f:
            f.write(messages[-1]["content"])

        # Tool usage for THIS iteration was decided by the state as of the
        # END of the previous iteration -- escalation.state right now.
        use_tools_this_iter = escalation.state == "escalated"

        llm_out, pt, ct = call_llm(model, messages)
        total_tokens += pt + ct

        with open(os.path.join(iter_dir, "llm_response.txt"), "w", encoding="utf-8") as f:
            f.write(llm_out)

        code = _extract_code(llm_out)
        v_path = os.path.join(iter_dir, f"{module_name}.v")
        with open(v_path, "w", encoding="utf-8") as f:
            f.write(code)

        for dep in dependencies:
            if os.path.exists(dep):
                shutil.copy(dep, iter_dir)
        shutil.copy(tb_path, iter_dir)

        tool_invocations = {"iverilog": 1, "vvp": 0, "verilator": 0, "yosys": 0}
        interpreter_invoked = False
        verilator_out = "(baseline: skipped)"
        interp_text, interp_codes = "", []
        yosys_report, has_latch, latch_lines, cell_count, has_loop, loop_modules = (
            "(baseline: skipped)", False, [], 0, False, [],
        )

        if use_tools_this_iter:
            verilator_out, verilator_flag = run_verilator_lint(v_path)
            tool_invocations["verilator"] = 1
            if verilator_flag:
                interp_text, interp_codes = interpret_verilator(verilator_out, v_path)
                if interp_text:
                    interpreter_invoked = True

        success, iverilog_fb = run_iverilog_sim(iter_dir, module_name)
        tool_invocations["vvp"] = 1 if "COMPILATION ERROR" not in iverilog_fb else 0

        if use_tools_this_iter and "COMPILATION ERROR" not in iverilog_fb:
            yosys_report, has_latch, latch_lines, cell_count, has_loop, loop_modules = \
                run_yosys_check(v_path, module_name)
            tool_invocations["yosys"] = 1
            if has_latch or has_loop:
                interpreter_invoked = True

        tool_invocations["count"] = sum(
            v for k, v in tool_invocations.items() if k != "count"
        )

        if success:
            iteration_log.append(IterationRecord(
                module=module_name, model=model, condition=condition,
                run_replicate=run_replicate, iteration=iter_num,
                # Same reasoning as the FAIL branch below: describe what
                # tooling actually ran this iteration, not escalation.state
                # (harmless here since observe_pass() hasn't run yet, but
                # kept consistent so this can't silently break if the code
                # around it moves).
                escalation_state="escalated" if use_tools_this_iter else "baseline",
                error_signature=None, raw_error=None,
                tool_invocations=tool_invocations,
                interpreter_invoked=interpreter_invoked,
                restart_injected=False,
                tokens_used=pt + ct, prompt_tokens=pt, completion_tokens=ct,
                result="pass", err_type="PASS",
            ))
            escalation.observe_pass()
            passed = True
            iterations_to_pass = iter_num
            break

        err_type = classify_error(iverilog_fb)
        sig = error_signature("iverilog", iverilog_fb, err_type, window=config.signature_window)
        event = escalation.observe_failure(sig, iteration=iter_num)

        restart_injected = False

        # 1) pre-existing STUCK_THRESHOLD mechanism, unmodified precedence
        if err_type == stuck_last_err:
            stuck_consecutive += 1
        else:
            stuck_consecutive = 1
            stuck_last_err = err_type

        if stuck_consecutive >= STUCK_THRESHOLD:
            messages.append({"role": "assistant", "content": llm_out})
            messages.append({"role": "user", "content": _REWRITE_PROMPT.format(
                n=stuck_consecutive, err_type=err_type, spec=spec)})
            stuck_consecutive = 0
        # 2) new restart trigger (sem_escalate_restart only), skipped if (1) already fired this iteration
        elif condition == "sem_escalate_restart" and event.restart_now:
            restart_injected = True
            messages.append({"role": "assistant", "content": llm_out})
            messages.append({"role": "user", "content": _REWRITE_PROMPT.format(
                n=event.streak_len, err_type=err_type, spec=spec)})
        else:
            if use_tools_this_iter:
                fb = _build_sem_adv_feedback(
                    verilator_out, yosys_report, latch_lines, iverilog_fb, err_type,
                    has_latch, cell_count, interp_text, interp_codes,
                    has_loop, loop_modules, v_path,
                )
            else:
                fb = _build_baseline_feedback(iverilog_fb, err_type)
            messages.append({"role": "assistant", "content": llm_out})
            messages.append({"role": "user", "content": fb})

        iteration_log.append(IterationRecord(
            module=module_name, model=model, condition=condition,
            run_replicate=run_replicate, iteration=iter_num,
            # Deliberately NOT escalation.state here: observe_failure() just
            # above may have already mutated it to "escalated" (when
            # event.escalated_now is True), but that transition takes effect
            # starting NEXT iteration — this field must describe what
            # tooling actually ran THIS iteration, which is exactly
            # use_tools_this_iter, decided before this iteration's LLM call.
            # (The previous version of this line read escalation.state and
            # was the actual bug caught by smoke_test.py: it logged
            # "escalated" for the very iteration whose tools were still
            # baseline-only.)
            escalation_state="escalated" if use_tools_this_iter else "baseline",
            error_signature=sig, raw_error=iverilog_fb,
            tool_invocations=tool_invocations,
            interpreter_invoked=interpreter_invoked,
            restart_injected=restart_injected,
            tokens_used=pt + ct, prompt_tokens=pt, completion_tokens=ct,
            result="fail", err_type=err_type,
            escalated_now=event.escalated_now, streak_len=event.streak_len,
        ))

    total_time = round(time.time() - t_start, 2)

    # escalation.restart_iterations is the state machine's view: "the
    # escalated-phase streak reached restart_after" -- computed with zero
    # knowledge of the pre-existing STUCK_THRESHOLD mechanism, which can
    # preempt actual injection on the same iteration (see the module
    # docstring's "KNOWN INTERACTION" note; caught concretely by
    # tests/test_escalation_runner_restart.py, where a deterministically
    # stuck model has both counters fire in lockstep and STUCK_THRESHOLD's
    # branch wins on some of those iterations). The two are reported
    # separately, and their difference explicitly, rather than collapsing
    # them into one number that would hide the interaction.
    threshold_reached = list(escalation.restart_iterations)
    actually_injected = [r.iteration for r in iteration_log if r.restart_injected]
    preempted = [i for i in threshold_reached if i not in actually_injected]

    summary = {
        "module": module_name, "model": model, "condition": condition,
        "run_replicate": run_replicate,
        "pass": passed, "iterations_to_pass": iterations_to_pass,
        "total_iterations": len(iteration_log),
        "escalation_iteration": escalation.escalation_iteration,
        "fired_escalate": escalation.escalation_iteration is not None,
        "restart_iterations": actually_injected,           # what was ACTUALLY sent to the model
        "fired_restart": len(actually_injected) > 0,
        "restart_threshold_reached_iterations": threshold_reached,  # what the fine-signature streak alone would trigger
        "restart_preempted_by_stuck_threshold": preempted,          # divergence between the two, made explicit
        "total_tokens": total_tokens,
        "total_time_sec": total_time,
        "config": asdict(config),
    }

    run_log = {"iterations": [asdict(r) for r in iteration_log], "summary": summary}
    with open(os.path.join(run_dir, "run_log.json"), "w", encoding="utf-8") as f:
        json.dump(run_log, f, indent=2)

    return run_log
