"""Set 4 API backends: one callable per provider with the engine's
call_llm(model, messages) -> (text, prompt_tokens, completion_tokens)
signature. Stdlib only (urllib), so nothing new is installed.

Every call:
  * checks the provider and global USD caps BEFORE sending, using the
    worst case (estimated input tokens x input price + max_tokens x
    output price); a call that could cross a cap raises BudgetExceeded;
  * retries 429 / 5xx / timeouts / connection errors at most 3 times with
    backoff, re-checking the budget before each retry, then raises
    CallFailed;
  * appends one JSON line to <ledger_dir>/<provider>_ledger.jsonl with
    provider-reported tokens (input, output, reasoning, cached), latency,
    response/request IDs, model version, system_fingerprint, UTC time,
    and computed USD cost. Keys never reach the ledger or exceptions.

BudgetExceeded, CallFailed and ReasoningDetected derive from BaseException
on purpose: the Set 3 engine wraps call_llm in `except Exception` (classic
conditions end the run as a FAIL on any exception), so a normal Exception
would be silently recorded as a model failure instead of a stop or an
errored run.
"""
import datetime
import json
import math
import os
import time
import urllib.error
import urllib.request

from api_secrets import key_for, redact

MOONSHOT_BASE = "https://api.moonshot.ai/v1"  # confirmed against Kimi docs before use; see SET4_PREREG.md
# overridable only so offline parity tests can point at a local fake server
OPENAI_BASE = os.environ.get("STITCH_OPENAI_BASE", "https://api.openai.com/v1")
ANTHROPIC_BASE = os.environ.get("STITCH_ANTHROPIC_BASE", "https://api.anthropic.com/v1")
GEMINI_BASE = os.environ.get("STITCH_GEMINI_BASE", "https://generativelanguage.googleapis.com/v1beta")

# USD per 1M tokens: input, cached input, output. Source URL + fetch date in
# PRICE_SOURCES. A model missing here cannot be called (no silent $0 pricing).
PRICES = {  # only the four selected Set 4 models can be called
    "gpt-4.1-mini-2025-04-14":   (0.40, 0.10, 1.60),
    "claude-haiku-4-5-20251001": (1.00, 0.10, 5.00),
    "gemini-2.5-flash":          (0.30, 0.03, 2.50),
    # Set 4c (Amendment 4), reasoning; output price includes thinking tokens.
    # ponytail: <=200k-token prompt tier only (Set 4b max prompt 23,473); >200k is 2.50 / 0.25 / 15.00
    "gemini-2.5-pro":            (1.25, 0.125, 10.00),
    "kimi-k2.6":                 (0.95, 0.16, 4.00),
}
# Kimi k2.6 with thinking disabled only accepts temperature 0.6 (docs:
# platform.kimi.ai/docs/api/models-overview); any other value is an error.
FIXED_TEMPERATURE = {"moonshot": 0.6}
PRICE_SOURCES = {
    "openai":    ("https://developers.openai.com/api/docs/pricing", "2026-09-28"),
    "anthropic": ("https://platform.claude.com/docs/en/about-claude/pricing", "2026-09-28"),
    "gemini":    ("https://ai.google.dev/gemini-api/docs/pricing", "2026-09-28"),
    "gemini-2.5-pro": ("https://ai.google.dev/gemini-api/docs/pricing (last updated 2026-10-09)", "2026-10-12"),
    "moonshot":  ("https://platform.kimi.ai/docs/pricing/chat", "2026-09-28"),
}

RETRYABLE_HTTP = {408, 409, 429, 500, 502, 503, 504, 529}
# auth, billing, credit, quota: stop the provider at once instead of erroring run after run
# (SET4_PREREG Amendment 3; 400 included because Anthropic signals exhausted credit with it)
STOP_HTTP = {400, 401, 402, 403}
TRUNCATED = {"length", "max_tokens", "MAX_TOKENS"}
MAX_RETRIES = 3
TIMEOUT_S = 180
CHARS_PER_TOKEN_LOWER_BOUND = 2.0  # ponytail: char-based input estimate, deliberately pessimistic (real code ~3-4 chars/token)

CONTEXT = {}  # set by the runner before each run: module/condition/replicate


class BudgetExceeded(BaseException):
    pass


class CallFailed(BaseException):
    pass


class ReasoningDetected(BaseException):
    pass


class ProviderStop(BaseException):
    """Auth/billing/credit failure (HTTP 400/401/402/403, or 429 after all retries), returned model ID !=
    requested, or a truncated completion: stop this provider."""


def _utc():
    return datetime.datetime.now(datetime.timezone.utc).isoformat(timespec="milliseconds")


def _post(url, headers, body):
    req = urllib.request.Request(url, data=json.dumps(body).encode(), headers=headers, method="POST")
    t0 = time.time()
    with urllib.request.urlopen(req, timeout=TIMEOUT_S) as r:
        data = json.loads(r.read().decode())
        hdrs = {k.lower(): v for k, v in r.headers.items()}
    return data, hdrs, time.time() - t0


# ── per-provider request/response mapping ────────────────────────────────
def _openai_like(provider, model, messages, max_tokens, temperature):
    base = OPENAI_BASE if provider == "openai" else MOONSHOT_BASE
    body = {"model": model, "messages": messages, "temperature": temperature,
            "max_completion_tokens": max_tokens}
    if provider == "moonshot":
        body["thinking"] = {"type": "disabled"}
    headers = {"Authorization": f"Bearer {key_for(provider)}", "Content-Type": "application/json"}
    data, hdrs, lat = _post(f"{base}/chat/completions", headers, body)
    u = data.get("usage") or {}
    ptd = u.get("prompt_tokens_details") or {}
    ctd = u.get("completion_tokens_details") or {}
    msg = data["choices"][0]["message"]
    return {
        "text": msg.get("content") or "",
        "input_tokens": u.get("prompt_tokens", 0),
        "cached_tokens": ptd.get("cached_tokens") or u.get("cached_tokens") or 0,
        "output_tokens": u.get("completion_tokens", 0),
        "reasoning_tokens": ctd.get("reasoning_tokens") or 0,
        "has_reasoning_content": bool(msg.get("reasoning_content")),
        "finish_reason": data["choices"][0].get("finish_reason"),
        "response_id": data.get("id"),
        "request_id": hdrs.get("x-request-id") or hdrs.get("msh-request-id"),
        "model_version": data.get("model"),
        "system_fingerprint": data.get("system_fingerprint"),
        "latency_s": lat,
    }


def _anthropic(model, messages, max_tokens, temperature):
    system = "\n\n".join(m["content"] for m in messages if m["role"] == "system")
    msgs = [{"role": m["role"], "content": m["content"]} for m in messages if m["role"] != "system"]
    body = {"model": model, "max_tokens": max_tokens, "temperature": temperature,
            "system": system, "messages": msgs}  # no `thinking` field: extended thinking stays off
    headers = {"x-api-key": key_for("anthropic"), "anthropic-version": "2023-06-01",
               "content-type": "application/json"}
    data, hdrs, lat = _post(f"{ANTHROPIC_BASE}/messages", headers, body)
    u = data.get("usage") or {}
    blocks = data.get("content") or []
    return {
        "text": "".join(b.get("text", "") for b in blocks if b.get("type") == "text"),
        "input_tokens": u.get("input_tokens", 0) + u.get("cache_read_input_tokens", 0)
                        + u.get("cache_creation_input_tokens", 0),
        "cached_tokens": u.get("cache_read_input_tokens", 0),
        "cache_write_tokens": u.get("cache_creation_input_tokens", 0),
        "output_tokens": u.get("output_tokens", 0),
        "reasoning_tokens": 0,
        "has_reasoning_content": any(b.get("type") in ("thinking", "redacted_thinking") for b in blocks),
        "finish_reason": data.get("stop_reason"),
        "response_id": data.get("id"),
        "request_id": hdrs.get("request-id"),
        "model_version": data.get("model"),
        "system_fingerprint": None,
        "latency_s": lat,
    }


def _gemini(model, messages, max_tokens, temperature, thinking_budget=0):
    system = "\n\n".join(m["content"] for m in messages if m["role"] == "system")
    contents = [{"role": "model" if m["role"] == "assistant" else "user", "parts": [{"text": m["content"]}]}
                for m in messages if m["role"] != "system"]
    gen = {"temperature": temperature, "maxOutputTokens": max_tokens,
           "thinkingConfig": {"thinkingBudget": thinking_budget}}   # no includeThoughts: no thought text returned
    body = {"systemInstruction": {"parts": [{"text": system}]}, "contents": contents,
            "generationConfig": gen}
    headers = {"x-goog-api-key": key_for("gemini"), "Content-Type": "application/json"}
    url = f"{GEMINI_BASE}/models/{model}:generateContent"
    data, hdrs, lat = _post(url, headers, body)
    u = data.get("usageMetadata") or {}
    cand = (data.get("candidates") or [{}])[0]
    parts = (cand.get("content") or {}).get("parts") or []
    return {
        "text": "".join(p.get("text", "") for p in parts if not p.get("thought")),
        "input_tokens": u.get("promptTokenCount", 0),
        "cached_tokens": u.get("cachedContentTokenCount", 0),
        "output_tokens": u.get("candidatesTokenCount", 0) + u.get("thoughtsTokenCount", 0),
        "reasoning_tokens": u.get("thoughtsTokenCount", 0),
        "has_reasoning_content": any(p.get("thought") for p in parts),
        "finish_reason": cand.get("finishReason"),
        "response_id": data.get("responseId"),
        "request_id": hdrs.get("x-request-id"),
        "model_version": data.get("modelVersion"),
        "system_fingerprint": None,
        "latency_s": lat,
    }


def cost_usd(model, r):
    p_in, p_cached, p_out = PRICES[model]
    uncached = max(r["input_tokens"] - r["cached_tokens"] - r.get("cache_write_tokens", 0), 0)
    return (uncached * p_in + r["cached_tokens"] * p_cached
            + r.get("cache_write_tokens", 0) * p_in * 1.25 + r["output_tokens"] * p_out) / 1e6


class Backend:
    def __init__(self, provider, model, *, max_tokens, ledger_dir,
                 budget_usd=25.0, provider_cap_usd=7.0, temperature=0.1, thinking_budget=None):
        if model not in PRICES:
            raise ValueError(f"no price recorded for {model!r}; add it to PRICES with its source first")
        self.provider, self.model = provider, model
        self.max_tokens = max_tokens
        self.temperature = FIXED_TEMPERATURE.get(provider, temperature)
        self.thinking_budget = thinking_budget   # None = non-reasoning (Sets 4/4b); int = Gemini thinkingBudget (Set 4c)
        self.budget_usd, self.provider_cap_usd = budget_usd, provider_cap_usd
        self.ledger_dir = ledger_dir
        os.makedirs(ledger_dir, exist_ok=True)
        self.ledger = os.path.join(ledger_dir, f"{provider}_ledger.jsonl")

    # ledger totals are re-read every call so separate processes / restarts see each other's spend
    def _spent(self, path):
        if not os.path.exists(path):
            return 0.0
        with open(path, encoding="utf-8") as f:
            return sum(json.loads(l).get("cost_usd", 0.0) for l in f if l.strip())

    def spent(self):
        total = sum(self._spent(os.path.join(self.ledger_dir, f))
                    for f in os.listdir(self.ledger_dir) if f.endswith("_ledger.jsonl"))
        return self._spent(self.ledger), total

    def worst_case(self, messages):
        chars = sum(len(m["content"]) for m in messages)
        p_in, _, p_out = PRICES[self.model]
        return (math.ceil(chars / CHARS_PER_TOKEN_LOWER_BOUND) * p_in + self.max_tokens * p_out) / 1e6

    def _check_budget(self, worst):
        mine, total = self.spent()
        if mine + worst > self.provider_cap_usd or total + worst > self.budget_usd:
            raise BudgetExceeded(
                f"{self.provider}: next call worst case ${worst:.4f} would exceed a cap "
                f"(provider ${mine:.4f}/{self.provider_cap_usd}, global ${total:.4f}/{self.budget_usd})")

    def _log(self, rec):
        with open(self.ledger, "a", encoding="utf-8") as f:
            f.write(redact(json.dumps(rec)) + "\n")

    def _send(self, messages):
        if self.provider in ("openai", "moonshot"):
            return _openai_like(self.provider, self.model, messages, self.max_tokens, self.temperature)
        if self.provider == "anthropic":
            return _anthropic(self.model, messages, self.max_tokens, self.temperature)
        if self.provider == "gemini":
            return _gemini(self.model, messages, self.max_tokens, self.temperature, self.thinking_budget or 0)
        raise ValueError(self.provider)

    def __call__(self, model, messages):
        assert model == self.model, (model, self.model)
        base = {"provider": self.provider, "model_requested": self.model,
                "max_tokens": self.max_tokens, "temperature": self.temperature, **CONTEXT}
        if self.thinking_budget is not None:
            base["thinking_budget"] = self.thinking_budget
        last_http = None
        for attempt in range(MAX_RETRIES + 1):
            worst = self.worst_case(messages)
            self._check_budget(worst)
            t0 = time.time()
            try:
                r = self._send(messages)
            except urllib.error.HTTPError as e:
                detail = redact(e.read().decode(errors="replace")[:400])
                self._log({**base, "ts_utc": _utc(), "attempt": attempt, "status": f"http_{e.code}",
                           "error": detail, "latency_s": time.time() - t0, "cost_usd": 0.0,
                           "worst_case_usd": worst})
                if e.code in STOP_HTTP:
                    raise ProviderStop(f"{self.provider} HTTP {e.code} (auth/billing/credit): {detail}")
                if e.code not in RETRYABLE_HTTP:
                    raise CallFailed(f"{self.provider} HTTP {e.code}: {detail}")
                last_http = e.code
                wait = float(e.headers.get("retry-after") or 0) or min(60, 5 * 2 ** attempt)
            except (urllib.error.URLError, TimeoutError, ConnectionError, OSError) as e:
                self._log({**base, "ts_utc": _utc(), "attempt": attempt, "status": "network_error",
                           "error": redact(f"{type(e).__name__}: {e}")[:400],
                           "latency_s": time.time() - t0, "cost_usd": 0.0, "worst_case_usd": worst})
                last_http = None
                wait = min(60, 5 * 2 ** attempt)
            else:
                cost = cost_usd(self.model, r)
                rec = {**base, "ts_utc": _utc(), "attempt": attempt, "status": "ok",
                       **{k: v for k, v in r.items() if k != "text"},
                       "cost_usd": cost, "worst_case_usd": worst}
                self._log(rec)
                if not str(r["model_version"] or "").startswith(self.model):
                    raise ProviderStop(f"{self.provider}: returned model {r['model_version']!r} "
                                       f"!= requested {self.model!r}")
                if r["reasoning_tokens"] > (self.thinking_budget or 0) or r["has_reasoning_content"]:
                    raise ReasoningDetected(f"{self.provider}/{self.model} returned reasoning "
                                            f"(reasoning_tokens={r['reasoning_tokens']}, allowed {self.thinking_budget or 0}); fix the setting")
                if str(r["finish_reason"]) in TRUNCATED:
                    raise ProviderStop(f"{self.provider}: truncated completion (finish_reason={r['finish_reason']})")
                return r["text"], r["input_tokens"], r["output_tokens"]
            if attempt < MAX_RETRIES:
                time.sleep(wait)
        if last_http == 429:
            raise ProviderStop(f"{self.provider}: HTTP 429 persisted after {MAX_RETRIES} retries (quota or credit)")
        raise CallFailed(f"{self.provider}: gave up after {MAX_RETRIES} retries")
