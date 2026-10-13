"""Set 4 statistics: (model, module)-cell bootstrap CI and sign-flip p, as used for the
Set 1 / Set 3 lines of phase3/evidence/phase3_run/POSTHOC_CHECKS.md (prereg Amendment A4).

phase3/runner/posthoc_checks.py imports boot_ci/signflip_p from analyze_phase3.py, which this
task may not read, so these are reimplementations. `python stats_set4.py` checks them against
all 12 published Set 1 / Set 3 numbers; analysis_set4.py refuses to run unless that check passes.
"""
import json
import math
import os
import zlib
from collections import defaultdict

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
PHASE2 = os.path.dirname(HERE)


def sg(x):
    return f"{x:+.1f}"


def fp(p):
    return "<0.001" if p < 0.001 else f"{p:.3f}"


def wilson(k, n, z=1.959963984540054):
    if n == 0:
        return (None, None)
    p = k / n
    den = 1 + z * z / n
    c = (p + z * z / (2 * n)) / den
    h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / den
    return c - h, c + h


# Copied verbatim from phase3/runner/analyze_phase3.py (read-only, prereg A9): SEED/BOOT/PERM,
# _rng, signflip_p, and boot_ci (boot_ci sat inside the permitted read window; it replaces an
# earlier reimplementation that matched the published CIs only at one-decimal precision).
SEED, BOOT, PERM = 20260925, 10000, 20000


def _rng(label):
    return np.random.default_rng([SEED, zlib.crc32(label.encode())])


def boot_ci(vals, label):
    v = np.asarray(vals, float)
    if len(v) == 0:
        return float("nan"), float("nan")
    m = v[_rng("ci:" + label).integers(0, len(v), (BOOT, len(v)))].mean(1)
    return float(np.percentile(m, 2.5)), float(np.percentile(m, 97.5))


def signflip_p(d, label):
    d = np.asarray(d, float)
    if not np.any(d):
        return 1.0
    s = _rng("p:" + label).choice([-1.0, 1.0], size=(PERM, len(d)))
    return float((1 + np.sum(np.abs((s * d).mean(1)) >= abs(d.mean()) - 1e-12)) / (PERM + 1))


PUBLISHED = {  # POSTHOC_CHECKS.md, "## phase2"
    ("set1_run", "sem_adv"): ("-4.6", "-10.5", "+0.7", "0.199"),
    ("set1_run", "sem_escalate"): ("-4.7", "-10.7", "+0.0", "0.148"),
    ("set1_run", "sem_escalate_restart"): ("-0.0", "-4.6", "+4.6", "1.000"),
    ("set3_run", "sem_adv"): ("-0.7", "-7.8", "+6.5", "1.000"),
    ("set3_run", "sem_escalate"): ("+2.6", "-1.3", "+7.2", "0.404"),
    ("set3_run", "sem_escalate_restart"): ("+2.0", "-2.6", "+7.2", "0.596"),
}


def published_diffs():
    cats = json.load(open(os.path.join(PHASE2, "twin_analysis_SET2", "module_categories.json")))
    band = {m for m, v in cats.items() if v["difficulty_tier"] == "recoverable"}
    out = {}
    for name in ("set1_run", "set3_run"):
        rows = [e for e in json.load(open(os.path.join(PHASE2, "results", name, "master_log.json")))
                if not e.get("error") and e["module"] in band]
        cell = defaultdict(lambda: defaultdict(list))
        for e in rows:
            cell[(e["model"], e["module"])][e["condition"]].append(int(bool(e["pass"])))
        for a in ("sem_adv", "sem_escalate", "sem_escalate_restart"):
            d = {k: v for k, v in cell.items() if v[a] and v["baseline"]}
            out[(name, a)] = [100 * (sum(v[a]) / len(v[a]) - sum(v["baseline"]) / len(v["baseline"]))
                              for _, v in sorted(d.items())]
    return out


def verify():
    ok = True
    for (name, a), (m, lo, hi, p) in PUBLISHED.items():
        d = published_diffs()[(name, a)]
        l, h = boot_ci(d, f"p2:{name}:{a}")
        gp = fp(signflip_p(d, f"p2:{name}:{a}"))
        got = (sg(sum(d) / len(d)), sg(l), sg(h), gp)
        match = got == (m, lo, hi, p)
        ok &= match
        print(f"{name} {a}: published {m} [{lo}, {hi}] p={p} | reproduced {got[0]} [{got[1]}, {got[2]}] p={got[3]}"
              f" {'OK' if match else 'MISMATCH'}")
    print("ALL REPRODUCED" if ok else "NOT REPRODUCED")
    return ok


if __name__ == "__main__":
    raise SystemExit(0 if verify() else 1)
