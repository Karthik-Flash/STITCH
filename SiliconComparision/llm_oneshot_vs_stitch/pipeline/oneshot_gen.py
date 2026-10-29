#!/usr/bin/env python3
"""One-shot generation: one LLM call per module, no feedback.

System prompt: phase3/runner/system_prompt.txt (the Phase 3 production prompt).
User prompt:   the module's spec (specs/<m>.md, which already holds the exact port list and the children's port
               lists; the "Unclear in golden" review note is removed) plus a fixed closing instruction.
Code extraction: stitch_runner_p3.extract_code, imported unchanged.
Writes prompts/<m>.txt, outputs/oneshot/<m>.v, and runs/oneshot/<m>/{response.txt,record.json}.
Bonus: --full-router also asks for the whole top_module router (all its descendants) in one prompt
(prompts/top_module_full.txt, outputs/oneshot/top_module_full.v).

Usage: python pipeline/oneshot_gen.py --model qwen2.5-coder:32b [--host http://127.0.0.1:11434] [--full-router]
       python pipeline/oneshot_gen.py --backend mock --mock-plan register_4bit=handwritten encoder=golden ...
Resumable: a module with an existing record.json is skipped (use --force to redo).
"""
from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import os
import re
import sys
import time
import urllib.request

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import p3_bridge as B  # noqa: E402
import make_tasks as MT  # noqa: E402

R = B.runner()                       # stitch_runner_p3, unmodified (Ollama client, extract_code, Mock)
STUDY = B.STUDY
SYSTEM_PROMPT_FILE = os.path.join(B.REPO, "phase3", "runner", "system_prompt.txt")
CLOSING = ("Write the complete Verilog-2001 module `{m}` that meets this specification, with exactly the port list "
           "above.{children}\nReturn only Verilog: one ```verilog code block, no explanation.")
CHILDREN_NOTE = (" The child modules listed under Children already exist and are compiled together with your file: "
                 "instantiate them as specified and do not define them yourself.")
FULL_CLOSING = ("Write the complete Verilog-2001 design for module `top_module`, including every module it needs, "
                "each module exactly as specified above.\nReturn only Verilog: one ```verilog code block, no explanation.")


def sha(text: str) -> str:
    return hashlib.sha256(text.replace("\r\n", "\n").encode()).hexdigest()


def spec_text(m: str) -> str:
    text = open(os.path.join(STUDY, "specs", f"{m}.md"), encoding="utf-8").read()
    text = re.sub(r"<!-- (BEGIN|END) generated: \w+ -->\n", "", text)
    return re.sub(r"\nUnclear in golden:.*\Z", "\n", text, flags=re.S).rstrip() + "\n"


def prompt_for(m: str, rows: dict) -> str:
    return spec_text(m) + "\n" + CLOSING.format(m=m, children=CHILDREN_NOTE if rows[m]["child_list"] else "")


def full_router_prompt(rows: dict) -> str:
    order = MT.descendants(rows, "top_module") + ["top_module"]
    order.sort(key=lambda m: int(rows[m]["bottom_up_order"]))
    return "\n\n".join(spec_text(m) for m in order) + "\n\n" + FULL_CLOSING


class MockGen:
    """golden: golden/reference file | handwritten: golden/handwritten file (latched registers stay latched) |
    broken: the golden with its final 'endmodule' removed (syntax error)."""
    def __init__(self, plan: dict, rows: dict):
        self.plan, self.rows = plan, rows

    def chat(self, system, user, module):
        mode = self.plan.get(module, "golden")
        if module == "top_module_full":
            text = "".join(open(os.path.join(STUDY, "golden", "reference", self.rows[m]["file"])).read()
                           for m in MT.descendants(self.rows, "top_module") + ["top_module"])
        else:
            src = "handwritten" if mode == "handwritten" else "reference"
            text = open(os.path.join(STUDY, "golden", src, self.rows[module]["file"])).read()
            if mode == "broken":
                text = text[:text.rfind("endmodule")]
        return "```verilog\n" + text + "\n```", len(user) // 4, len(text) // 4


def ollama_version(host: str) -> str:
    try:
        with urllib.request.urlopen(host.rstrip("/") + "/api/version", timeout=30) as r:
            return json.loads(r.read()).get("version", "?")
    except Exception as e:
        return f"UNAVAILABLE ({e.__class__.__name__})"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--model", default="qwen2.5-coder:32b")
    ap.add_argument("--backend", choices=["ollama", "mock"], default="ollama")
    ap.add_argument("--mock-plan", nargs="*", default=[], help="module=golden|handwritten|broken (mock backend)")
    ap.add_argument("--host", default=os.environ.get("OLLAMA_HOST", "http://127.0.0.1:11434"))
    ap.add_argument("--temperature", type=float, default=0.1)
    ap.add_argument("--num-ctx", type=int, default=32768, help="large enough for top_module's ports and children")
    ap.add_argument("--timeout", type=int, default=3600)
    ap.add_argument("--modules", nargs="*", default=None)
    ap.add_argument("--full-router", action="store_true")
    ap.add_argument("--force", action="store_true")
    a = ap.parse_args()
    if not a.host.startswith("http"):
        a.host = "http://" + a.host

    rows = MT.load_rows()
    modules = a.modules or sorted(rows, key=lambda m: int(rows[m]["bottom_up_order"]))
    system = open(SYSTEM_PROMPT_FILE, encoding="utf-8").read()
    if a.backend == "mock":
        llm = MockGen(dict(p.split("=", 1) for p in a.mock_plan), rows)
        digest, version = "mock", "mock"
    else:
        llm = R.Ollama(a.model, a.host, a.temperature, a.num_ctx, a.timeout)
        digest, version = R.model_digest(llm, a.model), ollama_version(a.host)
    jobs = [(m, prompt_for(m, rows)) for m in modules]
    if a.full_router:
        jobs.append(("top_module_full", full_router_prompt(rows)))
    for d in ("prompts", os.path.join("outputs", "oneshot")):
        os.makedirs(os.path.join(B.WORK, d), exist_ok=True)
    for m, prompt in jobs:
        rd = os.path.join(B.WORK, "runs", "oneshot", m)
        if os.path.exists(os.path.join(rd, "record.json")) and not a.force:
            print(f"skip {m} (done)")
            continue
        os.makedirs(rd, exist_ok=True)
        open(os.path.join(B.WORK, "prompts", f"{m}.txt"), "w", encoding="utf-8", newline="\n").write(prompt)
        t0 = time.time()
        if a.backend == "mock":
            resp, tin, tout = llm.chat(system, prompt, m)
        else:
            resp, tin, tout = llm.chat(system, prompt)
        code = R.extract_code(resp)
        open(os.path.join(rd, "response.txt"), "w", encoding="utf-8", newline="\n").write(resp)
        open(os.path.join(B.WORK, "outputs", "oneshot", f"{m}.v"), "w", encoding="utf-8", newline="\n").write(code)
        rec = {"module": m, "model": a.model, "backend": a.backend, "model_digest": digest, "ollama_version": version,
               "temperature": a.temperature, "num_ctx": a.num_ctx, "tokens_in": tin, "tokens_out": tout,
               "wall_s": round(time.time() - t0, 1), "timestamp": dt.datetime.now().isoformat(timespec="seconds"),
               "system_prompt_sha256_lf": sha(system), "prompt_sha256_lf": sha(prompt),
               "response_sha256": hashlib.sha256(resp.encode()).hexdigest(),
               "output_sha256": hashlib.sha256(code.encode()).hexdigest(),
               "mock_mode": llm.plan.get(m, "golden") if a.backend == "mock" else None}
        json.dump(rec, open(os.path.join(rd, "record.json"), "w"), indent=1)
        print(f"{m:<30} tokens in/out {tin}/{tout} {rec['wall_s']}s", flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
