#!/usr/bin/env python3
"""Ask one model one short Verilog prompt through a running Ollama server, the way the STITCH runner does
(/api/chat, options temperature and num_ctx only), and print what the study records for that model.

Exit 0 if the model is in the store (with the expected digest when --digest is given) and answers with a module
named and2 at 8 tok/s or more. Usage (hpc/step4_smoke_test.slurm):
  python3 hpc/model_check.py --model qwen2.5-coder:32b --host http://127.0.0.1:11500 [--digest <sha256>]
"""
import argparse
import json
import sys
import urllib.request

PROMPT = "Write a Verilog module named and2 with inputs a and b and output y, where y = a & b. Reply with the code only."
OPTIONS = {"temperature": 0.1, "num_ctx": 32768}
MIN_TOK_S = 8


def api(host, path, body=None, timeout=1800):
    data = None if body is None else json.dumps(body).encode()
    req = urllib.request.Request(host + path, data=data, headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.loads(r.read())


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--model", required=True)
    p.add_argument("--host", required=True)
    p.add_argument("--digest", default="")
    a = p.parse_args()
    bad = []

    version = api(a.host, "/api/version")["version"]
    m = {t["name"]: t for t in api(a.host, "/api/tags")["models"]}.get(a.model)
    if m is None:
        print(f"[model] BAD  {a.model} is not in the store (run hpc/step2_get_models.sh)")
        return 1
    d = m.get("details", {})
    print(f"[model] {a.model}: digest {m['digest']}, quantisation {d.get('quantization_level')}, "
          f"{d.get('parameter_size')} parameters, family {d.get('family')}, format {d.get('format')}, ollama {version}")
    if a.digest and m["digest"] != a.digest:
        bad.append("digest")
        print(f"[digest] BAD  expected {a.digest}")
    show = api(a.host, "/api/show", {"model": a.model})
    print(f"[capabilities] {', '.join(show.get('capabilities') or []) or 'none listed'}")

    r = api(a.host, "/api/chat", {"model": a.model, "stream": False, "options": OPTIONS,
                                  "messages": [{"role": "user", "content": PROMPT}]})
    msg = r.get("message", {})
    text, thinking = msg.get("content", ""), msg.get("thinking") or ""
    tok_s = r.get("eval_count", 0) / max(r.get("eval_duration", 1) / 1e9, 1e-9)
    print(f"[load] {r.get('load_duration', 0) / 1e9:.1f} s (model load into GPU memory, first call only)")
    print(f"[speed] {'ok  ' if tok_s >= MIN_TOK_S else 'BAD '} {tok_s:.1f} tok/s over {r.get('eval_count')} tokens "
          f"(need {MIN_TOK_S}), done_reason {r.get('done_reason')}")
    print(f"[thinking] {len(thinking)} characters of thinking returned with options {OPTIONS}")
    print("[answer] --- first 15 lines ---")
    print("\n".join(text.strip().splitlines()[:15]))
    print("[answer] ---")
    if tok_s < MIN_TOK_S:
        bad.append("speed")
    if "module" not in text or "and2" not in text:
        bad.append("answer")
        print("[answer] BAD  no 'module and2' in the reply")
    print(f"MODEL {a.model}: {'OK' if not bad else 'BAD (' + ', '.join(bad) + ')'}")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
