"""
phase_e_replay.py — Phase E: interpreter-only replay against saved .v files
from the OLD (pre-fix) sweep. No LLM calls, no iverilog/vvp re-runs.

For every sem_adv iteration file already on disk (v20 suite, all 5 complete
local models, deduped to the authoritative source_path via
phase1_consolidated.json), re-run ONLY:
  1. run_verilator_lint on the saved .v (deterministic, no sampling)
  2. the OLD (pre-fix) interpret_verilator logic, hand-reproduced exactly as
     it existed before Fix 1/2 — NOT imported from any current file, since
     the deprecated subfolder copy was already patched before the two-file
     duplication was discovered and no longer reflects pre-fix behavior.
  3. the NEW (fixed) interpret_verilator from stitch_interpreter.py

...and diffs the two directive texts. This holds the LLM-generated code
completely constant, so any difference is attributable ONLY to the
interpreter fix — no resampling confound, unlike Phase C.
"""

import json
import re
import subprocess
from pathlib import Path
import importlib.util

REPO = Path(r"D:\BITS Files\Year 3\3-2\LLM_Verilog Project\AgenticAI")
CONSOLIDATED = REPO / "AutoChipAdvFB" / "STITCHAdv" / "res" / "phase1_consolidated.json"

# ── NEW (fixed) interpreter — the real, current shared module ────────────────
spec = importlib.util.spec_from_file_location("stitch_interpreter", REPO / "AutoChipAdvFB" / "stitch_interpreter.py")
new_mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(new_mod)
NEW_VERILATOR_INTERP = new_mod._VERILATOR_INTERP  # same table, both old/new use it — only extraction/UNDRIVEN logic changed


# ── OLD (pre-fix) interpreter — hand-reproduced exactly, not imported ───────
# This is byte-for-byte what interpret_verilator looked like before any of
# Phase A's fixes, verified against the diff taken when the fix was applied.
def old_interpret_verilator(raw_out):
    if not raw_out or raw_out.startswith("("):
        return "", []
    blocks, codes = [], []
    for code, make_msg in NEW_VERILATOR_INTERP.items():
        if code not in raw_out:
            continue
        codes.append(code)
        sig = "the_signal"
        for line in raw_out.splitlines():
            if code in line:
                m = re.search(r"['\"]([A-Za-z_]\w*)['\"]", line)
                if not m:
                    m = re.search(r":\s*([A-Za-z_]\w*)\s*$", line)
                if m:
                    sig = m.group(1)
                    break
        blocks.append(make_msg(sig))
    return "\n\n".join(blocks), codes


def run_verilator(v_path):
    wsl_path = "/mnt/d" + str(v_path)[2:].replace("\\", "/")
    cmd = ["wsl", "timeout", "18", "verilator", "--lint-only", "-Wall", "--bbox-unsup",
           "-Wno-DECLFILENAME", "-Wno-TIMESCALEMOD", "-Wno-EOFNEWLINE", wsl_path]
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=25)
    except subprocess.TimeoutExpired:
        return "(timeout)"
    output = result.stdout + result.stderr
    kept = [s.strip() for s in output.splitlines() if s.strip()
            and "... Use" not in s and "... For warning" not in s
            and (s.strip().startswith("%Warning") or s.strip().startswith("%Error") or s.strip().startswith("..."))]
    return "\n".join(kept) if kept else "(no warnings)"


def is_placeholder_or_fabricated(sig, raw_out, code, source_text):
    """Was this OLD extraction actually trustworthy, or junk?
    Trustworthy = real identifier that appears in the source file."""
    if sig == "the_signal":
        return "placeholder"
    if not source_text:
        return "unknown (no source)"
    if re.search(r"\b" + re.escape(sig) + r"\b", source_text):
        return "real"
    return "fabricated"


def main():
    data = json.loads(CONSOLIDATED.read_text(encoding="utf-8"))
    cells = [r for r in data if r["suite"] == "v20" and r["condition"] == "sem_adv"]
    print(f"{len(cells)} (model, module) cells to replay (v20, sem_adv)")

    all_iters = []
    per_bucket = {"identical_directive": [], "fix_declined_junk": [], "fix_reclassified": [],
                  "fix_newly_extracted": [], "fix_now_declines_where_old_extracted": []}
    no_warnings_count = 0
    total_replayed = 0

    for cell in cells:
        model, module = cell["model"], cell["module"]
        project_dir = Path(cell["source_path"]).parent
        iter_dirs = sorted(project_dir.glob("iter_*"), key=lambda p: int(p.name.split("_")[1]))

        for iter_dir in iter_dirs:
            v_files = [f for f in iter_dir.glob("*.v") if not f.name.endswith("_tb.v")
                       and f.name == f"{module}.v"]
            if not v_files:
                continue
            v_path = v_files[0]
            source_text = v_path.read_text(encoding="utf-8", errors="ignore")

            raw_out = run_verilator(v_path)
            total_replayed += 1
            if raw_out.startswith("(") or not raw_out.strip():
                no_warnings_count += 1
                continue

            old_text, old_codes = old_interpret_verilator(raw_out)
            new_text, new_codes = new_mod.interpret_verilator(raw_out, str(v_path))

            iter_num = int(iter_dir.name.split("_")[1])
            record = {"model": model, "module": module, "iter": iter_num,
                      "old_codes": old_codes, "new_codes": new_codes,
                      "old_text": old_text, "new_text": new_text, "notes": []}

            if old_text == new_text:
                per_bucket["identical_directive"].append(record)
                all_iters.append((record, "identical_directive"))
                continue

            # Per-code breakdown to detect what actually happened
            regression = False
            reclassified = False
            declined_junk = False
            newly_extracted = False

            for code in set(old_codes) | set(new_codes):
                in_old, in_new = code in old_codes, code in new_codes
                # recover the old sig for this code by re-running the same extraction logic
                old_sig = "the_signal"  # matches old_interpret_verilator's own default
                for line in raw_out.splitlines():
                    if code in line:
                        m = re.search(r"['\"]([A-Za-z_]\w*)['\"]", line)
                        if not m:
                            m = re.search(r":\s*([A-Za-z_]\w*)\s*$", line)
                        if m:
                            old_sig = m.group(1)
                            break  # only stop once a match is actually found, same as
                                   # old_interpret_verilator itself — a Verilator code can
                                   # appear on multiple lines (e.g. 4 separate COMBDLY hits),
                                   # and the real function keeps scanning past a non-matching
                                   # one instead of giving up on the first line.
                trust = is_placeholder_or_fabricated(old_sig, raw_out, code, source_text)

                if code == "UNDRIVEN" and in_old and in_new:
                    old_trust = is_placeholder_or_fabricated(old_sig, raw_out, code, source_text)
                    if old_trust == "real":
                        # Old's signal was legitimate — did the NEW disambiguation logic
                        # actually change the advice, or just reword an equivalent Path A?
                        classification = new_mod._classify_undriven_signal(old_sig, source_text)
                        if classification != "output_port":
                            reclassified = True
                            record["notes"].append(
                                f"UNDRIVEN on '{old_sig}': old gave blanket 'add an assignment' "
                                f"advice (assumes declared output); new correctly classifies as "
                                f"'{classification}' and gives different, source-grounded guidance")
                        # else: same classification (output_port both times) -> cosmetic wording
                        # difference only, not a real reclassification; no bucket assigned here.
                    else:
                        # old's UNDRIVEN signal was itself placeholder/fabricated — this is a
                        # newly_extracted case (old had garbage), not a real reclassification.
                        newly_extracted = True
                        record["notes"].append(
                            f"UNDRIVEN: old signal '{old_sig}' was {old_trust}; new re-extracted "
                            f"and correctly classified it")
                elif in_old and not in_new:
                    if trust == "real":
                        regression = True
                        record["notes"].append(f"REGRESSION: code={code} old_sig='{old_sig}' (verified real, appears in source) but NEW declined it")
                    else:
                        declined_junk = True
                        record["notes"].append(f"DECLINED: code={code} old_sig='{old_sig}' ({trust}) -- new correctly declined")
                elif not in_old and in_new:
                    newly_extracted = True
                    record["notes"].append(f"NEW: code={code} -- interpreter now fires where old never matched this code at all")
                elif in_old and in_new and trust == "placeholder":
                    newly_extracted = True
                    record["notes"].append(f"code={code}: old used placeholder 'the_signal'; new extracted a real signal")

            if regression:
                bucket = "fix_now_declines_where_old_extracted"
            elif reclassified:
                bucket = "fix_reclassified"
            elif declined_junk:
                bucket = "fix_declined_junk"
            elif newly_extracted:
                bucket = "fix_newly_extracted"
            else:
                # Text differed but nothing matched a specific category — almost certainly a
                # cosmetic-only Path-A wording difference (see UNDRIVEN handling above). Flag
                # for manual inspection rather than silently mislabeling as "identical".
                bucket = "identical_directive"
                record["notes"].append("QA FLAG: old_text != new_text but no specific fix category "
                                        "matched (likely cosmetic-only wording change) -- check manually")

            per_bucket[bucket].append(record)
            all_iters.append((record, bucket))

    out = {
        "total_iterations_replayed": total_replayed,
        "no_warnings_count": no_warnings_count,
        "bucket_counts": {k: len(v) for k, v in per_bucket.items()},
        "buckets": per_bucket,
    }
    out_path = Path(__file__).resolve().parent.parent / "res" / "phase_e_raw.json"
    out_path.write_text(json.dumps(out, indent=2), encoding="utf-8")

    print(f"\nTotal iterations replayed (had verilator warnings): {total_replayed - no_warnings_count}")
    print(f"Iterations with no verilator warnings at all (skipped, not categorized): {no_warnings_count}")
    print(f"Total .v files examined: {total_replayed}")
    print("\nBucket counts:")
    for k, v in out["bucket_counts"].items():
        print(f"  {k:<45} {v}")
    print(f"\nRaw data -> {out_path}")


if __name__ == "__main__":
    main()
