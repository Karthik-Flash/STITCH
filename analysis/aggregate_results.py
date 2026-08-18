"""
aggregate_results.py — consolidate STITCH run results into one clean CSV/JSON.

Walks one or more run-root folders, finds every metrics.json written by
autochip_stitch_runner.run_one_condition (path shape:
  <run_root>/<suite>/<safe_model>/<condition>/<module>/metrics.json
), and merges them into a single table. If the same (suite, model, condition,
module) combo appears in more than one run root (e.g. an old nightly_* run
and a newer resume_* run), the newest metrics.json (by mtime) wins — pass
--prefer to force a specific run root to always win instead.

No manual JSON copy-pasting needed: point this at STITCHAdv/runs (the
default) and it picks up every run folder underneath automatically.

Usage:
  python aggregate_results.py
  python aggregate_results.py --runs runs\resume_20260814_135236 runs\nightly_20260814_012758
  python aggregate_results.py --prefer runs\resume_20260814_135236
  python aggregate_results.py --out combined
"""

import argparse
import csv
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
DEFAULT_RUNS_DIR = HERE / "runs"

FIELDS = [
    "suite", "model", "condition", "module", "pass", "iterations_to_pass",
    "time_to_pass_sec", "total_time_sec", "total_iterations",
    "compile_errors", "sim_errors", "latch_warnings", "verilator_catches",
    "semantic_fired", "total_prompt_tokens", "total_completion_tokens",
    "total_tokens", "run_root", "metrics_path", "mtime",
]


def find_metrics_files(run_roots: list[Path]) -> list[Path]:
    found = []
    for root in run_roots:
        if not root.exists():
            print(f"  WARNING: run root not found, skipping: {root}")
            continue
        found.extend(root.rglob("metrics.json"))
    return found


def load_row(path: Path, run_root: Path) -> dict | None:
    try:
        m = json.loads(path.read_text(encoding="utf-8"))
    except Exception as e:
        print(f"  WARNING: could not parse {path}: {e}")
        return None

    # suite is the path component directly under the run root
    try:
        rel = path.relative_to(run_root)
        suite = rel.parts[0]
    except ValueError:
        suite = "unknown"

    row = {k: m.get(k) for k in FIELDS if k in m}
    row["suite"] = suite
    row["run_root"] = str(run_root)
    row["metrics_path"] = str(path)
    row["mtime"] = path.stat().st_mtime
    for k in FIELDS:
        row.setdefault(k, None)
    return row


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--runs", nargs="*", default=None,
                         help="Run-root folders to scan (default: every folder under STITCHAdv/runs)")
    parser.add_argument("--prefer", default=None,
                         help="If a combo exists in multiple run roots, always prefer this one over mtime")
    parser.add_argument("--out", default=str(HERE / "res" / "combined_results"),
                         help="Output path prefix (writes <out>.csv and <out>.json)")
    args = parser.parse_args()

    if args.runs:
        run_roots = [Path(r).resolve() for r in args.runs]
    else:
        if not DEFAULT_RUNS_DIR.exists():
            raise SystemExit(f"No --runs given and default runs dir missing: {DEFAULT_RUNS_DIR}")
        run_roots = sorted(p for p in DEFAULT_RUNS_DIR.iterdir() if p.is_dir())

    print(f"Scanning {len(run_roots)} run root(s):")
    for r in run_roots:
        print(f"  - {r}")

    prefer_root = str(Path(args.prefer).resolve()) if args.prefer else None

    files = find_metrics_files(run_roots)
    print(f"Found {len(files)} metrics.json file(s)")

    best: dict[tuple, dict] = {}
    for f in files:
        run_root = next((r for r in run_roots if r in f.resolve().parents), None)
        if run_root is None:
            continue
        row = load_row(f, run_root)
        if row is None:
            continue

        key = (row["suite"], row["model"], row["condition"], row["module"])
        existing = best.get(key)
        if existing is None:
            best[key] = row
            continue

        if prefer_root:
            if row["run_root"] == prefer_root and existing["run_root"] != prefer_root:
                best[key] = row
            # else keep existing (either existing is preferred, or neither is)
        elif row["mtime"] > existing["mtime"]:
            best[key] = row

    rows = sorted(best.values(), key=lambda r: (r["suite"], r["model"], r["condition"], r["module"]))

    out_csv = Path(f"{args.out}.csv")
    out_json = Path(f"{args.out}.json")

    with out_csv.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDS)
        writer.writeheader()
        for row in rows:
            writer.writerow(row)

    out_json.write_text(json.dumps(rows, indent=2), encoding="utf-8")

    print(f"\nWrote {len(rows)} unique (suite, model, condition, module) rows")
    print(f"  -> {out_csv}")
    print(f"  -> {out_json}")

    # quick pass-rate summary per model/suite/condition
    summary: dict[tuple, list] = {}
    for row in rows:
        key = (row["suite"], row["model"], row["condition"])
        summary.setdefault(key, []).append(row["pass"])

    print("\nPass rate summary:")
    for key in sorted(summary):
        passes = summary[key]
        n_pass = sum(1 for p in passes if p)
        print(f"  {key[0]:>4} | {key[1]:<22} | {key[2]:<10} | {n_pass}/{len(passes)} passed")


if __name__ == "__main__":
    main()
