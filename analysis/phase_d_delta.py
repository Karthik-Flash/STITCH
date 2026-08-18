"""
phase_d_delta.py — Phase D: compute the old-vs-fixed-interpreter delta for
the 18 Phase C cells.

Per-cell columns: model | module | old regime | new regime | old pass |
new pass | old semantic_fired | new semantic_fired | transition category

Transition category (the semantic_fired-semantics addition):
  - "genuine"     : regime changed (or codes changed) for a real behavioral
                    reason — the interpreter produced meaningfully different
                    output that changed something.
  - "definitional": semantic_fired flipped from >0 to 0 (or vice versa)
                    PURELY because the extractor now correctly declines to
                    fabricate a name it used to fabricate — with the
                    underlying baseline/sem_adv pass-fail outcome unchanged.
                    Not an improvement or a regression; a measurement fix.
  - "unchanged"   : nothing differs between old and new for this cell.

Also separately counts cells where semantic_fired changed from >0 to 0 due
to the extraction-failure skip, independent of whether that also changed
the regime — per the brief, "count these separately from harmful/enabling/
no_change movement."
"""

import json
from pathlib import Path

REPO = Path(r"D:\BITS Files\Year 3\3-2\LLM_Verilog Project\AgenticAI")
OLD_DATA = json.loads((REPO / "AutoChipAdvFB" / "STITCHAdv" / "res" / "phase1_consolidated.json").read_text(encoding="utf-8"))
NEW_ROOT = REPO / "AutoChipAdvFB" / "STITCHAdv" / "runs" / "v2_fixes_20260816_030703" / "v20"

CELLS = [
    ("llama3.1:latest",     "full_adder",        "harmful"),
    ("llama3.1:latest",     "simple_cpu_alu",    "harmful"),
    ("llama3.1:latest",     "sync_fifo_8",       "harmful"),
    ("llama3.1:latest",     "gray_counter_4bit", "unexplained_variance"),
    ("deepseek-coder:6.7b", "counter_4bit",      "harmful"),
    ("deepseek-coder:6.7b", "pipeline_mult_4x4", "harmful"),
    ("deepseek-coder:6.7b", "ripple_carry_adder","harmful"),
    ("deepseek-coder:6.7b", "sync_fifo_8",       "harmful"),
    ("deepseek-coder:6.7b", "alu_8bit",          "unexplained_variance"),
    ("deepseek-coder:6.7b", "full_adder",        "unexplained_variance"),
    ("deepseek-coder:6.7b", "pwm_generator",     "unexplained_variance"),
    ("gemma3:4b", "alu_8bit",        "control_stale_label"),
    ("gemma3:4b", "spi_master_8bit", "control_stale_label"),
    ("deepseek-coder:6.7b", "spi_master_8bit",   "control_fired_no_effect"),
    ("deepseek-coder:6.7b", "gray_counter_4bit", "control_fired_no_effect"),
    ("gemma3:4b",           "lfsr_8bit",         "control_fired_no_effect"),
    ("llama3.1:latest",     "alu_8bit",          "control_fired_no_effect"),
    ("deepseek-coder:6.7b", "fsm_seq_detector",  "control_fired_no_effect"),
]


def regime(base_pass, sem_pass, sem_fired):
    flipped = base_pass != sem_pass
    fired = sem_fired > 0
    if flipped and fired:
        return "harmful" if (base_pass and not sem_pass) else "enabling"
    if flipped and not fired:
        return "unexplained_variance"
    if not flipped and fired:
        return "fired_no_effect"
    return "no_change_pass" if base_pass else "no_change_fail"


def load_old(model, module):
    base = next((r for r in OLD_DATA if r["suite"] == "v20" and r["model"] == model
                 and r["module"] == module and r["condition"] == "baseline"), None)
    sem = next((r for r in OLD_DATA if r["suite"] == "v20" and r["model"] == model
                and r["module"] == module and r["condition"] == "sem_adv"), None)
    return base, sem


def load_new(model, module):
    safe = model.replace(":", "_").replace(".", "")
    base_f = NEW_ROOT / safe / "baseline" / module / "metrics.json"
    sem_f = NEW_ROOT / safe / "sem_adv" / module / "metrics.json"
    base = json.loads(base_f.read_text(encoding="utf-8")) if base_f.exists() else None
    sem = json.loads(sem_f.read_text(encoding="utf-8")) if sem_f.exists() else None
    return base, sem


def main():
    rows = []
    definitional_sf_change_count = 0
    genuine_change_count = 0

    print(f"{'model':<22} {'module':<20} {'old_regime':<22} {'new_regime':<22} "
          f"{'old_p':<6} {'new_p':<6} {'old_sf':<7} {'new_sf':<7} {'base_drift':<11} category")
    print("-" * 160)

    for model, module, reason in CELLS:
        old_base, old_sem = load_old(model, module)
        new_base, new_sem = load_new(model, module)
        if not all([old_base, old_sem, new_base, new_sem]):
            print(f"  MISSING DATA: {model}/{module}")
            continue

        old_r = regime(old_base["pass"], old_sem["pass"], old_sem.get("semantic_fired", 0) or 0)
        new_r = regime(new_base["pass"], new_sem["pass"], new_sem.get("semantic_fired", 0) or 0)

        base_drift = old_base["pass"] != new_base["pass"]  # baseline is regenerated fresh too
        old_sf = old_sem.get("semantic_fired", 0) or 0
        new_sf = new_sem.get("semantic_fired", 0) or 0

        sf_dropped_to_zero = old_sf > 0 and new_sf == 0
        sf_appeared = old_sf == 0 and new_sf > 0
        outcome_unchanged = (old_base["pass"] == new_base["pass"]) and (old_sem["pass"] == new_sem["pass"])

        if (sf_dropped_to_zero or sf_appeared) and old_r != new_r:
            definitional_sf_change_count += 1

        if old_r == new_r and old_sem["pass"] == new_sem["pass"] and not base_drift:
            category = "unchanged"
        elif (sf_dropped_to_zero or sf_appeared) and outcome_unchanged:
            category = "definitional"
        else:
            category = "genuine"
            genuine_change_count += 1

        rows.append(dict(model=model, module=module, reason=reason,
                          old_regime=old_r, new_regime=new_r,
                          old_pass=old_sem["pass"], new_pass=new_sem["pass"],
                          old_sf=old_sf, new_sf=new_sf,
                          base_drift=base_drift, category=category))

        print(f"{model:<22} {module:<20} {old_r:<22} {new_r:<22} "
              f"{str(old_sem['pass']):<6} {str(new_sem['pass']):<6} {old_sf:<7} {new_sf:<7} "
              f"{str(base_drift):<11} {category}")

    print("\n" + "=" * 90)
    print("SUMMARY — bucket counts, old sweep vs v2-fixed sweep (18 cells)")
    print("=" * 90)
    buckets = ["harmful", "enabling", "unexplained_variance", "fired_no_effect", "no_change_pass", "no_change_fail"]
    old_counts = {b: sum(1 for r in rows if r["old_regime"] == b) for b in buckets}
    new_counts = {b: sum(1 for r in rows if r["new_regime"] == b) for b in buckets}
    print(f"{'bucket':<24} {'old':>5} {'new':>5} {'delta':>7}")
    for b in buckets:
        d = new_counts[b] - old_counts[b]
        print(f"{b:<24} {old_counts[b]:>5} {new_counts[b]:>5} {d:>+7}")

    print(f"\nCells where semantic_fired flipped >0<->0 AND regime changed as a result "
          f"(pure measurement-definition change, not real interpreter-behavior change): "
          f"{definitional_sf_change_count}")
    print(f"Cells with a genuine behavioral change (category='genuine'): {genuine_change_count}")
    print(f"Cells flagged 'genuine' but ALSO show baseline drift (confounded — old vs new sweep "
          f"resampled baseline independently, so some of the apparent change may be baseline "
          f"sampling variance, not the interpreter fix):")
    for r in rows:
        if r["category"] == "genuine" and r["base_drift"]:
            print(f"  {r['model']}/{r['module']}: baseline flipped "
                  f"{'FAIL->PASS' if not r['old_pass'] else 'result'} — treat this cell's "
                  f"delta with extra caution")

    out_path = Path(__file__).resolve().parent.parent / "res" / "phase_d_delta.json"
    out_path.write_text(json.dumps(rows, indent=2), encoding="utf-8")
    print(f"\nFull per-cell table written -> {out_path}")


if __name__ == "__main__":
    main()
