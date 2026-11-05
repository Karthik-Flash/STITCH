#!/usr/bin/env python3
"""Freeze manifest: sha256 (LF line endings) of every file that decides what the models are asked and how the answers
are judged. Written once before the first HPC job; any change afterwards means rerunning every arm on both models.

  specs/*.md, tasks/**, pipeline/*.py, hpc/hpc_env.sh, hpc/gen_job.slurm, the Phase 3 runner files the pipeline
  imports (stitch_runner_p3.py, p3_eval.py, system_prompt.txt) and the three src/interpreter modules.
Paths in FREEZE.sha256 are relative to the repository root, so `sha256sum -c` works from there on LF copies.

Usage: python pipeline/freeze.py            write FREEZE.sha256 (study folder)
       python pipeline/freeze.py --check    exit 1 if any listed file is missing or changed, or a file is unlisted
"""
import glob
import hashlib
import os
import sys

STUDY = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REPO = os.path.dirname(os.path.dirname(STUDY))
MANIFEST = os.path.join(STUDY, "FREEZE.sha256")


def files():
    s = lambda *p: glob.glob(os.path.join(STUDY, *p), recursive=True)  # noqa: E731
    out = s("specs", "*.md") + s("tasks", "**", "*") + s("pipeline", "*.py") + \
        [os.path.join(STUDY, "hpc", f) for f in ("hpc_env.sh", "gen_job.slurm")] + \
        [os.path.join(REPO, "phase3", "runner", f) for f in ("stitch_runner_p3.py", "p3_eval.py", "system_prompt.txt")] + \
        [os.path.join(REPO, "src", "interpreter", f) for f in ("stitch_interpreter.py", "stitch_interpreter_v3.py",
                                                                 "_v3_parsers.py")]
    return sorted(os.path.relpath(p, REPO).replace(os.sep, "/") for p in out if os.path.isfile(p))


def sha256_lf(rel):
    return hashlib.sha256(open(os.path.join(REPO, rel), "rb").read().replace(b"\r\n", b"\n")).hexdigest()


def check():
    """(number of listed files, problems)"""
    if not os.path.exists(MANIFEST):
        return 0, ["FREEZE.sha256 missing"]
    listed = dict(reversed(l.split("  ", 1)) for l in open(MANIFEST).read().splitlines() if l.strip())
    bad = [f"changed {p}" for p, h in listed.items() if not os.path.isfile(os.path.join(REPO, p)) or sha256_lf(p) != h]
    bad += [f"unlisted {p}" for p in files() if p not in listed]
    return len(listed), bad


if __name__ == "__main__":
    if "--check" in sys.argv:
        n, bad = check()
        print(f"freeze: {n} files, " + ("all unchanged" if not bad else "PROBLEMS:\n  " + "\n  ".join(bad)))
        sys.exit(1 if bad else 0)
    rows = [f"{sha256_lf(p)}  {p}" for p in files()]
    open(MANIFEST, "w", newline="\n").write("\n".join(rows) + "\n")
    print(f"wrote {MANIFEST}: {len(rows)} files")
