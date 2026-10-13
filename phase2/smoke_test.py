"""
phase2/smoke_test.py -- RTLCoder-Deepseek-v1.1 adapter smoke test.

Proves, on ONE golden RTLLM module, that all four trivial-failure points
are defended BEFORE any real benchmark run:
  (a) MODEL LOADS      -- weights present, model+tokenizer load cleanly,
                           or fail loudly with a clear fix instead of
                           silently producing an empty/garbage model.
  (b) GENERATION WORKS  -- a real prompt produces real, non-empty output.
  (c) POSTPROCESSING WORKS -- raw vs. postprocessed shown side by side,
                           so the endmodulemodule split can be eyeballed,
                           not just trusted.
  (d) COMPILE + MODULE-NAME -- the postprocessed code declares the module
                           name the testbench instantiates, and iverilog
                           compiles it. This is the exact contract that
                           silently broke RTLLM before (phase1 pilot).

Run this on HPC (see docs/HPC_COMMANDS.md) -- it needs the
real model loaded via transformers and a GPU (or CPU, slow but same code
path). Native-Linux only: HPC compute nodes run Linux directly, so this
calls iverilog/vvp as plain subprocesses -- no WSL wrapper, unlike
stitch_runner.py's Windows-specific invocation.

This does NOT run a benchmark. It runs the pipeline exactly once, end to
end, on one already-screened-compatible module, and reports pass/fail on
each of the four checks above. If any check fails, it stops there and
says which -- it does not proceed to declare the adapter working.

Usage: python phase2/smoke_test.py [--module accu] [--rtllm-root PATH]
Exit code 0 iff all four checks pass.
"""
import argparse
import os
import re
import shutil
import subprocess
import sys

_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, _HERE)
import rtlcoder_adapter as rc  # noqa: E402

# RTLLM is never copied into this repo (same policy as phase1) -- read
# live from wherever it's checked out on HPC. No default baked in beyond
# the env var / --rtllm-root override; there is no "correct" scratch
# username to assume here.
DEFAULT_RTLLM_ROOT = os.environ.get("RTLLM_ROOT", os.path.expandvars("/scratch/$USER/RTLLM"))
MODULE_REL = {"accu": "Arithmetic/Accumulator/accu"}

RESULTS_DIR = os.path.join(_HERE, "results", "rtlcoder_smoke")


def _progress(n, total, label, status):
    print(f"[{n}/{total}] {label} -- {status}")


def check_model_loads():
    print("\n=== (a) MODEL LOADS ===")
    try:
        model, tokenizer = rc.load_model()
        print(f"  OK: {rc.MODEL_ID} loaded, device={model.device}")
        return True
    except Exception as e:
        # rc.load_model() already wraps load errors in a loud, actionable
        # RuntimeError (no-internet-on-login-node etc.) -- just surface it.
        print(f"  FAIL: {e}")
        return False


def check_generation(prompt):
    print("\n=== (b) GENERATION WORKS ===")
    try:
        raw = rc.generate_raw(prompt)
    except Exception as e:
        print(f"  FAIL: {type(e).__name__}: {e}")
        return False, None
    # FIX 2026-08-22: generate_raw() now slices the prompt off in TOKEN
    # space before decoding (see rtlcoder_adapter.py's fix note) -- `raw`
    # is already just the new content, no more prompt-stripping needed
    # or possible here.
    ok = len(raw.strip()) > 0
    print(f"  {'OK' if ok else 'FAIL'}: {len(raw)} chars of newly "
          f"generated content decoded")
    return ok, raw


def _starts_clean(code):
    """First non-empty, non-comment line should open the file, not
    trail behind leftover prompt text or a special token -- skips blank
    lines and `//` line comments, then requires `module` or a
    `` `timescale `` directive."""
    for line in code.splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("//"):
            continue
        return stripped.startswith("module") or stripped.startswith("`timescale")
    return False


def check_postprocessing(raw, code):
    """`raw` is generate_raw()'s output -- prompt-sliced but WITHOUT the
    module-header stub rejoined, shown here for human inspection only.
    `code` is generate()'s real return value (stub-rejoined +
    postprocessed) and is what actually gets validated below, since
    that's the function the real benchmark calls.

    FIX 2026-08-22 (fourth real HPC smoke test failure): this used to
    call rc.postprocess(raw) directly here, which bypasses generate()'s
    stub rejoin entirely. `raw` alone has no module header -- RTLCoder is
    trained to COMPLETE the "module <name>(" stub, not re-emit it -- so
    postprocess(raw) always started at whatever port line the model
    generated first (e.g. "input clk,"), not "module accu(". That wasn't
    a postprocessing bug; generate() itself (rtlcoder_adapter.py) was
    already correct. This smoke test just wasn't calling it -- it was
    checking a path the real benchmark never takes."""
    print("\n=== (c) POSTPROCESSING WORKS ===")
    print("  --- RAW generate_raw() output (last 600 chars, human inspection")
    print("      only -- this is prompt-sliced but has NOT had the module-header")
    print("      stub rejoined, so it will not look like a complete module by")
    print("      itself; that's expected, it isn't what gets validated) ---")
    print("  " + raw[-600:].replace("\n", "\n  "))
    print("  --- generate() OUTPUT (stub-rejoined + postprocessed -- THIS is")
    print("      the real, harness-facing value being validated) ---")
    print("  " + code.replace("\n", "\n  "))
    ok_ends = code.strip().endswith("endmodule") and re.search(r"\bmodule\s+\w+", code) is not None
    # FIX 2026-08-22: this used to only check the END of the output --
    # it passed on a real HPC run whose extraction still had the ENTIRE
    # prompt text sitting in front of the code, because "ends with
    # endmodule and contains a module decl" is true of "<prompt text>
    # module foo(...); ... endmodule" too. Check (d)'s iverilog compile
    # then failed at line 1 on the English -- a check (c) should have
    # caught. Now also requires the first non-empty, non-comment line to
    # actually BE the module (or a `timescale directive ahead of it),
    # so prompt-contaminated or special-token-contaminated extraction
    # fails HERE instead of silently reaching check (d).
    ok_starts = _starts_clean(code)
    ok = ok_ends and ok_starts
    if not ok_starts:
        reason = ("the first non-empty, non-comment line is NOT `module`/`timescale "
                   "-- looks like leftover prompt text or a stray special token is "
                   "still attached ahead of the real code (inspect the POSTPROCESSED "
                   "block above)")
    elif not ok_ends:
        reason = "does not end with endmodule / no module declaration found"
    else:
        reason = "starts cleanly with module/timescale and ends with endmodule"
    print(f"  {'OK' if ok else 'FAIL'}: postprocessed code {reason}")
    return ok


def check_compile(code, module_name, module_dir, deps):
    print("\n=== (d) COMPILE + MODULE-NAME ===")
    if not re.search(r"\bmodule\s+" + re.escape(module_name) + r"\b", code):
        print(f"  FAIL: postprocessed code does not declare "
              f"'module {module_name}' -- the testbench instantiates "
              f"'{module_name}' by that exact bare name; a mismatch fails "
              f"every run regardless of logic. This is the precise bug "
              f"that zeroed out several RTLLM modules in the phase1 "
              f"pilot before it was diagnosed.")
        return False

    work_dir = os.path.join(RESULTS_DIR, module_name)
    os.makedirs(work_dir, exist_ok=True)
    with open(os.path.join(work_dir, f"{module_name}.v"), "w", encoding="utf-8") as f:
        f.write(code)
    shutil.copy(os.path.join(module_dir, "testbench.v"), os.path.join(work_dir, "testbench.v"))
    for dep in deps:
        shutil.copy(dep, os.path.join(work_dir, os.path.basename(dep)))

    v_files = [f for f in sorted(os.listdir(work_dir)) if f.endswith(".v")]
    vvp_out = os.path.join(work_dir, "sim.vvp")
    try:
        comp = subprocess.run(["iverilog", "-o", vvp_out] + v_files,
                               cwd=work_dir, capture_output=True, text=True, timeout=30)
    except subprocess.TimeoutExpired:
        print("  FAIL: iverilog did not finish in 30s")
        return False
    except FileNotFoundError:
        print("  FAIL: `iverilog` not found on PATH -- load the EDA "
              "toolchain module or check the sbatch script's environment.")
        return False
    if comp.returncode != 0:
        print(f"  FAIL: iverilog compile error:\n  {comp.stderr}")
        return False
    print("  OK: compiled cleanly (module-name contract holds)")

    try:
        sim = subprocess.run(["vvp", os.path.basename(vvp_out)],
                              cwd=work_dir, capture_output=True, text=True, timeout=35)
    except subprocess.TimeoutExpired:
        print("  FAIL: vvp did not finish in 35s")
        return False
    print("  Simulation ran. Output (last 400 chars) -- pass/fail on THIS "
          "specific generation is a separate question from this smoke "
          "test; the model output used here is whatever it happened to "
          "generate, not curated to pass:")
    print("  " + sim.stdout[-400:].replace("\n", "\n  "))
    return True


def _report(results):
    print("\n=== CHECKLIST ===")
    labels = {
        "a_model_loads": "(a) MODEL LOADS",
        "b_generation": "(b) GENERATION WORKS",
        "c_postprocessing": "(c) POSTPROCESSING WORKS",
        "d_compile": "(d) COMPILE + MODULE-NAME",
    }
    for key, label in labels.items():
        status = "PASS" if results.get(key) else ("FAIL" if key in results else "NOT RUN")
        print(f"  [{status}] {label}")
    if len(results) == len(labels) and all(results.values()):
        print("\nAll four checks passed. Adapter is ready for a real run.")
    else:
        print("\nAt least one check failed or was not reached -- do NOT "
              "proceed to a real benchmark run until this is green.")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--module", default="accu", choices=list(MODULE_REL))
    parser.add_argument("--rtllm-root", default=DEFAULT_RTLLM_ROOT)
    args = parser.parse_args()

    module_dir = os.path.join(args.rtllm_root, MODULE_REL[args.module])
    spec_path = os.path.join(module_dir, "design_description.txt")
    if not os.path.exists(spec_path):
        print(f"FATAL: {spec_path} not found -- pass --rtllm-root pointing "
              f"at a real RTLLM checkout (see docs/HPC_COMMANDS.md).")
        sys.exit(1)
    with open(spec_path, encoding="utf-8") as f:
        spec = f.read()
    deps = [os.path.join(module_dir, f) for f in os.listdir(module_dir)
            if f not in ("testbench.v", "makefile", "design_description.txt")
            and not f.startswith("verified_")]

    prompt = rc.build_prompt(spec, args.module)
    total = 4
    results = {}

    _progress(1, total, "model load", "running")
    results["a_model_loads"] = check_model_loads()
    _progress(1, total, "model load", "OK" if results["a_model_loads"] else "FAILED -- stopping")
    if not results["a_model_loads"]:
        _report(results)
        sys.exit(1)

    _progress(2, total, "generation", "running")
    ok_b, raw = check_generation(prompt)
    results["b_generation"] = ok_b
    _progress(2, total, "generation", "OK" if ok_b else "FAILED -- stopping")
    if not ok_b:
        _report(results)
        sys.exit(1)

    _progress(3, total, "postprocessing", "running")
    # Call generate() ONCE here -- the real, harness-facing function
    # (stub rejoin + postprocess), not a hand-reconstruction of its
    # logic. Checks (c) and (d) both validate/compile THIS SAME value,
    # so they agree on what's actually being tested (2026-08-22 fix --
    # see check_postprocessing()'s docstring for what this replaces).
    try:
        code = rc.generate(prompt)
    except Exception as e:
        print(f"\n=== (c) POSTPROCESSING WORKS ===\n  FAIL: generate() raised {type(e).__name__}: {e}")
        code, ok_c = None, False
    else:
        ok_c = check_postprocessing(raw, code)
    results["c_postprocessing"] = ok_c
    _progress(3, total, "postprocessing", "OK" if ok_c else "FAILED -- stopping")
    if not ok_c:
        _report(results)
        sys.exit(1)

    _progress(4, total, "compile + module-name", "running")
    results["d_compile"] = check_compile(code, args.module, module_dir, deps)
    _progress(4, total, "compile + module-name", "OK" if results["d_compile"] else "FAILED")

    _report(results)
    sys.exit(0 if all(results.values()) else 1)


if __name__ == "__main__":
    main()
