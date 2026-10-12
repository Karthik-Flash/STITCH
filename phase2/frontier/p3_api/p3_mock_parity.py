"""A3(b) mock parity: the prompts the API wrapper sends must be byte-identical to the Ollama path's, for all
6 conditions on mux3, register_4bit, register_1bit (N=1). One fake server answers Ollama /api/chat,
OpenAI /v1/chat/completions, Anthropic /v1/messages and Gemini :generateContent with the SAME deterministic reply (it echoes the
CURRENT RTL back, so runs iterate to the budget where the input does not already pass). Every request's
(system, user) is recorded per path; per (condition, task) the sequences are hashed and compared.
No paid calls: dummy keys, local server. Run in WSL with STITCH_SET4_OSSCAD set.
"""
import hashlib
import http.server
import json
import os
import re
import subprocess
import sys
import tempfile
import threading

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(os.path.dirname(os.path.dirname(HERE)))
TASKS = ["mux3", "register_4bit", "register_1bit"]
SEEN = {"ollama": [], "openai": [], "anthropic": [], "gemini": []}


def reply_for(user):
    m = re.search(r"CURRENT RTL:\n```verilog\n(.*?)```", user, re.S)
    return "```verilog\n" + (m.group(1) if m else "") + "```"


class Fake(http.server.BaseHTTPRequestHandler):
    def do_POST(self):
        body = json.loads(self.rfile.read(int(self.headers["Content-Length"])))
        if self.path.endswith("/api/chat"):
            sysm, user = body["messages"][0]["content"], body["messages"][1]["content"]
            SEEN["ollama"].append((sysm, user))
            out = {"message": {"content": reply_for(user)}, "prompt_eval_count": 1, "eval_count": 1}
        elif self.path.endswith("/chat/completions"):
            sysm, user = body["messages"][0]["content"], body["messages"][1]["content"]
            SEEN["openai"].append((sysm, user))
            out = {"id": "x", "model": body["model"], "choices": [{"message": {"content": reply_for(user)},
                   "finish_reason": "stop"}], "usage": {"prompt_tokens": 1, "completion_tokens": 1}}
        elif self.path.endswith(":generateContent"):
            sysm, user = body["systemInstruction"]["parts"][0]["text"], body["contents"][0]["parts"][0]["text"]
            SEEN["gemini"].append((sysm, user))
            out = {"responseId": "x", "modelVersion": self.path.split("/models/")[1].split(":")[0],
                   "candidates": [{"content": {"parts": [{"text": reply_for(user)}]}, "finishReason": "STOP"}],
                   "usageMetadata": {"promptTokenCount": 1, "candidatesTokenCount": 1}}
        else:
            sysm, user = body["system"], body["messages"][0]["content"]
            SEEN["anthropic"].append((sysm, user))
            out = {"id": "x", "model": body["model"], "content": [{"type": "text", "text": reply_for(user)}],
                   "stop_reason": "end_turn", "usage": {"input_tokens": 1, "output_tokens": 1}}
        data = json.dumps(out).encode()
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def do_GET(self):  # /api/tags for the Ollama path's model digest
        data = json.dumps({"models": [{"name": "fake", "digest": "0" * 64}]}).encode()
        self.send_response(200)
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def log_message(self, *a):
        pass


def seq_hashes(out):
    """sha256 over the ordered prompt.txt files of each (condition, task) run dir."""
    h = {}
    for cond_dir in sorted(os.listdir(out)):
        root = os.path.join(out, cond_dir)
        if not os.path.isdir(root):
            continue
        for cond in sorted(os.listdir(root)):
            for task in TASKS:
                d = os.path.join(root, cond, task, "rep1")
                its = sorted((int(x[4:]) for x in os.listdir(d) if x.startswith("iter") and x[4:].isdigit()))
                blob = b"".join(open(os.path.join(d, f"iter{i}", "prompt.txt"), "rb").read() + b"\0"
                                for i in its if os.path.exists(os.path.join(d, f"iter{i}", "prompt.txt")))
                h[(cond, task)] = (hashlib.sha256(blob).hexdigest(), len(its) - 1)
    return h


def main():
    srv = http.server.ThreadingHTTPServer(("127.0.0.1", 0), Fake)
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    url = f"http://127.0.0.1:{srv.server_port}"
    env = dict(os.environ, PYTHONDONTWRITEBYTECODE="1", OPENAI_API_KEY="dummy-openai", ANTHROPIC_API_KEY="dummy-anth",
               GEMINI_API_KEY="dummy-gemini", STITCH_OPENAI_BASE=url + "/v1", STITCH_ANTHROPIC_BASE=url + "/v1",
               STITCH_GEMINI_BASE=url + "/v1beta")
    tmp = tempfile.mkdtemp(prefix="p3parity_")
    sp = os.path.join(REPO, "phase3", "runner", "system_prompt.txt")
    common = ["--tasks", *TASKS, "--reps", "1"]
    subprocess.run([sys.executable, os.path.join(REPO, "phase3", "runner", "stitch_runner_p3.py"), "--backend", "ollama",
                    "--host", url, "--model", "fake", "--temperature", "0.1", "--max-iters", "6",
                    "--system-prompt-file", sp, "--out", os.path.join(tmp, "ollama"), *common],
                   env=env, check=True, stdout=subprocess.DEVNULL)
    for api, model in (("openai", "gpt-4.1-mini-2025-04-14"), ("anthropic", "claude-haiku-4-5-20251001"),
                       ("gemini", "gemini-2.5-flash")):
        subprocess.run([sys.executable, os.path.join(HERE, "p3_api_runner.py"), "--api", api, "--model", model,
                        "--tag", "parity", "--out", os.path.join(tmp, api), "--provider-cap-usd", "100",
                        "--ledger-dir", os.path.join(tmp, "ledgers"), "--", *common],
                       env=env, check=True, stdout=subprocess.DEVNULL)
    ref = seq_hashes(os.path.join(tmp, "ollama"))
    ok = True
    print(f"{'condition':20s} {'task':14s} {'calls':>5s}  ollama-path sha256 (prompt sequence)         openai  anthropic  gemini")
    for api in ("openai", "anthropic", "gemini"):
        got = seq_hashes(os.path.join(tmp, api))
        ok &= got == ref
        SEEN[api + "_hash"] = got
    for k in sorted(ref):
        print(f"{k[0]:20s} {k[1]:14s} {ref[k][1]:5d}  {ref[k][0][:40]}  "
              + "  ".join("same" if SEEN[api + "_hash"].get(k) == ref[k] else "DIFF" for api in ("openai", "anthropic", "gemini")))
    # the bytes actually sent on the wire (system + user) must also match across paths, in order
    for api in ("openai", "anthropic", "gemini"):
        same = SEEN[api] == SEEN["ollama"]
        ok &= same
        print(f"wire-level (system, user) sequence, {api} vs ollama: {len(SEEN[api])} vs {len(SEEN['ollama'])} "
              f"requests, {'IDENTICAL' if same else 'DIFFERENT'}")
    print("MOCK PARITY:", "PASS" if ok else "FAIL")
    srv.shutdown()
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
