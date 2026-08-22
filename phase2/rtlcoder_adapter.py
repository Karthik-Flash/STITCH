"""
phase2/rtlcoder_adapter.py -- RTLCoder-DeepSeek-v1.1 inference adapter.

Path A: native HuggingFace `transformers` (AutoModelForCausalLM +
AutoTokenizer), NOT Ollama. ishorn5/RTLCoder-Deepseek-v1.1 is a
transformers checkpoint, not something `ollama pull` can serve, and it is
the fine-tuning twin of deepseek-coder:6.7b (same base weights) -- the
whole point of running it is that twin comparison, so this loads the
real checkpoint natively rather than going through a GGUF conversion or
any Ollama-shaped code path. Do not template this against the existing
Ollama call_llm() dispatch in src/runner/stitch_runner.py -- the model
loading, generation, and (especially) postprocessing are all specific to
this checkpoint and unrelated to that code path.

Postprocessing is SEPARATE from stitch_runner.py's fence-marker fix
(2026-08-21, phase1 harness bugs). That fix strips a stray, unclosed
```verilog fence LLMs sometimes leave in chat-style responses.
RTLCoder-Deepseek doesn't chat -- it's a raw completion model that keeps
generating past the end of the intended module, straight into a second,
unrelated training example (literally producing the substring
"endmodulemodule" with no separator between the two). Different failure
mode, different fix; see postprocess() below. This is the RTLCoder
authors' own documented cleanup, copied verbatim from
github.com/hkust-zhiyao/RTL-Coder's README (not invented here) --
confirmed 2026-08-22 by fetching that README directly.

Native prompt format: RTLCoder-Deepseek was trained on prompts of the
shape "Please act as a professional verilog designer. ... Give me the
complete code.\n\nmodule <name>(\n" -- ending on an open module header
stub the model is expected to complete, not a chat turn. This is a
DELIBERATE experimental choice for now: RTLLM's own design_description.txt
files already happen to be written in exactly this template (confirmed
against Arithmetic/Accumulator/accu's spec), so the smoke test uses it
unmodified. Whether the real Phase 2 comparison run should use this
native format or reformat through the harness's own SYSTEM_PROMPT
convention (for a controlled comparison against deepseek-coder:6.7b under
identical prompting) is an open decision, NOT made here -- flagged in
phase1/PHASE1_FINDINGS.md and left for that design conversation.

Usage (on HPC only -- see phase2/HPC_RTLCODER_COMMANDS.md):
    from rtlcoder_adapter import generate
    code = generate(prompt)
"""
import os
import re

MODEL_ID = "ishorn5/RTLCoder-Deepseek-v1.1"

_model = None
_tokenizer = None


def _check_hf_home():
    """HF_HOME must point at scratch, not home (40GB quota on HPC) -- see
    HPC_RTLCODER_COMMANDS.md. Warn, don't fail: this matters on HPC, is a
    non-issue for a local smoke test off scratch, and transformers will
    still work correctly either way (it just risks filling home quota)."""
    hf_home = os.environ.get("HF_HOME")
    if not hf_home:
        print("WARNING: HF_HOME is not set. transformers will cache "
              "weights under ~/.cache/huggingface by default -- on HPC "
              "that's the 40GB HOME quota, not /scratch. Export HF_HOME "
              "to a scratch path before loading the model there (see "
              "phase2/HPC_RTLCODER_COMMANDS.md).")
    return hf_home


def load_model(model_id=MODEL_ID, device_map="auto"):
    """Loads the model + tokenizer once (module-level cache -- repeated
    calls are free). Fails LOUDLY on any load error rather than returning
    a partial/None model: a login node with no internet access will raise
    here (huggingface_hub can't reach huggingface.co and the weights
    aren't cached locally yet), and that must stop the caller immediately,
    not produce empty/garbage generations downstream."""
    global _model, _tokenizer
    if _model is not None:
        return _model, _tokenizer

    hf_home = _check_hf_home()

    try:
        import torch
        from transformers import AutoModelForCausalLM, AutoTokenizer
    except ImportError as e:
        raise RuntimeError(
            "FAILED to import torch/transformers. Activate the venv set "
            "up per phase2/HPC_RTLCODER_COMMANDS.md (pip install -r "
            "requirements first) before running this adapter. "
            f"Underlying error: {type(e).__name__}: {e}"
        ) from e

    try:
        tokenizer = AutoTokenizer.from_pretrained(model_id)
        model = AutoModelForCausalLM.from_pretrained(
            model_id, torch_dtype=torch.float16, device_map=device_map,
        )
    except Exception as e:
        raise RuntimeError(
            f"FAILED to load {model_id} (HF_HOME={hf_home!r}). "
            "The most likely cause on HPC: this is the login node, which "
            "has no internet access, and the weights are not yet cached "
            "under HF_HOME. Fix: download the weights first, either (a) "
            "via an sbatch job on a compute node with internet, or (b) "
            "on your laptop + `scp` the HF_HOME cache directory over -- "
            "both documented in phase2/HPC_RTLCODER_COMMANDS.md. Do NOT "
            "retry blindly; this adapter will not silently fall back to "
            "an empty or randomly-initialized model. "
            f"Underlying error: {type(e).__name__}: {e}"
        ) from e

    model.eval()
    _model, _tokenizer = model, tokenizer
    return model, tokenizer


def build_prompt(spec, module_name):
    """RTLCoder-Deepseek's native template: the spec text (RTLLM's
    design_description.txt is already written in this exact "Please act
    as a professional verilog designer. ... Give me the complete code."
    shape) followed by an open module header stub for the model to
    complete. `spec` is used verbatim -- callers should pass the raw
    design_description.txt content, not a reformatted version."""
    spec = spec.rstrip()
    return f"{spec}\n\nmodule {module_name}(\n"


def _extract_stub(prompt):
    """Recovers the literal "module <name>(\\n" header stub build_prompt()
    appended to the tail of the prompt. RTLCoder is trained to COMPLETE
    that stub, not re-emit it -- generate_raw() slices the prompt off in
    token space, which correctly removes the English spec text but also
    removes this stub, since it's part of the same prompt. The stub is
    genuinely part of the answer (the module header), so it has to be
    rejoined onto the completion, not discarded.

    rfind(), not a right-anchored regex on the whole prompt: an earlier
    RTLLM spec by convention writes "Module name:" capitalized, so it
    won't collide with lowercase "module " -- but rfind() finds the LAST
    occurrence regardless, which by construction of build_prompt() is
    always the real stub, so this is robust even if some future spec
    text happens to contain the word "module" verbatim somewhere in its
    body."""
    idx = prompt.rfind("module ")
    if idx == -1 or not re.match(r"module\s+\w+\s*\(", prompt[idx:]):
        raise ValueError(
            "generate(): could not find a 'module <name>(' stub at the "
            "tail of the prompt. This rejoin step assumes the prompt was "
            "built by build_prompt() -- a differently-shaped prompt "
            "(e.g. a future harness-SYSTEM_PROMPT-formatted variant, see "
            "the module docstring's open decision) isn't supported here "
            "without updating this function too."
        )
    return prompt[idx:]


def postprocess(raw_output):
    """Cleans up a reassembled (stub + completion) module. Started as
    RTLCoder-Deepseek's own documented cleanup, copied verbatim from
    github.com/hkust-zhiyao/RTL-Coder's README (2026-08-22) -- the model
    does not stop cleanly at the end of the intended module, it keeps
    generating past it. This is NOT the stitch_runner.py fence-marker
    fix; it's a separate, model-specific extraction path for a raw
    completion model, not a chat model.

    Only ever needs to worry about TRAILING junk -- generate_raw() now
    slices the prompt off in token space before this ever sees the text,
    so there is no corresponding leading-junk case to strip here.

    FIX 2026-08-22 (third real HPC smoke test failure, check (c) FAILED
    a third way): the inherited logic branched on whether the overrun
    was the documented "endmodulemodule" no-separator glom -- if so,
    split there; if not, `rsplit("endmodule", 1)`, splitting at the LAST
    "endmodule" in the whole text. That fallback assumed a NOT-glommed
    overrun meant the model stopped after exactly one module. On this
    real run it didn't: the overrun was cleanly separator-delimited
    ("endmodule\n  module counter_32 (...) ... endmodule\n  module
    adder_8 (...)"), no "endmodulemodule" substring anywhere, so it hit
    the rsplit fallback -- which then dragged counter_32 AND adder_8
    into the "extracted" code, because rsplit(..., 1) on the LAST
    occurrence keeps everything before it, including every module in
    between.

    Replaced with a single first-occurrence cut instead of branching on
    which pattern occurred: take everything up to and including the
    FIRST "endmodule" in the text. This handles both patterns with one
    rule, because "endmodule" is a literal substring of "endmodulemodule"
    too -- the first occurrence of "endmodule" lands at the intended
    module's real closing boundary either way, glommed or
    separator-delimited."""
    idx = raw_output.find("endmodule")
    if idx == -1:
        # No "endmodule" anywhere -- e.g. generation was truncated
        # before the module closed (max_new_tokens too low, or the
        # model just ran long). Nothing to cut cleanly; return the raw
        # text stripped, so downstream checks see the real, incomplete
        # output rather than a fabricated "endmodule" papering over it.
        return raw_output.strip()
    s = raw_output[:idx + len("endmodule")]

    if "top_module" in s:
        s = s.split("top_module", 1)[0].rsplit("endmodule", 1)[0] + "\nendmodule"

    index = s.rfind("tb_module") if "tb_module" in s else s.find("testbench")
    if index != -1:
        s = s[:index].rsplit("endmodule", 1)[0] + "\nendmodule"

    return s.strip()


def generate_raw(prompt, max_new_tokens=1024, temperature=0.5, top_p=0.9):
    """Runs the model and returns ONLY the newly generated text -- the
    prompt is sliced off in TOKEN space before decoding, never decoded
    at all. Exposed separately from generate() so the smoke test can
    show raw vs. postprocessed side by side (Task 2c).

    FIX 2026-08-22 (real HPC smoke test failure, check (d) FAILED):
    this used to decode `sample[0]` whole (prompt + completion) and rely
    on postprocess() to clean it up -- but postprocess() only ever
    strips TRAILING junk (the endmodulemodule quirk etc.), it never
    stripped the LEADING prompt text, so the .v file written to disk was
    literally "Please act as a professional verilog designer...` +
    Verilog, and iverilog failed at line 1 on the English. Matches
    RTLCoder's own inference script's approach: slice
    `sample[0][input_ids.shape[1]:]` off in token space before decoding,
    so the prompt is structurally never in the output to begin with --
    not "strip it after the fact" which is what silently failed here.

    Same fix also covers a second real failure from the same log:
    decoding without `skip_special_tokens=True` left DeepSeek's literal
    `<|begin_of_sentence|>` token as text at the start of the output.

    Also raises the generation cap: `max_length=512` (counts the PROMPT
    too) was cutting real modules off mid-statement
    (`valid_out <= 1'b` then truncated) even before extraction. Now
    `max_new_tokens=1024`, which counts only the completion. And sets
    `attention_mask` + `pad_token_id` explicitly (the HPC .err log
    warned about both being left to a default) -- DeepSeek-based
    checkpoints commonly have no `pad_token_id` set at all, which
    `generate()` will warn about, or silently reuse `eos_token_id` in a
    way that isn't guaranteed reliable across transformers versions."""
    import torch
    model, tokenizer = load_model()
    if tokenizer.pad_token_id is None:
        tokenizer.pad_token_id = tokenizer.eos_token_id

    enc = tokenizer(prompt, return_tensors="pt").to(model.device)
    with torch.no_grad():
        sample = model.generate(
            input_ids=enc.input_ids,
            attention_mask=enc.attention_mask,
            max_new_tokens=max_new_tokens,
            temperature=temperature, top_p=top_p, do_sample=True,
            pad_token_id=tokenizer.pad_token_id,
        )
    new_tokens = sample[0][enc.input_ids.shape[1]:]
    return tokenizer.decode(new_tokens, skip_special_tokens=True)


def generate(prompt, max_new_tokens=1024, temperature=0.5, top_p=0.9):
    """generate(prompt) -> code. The harness-facing entry point: runs
    generation, REJOINS the module header stub build_prompt() put at the
    end of the prompt, then runs this model's own postprocessing --
    returning a complete module starting with "module <name>(" and
    ending at the first "endmodule", directly usable Verilog (unlike
    stitch_runner.call_llm(), which returns raw chat text and leaves
    fence extraction to the caller -- RTLCoder needs its own non-fence
    extraction, so that step lives here instead).

    FIX 2026-08-22 (second real HPC smoke test failure, check (c) FAILED
    the opposite way this time): generate_raw()'s prompt slice correctly
    removes the English spec text, but it ALSO removes the
    "module <name>(" stub -- RTLCoder is trained to complete that stub,
    not re-emit it, so the raw completion genuinely starts at
    "input clk," with no module header at all. That's not a model
    problem; the header is real, it's just sitting in the prompt half,
    not the completion half. Rejoin it here, where build_prompt()'s
    contract (always ends the prompt with the stub) is known, rather
    than guessing at it from the model's output."""
    raw = generate_raw(prompt, max_new_tokens=max_new_tokens, temperature=temperature, top_p=top_p)
    stub = _extract_stub(prompt)
    return postprocess(stub + raw)
