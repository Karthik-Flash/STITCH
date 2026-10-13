#!/usr/bin/env python3
"""T3: confirm the repo's MPSoC sources are the ones analysed (module bodies compared after comment stripping).
Usage (repo root): python phase3/runner/check_mpsoc_identity.py ["MPSoC/MPSoC Source Codes"]
Expected: only in repo ['test'] | only in ref [] | differing ['main', 'new1', 'nidepack']  -> exit 0"""
import glob, os, re, sys
root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
src = sys.argv[1] if len(sys.argv) > 1 else os.path.join(root, "MPSoC", "MPSoC Source Codes")
nocom = lambda s: re.sub(r"//[^\n]*|/\*.*?\*/", "", s.replace("\r", ""), flags=re.S)
def mods(files):
    return {m.group(1): re.sub(r"\s+", " ", m.group(0)).strip() for f in files
            for m in re.finditer(r"\bmodule\s+(\w+).*?\bendmodule", nocom(open(f, errors="ignore").read()), re.S)}
repo = mods(glob.glob(os.path.join(src, "**", "*.v"), recursive=True))
ref = mods(glob.glob(os.path.join(root, "phase3", "designs", "mpsoc_ref", "*.v")))
a, b = sorted(set(repo) - set(ref)), sorted(set(ref) - set(repo))
d = sorted(m for m in set(repo) & set(ref) if repo[m] != ref[m])
print("source:", src, "| modules repo/ref:", len(repo), len(ref))
print("only in repo:", a); print("only in ref:", b); print("differing bodies:", d)
ok = a == ["test"] and b == [] and d == ["main", "new1", "nidepack"]
print("T3:", "PASS" if ok else "FINDING"); sys.exit(0 if ok else 1)
