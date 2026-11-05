#!/usr/bin/env python3
"""Generation for one model: one-shot, then the two feedback arms, 5 paired repetitions, all 7 modules.

  oneshot  one LLM call per module and rep, no feedback. System prompt phase3/runner/system_prompt.txt; user prompt =
           tasks/<m>/spec.md + the closed study's closing instruction (prompts/<m>.txt, the same for every rep)
  simloop  Phase 3 runner condition `baseline`: simulation feedback only, stops at the first testbench pass
  stitch   Phase 3 runner condition `sem_esc_restart_v3`: stops at the first testbench pass that is also struct_clean
Both arms of rep r start from the one-shot output of rep r. Budget 6 LLM calls per arm run, T = 0.1, num_ctx 32768.
Ollama gets only temperature and num_ctx (and num_thread, p3_bridge.py); it has no seed, so reps may coincide.
Parents are generated alone and tested with the golden children (tasks/<m>/lib). The runner is imported unmodified.

Output folder (WORK): $GEN_WORK, else results/<model>/ (one folder per model, so two models can run at once):
  prompts/<m>.txt                              user prompt of the one-shot call
  oneshot/rep<r>/<m>/{response.txt,record.json}
  arms/rep<r>/tasks/<m>/                       copy of tasks/<m> with input.v = the one-shot output of rep r
  arms/rep<r>/results/<model>/<condition>/<m>/rep1/   the runner's run folder (iter*/, metrics.json)
  outputs/{oneshot,simloop,stitch}/rep<r>/<m>.v       final file of every module, arm and rep
Resumable: finished one-shot calls (record status ok, output hash unchanged) and arm runs (metrics.json) are
skipped; infra errors and half-written runs are retried. Exit 2 if anything is unfinished (resubmit), 3 if the
first-call check fails (p3_bridge.py).

Usage: python3 pipeline/generate.py --model qwen2.5-coder:32b --host http://127.0.0.1:11500
       python3 pipeline/generate.py --backend mock --model mock --reps 2 --mock-plan flit_mux=latch ...
"""
import argparse
import datetime as dt
import glob
import hashlib
import json
import os
import re
import shutil
import sys
import time
import urllib.request

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import p3_bridge as B  # noqa: E402

R = B.runner()                       # stitch_runner_p3, unmodified (Ollama client, extract_code, Mock, main)
STUDY = B.STUDY
TASKS = os.path.join(STUDY, "tasks")
MODULES = ["fifo", "route_compute", "rr_arbiter", "flit_mux", "input_port", "output_port", "router_5port"]
ARMS = {"baseline": "simloop", "sem_esc_restart_v3": "stitch"}
SYSTEM_PROMPT_FILE = os.path.join(B.REPO, "phase3", "runner", "system_prompt.txt")
# The closed study's closing instruction, unchanged.
CLOSING = ("Write the complete Verilog-2001 module `{m}` that meets this specification, with exactly the port list "
           "above.{children}\nReturn only Verilog: one ```verilog code block, no explanation.")
CHILDREN_NOTE = (" The child modules listed under Children already exist and are compiled together with your file: "
                 "instantiate them as specified and do not define them yourself.")
# Mock one-shot (local test only): a flit_mux whose index register latches but that passes its testbench.
LATCHED_FLIT_MUX = """module flit_mux (input [3:0] sel, input [31:0] in0, input [31:0] in1, input [31:0] in2,
                 input [31:0] in3, output reg [31:0] out);
    reg [1:0] idx;
    always @(*) begin
        case (sel)
            4'b0001: idx = 2'd0;
            4'b0010: idx = 2'd1;
            4'b0100: idx = 2'd2;
            4'b1000: idx = 2'd3;
        endcase
        if (sel == 4'b0001 || sel == 4'b0010 || sel == 4'b0100 || sel == 4'b1000)
            out = (idx == 2'd0) ? in0 : (idx == 2'd1) ? in1 : (idx == 2'd2) ? in2 : in3;
        else
            out = 32'h6000_0000;
    end
endmodule
"""


def sha(text):
    return hashlib.sha256(text.replace("\r\n", "\n").encode()).hexdigest()


def safe(model):
    return re.sub(r"[^A-Za-z0-9_.-]", "_", model)


def write(path, text):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    tmp = path + ".tmp"
    open(tmp, "w", encoding="utf-8", newline="\n").write(text)
    os.replace(tmp, path)                            # a job killed mid-write never leaves a half file


def prompt_for(m):
    meta = json.load(open(os.path.join(TASKS, m, "meta.json")))
    spec = open(os.path.join(TASKS, m, "spec.md"), encoding="utf-8").read().rstrip() + "\n"
    return spec + "\n" + CLOSING.format(m=m, children=CHILDREN_NOTE if meta["children"] else "")


class MockGen:
    """golden: tasks/<m>/golden.v | broken: golden without its last 'endmodule' | latch: LATCHED_FLIT_MUX |
    timeout: raises like the runner client after its retries."""
    def __init__(self, plan):
        self.plan = plan

    def chat(self, system, user, module):
        mode = self.plan.get(module, "golden")
        if mode == "timeout":
            raise RuntimeError("ollama failed after retries: timed out")
        text = LATCHED_FLIT_MUX if mode == "latch" else open(os.path.join(TASKS, module, "golden.v")).read()
        if mode == "broken":
            text = text[:text.rfind("endmodule")]
        return "```verilog\n" + text + "\n```", len(user) // 4, len(text) // 4


def oneshot_done(work, r, m):
    try:
        rec = json.load(open(os.path.join(work, "oneshot", f"rep{r}", m, "record.json")))
        out = open(os.path.join(work, "outputs", "oneshot", f"rep{r}", f"{m}.v"), encoding="utf-8").read()
    except (OSError, ValueError):
        return False
    return rec.get("status") == "ok" and sha(out) == rec.get("output_sha256")


def oneshot(a, work, llm, digest, version, system):
    infra = []
    for r in range(1, a.reps + 1):
        for m in a.modules:
            if oneshot_done(work, r, m):
                print(f"skip oneshot rep{r} {m} (done)", flush=True)
                continue
            prompt = prompt_for(m)
            write(os.path.join(work, "prompts", f"{m}.txt"), prompt)
            rd, out = os.path.join(work, "oneshot", f"rep{r}", m), os.path.join(work, "outputs", "oneshot", f"rep{r}", f"{m}.v")
            os.makedirs(rd, exist_ok=True)
            base = {"module": m, "rep": r, "model": a.model, "backend": a.backend, "model_digest": digest,
                    "ollama_version": version, "temperature": a.temperature, "num_ctx": a.num_ctx,
                    "system_prompt_sha256_lf": sha(system), "prompt_sha256_lf": sha(prompt)}
            t0 = time.time()
            try:
                resp, tin, tout = llm.chat(system, prompt, m) if a.backend == "mock" else llm.chat(system, prompt)
            except (RuntimeError, OSError) as e:          # runner client after retries, timeout, connection error
                B.pop_chat_meta()
                if os.path.exists(out):
                    os.remove(out)                       # never score a stale file for a failed call
                write(os.path.join(rd, "record.json"), json.dumps({**base, "status": "infra_error", "error": repr(e),
                      "wall_s": round(time.time() - t0, 1), "timestamp": dt.datetime.now().isoformat(timespec="seconds")}, indent=1))
                infra.append(f"rep{r}/{m}")
                print(f"oneshot rep{r} {m:<14} INFRA_ERROR {e!r}; continuing", flush=True)
                continue
            meta = B.pop_chat_meta()
            code = R.extract_code(resp)
            write(os.path.join(rd, "response.txt"), resp)
            write(out, code)
            rec = {**base, "status": "ok", "tokens_in": tin, "tokens_out": tout, "done_reason": meta.get("done_reason"),
                   "thinking_chars": meta.get("thinking_chars"), "llm_meta": meta, "wall_s": round(time.time() - t0, 1),
                   "timestamp": dt.datetime.now().isoformat(timespec="seconds"),
                   "response_sha256": hashlib.sha256(resp.encode()).hexdigest(), "output_sha256": sha(code),
                   "mock_mode": llm.plan.get(m, "golden") if a.backend == "mock" else None}
            write(os.path.join(rd, "record.json"), json.dumps(rec, indent=1))
            print(f"oneshot rep{r} {m:<14} tokens in/out {tin}/{tout} thinking {rec['thinking_chars']} chars "
                  f"done_reason {rec['done_reason']} {rec['wall_s']}s", flush=True)
    return infra


def arms(a, work, r):
    """Both arms for rep r through the runner. Returns the unfinished runs."""
    base = os.path.join(work, "arms", f"rep{r}")
    mods = [m for m in a.modules if oneshot_done(work, r, m)]
    missing = [f"rep{r}/{m}: no finished one-shot output" for m in a.modules if m not in mods]
    for m in mods:
        src, dst = os.path.join(TASKS, m), os.path.join(base, "tasks", m)
        oneshot_v = os.path.join(work, "outputs", "oneshot", f"rep{r}", f"{m}.v")
        if os.path.isdir(dst):
            if sha(open(os.path.join(dst, "input.v")).read()) != sha(open(oneshot_v).read()):
                raise SystemExit(f"{dst}/input.v differs from {oneshot_v}: use a new GEN_WORK for a new generation")
            continue
        shutil.copytree(src, dst)
        shutil.copyfile(oneshot_v, os.path.join(dst, "input.v"))
    stamp = time.strftime("%Y%m%d_%H%M%S")
    todo = []
    for cond in ARMS:
        for m in mods:
            rd = os.path.join(base, "results", safe(a.model), cond, m, "rep1")
            if os.path.isdir(rd) and not os.path.exists(os.path.join(rd, "metrics.json")):
                os.replace(rd, f"{rd}.failed_{stamp}")       # no stale iterations from a killed job
                print(f"retry rep{r} {cond} {m} (earlier attempt kept as rep1.failed_{stamp})", flush=True)
            if not os.path.exists(os.path.join(rd, "metrics.json")):
                todo.append(m)
    if todo:
        R.TASKS_DIR = os.path.join(base, "tasks")
        sys.argv = ["stitch_runner_p3.py", "--model", a.model, "--backend", a.backend, "--mock-mode", a.mock_mode,
                    "--host", a.host, "--conditions", *ARMS, "--tasks", *dict.fromkeys(todo), "--reps", "1",
                    "--temperature", str(a.temperature), "--max-iters", str(a.max_iters), "--num-ctx", str(a.num_ctx),
                    "--timeout", str(B.CLIENT_TIMEOUT_S), "--system-prompt-file", SYSTEM_PROMPT_FILE,
                    "--out", os.path.join(base, "results")]
        print(f"== arms rep{r}: runner " + " ".join(sys.argv[1:]), flush=True)
        R.main()
    for cond, arm in ARMS.items():
        for m in mods:
            rd = os.path.join(base, "results", safe(a.model), cond, m, "rep1")
            mp = os.path.join(rd, "metrics.json")
            if os.path.exists(mp):
                final = json.load(open(mp))["final_candidate"]
                write(os.path.join(work, "outputs", arm, f"rep{r}", f"{m}.v"), open(final, encoding="utf-8").read())
            else:
                err = os.path.join(rd, "error.json")
                missing.append(f"rep{r}/{arm}/{m}: " + (json.load(open(err)).get("error", "") if os.path.exists(err)
                                                         else "no metrics.json, no error.json"))
    return missing


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--model", required=True)
    ap.add_argument("--backend", choices=["ollama", "mock"], default="ollama")
    ap.add_argument("--mock-plan", nargs="*", default=[], help="module=golden|broken|latch|timeout (mock one-shot)")
    ap.add_argument("--mock-mode", choices=["golden", "echo", "fix_on_2"], default="fix_on_2", help="mock arms")
    ap.add_argument("--host", default="http://" + os.environ.get("OLLAMA_HOST", "127.0.0.1:11434"))
    ap.add_argument("--modules", nargs="*", default=MODULES, choices=MODULES)
    ap.add_argument("--reps", type=int, default=5)
    ap.add_argument("--temperature", type=float, default=0.1)
    ap.add_argument("--num-ctx", type=int, default=32768)
    ap.add_argument("--max-iters", type=int, default=6)
    a = ap.parse_args()
    work = os.path.abspath(os.environ.get("GEN_WORK") or os.path.join(STUDY, "results", safe(a.model)))
    os.makedirs(work, exist_ok=True)
    print(f"== {dt.datetime.now():%F %T} generate: model {a.model}, backend {a.backend}, reps {a.reps}, "
          f"modules {' '.join(a.modules)}, work {work}", flush=True)
    system = open(SYSTEM_PROMPT_FILE, encoding="utf-8").read()
    if a.backend == "mock":
        llm, digest, version = MockGen(dict(p.split("=", 1) for p in a.mock_plan)), "mock", "mock"
    else:
        llm = R.Ollama(a.model, a.host, a.temperature, a.num_ctx, B.CLIENT_TIMEOUT_S)
        digest = R.model_digest(llm, a.model)
        with urllib.request.urlopen(a.host.rstrip("/") + "/api/version", timeout=30) as resp:
            version = json.loads(resp.read()).get("version", "?")
    print(f"== {dt.datetime.now():%F %T} one-shot: {len(a.modules)} modules x {a.reps} reps", flush=True)
    unfinished = oneshot(a, work, llm, digest, version, system)
    for r in range(1, a.reps + 1):                   # rep-major: a job cut short still leaves whole reps
        print(f"== {dt.datetime.now():%F %T} arms rep{r}", flush=True)
        unfinished += arms(a, work, r)
    n = {arm: len(glob.glob(os.path.join(work, "outputs", arm, "rep*", "*.v"))) for arm in ("oneshot", *ARMS.values())}
    print(f"== {dt.datetime.now():%F %T} outputs: " + ", ".join(f"{k} {v}" for k, v in n.items()) +
          f" (expected {len(a.modules) * a.reps} each)", flush=True)
    if unfinished:
        print(f"GENERATION NOT FINISHED ({len(unfinished)}): resubmit to retry", flush=True)
        for u in unfinished:
            print("  " + u, flush=True)
        return 2
    print("GENERATION DONE", flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
