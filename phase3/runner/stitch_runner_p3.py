#!/usr/bin/env python3
"""
stitch_runner_p3.py -- Phase 3 runner: repair of real MPSoC leaves (Track R) + seeded RISC-V/NoC tasks (Track S).

Conditions (all share ONE iteration budget, --max-iters, restarts included -> removes the Set 3
Pass@8-vs-Pass@6 confound):
  baseline             AutoChip: simulation feedback only; stops at func_pass (clean_pass scored post hoc)
  raw_adv              sim + raw Verilator/Yosys text; stops at clean_pass
  sem_adv_v2           sim + PRODUCTION interpreter (stitch_interpreter.py, unmodified) + raw; stops at clean_pass
  sem_adv_v3           sim + v3 layer (stitch_interpreter_v3.py) + raw; stops at clean_pass
  sem_esc_restart_v3   starts as baseline behind a clean-pass gate (generic "fails synthesis sign-off" message,
                       no tool detail); escalates to v3 after 2 consecutive identical signatures; blank-slate
                       restart if still stuck 2 iterations after escalating.
Every candidate is ALWAYS fully evaluated (sim + lint + synth) for SCORING; conditions differ only in what is FED BACK.

Usage (HPC):  python phase3/runner/stitch_runner_p3.py --model llama3.1:8b --reps 3 --out results/phase3
Smoke test:   python phase3/runner/stitch_runner_p3.py --backend mock --mock-mode fix_on_2 --reps 1 --out /tmp/p3smoke
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import os
import re
import sys
import time
import urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
PHASE3_ROOT = os.path.dirname(HERE)                      # <repo>/phase3  (or /scratch/.../Phase3_HPC/phase3)
REPO_ROOT = os.path.dirname(PHASE3_ROOT)
INTERP_DIR = (os.environ.get("STITCH_INTERPRETER_DIR") or os.environ.get("STITCH_INTERP_DIR")
              or os.path.join(REPO_ROOT, "src", "interpreter"))
sys.path.insert(0, HERE)
sys.path.insert(0, INTERP_DIR)
from p3_eval import evaluate                   # noqa: E402
import stitch_interpreter_v3 as IV3            # noqa: E402  (imports production stitch_interpreter unmodified)

CONDITIONS = ["baseline", "raw_adv", "sem_adv_v2", "sem_adv_v3", "sem_esc_restart_v3"]
TASKS_DIR = os.path.join(PHASE3_ROOT, "tasks")

DEFAULT_SYSTEM_PROMPT = """You are an expert digital hardware engineer writing synthesizable Verilog-2001.
Rules:
1. Signals assigned inside an always block are declared reg; signals driven by assign are wire.
2. Combinational always blocks use always @(*) and blocking '='. Clocked blocks use always @(posedge clk) and '<='.
3. Every output of a combinational block is assigned on every path (defaults at the top, a default: case item).
4. Each signal has exactly one driver.
5. Widths on both sides of every assignment and port connection match exactly.
6. Output only the complete module inside a single ```verilog code block."""


# --------------------------------------------------------------------------- LLM backends
class Ollama:
    def __init__(self, model, host, temperature, num_ctx, timeout):
        self.model, self.host, self.t, self.ctx, self.timeout = model, host.rstrip("/"), temperature, num_ctx, timeout

    def chat(self, system, user):
        body = json.dumps({"model": self.model, "stream": False,
                           "messages": [{"role": "system", "content": system}, {"role": "user", "content": user}],
                           "options": {"temperature": self.t, "num_ctx": self.ctx}}).encode()
        last = None
        for attempt in range(3):
            try:
                req = urllib.request.Request(self.host + "/api/chat", data=body,
                                             headers={"Content-Type": "application/json"})
                with urllib.request.urlopen(req, timeout=self.timeout) as r:
                    j = json.loads(r.read())
                return j["message"]["content"], j.get("prompt_eval_count", 0), j.get("eval_count", 0)
            except Exception as e:                     # transient Ollama timeouts: retry, then surface
                last = e
                time.sleep(5 * (attempt + 1))
        raise RuntimeError(f"ollama failed after retries: {last}")


class Mock:
    """golden: always returns golden.v | echo: returns the input unchanged | fix_on_2: input first, golden after."""
    def __init__(self, mode):
        self.mode, self.calls = mode, {}

    def bind(self, task_dir):
        self.task_dir, self.n = task_dir, 0

    def chat(self, system, user):
        self.n += 1
        f = "golden.v" if (self.mode == "golden" or (self.mode == "fix_on_2" and self.n >= 2)) else "input.v"
        return "```verilog\n" + open(os.path.join(self.task_dir, f)).read() + "\n```", len(user) // 4, 200


# --------------------------------------------------------------------------- helpers
def extract_code(text: str) -> str:
    text = re.sub(r"<think>.*?</think>", "", text, flags=re.S)
    text = text.encode("ascii", "ignore").decode()
    m = re.search(r"```(?:verilog|systemverilog|v|sv)?\s*\n(.*?)```", text, re.S)
    if m:
        code = m.group(1)
    else:
        m = re.search(r"```(?:verilog|systemverilog|v|sv)?\s*\n(.*)", text, re.S)   # unclosed fence (Defect B)
        code = m.group(1) if m else text
    s, e = code.find("module"), code.rfind("endmodule")
    if s >= 0 and e > s:
        code = code[s:e + len("endmodule")]
    return code.strip() + "\n"


def strip_paths(t: str, *dirs) -> str:
    for d in dirs:
        if d:
            t = t.replace(os.path.abspath(d) + os.sep, "").replace(os.path.abspath(d), ".")
    return t


def sim_feedback(ev) -> str:
    log = ev["_logs"]["sim"]
    if not ev["compile_ok"]:
        return "COMPILATION FAILED:\n" + "\n".join(log.splitlines()[:25])
    if ev["sim_outcome"] == "PASS":
        return "SIMULATION PASSED."
    fails = [l for l in log.splitlines() if "FAIL" in l][:15]
    return f"SIMULATION {ev['sim_outcome']}:\n" + "\n".join(fails)


def raw_tool_text(ev, max_lines=40) -> str:
    v = [l for l in ev["_logs"]["verilator"].splitlines() if l.startswith("%") and "Exiting due to" not in l]
    y = []
    lines = ev["_logs"]["yosys"].splitlines()
    for i, l in enumerate(lines):
        if ("Latch inferred for signal" in l and not l.strip().startswith("No")) or l.startswith("ERROR") or \
                (l.startswith("Warning:") and "Replacing memory" not in l):
            y.append(l)
            if "logic loop" in l:
                y += [x for x in lines[i + 1:i + 12] if x.startswith("    ")]
    out = []
    if v:
        out.append("VERILATOR LINT OUTPUT:\n" + "\n".join(v[:max_lines]))
    if y:
        out.append("YOSYS SYNTHESIS OUTPUT:\n" + "\n".join(dict.fromkeys(y[:max_lines])))
    return "\n\n".join(out)


def signature(ev, interp=None) -> str:
    s = "COMPILE" if not ev["compile_ok"] else ("SIMFAIL" if not ev["func_pass"] else "SIMOK")
    return s + "|" + (interp["signature"] if interp else "")


def user_prompt(spec, code, feedback=None, first=False) -> str:
    head = "Repair the following Verilog-2001 module so that it meets the specification and is synthesizable."
    p = f"{head}\n\nSPECIFICATION:\n{spec}\n\nCURRENT RTL{' (may contain functional and/or synthesis defects)' if first else ''}:\n```verilog\n{code}```\n"
    if feedback:
        p += f"\nFEEDBACK FROM THE LAST ATTEMPT:\n{feedback}\n"
    p += "\nReturn the COMPLETE corrected module in one ```verilog block. Keep the module name and port names as specified."
    return p


# --------------------------------------------------------------------------- one run
def run_one(llm, model, cond, task, rep, args, run_dir, gate_cache):
    tdir = os.path.join(TASKS_DIR, task)
    meta = json.load(open(os.path.join(tdir, "meta.json")))
    top, spec = meta["top"], open(os.path.join(tdir, "spec.md")).read()
    code0 = open(os.path.join(tdir, "input.v")).read()
    if task not in gate_cache:
        g = evaluate(os.path.join(tdir, "input.v"), tdir, top)
        gate_cache[task] = {k: g[k] for k in ("latch_events", "latch_cells", "func_pass", "clean_pass",
                                              "verilator_warnings_count", "yosys_ok")}
    before = gate_cache[task]
    if isinstance(llm, Mock):
        llm.bind(tdir)
    code, feedback = code0, None
    escalated_at, restarted, stuck, last_sig, restart_armed = None, False, 0, None, False
    iters, sem_iters, classes_union, tok_in, tok_out, fb_tool_iters = [], [], set(), 0, 0, 0
    stop_reason, ev, t0 = "budget", None, time.time()
    for it in range(1, args.max_iters + 1):
        idir = os.path.join(run_dir, f"iter{it}")
        os.makedirs(idir, exist_ok=True)
        prompt = user_prompt(spec, code, feedback, first=(feedback is None))
        open(os.path.join(idir, "prompt.txt"), "w").write(prompt)
        resp, ti, to = llm.chat(args.system_prompt, prompt)
        tok_in += ti or 0; tok_out += to or 0
        open(os.path.join(idir, "response.txt"), "w").write(resp)
        cand = extract_code(resp)
        cpath = os.path.join(idir, "dut.v")
        open(cpath, "w").write(cand)
        ev = evaluate(cpath, tdir, top, workdir=idir, keep=True)
        for k, v in ev["_logs"].items():
            open(os.path.join(idir, f"{k}.log"), "w").write(v)
        code = cand
        rec = {"iter": it, **{k: v for k, v in ev.items() if k != "_logs"}}
        # ---- stopping rule
        if cond == "baseline" and ev["func_pass"]:
            iters.append(rec); stop_reason = "func_pass"; break
        if cond != "baseline" and ev["clean_pass"]:
            iters.append(rec); stop_reason = "clean_pass"; break
        # ---- feedback construction (what differs between conditions)
        fb = [sim_feedback(ev)]
        interp = None
        if cond in ("raw_adv", "sem_adv_v2", "sem_adv_v3") or (cond == "sem_esc_restart_v3" and escalated_at):
            fb_tool_iters += 1
            if cond == "raw_adv":
                fb.append(raw_tool_text(ev))
            else:
                ver = "v2" if cond == "sem_adv_v2" else "v3"
                interp = IV3.interpret(ev["_logs"]["verilator"], ev["_logs"]["yosys"], cpath, version=ver, top=top,
                                       **({"max_directives": args.max_directives} if ver == "v3" else {}))
                if interp["fired"]:
                    fb.append("SEMANTIC ANALYSIS (fix these):\n" + interp["text"])
                    sem_iters.append(it); classes_union |= set(interp["classes_fired"])
                if args.sem_include_raw or not interp["fired"]:
                    fb.append(raw_tool_text(ev))
        elif cond in ("baseline", "sem_esc_restart_v3") and ev["func_pass"] and not ev["struct_clean"]:
            fb.append("The design simulates correctly but FAILS SYNTHESIS SIGN-OFF. Re-check it for synthesis problems.")
        if cond == "sem_esc_restart_v3":
            sig_interp = interp or IV3.interpret(ev["_logs"]["verilator"], ev["_logs"]["yosys"], cpath, top=top)
            sig = signature(ev, sig_interp)
            stuck = stuck + 1 if sig == last_sig else 1
            last_sig = sig
            rec["signature"] = sig
            if not escalated_at and stuck >= 2:
                escalated_at, stuck = it, 0
                it_interp = IV3.interpret(ev["_logs"]["verilator"], ev["_logs"]["yosys"], cpath, top=top,
                                          max_directives=args.max_directives)
                fb = [sim_feedback(ev)]
                if it_interp["fired"]:
                    fb.append("SEMANTIC ANALYSIS (fix these):\n" + it_interp["text"])
                    sem_iters.append(it); classes_union |= set(it_interp["classes_fired"])
                if args.sem_include_raw or not it_interp["fired"]:
                    fb.append(raw_tool_text(ev))
                fb_tool_iters += 1
            elif escalated_at and not restarted and stuck >= 2:
                restarted, stuck, last_sig = True, 0, None
                rec["restart"] = True
                code, feedback = code0, None               # blank slate, still escalated
                iters.append(rec)
                continue
        rec["semantic_fired"] = bool(interp and interp["fired"]) or (it in sem_iters)
        rec["classes_fired"] = sorted(interp["classes_fired"]) if interp else []
        iters.append(rec)
        feedback = strip_paths("\n\n".join(x for x in fb if x), idir, tdir)
    final = iters[-1]
    m = {
        "model": model, "condition": cond, "task": task, "track": meta["track"], "rep": rep,
        "timestamp": dt.datetime.now().isoformat(timespec="seconds"),
        "interp_v3_version": IV3.V3_VERSION, "base_interp_sha256_lf": IV3.base_fingerprint(),
        "temperature": args.temperature, "max_iters": args.max_iters, "sem_include_raw": args.sem_include_raw,
        "iterations": len(iters), "stop_reason": stop_reason,
        "latch_count_before": before["latch_events"], "latch_cells_before": before["latch_cells"],
        "input_func_pass": before["func_pass"], "input_yosys_ok": before["yosys_ok"],
        "latch_count_after": final["latch_events"], "latch_cells_after": final["latch_cells"],
        "semantic_fired": bool(sem_iters), "semantic_fired_iters": sem_iters, "classes_fired": sorted(classes_union),
        "verilator_warnings_count": final["verilator_warnings_count"], "verilator_codes_final": final["verilator_codes"],
        "func_pass": final["func_pass"], "clean_pass": final["clean_pass"],
        "silent_structural_pass": final["silent_structural_pass"], "final_yosys_ok": final["yosys_ok"],
        "final_compile_ok": final["compile_ok"], "final_candidate": os.path.join(run_dir, f"iter{final['iter']}", "dut.v"),
        "tokens_in": tok_in, "tokens_out": tok_out, "wall_s": round(time.time() - t0, 1),
        "tool_feedback_iters": fb_tool_iters, "escalated_at": escalated_at, "restarted": restarted,
        "top_level_synthesis_pass": None,        # filled by compose.py --from-results
        "per_iter": iters,
    }
    json.dump(m, open(os.path.join(run_dir, "metrics.json"), "w"), indent=1)
    return m


def _version(cmd):
    import subprocess
    try:
        p = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
        return ((p.stdout or "") + (p.stderr or "")).strip().splitlines()[0]
    except Exception as e:
        return f"MISSING ({e.__class__.__name__})"


def run_manifest(a, tasks):
    import p3_eval as E
    return {"host": os.uname().nodename if hasattr(os, "uname") else "?", "model": a.model, "backend": a.backend,
            "started": dt.datetime.now().isoformat(timespec="seconds"), "tasks": tasks, "conditions": a.conditions,
            "reps": a.reps, "temperature": a.temperature, "max_iters": a.max_iters, "max_directives": a.max_directives,
            "sem_include_raw": a.sem_include_raw, "system_prompt_file": a.system_prompt_file,
            "interpreter_dir": INTERP_DIR, "base_interp_sha256_lf": IV3.base_fingerprint(), "v3_version": IV3.V3_VERSION,
            "toolchain": {"yosys": _version([E.YOSYS, "-V"]), "verilator": _version([E.VERILATOR, "--version"]),
                          "iverilog": _version([E.IVERILOG, "-V"])}}


def append_master(out_dir, rec):
    """master_log.json (list) -- same monitoring one-liner as Sets 1-3. Atomic replace."""
    p = os.path.join(out_dir, "master_log.json")
    try:
        data = json.load(open(p)) if os.path.exists(p) else []
    except Exception:
        data = []
    data.append(rec)
    tmp = p + ".tmp"
    json.dump(data, open(tmp, "w"))
    os.replace(tmp, p)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--model", default="mock")
    ap.add_argument("--backend", choices=["ollama", "mock"], default="ollama")
    ap.add_argument("--mock-mode", choices=["golden", "echo", "fix_on_2"], default="fix_on_2")
    ap.add_argument("--host", default=os.environ.get("OLLAMA_HOST", "http://127.0.0.1:11434"))
    ap.add_argument("--conditions", nargs="*", default=CONDITIONS)
    ap.add_argument("--tasks", nargs="*", default=None)
    ap.add_argument("--reps", type=int, default=3)
    ap.add_argument("--temperature", type=float, default=0.1)
    ap.add_argument("--max-iters", type=int, default=6)
    ap.add_argument("--max-directives", type=int, default=3)
    ap.add_argument("--sem-include-raw", type=int, default=1,
                    help="1 = directives + raw tool text (matches production comment in interpret_verilator)")
    ap.add_argument("--num-ctx", type=int, default=8192)
    ap.add_argument("--timeout", type=int, default=900)
    ap.add_argument("--system-prompt-file", default=None, help="use the production SYSTEM_PROMPT for comparability")
    ap.add_argument("--out", default="results/phase3_run")
    ap.add_argument("--models", nargs="*", default=None,
                    help="--dry-run only: model list used to report the full-plan run count")
    ap.add_argument("--dry-run", action="store_true",
                    help="check tools/tasks/interpreter, print the plan and run count, run nothing")
    a = ap.parse_args()
    a.system_prompt = open(a.system_prompt_file).read() if a.system_prompt_file else DEFAULT_SYSTEM_PROMPT
    tasks = a.tasks or sorted(d for d in os.listdir(TASKS_DIR) if os.path.isdir(os.path.join(TASKS_DIR, d)))
    manifest = run_manifest(a, tasks)
    if a.dry_run:
        n_models = len(a.models) if a.models else 1
        per_model = len(tasks) * len(a.conditions) * a.reps
        print(json.dumps(manifest, indent=1))
        print(f"plan: {len(tasks)} tasks x {len(a.conditions)} conditions x {a.reps} reps = {per_model} runs/model; "
              f"x {n_models} model(s) = {per_model * n_models} runs")
        missing = [k for k, v in manifest["toolchain"].items() if v.startswith("MISSING")]
        sys.exit(2 if missing else 0)
    os.makedirs(a.out, exist_ok=True)
    json.dump(manifest, open(os.path.join(a.out, f"run_manifest_{re.sub(r'[^A-Za-z0-9_.-]', '_', a.model)}.json"), "w"), indent=1)
    llm = Mock(a.mock_mode) if a.backend == "mock" else Ollama(a.model, a.host, a.temperature, a.num_ctx, a.timeout)
    safe = re.sub(r"[^A-Za-z0-9_.-]", "_", a.model)
    gate_cache, n_done = {}, 0
    for rep in range(1, a.reps + 1):                   # rep-major order: partial jobs still give balanced N
        for task in tasks:
            for cond in a.conditions:
                rd = os.path.join(a.out, safe, cond, task, f"rep{rep}")
                if os.path.exists(os.path.join(rd, "metrics.json")):
                    continue                           # resume
                os.makedirs(rd, exist_ok=True)
                try:
                    m = run_one(llm, a.model, cond, task, rep, a, rd, gate_cache)
                    n_done += 1
                    append_master(a.out, {k: m[k] for k in ("model", "condition", "task", "rep", "iterations",
                                                            "func_pass", "clean_pass", "semantic_fired", "wall_s")})
                    print(f"[{safe}] rep{rep} {task:<16} {cond:<19} it={m['iterations']} func={m['func_pass']!s:<5} "
                          f"clean={m['clean_pass']!s:<5} sf={int(m['semantic_fired'])} {m['classes_fired']}", flush=True)
                except Exception as e:                 # record, never silently drop
                    json.dump({"model": a.model, "condition": cond, "task": task, "rep": rep, "error": repr(e)},
                              open(os.path.join(rd, "error.json"), "w"))
                    append_master(a.out, {"model": a.model, "condition": cond, "task": task, "rep": rep, "error": repr(e)})
                    print(f"[{safe}] ERROR {task} {cond} rep{rep}: {e}", flush=True)
    print(f"done: {n_done} new runs")


if __name__ == "__main__":
    main()
