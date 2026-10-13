"""Proof that the Ollama path is untouched by Set 4.

1. Every engine file Set 3 ran is byte-identical to git HEAD.
2. Mock run: set3_runner imported ALONE (no frontier module loaded), talking to
   a stub Ollama server that returns RTLLM's golden design. One sem_adv run
   and one sem_escalate run must PASS on iteration 1, and the request the stub
   receives must be exactly Set 3's: model name, temperature 0.1, the
   engine's SYSTEM_PROMPT, the spec as the user turn.
Run in WSL:
  PYTHONPATH=$WIN_HOME/stitch_set4_pylib RTLLM_ROOT=$RTLLM_ROOT \\
  python3 phase2/frontier/ollama_parity_mock.py
"""
import http.server
import json
import os
import subprocess
import sys
import tempfile
import threading

HERE = os.path.dirname(os.path.abspath(__file__))
PHASE2 = os.path.dirname(HERE)
REPO = os.path.dirname(PHASE2)
ENGINE = ["phase2/set3_runner.py", "phase2/stitch_runner_hpc.py", "phase2/escalation_runner_hpc.py",
          "phase1/escalation_state.py", "phase1/error_signature.py",
          "src/interpreter/stitch_interpreter.py", "src/interpreter/pass_detection.py"]
MODULE = "adder_8bit"
SEEN, REPLY = [], {}


def git(*a):
    return subprocess.run(["git", "-C", REPO, *a], capture_output=True, text=True).stdout.strip()


class FakeOllama(http.server.BaseHTTPRequestHandler):
    def do_POST(self):
        body = json.loads(self.rfile.read(int(self.headers["Content-Length"])))
        SEEN.append(body)
        out = {"id": "x", "object": "chat.completion", "created": 0, "model": body["model"],
               "choices": [{"index": 0, "finish_reason": "stop",
                            "message": {"role": "assistant", "content": REPLY["text"]}}],
               "usage": {"prompt_tokens": 11, "completion_tokens": 7, "total_tokens": 18}}
        data = json.dumps(out).encode()
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def log_message(self, *a):
        pass


def main():
    for f in ENGINE:
        # CRLF-normalised compare: the checkout uses core.autocrlf=true on Windows
        head = subprocess.run(["git", "-C", REPO, "show", f"HEAD:{f}"], capture_output=True).stdout
        work = open(os.path.join(REPO, f), "rb").read()
        same = work.replace(b"\r\n", b"\n") == head.replace(b"\r\n", b"\n")
        print(f"{'identical' if same else 'MODIFIED '} to HEAD: {f}")
        assert same, f"{f} differs from HEAD"

    srv = http.server.HTTPServer(("127.0.0.1", 0), FakeOllama)
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    os.environ["OLLAMA_HOST"] = f"127.0.0.1:{srv.server_port}"

    sys.path.insert(0, PHASE2)
    import set3_runner as s3
    import stitch_runner_hpc as sr
    import escalation_runner_hpc as erh
    assert sr.call_llm is s3._call_ollama_set3 and erh.call_llm is s3._call_ollama_set3
    assert not any(m in sys.modules for m in ("backends", "set4_runner", "api_secrets"))

    pool = {p[0]: p for p in s3._load_module_pool(s3.RTLLM_ROOT, s3.TASK_A_SCREEN_JSON,
                                                   s3.MODULE_CATEGORIES_JSON)}
    design, category, rel = pool[MODULE]
    golden = open(os.path.join(s3.RTLLM_ROOT, rel, f"verified_{MODULE}.v"), encoding="utf-8").read()
    golden = golden.replace(f"verified_{MODULE}", MODULE)  # same rename rtllm_task_a_screen.py applies
    REPLY["text"] = f"```verilog\n{golden}\n```"

    with tempfile.TemporaryDirectory() as tmp:
        for attr in ("RESULTS_ROOT", "RAW_CLASSIC_ROOT", "RAW_ESCALATION_ROOT", "STAGED_ROOT"):
            setattr(s3, attr, os.path.join(tmp, attr))
        tb, deps = s3._stage_testbench(design, rel)
        spec = s3._get_spec(rel)
        model = s3.MODELS[0]
        r1 = s3._run_classic(design, category, model, "sem_adv", spec, tb, deps, 1)
        r2 = s3._run_escalation(design, category, model, "sem_escalate", spec, tb, deps, 1)

    for name, r in (("sem_adv", r1), ("sem_escalate", r2)):
        print(f"{name}: pass={r['pass']} iterations_to_pass={r['iterations_to_pass']} tokens={r['total_tokens']}")
        assert r["pass"] and r["iterations_to_pass"] == 1 and r["total_tokens"] == 18
    for body in SEEN:
        assert body["model"] == model and body["temperature"] == 0.1
        assert body["messages"][0] == {"role": "system", "content": sr.SYSTEM_PROMPT}
        assert body["messages"][1] == {"role": "user", "content": spec}
        assert "max_tokens" not in body and "max_completion_tokens" not in body
    print(f"stub saw {len(SEEN)} requests, all Set-3-shaped (model={model}, T=0.1, no max_tokens)")
    print("OLLAMA PATH UNCHANGED: PASS")
    srv.shutdown()


if __name__ == "__main__":
    main()
