#!/bin/bash
# Final-batch status check. READ-ONLY: never submits, cancels or writes anything; prints to stdout only.
# Run on the HPC login node from /scratch/soumyaj/Phase3_HPC:
#   bash phase3/hpc/check_final_batch.sh <G> <P> <A> <C> <D1> <D2>     (job IDs echoed at submission)
# One line per check: PASS / FAIL / WAITING, with a short reason.
if [ $# -ne 6 ]; then echo "usage: bash phase3/hpc/check_final_batch.sh <G> <P> <A> <C> <D1> <D2>"; exit 2; fi
PY=/scratch/soumyaj/oss-cad-suite/py3bin/python3; [ -x "$PY" ] || PY=python3
exec "$PY" - "$@" <<'PY'
import glob, hashlib, json, os, re, subprocess, sys, time

G, P, A, C, D1, D2 = sys.argv[1:7]
JOBS = {"G": G, "P": P, "A": A, "C": C, "D1": D1, "D2": D2}
RES = {"A": "results/phase3_gate_ctrl", "C": "results/phase3_32b"}
M6 = ["llama3.2:3b", "gemma3:4b", "deepseek-coder:6.7b", "qwen2.5-coder:7b", "llama3.1:latest", "qwen2.5-coder:14b"]
GATE = "The design simulates correctly but FAILS SYNTHESIS SIGN-OFF. Re-check it for synthesis problems."
FREEZE = "phase3/evidence/FREEZE_FINAL.md"


def say(n, status, msg):
    print(f"[{n}] {status:<7} {msg}")


def sh(cmd):
    try:
        return subprocess.run(cmd, capture_output=True, text=True, timeout=60).stdout
    except Exception:
        return ""


def sha(p):
    return hashlib.sha256(open(p, "rb").read().replace(b"\r\n", b"\n")).hexdigest()


def read(p):
    return open(p, encoding="utf-8", errors="ignore").read() if os.path.exists(p) else None


# ---- expected hashes from FREEZE_FINAL.md: "| `<sha>` | `<path>` ..." rows and the per-task tb.v column
fz = read(FREEZE) or ""
exp = {m.group(2): m.group(1) for m in re.finditer(r"^\| `([0-9a-f]{64})` \| `([^`]+)`", fz, re.M)}
for m in re.finditer(r"^\| (\w+) \| `[0-9a-f]{64}` \| `([0-9a-f]{64})` \|", fz, re.M):
    exp[f"phase3/tasks/{m.group(1)}/tb.v"] = m.group(2)
WANT = ["src/interpreter/stitch_interpreter.py", "src/interpreter/stitch_interpreter_v3.py", "src/interpreter/_v3_parsers.py",
        "phase3/runner/stitch_runner_p3.py", "phase3/runner/p3_eval.py", "phase3/runner/system_prompt.txt",
        "phase3/evidence/PREREG_FINAL.md"] + sorted(k for k in exp if k.endswith("/tb.v"))

# 1. DEPLOY
if not fz:
    say(1, "FAIL", f"DEPLOY: {FREEZE} not found (run from /scratch/soumyaj/Phase3_HPC)")
else:
    bad = [f for f in WANT if f not in exp or not os.path.exists(f) or sha(f) != exp[f]]
    tbs = sum(f.endswith("/tb.v") for f in WANT)
    say(1, "FAIL" if bad or tbs != 11 else "PASS",
        f"DEPLOY: {len(WANT) - len(bad)}/{len(WANT)} hashes match FREEZE_FINAL ({tbs} tb.v)" +
        (f"; MISMATCH: {', '.join(bad)}" if bad else f"; PREREG {exp.get('phase3/evidence/PREREG_FINAL.md', '?')[:16]}"))

# 3 first (states feed the others)
state = {}
for k, j in JOBS.items():
    q = sh(["squeue", "-h", "-j", j, "-o", "%T|%r|%M|%N"]).strip()
    if q:
        st, reason, el, node = q.split("|")
    else:
        s = sh(["sacct", "-X", "-n", "-P", "-j", j, "-o", "State,Elapsed,NodeList,ExitCode"]).strip().splitlines()
        st, el, node, ec = (s[0].split("|") + ["?"] * 4)[:4] if s else ("UNKNOWN", "?", "?", "?")
        reason = f"exit {ec}"
    state[k] = (st.split()[0] if st else "UNKNOWN", reason, el, node)

# 2. GATE
g = read(f"logs/p3_gate_{G}.log")
if g is None or (state["G"][0] in ("PENDING", "RUNNING") and "ALL GATES PASSED" not in (g or "")):
    say(2, "WAITING", f"GATE: job {G} {state['G'][0]}, log {'not yet written' if g is None else 'incomplete'}")
elif "ALL GATES PASSED" in g and "G5 PASS" in g:
    say(2, "PASS", "GATE: ALL GATES PASSED, G5 PASS; " + (re.findall(r"plan: .*", g) or ["(no plan line)"])[-1])
else:
    last = [l for l in g.splitlines() if l.strip()][-1:] or ["(empty)"]
    say(2, "FAIL", f"GATE: ALL GATES PASSED={'ALL GATES PASSED' in g}, G5={'G5 PASS' in g}; last line: {last[0][:120]}")

# 3. JOBS
never = [JOBS[k] for k, v in state.items() if v[0] == "PENDING" and "DependencyNeverSatisfied" in v[1]]
dead = [k for k, v in state.items() if v[0] in ("FAILED", "CANCELLED", "TIMEOUT", "OUT_OF_MEMORY", "NODE_FAIL", "PREEMPTED")]
summary = "; ".join(f"{k}={JOBS[k]} {v[0]}" + (f" ({v[1]})" if v[0] == "PENDING" else f" {v[2]} {v[3]}") for k, v in state.items())
say(3, "FAIL" if never or dead else ("WAITING" if any(v[0] == "UNKNOWN" for v in state.values()) else "PASS"),
    "JOBS: " + summary)
if never:
    print(f"         -> dependency can never be met; run:  scancel {' '.join(never)}")

# 4. PULL
p = read(f"logs/ollama_pull_{P}.log")


def listing(txt):
    ids = {}
    for l in txt.splitlines():
        t = l.split()
        if len(t) >= 2 and re.fullmatch(r"[0-9a-f]{12}", t[1]):
            ids[t[0]] = t[1]
    return ids


if p is None or "== after" not in p:
    say(4, "WAITING", f"PULL: job {P} {state['P'][0]}, no complete listing yet")
else:
    before = listing(p.split("== before", 1)[1].split("== pull", 1)[0]) if "== before" in p else {}
    after = listing(p.split("== after", 1)[1])
    diff = [m for m in M6 if not before.get(m) or before.get(m) != after.get(m)]
    ok = not diff and "qwen2.5-coder:32b" in after and "ALL MODELS PRESENT" in p
    say(4, "PASS" if ok else "FAIL", f"PULL: six original IDs identical before/after: {not diff}"
        + (f" (differ/missing: {diff})" if diff else "") + f"; qwen2.5-coder:32b present: {'qwen2.5-coder:32b' in after}"
        + f" ({after.get('qwen2.5-coder:32b', '-')}); ALL MODELS PRESENT: {'ALL MODELS PRESENT' in p}")
    for m in M6:
        print(f"         {m:<22} before {before.get(m, '-'):<13} after {after.get(m, '-')}")

# 5. GATE ARM
fs = sorted(glob.glob(RES["A"] + "/*/baseline_gate/*/rep*/metrics.json"), key=os.path.getmtime)
if not fs:
    say(5, "WAITING", f"GATE ARM: no finished baseline_gate run in {RES['A']} yet")
else:
    f = fs[-1]; m = json.load(open(f)); d = os.path.dirname(f)
    prompts = sorted(glob.glob(d + "/iter*/prompt.txt"), key=lambda x: int(re.search(r"iter(\d+)", x).group(1)))
    probs = []
    for i, pp in enumerate(prompts):
        fb = open(pp).read().split("VERIFICATION FEEDBACK ON THE CURRENT RTL:\n", 1)[-1].split("\n\nReturn the COMPLETE module")[0]
        pi = m["per_iter"][i]
        if pi["func_pass"] and not pi["struct_clean"]:
            if fb != "SIMULATION PASSED.\n\n" + GATE:
                probs.append(f"iter{i + 1}: not exactly sim line + gate message")
        elif GATE in fb or any(k in fb for k in ("VERILATOR", "YOSYS", "SEMANTIC")) or \
                not fb.startswith(("SIMULATION ", "COMPILATION FAILED")):
            probs.append(f"iter{i + 1}: feedback is not the simulation result alone")
    for k, want in (("tool_feedback_iters", 0), ("semantic_fired", False), ("escalated_at", None), ("restarted", False)):
        if m.get(k) != want:
            probs.append(f"{k}={m.get(k)}")
    if "would_fire" not in m or any("would_fire" not in x for x in m["per_iter"]):
        probs.append("would_fire missing")
    pv = m.get("provenance", {})
    pairs = {"runner_sha256_lf": "phase3/runner/stitch_runner_p3.py", "p3_eval_sha256_lf": "phase3/runner/p3_eval.py",
             "base_interp_sha256_lf": "src/interpreter/stitch_interpreter.py",
             "v3_interp_sha256_lf": "src/interpreter/stitch_interpreter_v3.py",
             "v3_parsers_sha256_lf": "src/interpreter/_v3_parsers.py",
             "system_prompt_sha256_lf": "phase3/runner/system_prompt.txt", "tb_v_sha256_lf": f"phase3/tasks/{m['task']}/tb.v"}
    probs += [f"provenance {k} != FREEZE" for k, fn in pairs.items() if pv.get(k) != exp.get(fn)]
    if not re.fullmatch(r"(sha256:)?[0-9a-f]{64}", str(pv.get("model_digest", ""))):
        probs.append(f"model_digest={pv.get('model_digest')}")
    say(5, "FAIL" if probs else "PASS", f"GATE ARM: {m['model']} {m['task']} rep{m['rep']}: calls={m['llm_calls']} "
        f"stop={m['stop_reason']} clean={m['clean_pass']} toolfb={m['tool_feedback_iters']} sf={int(m['semantic_fired'])} "
        f"would_fire={m.get('would_fire')} {m.get('would_class')} digest={str(pv.get('model_digest'))[:19]}"
        + (f"; PROBLEMS: {'; '.join(probs)}" if probs else ""))
    if prompts:
        print("         ---- first prompt of that run " + "-" * 40)
        print("\n".join("         " + l for l in open(prompts[0]).read().splitlines()))
        print("         " + "-" * 70)

# 6. JOB C: own port and GPU (from each job's ollama serve log)
def serve(j):
    t = read(f"logs/ollama_serve_{j}.log") or ""
    port = (re.findall(r"Listening on [\d.]+:(\d+)", t) or [None])[0]
    gpus = sorted(set(re.findall(r"inference compute.*?\bid=(\S+)", t)))
    name = (re.findall(r'inference compute.*?\bname=("[^"]*"|\S+)', t) or ["?"])[0]
    return port, gpus, name


pa, ga, _ = serve(A)
pc, gc, nc = serve(C)
if pc is None:
    say(6, "WAITING", f"JOB C: logs/ollama_serve_{C}.log has no 'Listening on' line yet (job {state['C'][0]})")
else:
    ok = pc != pa and (not ga or not gc or not set(ga) & set(gc))
    say(6, "PASS" if ok else "FAIL", f"JOB C: port {pc} (A: {pa}); GPU {gc or '?'} {nc} (A: {ga or '?'})")

# 7. PROGRESS
for k in ("A", "C"):
    ms = [json.load(open(f)) for f in glob.glob(RES[k] + "/*/*/*/rep*/metrics.json")]
    errs = [e for e in glob.glob(RES[k] + "/*/*/*/rep*/error.json") if not os.path.exists(os.path.join(os.path.dirname(e), "metrics.json"))]
    n = len(ms)
    if not n:
        say(7, "WAITING", f"PROGRESS {k}: 0/198 (job {state[k][0]})")
        continue
    mean = sum(x["wall_s"] for x in ms) / n
    eta = (198 - n) * mean / 3600
    say(7, "PASS" if not errs else "FAIL", f"PROGRESS {k}: {n}/198 done, {len(errs)} errored (retried on resubmit), "
        f"mean {mean:.0f} s/run, ETA ~{eta:.1f} h" + (" (done)" if n >= 198 else ""))
PY
