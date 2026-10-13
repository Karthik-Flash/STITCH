"""Offline checks for backends.py against a local stub server (no paid calls,
dummy key). Run: python phase2/frontier/test_backends.py"""
import http.server
import json
import os
import sys
import tempfile
import threading

os.environ["MOONSHOT_API_KEY"] = "dummy-test-key-0000"
os.environ["GEMINI_API_KEY"] = "dummy-gemini-0000"   # the local stub must never receive a real key
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import backends as B  # noqa: E402

B.MAX_RETRIES, B.TIMEOUT_S = 3, 5
B.time.sleep = lambda s: None  # no real backoff waits in tests
SCRIPT = []   # queued (status, body) replies
SEEN = []     # (auth header, request body) per request


class Stub(http.server.BaseHTTPRequestHandler):
    def do_POST(self):
        SEEN.append((self.headers.get("Authorization"), json.loads(self.rfile.read(int(self.headers["Content-Length"])))))
        status, body = SCRIPT.pop(0)
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("x-request-id", "req-123")
        self.end_headers()
        self.wfile.write(json.dumps(body).encode())

    def log_message(self, *a):
        pass


def ok(content="```verilog\nmodule m; endmodule\n```", reasoning=0):
    return 200, {"id": "resp-1", "model": "kimi-k2.6-20260901", "system_fingerprint": "fp_x",
                 "choices": [{"message": {"content": content}, "finish_reason": "stop"}],
                 "usage": {"prompt_tokens": 1000, "completion_tokens": 200,
                           "prompt_tokens_details": {"cached_tokens": 400},
                           "completion_tokens_details": {"reasoning_tokens": reasoning}}}


def main():
    srv = http.server.HTTPServer(("127.0.0.1", 0), Stub)
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    B.MOONSHOT_BASE = f"http://127.0.0.1:{srv.server_port}"
    msgs = [{"role": "system", "content": "s"}, {"role": "user", "content": "x" * 400}]
    with tempfile.TemporaryDirectory() as d:
        be = B.Backend("moonshot", "kimi-k2.6", max_tokens=1000, ledger_dir=d,
                       budget_usd=1.0, provider_cap_usd=1.0)
        assert be.temperature == 0.6  # Kimi fixed non-thinking temperature

        SCRIPT.append(ok())
        text, pt, ct = be("kimi-k2.6", msgs)
        assert (pt, ct) == (1000, 200) and "module m" in text
        body = SEEN[-1][1]
        assert body["thinking"] == {"type": "disabled"} and body["max_completion_tokens"] == 1000
        rec = json.loads(open(be.ledger).read().splitlines()[-1])
        want = (600 * 0.95 + 400 * 0.16 + 200 * 4.00) / 1e6
        assert abs(rec["cost_usd"] - want) < 1e-12, rec["cost_usd"]
        assert rec["request_id"] == "req-123" and rec["system_fingerprint"] == "fp_x"
        assert "dummy-test-key" not in open(be.ledger).read()

        # 429 three times then success: 4 attempts, 3 retries
        SCRIPT.extend([(429, {"error": "rate"})] * 3 + [ok()])
        n0 = len(SEEN)
        be("kimi-k2.6", msgs)
        assert len(SEEN) - n0 == 4

        # 4 failures: gives up with CallFailed (BaseException, escapes `except Exception`)
        SCRIPT.extend([(503, {"error": "down"})] * 4)
        try:
            be("kimi-k2.6", msgs)
            raise AssertionError("expected CallFailed")
        except B.CallFailed:
            pass
        assert not issubclass(B.CallFailed, Exception)

        # non-retryable 404 fails at once
        SCRIPT.append((404, {"error": "bad dummy-test-key-0000"}))
        n0 = len(SEEN)
        try:
            be("kimi-k2.6", msgs)
            raise AssertionError("expected CallFailed on 404")
        except B.CallFailed as e:
            assert "dummy-test-key" not in str(e)  # redacted
        assert len(SEEN) - n0 == 1

        # billing/credit (400, 402) stops the provider at once; 429 that outlasts the retries stops it too
        for code in (400, 402):
            SCRIPT.append((code, {"error": "credit balance too low"}))
            n0 = len(SEEN)
            try:
                be("kimi-k2.6", msgs)
                raise AssertionError(f"expected ProviderStop on {code}")
            except B.ProviderStop:
                pass
            assert len(SEEN) - n0 == 1
        SCRIPT.extend([(429, {"error": "quota"})] * 4)
        try:
            be("kimi-k2.6", msgs)
            raise AssertionError("expected ProviderStop on persistent 429")
        except B.ProviderStop:
            pass

        # truncated completion -> provider stop
        trunc = ok()
        trunc[1]["choices"][0]["finish_reason"] = "length"
        SCRIPT.append(trunc)
        try:
            be("kimi-k2.6", msgs)
            raise AssertionError("expected ProviderStop on truncation")
        except B.ProviderStop:
            pass

        # auth failure and model-ID mismatch -> provider stop
        SCRIPT.append((401, {"error": "auth"}))
        try:
            be("kimi-k2.6", msgs)
            raise AssertionError("expected ProviderStop on 401")
        except B.ProviderStop:
            pass
        bad = ok()
        bad[1]["model"] = "some-other-model"
        SCRIPT.append(bad)
        try:
            be("kimi-k2.6", msgs)
            raise AssertionError("expected ProviderStop on model mismatch")
        except B.ProviderStop:
            pass

        # reasoning tokens > 0 -> hard stop
        SCRIPT.append(ok(reasoning=5))
        try:
            be("kimi-k2.6", msgs)
            raise AssertionError("expected ReasoningDetected")
        except B.ReasoningDetected:
            pass

        # budget: a call whose worst case crosses the cap is never sent
        be.provider_cap_usd = be.spent()[0] + 0.001  # worst case here is ~$0.0042
        n0 = len(SEEN)
        try:
            be("kimi-k2.6", msgs)
            raise AssertionError("expected BudgetExceeded")
        except B.BudgetExceeded:
            pass
        assert len(SEEN) == n0, "request was sent despite budget"

        # Gemini thinking (Set 4c): within budget passes and is billed as output; over budget stops
        B.GEMINI_BASE = f"http://127.0.0.1:{srv.server_port}"

        def gem(thoughts):
            return 200, {"responseId": "g", "modelVersion": "gemini-2.5-pro",
                         "candidates": [{"content": {"parts": [{"text": "ok"}]}, "finishReason": "STOP"}],
                         "usageMetadata": {"promptTokenCount": 100, "candidatesTokenCount": 10, "thoughtsTokenCount": thoughts}}
        gp = B.Backend("gemini", "gemini-2.5-pro", max_tokens=10240, ledger_dir=d, budget_usd=5.0,
                       provider_cap_usd=5.0, thinking_budget=2048)
        SCRIPT.append(gem(1500))
        text, pt, ct = gp("gemini-2.5-pro", msgs)
        gcfg = SEEN[-1][1]["generationConfig"]
        assert ct == 1510 and gcfg["thinkingConfig"] == {"thinkingBudget": 2048} and gcfg["maxOutputTokens"] == 10240
        rec = json.loads(open(gp.ledger).read().splitlines()[-1])
        assert rec["reasoning_tokens"] == 1500 and rec["thinking_budget"] == 2048
        assert abs(rec["cost_usd"] - (100 * 1.25 + 1510 * 10.0) / 1e6) < 1e-12
        SCRIPT.append(gem(2049))
        try:
            gp("gemini-2.5-pro", msgs)
            raise AssertionError("expected ReasoningDetected over the thinking budget")
        except B.ReasoningDetected:
            pass
        flash = B.Backend("gemini", "gemini-2.5-flash", max_tokens=8192, ledger_dir=d, budget_usd=5.0, provider_cap_usd=5.0)
        bad = gem(5)
        bad[1]["modelVersion"] = "gemini-2.5-flash"
        SCRIPT.append(bad)
        try:
            flash("gemini-2.5-flash", msgs)
            raise AssertionError("expected ReasoningDetected without a thinking budget")
        except B.ReasoningDetected:
            pass
        assert SEEN[-1][1]["generationConfig"]["thinkingConfig"] == {"thinkingBudget": 0}
        for f in ("gemini_ledger.jsonl",):
            os.remove(os.path.join(d, f))

        # global cap reads every provider ledger in the directory
        open(os.path.join(d, "openai_ledger.jsonl"), "w").write(json.dumps({"cost_usd": 0.999}) + "\n")
        be.provider_cap_usd = 1.0
        try:
            be("kimi-k2.6", msgs)
            raise AssertionError("expected global BudgetExceeded")
        except B.BudgetExceeded:
            pass
    srv.shutdown()
    print("test_backends: all checks passed")


if __name__ == "__main__":
    main()
