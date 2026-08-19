"""
phase2_reconstruct.py — reconstruct what llama3.1:latest actually saw and did,
iteration by iteration, for the 4 v20 modules flagged in the Phase 1 regime
breakdown (full_adder, simple_cpu_alu, sync_fifo_8, gray_counter_4bit).

The runner never persists verilator_out / yosys_report / the interpreter's
directive text to disk — only llm_response.txt (model output) and sim_log.txt
(iverilog result) survive per iteration. But it DOES persist the exact
generated <module>.v per iteration, and verilator/yosys are deterministic
static tools, so we re-run the SAME lint/synth calls the runner used on the
SAME saved .v file to reconstruct the exact directive text that would have
been built — and cross-check against metrics.json's recorded interp_codes
per iteration to confirm the reconstruction matches what actually fired.
"""

import importlib.util
import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[3]
# NOTE (frozen/historical script): this points at the DEPRECATED AutoChipSTITCH/
# copy of the runner, which is what was live when this reconstruction was
# originally done for the llama3.1 anomaly investigation. That copy's
# stitch_interpreter import is now intentionally broken (module moved to
# AutoChipAdvFB/stitch_interpreter.py — see AutoChipAdvFB/AutoChipSTITCH's own
# deprecation banner), so this script will NOT run as-is anymore. It is kept
# only as a record of exactly how phase2_reconstructed.json was produced; the
# findings are already written up in llama31_anomaly_notes.md and don't need
# to be regenerated. If this ever needs to run again, point RUNNER_PATH at
# AutoChipAdvFB/autochip_stitch_runner.py (the real, current runner) instead.
RUNNER_PATH = REPO / "AutoChipAdvFB" / "AutoChipSTITCH" / "autochip_stitch_runner.py"

spec = importlib.util.spec_from_file_location("stitch", RUNNER_PATH)
stitch = importlib.util.module_from_spec(spec)
sys.modules["stitch"] = stitch
spec.loader.exec_module(stitch)

RUN_ROOT = REPO / "AutoChipAdvFB" / "STITCHAdv" / "runs" / "resume_20260814_135236" / "v20" / "llama31_latest"
MODULES = ["full_adder", "simple_cpu_alu", "sync_fifo_8", "gray_counter_4bit"]
CONDITIONS = ["raw_adv", "sem_adv"]

OUT = Path(__file__).resolve().parent.parent / "res" / "phase2_reconstructed.json"


def reconstruct_module(module, condition):
    mod_dir = RUN_ROOT / condition / module
    metrics = json.loads((mod_dir / "metrics.json").read_text(encoding="utf-8"))
    iters_out = []

    iter_dirs = sorted(mod_dir.glob("iter_*"), key=lambda p: int(p.name.split("_")[1]))
    for idx, iter_dir in enumerate(iter_dirs):
        i = idx + 1
        v_file = iter_dir / f"{module}.v"
        llm_resp = (iter_dir / "llm_response.txt").read_text(encoding="utf-8", errors="replace") if (iter_dir / "llm_response.txt").exists() else ""
        code = v_file.read_text(encoding="utf-8", errors="replace") if v_file.exists() else ""

        recorded = next((d for d in metrics["per_iter_detail"] if d["iter"] == i), {})

        verilator_out, verilator_flag = stitch.run_verilator_lint(str(v_file))
        interp_text, interp_codes = ("", [])
        yosys_report, has_latches, latch_lines, cell_count = "(skipped)", False, [], 0
        if condition == "sem_adv" and verilator_flag:
            interp_text, interp_codes = stitch.interpret_verilator(verilator_out)

        row = {
            "iter": i,
            "result": recorded.get("result"),
            "err_type": recorded.get("err_type"),
            "recorded_interp_codes": recorded.get("interp_codes", []),
            "recorded_semantic_fired": recorded.get("semantic_fired"),
            "reconstructed_verilator_flag": verilator_flag,
            "reconstructed_verilator_out": verilator_out,
            "reconstructed_interp_codes": interp_codes,
            "reconstructed_interp_text": interp_text,
            "codes_match_recorded": sorted(interp_codes) == sorted(recorded.get("interp_codes", [])),
            "llm_response_has_code_fence": "```" in llm_resp,
            "llm_response_len": len(llm_resp),
            "code_len": len(code),
            "code": code,
            "llm_response_raw": llm_resp,
        }
        iters_out.append(row)

    return {
        "module": module, "condition": condition,
        "pass": metrics["pass"], "iterations_to_pass": metrics["iterations_to_pass"],
        "iters": iters_out,
    }


def main():
    all_data = []
    for module in MODULES:
        for condition in CONDITIONS:
            print(f"Reconstructing {module} / {condition} ...")
            all_data.append(reconstruct_module(module, condition))

    OUT.write_text(json.dumps(all_data, indent=2), encoding="utf-8")
    print(f"\nWrote {OUT}")

    # sanity check: did our reconstruction match what the runner actually recorded?
    print("\n--- Reconstruction sanity check (codes_match_recorded should be True everywhere) ---")
    mismatches = 0
    for entry in all_data:
        for it in entry["iters"]:
            if not it["codes_match_recorded"]:
                mismatches += 1
                print(f"  MISMATCH {entry['module']}/{entry['condition']} iter {it['iter']}: "
                      f"recorded={it['recorded_interp_codes']} reconstructed={it['reconstructed_interp_codes']}")
    if mismatches == 0:
        print("  All iterations match. Reconstruction is reliable.")
    else:
        print(f"  {mismatches} mismatches found — treat reconstructed directive text for those iterations with caution.")


if __name__ == "__main__":
    main()
