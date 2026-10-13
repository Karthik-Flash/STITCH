"""
rtllm_task_a_screen.py — RTLLM v2.1 pilot, TASK A: batch compatibility
screen. Not a STITCH run -- no LLM involved. For each of the 50 RTLLM
designs, copies its whole design directory to a scratch working dir,
renames the module the reference file declares (module verified_XXXX ->
module <design>, matching whatever the testbench actually instantiates --
two designs have a filename/module-name mismatch, handled by extracting
the real module name via regex rather than assuming
verified_<design>.v/module verified_<design>), compiles the renamed
reference plus testbench.v under real iverilog+vvp (WSL), and records
pass/fail/compile-error per design. This is what tells us the actually-
usable pool before Task B picks anything.

Requires: WSL (Icarus Verilog only -- no Ollama, no LLM calls; this
screens the REFERENCE solutions, not model output).
Produced: the Task A compatibility table -- see
phase1/results/rtllm_pilot/task_a_screen.json for the raw per-design
record and phase1/RTLLM_PILOT_PREREG.md for the summary this fed into.

Usage: python phase1/rtllm_task_a_screen.py
"""
import json
import os
import re
import shutil
import subprocess
import sys

_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(_HERE, "..", "src", "interpreter"))
# FIX 2026-08-24 (Bug #3 class): this screen used to carry its own THIRD
# independent hardcoded pass check (`"Your Design Passed" in sim_out`) --
# correct for RTLLM (unlike stitch_runner's original check), but still a
# separate implementation that could silently drift from the other two.
# Routed through the same shared detect_outcome() everything else now
# uses. See src/interpreter/pass_detection.py.
from pass_detection import detect_outcome  # noqa: E402

RTLLM_ROOT = os.environ.get("RTLLM_ROOT") or os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "RTLLM"))
CATEGORIES = ["Arithmetic", "Control", "Memory", "Miscellaneous"]

SCRATCH_ROOT = os.path.join(_HERE, "results", "rtllm_pilot", "task_a_screen")
OUT_JSON = os.path.join(_HERE, "results", "rtllm_pilot", "task_a_screen.json")

_MODULE_RE = re.compile(r"\bmodule\s+(verified_[A-Za-z0-9_]+)\b")


def win_to_wsl(win_path):
    p = os.path.abspath(win_path).replace("\\", "/")
    if len(p) > 1 and p[1] == ":":
        p = f"/mnt/{p[0].lower()}" + p[2:]
    return p


def discover_designs():
    """Returns [(category, design_name, abs_dir_path), ...] for all 50."""
    designs = []
    for cat in CATEGORIES:
        cat_dir = os.path.join(RTLLM_ROOT, cat)
        for sub in sorted(os.listdir(cat_dir)):
            sub_dir = os.path.join(cat_dir, sub)
            if not os.path.isdir(sub_dir):
                continue
            for design in sorted(os.listdir(sub_dir)):
                design_dir = os.path.join(sub_dir, design)
                if os.path.isdir(design_dir) and os.path.exists(
                    os.path.join(design_dir, "testbench.v")
                ):
                    designs.append((cat, design, design_dir))
    return designs


def screen_one(category, design, design_dir):
    scratch = os.path.join(SCRATCH_ROOT, design)
    if os.path.exists(scratch):
        shutil.rmtree(scratch)
    shutil.copytree(design_dir, scratch)

    verified_files = [f for f in os.listdir(scratch) if f.startswith("verified_") and f.endswith(".v")]
    if len(verified_files) != 1:
        return {
            "category": category, "design": design,
            "status": "error", "reason": f"expected exactly 1 verified_*.v, found {verified_files}",
        }
    vfile = verified_files[0]
    vpath = os.path.join(scratch, vfile)
    with open(vpath, encoding="utf-8", errors="replace") as f:
        content = f.read()

    filename_mismatch = (vfile != f"verified_{design}.v")

    # Three naming patterns observed across the 50 designs:
    #   1. module verified_<design>  -- the common case, needs a rename.
    #   2. module verified_<something else entirely> (2 designs: the file
    #      itself is misnamed too, e.g. verified_booth4_mul.v declaring
    #      verified_multi_booth_8bit) -- rename whatever verified_XXXX
    #      name is actually declared, not an assumed one.
    #   3. module <design> already, no "verified_" prefix on the module
    #      at all (the filename has the prefix, the module doesn't) --
    #      no rename needed, use the file as-is.
    already_bare = re.search(r"\bmodule\s+" + re.escape(design) + r"\b", content)
    if already_bare:
        actual_module_name = design
        module_name_matches_design = True
        renamed = content
    else:
        m = _MODULE_RE.search(content)
        if not m:
            return {
                "category": category, "design": design,
                "status": "error",
                "reason": f"module name in {vfile} is neither '{design}' nor a 'verified_*' pattern -- needs manual inspection",
            }
        actual_module_name = m.group(1)
        module_name_matches_design = (actual_module_name == f"verified_{design}")
        renamed = content.replace(actual_module_name, design)

    design_v_path = os.path.join(scratch, f"{design}.v")
    with open(design_v_path, "w", encoding="utf-8") as f:
        f.write(renamed)
    if os.path.exists(vpath) and vfile != f"{design}.v":
        os.remove(vpath)

    data_files = [
        f for f in os.listdir(scratch)
        if f not in ("testbench.v", "makefile", "design_description.txt", f"{design}.v")
    ]

    wsl_dir = win_to_wsl(scratch)
    compile_cmd = ["wsl", "bash", "-lc", f"cd '{wsl_dir}' && iverilog -o sim.vvp {design}.v testbench.v"]
    try:
        comp = subprocess.run(compile_cmd, capture_output=True, text=True, timeout=30)
    except subprocess.TimeoutExpired:
        return {
            "category": category, "design": design, "status": "compile_timeout",
            "actual_module_name": actual_module_name, "filename_mismatch": filename_mismatch,
            "module_name_matches_design": module_name_matches_design, "data_files": data_files,
        }

    if comp.returncode != 0:
        return {
            "category": category, "design": design, "status": "compile_error",
            "compile_stderr": (comp.stdout + comp.stderr).strip()[:2000],
            "actual_module_name": actual_module_name, "filename_mismatch": filename_mismatch,
            "module_name_matches_design": module_name_matches_design, "data_files": data_files,
        }

    sim_cmd = ["wsl", "bash", "-lc", f"cd '{wsl_dir}' && vvp sim.vvp"]
    try:
        sim = subprocess.run(sim_cmd, capture_output=True, text=True, timeout=30)
    except subprocess.TimeoutExpired:
        return {
            "category": category, "design": design, "status": "sim_timeout",
            "actual_module_name": actual_module_name, "filename_mismatch": filename_mismatch,
            "module_name_matches_design": module_name_matches_design, "data_files": data_files,
        }

    sim_out = sim.stdout + sim.stderr
    passed = detect_outcome(sim_out, "rtllm") == "PASS"
    return {
        "category": category, "design": design,
        "status": "pass" if passed else "sim_fail",
        "sim_output_tail": sim_out.strip()[-1000:],
        "actual_module_name": actual_module_name, "filename_mismatch": filename_mismatch,
        "module_name_matches_design": module_name_matches_design, "data_files": data_files,
    }


def main():
    designs = discover_designs()
    print(f"Discovered {len(designs)} designs.")
    results = []
    for i, (cat, design, design_dir) in enumerate(designs, 1):
        print(f"[{i}/{len(designs)}] {cat} / {design}", end=" ... ")
        r = screen_one(cat, design, design_dir)
        print(r["status"])
        results.append(r)

    os.makedirs(os.path.dirname(OUT_JSON), exist_ok=True)
    with open(OUT_JSON, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2)

    n_pass = sum(1 for r in results if r["status"] == "pass")
    print(f"\n{n_pass}/{len(results)} pass clean. Full detail -> {OUT_JSON}")


if __name__ == "__main__":
    main()
