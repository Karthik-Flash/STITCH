"""Phase 3 API ladder rows under the sign-off oracle, in the format of Table 12 of paper/STITCH_EXT_v8.tex:
signoff_clean of 33 (sim-silent of 18 / sim-visible of 15) and tokens per run, per API model and condition.

Scored exactly as phase3/evidence/phase3_final/paper_numbers.py scores the API rows (load_many + apply_signoff from
phase3/runner/analyze_phase3.py, imported read-only), but against a COPY of phase3/evidence/signoff_cache.json kept
in phase2/results/p3_api/, so nothing under phase3/ is written. Before printing, the GPT-4.1 mini and Claude Haiku 4.5
rows are checked against the published Table 12.
  --score    simulate candidates missing from the cache against tb_signoff.v (WSL, matched 0.69 suite)
  --recheck  re-simulate every cached GPT/Haiku candidate into a scratch cache and compare verdicts (toolchain check)
Run in WSL:  bash p3_env.sh p3_signoff_ladder.py [--score] [--recheck]
"""
import argparse
import json
import os
import shutil
import sys
import tempfile
from collections import defaultdict

sys.dont_write_bytecode = True
HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(os.path.dirname(os.path.dirname(HERE)))
P3 = os.path.join(REPO, "phase3")
P3A = os.path.join(REPO, "phase2", "results", "p3_api")
TASKS = os.path.join(P3, "tasks")
CACHE = os.path.join(P3A, "signoff_cache.json")
OUT = os.path.join(P3A, "analysis", "p3_ladder_signoff.json")
if os.environ.get("STITCH_SET4_OSSCAD"):
    os.environ["PATH"] = os.path.join(os.environ["STITCH_SET4_OSSCAD"], "bin") + os.pathsep + os.environ["PATH"]
sys.path.insert(0, os.path.join(P3, "runner"))
import analyze_phase3 as A  # noqa: E402

C = ["baseline", "baseline_gate", "raw_adv", "sem_adv_v2", "sem_adv_v3", "sem_esc_restart_v3"]   # Table 12 row order
# Table 12 (tab:mpsoc-ladder): condition -> (signoff_clean of 33, sim-silent, sim-visible, tokens/run)
PUBLISHED = {
    "gpt-4.1-mini-2025-04-14": {"baseline": (12, 0, 12, 440), "baseline_gate": (28, 16, 12, 1529),
                                "raw_adv": (30, 18, 12, 1164), "sem_adv_v2": (30, 18, 12, 1255),
                                "sem_adv_v3": (30, 18, 12, 1257), "sem_esc_restart_v3": (30, 18, 12, 1404)},
    "claude-haiku-4-5-20251001": {"baseline": (12, 0, 12, 517), "baseline_gate": (30, 18, 12, 1099),
                                  "raw_adv": (30, 18, 12, 1334), "sem_adv_v2": (30, 18, 12, 1517),
                                  "sem_adv_v3": (30, 18, 12, 1524), "sem_esc_restart_v3": (30, 18, 12, 1101)},
}


def k(rs, key):
    return sum(bool(r[key]) for r in rs)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--score", action="store_true")
    ap.add_argument("--recheck", action="store_true")
    a = ap.parse_args()
    if not os.path.exists(CACHE):
        shutil.copy(os.path.join(P3, "evidence", "signoff_cache.json"), CACHE)
    dirs = [os.path.join(P3A, "full", p) for p in ("openai", "anthropic", "gemini") if os.path.isdir(os.path.join(P3A, "full", p))]
    runs, _, _ = A.load_many(dirs, TASKS)
    res = {"dirs": [os.path.relpath(d, REPO) for d in dirs]}

    if a.recheck:
        old = [r for r in runs if r["model"] in PUBLISHED]
        scratch = os.path.join(tempfile.mkdtemp(prefix="p3so_"), "cache.json")
        A.apply_signoff(old, TASKS, allow_sim=True, cache_path=scratch)
        new, ref = json.load(open(scratch)), json.load(open(CACHE))
        n = sum(len(v) for v in new.values())
        same = sum(ref.get(tb, {}).get(c) == v for tb, d in new.items() for c, v in d.items())
        res["recheck"] = {"candidates": n, "same_verdict": same}
        print(f"recheck: {same}/{n} GPT/Haiku candidates get the cached verdict on this toolchain")

    before = sum(len(v) for v in json.load(open(CACHE)).values())
    so, viol = A.apply_signoff(runs, TASKS, allow_sim=a.score, cache_path=CACHE)
    after = sum(len(v) for v in json.load(open(CACHE)).values())
    res.update(signoff_tb=so, superset_violations=viol, cache_entries_added=after - before)
    print(f"sign-off cache {os.path.relpath(CACHE, REPO)}: {before} -> {after} candidates; tb_signoff differs from tb.v on "
          f"{[t for t, v in so.items() if v != 'identical to tb.v']}; passing tb_signoff but failing tb.v: {viol}")

    prov = {f: sorted({str(r[f]) for r in runs}) for f in ("protocol", "interp_v3_version", "base_interp_sha256_lf",
                                                            "temperature", "max_iters", "sem_include_raw")}
    prov["runner"] = sorted({r["provenance"]["runner_sha256_lf"] for r in runs})
    prov["toolchain"] = sorted({json.dumps(r["provenance"]["toolchain"], sort_keys=True) for r in runs})
    res["provenance"] = prov
    print(f"provenance over {len(runs)} runs: {json.dumps(prov)}")

    models = [m for m in ("gpt-4.1-mini-2025-04-14", "claude-haiku-4-5-20251001", "gemini-2.5-flash")
              if any(r["model"] == m for r in runs)]
    table, extra = {}, {}
    for m in models:
        for c in C:
            rs = [r for r in runs if r["model"] == m and r["condition"] == c]
            sil, vi = [r for r in rs if r["silent"]], [r for r in rs if not r["silent"]]
            table[f"{m}|{c}"] = (k(rs, "signoff_clean"), k(sil, "signoff_clean"), k(vi, "signoff_clean"),
                                 round(sum(r["tokens"] for r in rs) / len(rs)) if rs else None)
            extra[f"{m}|{c}"] = {"n": len(rs), "n_silent": len(sil), "n_visible": len(vi),
                                 "clean_as_run": k(rs, "clean_pass"), "signed_off_defective": k(rs, "signed_off_defective"),
                                 "signed_off_defective_silent": k(sil, "signed_off_defective")}
    res["table12"], res["extra"] = table, extra
    ok = all(table.get(f"{m}|{c}") == v for m, row in PUBLISHED.items() for c, v in row.items())
    res["published_rows_reproduced"] = ok
    print(f"published Table 12 rows for GPT-4.1 mini and Claude Haiku 4.5 reproduced: {'YES' if ok else 'NO'}")

    print("\n| Condition | " + " | ".join(f"{m} clean | tokens" for m in models) + " |")
    print("|---|" + "---|---|" * len(models))
    for c in C:
        cells = []
        for m in models:
            t = table[f"{m}|{c}"]
            cells += [f"{t[0]} ({t[1]}/{t[2]})", f"{t[3]:,}"]
        print(f"| {c} | " + " | ".join(cells) + " |")
    print("\nclean of 33 (sim-silent of 18 / sim-visible of 15); tokens per run over all 33 runs")
    for key, e in extra.items():
        print(f"- {key}: n {e['n']} ({e['n_silent']}/{e['n_visible']}), as run clean {e['clean_as_run']}, signed off defective "
              f"{e['signed_off_defective']} (sim-silent {e['signed_off_defective_silent']})")
    na = defaultdict(int)
    for r in runs:
        if not r["signoff_clean"] and r["condition"] != "baseline":
            na[f"{r['model']} | {r['task']} | {r['condition']}"] += 1
    res["not_signoff_clean_non_baseline"] = dict(sorted(na.items()))
    print(f"- non-baseline runs not signoff_clean, by (model, task, condition): {res['not_signoff_clean_non_baseline']}")
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    json.dump(res, open(OUT, "w"), indent=1)
    if not ok:
        sys.exit("STOP: the published GPT-4.1 mini / Claude Haiku 4.5 rows are not reproduced")


if __name__ == "__main__":
    main()
