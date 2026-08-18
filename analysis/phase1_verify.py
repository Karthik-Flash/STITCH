"""
phase1_verify.py — fresh, from-scratch rebuild of the new-sweep results table.

Scope: ONLY the new sweep under AutoChipAdvFB/STITCHAdv/runs/**. This
deliberately excludes the old conference-era result trees found elsewhere
in the repo (AutoChipAdvFB/results_stitch, results_v2, storeandmisc,
AutoChipFinalTEST/results, AutoChipTEST/results, AutoChipTEST/hpc_results_final,
AutoChipAdvFB/AutoChipSTITCH ad-hoc runs) — those are the single-run,
pre-STITCHAdv data the paper's R1 variance complaint is about, not the new
evidence being built here. They are reported separately for visibility, not merged.

Does NOT read or trust combined_results.csv/json from any prior run — walks
every metrics.json under STITCHAdv/runs fresh, every time.
"""

import json
from collections import defaultdict
from pathlib import Path

REPO = Path(__file__).resolve().parents[3]  # .../AgenticAI
STITCHADV_RUNS = REPO / "AutoChipAdvFB" / "STITCHAdv" / "runs"

LEGACY_DIRS = [
    REPO / "AutoChipAdvFB" / "results_stitch",
    REPO / "AutoChipAdvFB" / "results_v2",
    REPO / "AutoChipAdvFB" / "storeandmisc",
    REPO / "AutoChipAdvFB" / "AutoChipSTITCH",
    REPO / "AutoChipFinalTEST" / "results",
    REPO / "AutoChipTEST" / "results",
    REPO / "AutoChipTEST" / "hpc_results_final",
]

FOUR_COMPLETE_V20_MODELS = ["gemma3:4b", "gemma3:12b", "qwen2.5-coder:14b", "llama3.1:latest"]


def load_all():
    files = list(STITCHADV_RUNS.rglob("metrics.json"))
    run_roots = sorted({f.relative_to(STITCHADV_RUNS).parts[0] for f in files})

    best = {}
    skipped = 0
    for f in files:
        try:
            m = json.loads(f.read_text(encoding="utf-8"))
        except Exception as e:
            print(f"  WARNING: unparseable {f}: {e}")
            skipped += 1
            continue
        rel = f.relative_to(STITCHADV_RUNS)
        suite = rel.parts[1]  # <run_root>/<suite>/<model>/<condition>/<module>/metrics.json
        key = (suite, m["model"], m["condition"], m["module"])
        mtime = f.stat().st_mtime
        if key not in best or mtime > best[key][1]:
            best[key] = (m, mtime, str(f))
    return files, run_roots, best, skipped


def main():
    files, run_roots, best, skipped = load_all()

    print(f"Run roots under STITCHAdv/runs: {run_roots}")
    print(f"Total metrics.json under STITCHAdv/runs: {len(files)} (skipped unparsable: {skipped})")
    print(f"Unique (suite, model, condition, module) rows after de-dup: {len(best)}")

    print("\n--- Legacy/other result trees found (NOT included above, listed for awareness only) ---")
    for d in LEGACY_DIRS:
        if d.exists():
            n = len(list(d.rglob("metrics.json")))
            print(f"  {d.relative_to(REPO)}: {n} metrics.json")
        else:
            print(f"  {d.relative_to(REPO)}: (does not exist)")

    print("\n--- Counts per (suite, model, condition) in the new sweep ---")
    counts = defaultdict(int)
    for (suite, model, cond, module), (m, mtime, path) in best.items():
        counts[(suite, model, cond)] += 1
    for key in sorted(counts):
        print(f"  {key[0]:>4} | {key[1]:<22} | {key[2]:<10} | n={counts[key]}")

    # ---- Numbers 1: aggregate pass rate by condition across the 4 complete v20 models ----
    print("\n=== NUMBER 1: aggregate pass rate by condition, v20, across the 4 complete models ===")
    for cond in ["baseline", "raw_adv", "sem_adv"]:
        total = 0
        passed = 0
        per_model = []
        for model in FOUR_COMPLETE_V20_MODELS:
            rows = [(k, v) for k, v in best.items() if k[0] == "v20" and k[1] == model and k[2] == cond]
            n = len(rows)
            p = sum(1 for k, (m, mt, path) in rows if m["pass"])
            per_model.append((model, p, n))
            total += n
            passed += p
        pct = 100.0 * passed / total if total else float("nan")
        print(f"  {cond:<10}: {passed}/{total} = {pct:.1f}%   " + ", ".join(f"{mo}={p}/{n}" for mo, p, n in per_model))

    # ---- Numbers 2: per-model regime breakdown ----
    # CORRECTED definition (per user direction after Phase 1 review): a regime label of
    # harmful/enabling requires semantic_fired > 0 for that module-run — the interpreter
    # must have actually engaged for STITCH to be attributable as the cause. An outcome
    # flip (base PASS/FAIL != sem_adv PASS/FAIL) with semantic_fired == 0 is NOT harmful
    # or enabling — it's unexplained single-run variance and is counted separately.
    # Unchanged outcomes are split into fired_no_effect (interpreter fired, no change)
    # vs no_change (interpreter never fired, no change).
    print("\n=== NUMBER 2 (CORRECTED): per-model regime breakdown, v20 (baseline vs sem_adv), gated on semantic_fired>0 ===")
    for model in FOUR_COMPLETE_V20_MODELS:
        base = {k[3]: v[0] for k, v in best.items() if k[0] == "v20" and k[1] == model and k[2] == "baseline"}
        sem = {k[3]: v[0] for k, v in best.items() if k[0] == "v20" and k[1] == model and k[2] == "sem_adv"}
        modules = sorted(set(base) & set(sem))
        harmful, enabling, fired_no_effect, unexplained_variance = [], [], [], []
        no_change_pass, no_change_fail = 0, 0
        for mod in modules:
            b, s = base[mod]["pass"], sem[mod]["pass"]
            fired = sem[mod].get("semantic_fired", 0) and sem[mod]["semantic_fired"] > 0
            flipped = b != s
            if flipped and fired:
                (harmful if (b and not s) else enabling).append(mod)
            elif flipped and not fired:
                unexplained_variance.append(mod)
            elif not flipped and fired:
                fired_no_effect.append(mod)
            elif not flipped and not fired:
                if b:
                    no_change_pass += 1
                else:
                    no_change_fail += 1
        print(f"\n  {model} (n_modules={len(modules)}, missing from either side: {sorted(set(base) ^ set(sem)) or 'none'})")
        print(f"    harmful             (flip + fired, base PASS->sem FAIL): {len(harmful)}  {harmful}")
        print(f"    enabling            (flip + fired, base FAIL->sem PASS): {len(enabling)}  {enabling}")
        print(f"    unexplained_variance(flip + NOT fired)                 : {len(unexplained_variance)}  {unexplained_variance}")
        print(f"    fired_no_effect     (fired, no flip)                   : {len(fired_no_effect)}  {fired_no_effect}")
        print(f"    no_change_pass: {no_change_pass}   no_change_fail: {no_change_fail}")

    # ---- Number 3: llama3.1 interpreter-fired -> outcome ----
    print("\n=== NUMBER 3: llama3.1:latest — modules where interpreter fired under sem_adv, and outcome ===")
    sem = {k[3]: v[0] for k, v in best.items() if k[0] == "v20" and k[1] == "llama3.1:latest" and k[2] == "sem_adv"}
    fired = {mod: m for mod, m in sem.items() if m.get("semantic_fired", 0) and m["semantic_fired"] > 0}
    fired_fail = {mod: m for mod, m in fired.items() if not m["pass"]}
    fired_pass = {mod: m for mod, m in fired.items() if m["pass"]}
    print(f"  Total v20 modules for llama3.1:latest sem_adv: {len(sem)}")
    print(f"  Modules where interpreter fired (semantic_fired>0): {len(fired)}  -> {sorted(fired)}")
    print(f"    of those, FAIL: {len(fired_fail)}  -> {sorted(fired_fail)}")
    print(f"    of those, PASS: {len(fired_pass)}  -> {sorted(fired_pass)}")

    # dump the fresh consolidated table for downstream phases
    out_rows = []
    for (suite, model, cond, module), (m, mtime, path) in sorted(best.items()):
        row = dict(m)
        row["suite"] = suite
        row["source_path"] = path
        out_rows.append(row)
    out_path = Path(__file__).resolve().parent.parent / "res" / "phase1_consolidated.json"
    out_path.write_text(json.dumps(out_rows, indent=2), encoding="utf-8")
    print(f"\nFresh consolidated table written -> {out_path}")


if __name__ == "__main__":
    main()
