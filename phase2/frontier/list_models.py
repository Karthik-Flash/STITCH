"""Query each provider's (free) list-models endpoint. Prints model IDs only."""
import json
import os
import sys
import urllib.request

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from api_secrets import key_for, redact  # noqa: E402

ENDPOINTS = {
    "openai": ("https://api.openai.com/v1/models", lambda k: {"Authorization": f"Bearer {k}"},
               lambda d: [m["id"] for m in d["data"]]),
    "moonshot": ("https://api.moonshot.ai/v1/models", lambda k: {"Authorization": f"Bearer {k}"},
                 lambda d: [m["id"] for m in d["data"]]),
    "anthropic": ("https://api.anthropic.com/v1/models?limit=100",
                  lambda k: {"x-api-key": k, "anthropic-version": "2023-06-01"},
                  lambda d: [m["id"] for m in d["data"]]),
    "gemini": ("https://generativelanguage.googleapis.com/v1beta/models?pageSize=1000",
               lambda k: {"x-goog-api-key": k},
               lambda d: [m["name"].removeprefix("models/") for m in d["models"]
                          if "generateContent" in m.get("supportedGenerationMethods", [])]),
}

for provider, (url, hdr, ids) in ENDPOINTS.items():
    try:
        req = urllib.request.Request(url, headers=hdr(key_for(provider)))
        with urllib.request.urlopen(req, timeout=30) as r:
            models = sorted(ids(json.loads(r.read().decode())))
        print(f"{provider}: {len(models)} models: {', '.join(models)}")
    except Exception as e:  # report and continue; this is a read-only probe
        body = e.read().decode(errors="replace")[:200] if hasattr(e, "read") else ""
        print(f"{provider}: FAILED {type(e).__name__} {redact(str(e))} {redact(body)}")
