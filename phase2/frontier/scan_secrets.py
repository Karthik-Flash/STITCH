"""Grep the repo tree and the Set 4 results dir for the loaded key values.
Prints only match counts per path, never the keys. Exit 1 if any match.

Skips .git/ (history is audited separately with git log -S) and the key
env file itself, which lives outside the repo.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from api_secrets import load  # noqa: E402

REPO = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))
SKIP_DIRS = {".git", ".venv", "venv", "__pycache__", "node_modules"}
MAX_BYTES = 50_000_000


def main():
    keys = [v.encode() for v in load().values()]
    if not keys:
        sys.exit("no keys loaded; nothing to scan for")
    roots = [REPO]
    total, files = 0, 0
    for root in roots:
        for dirpath, dirnames, filenames in os.walk(root):
            dirnames[:] = [d for d in dirnames if d not in SKIP_DIRS]
            for fn in filenames:
                p = os.path.join(dirpath, fn)
                try:
                    if os.path.getsize(p) > MAX_BYTES:
                        continue
                    with open(p, "rb") as f:
                        data = f.read()
                except OSError:
                    continue
                files += 1
                n = sum(data.count(k) for k in keys)
                if n:
                    total += n
                    print(f"{n:4d}  {os.path.relpath(p, REPO)}")
    print(f"scanned {files} files under {REPO} (includes phase2/results/set4_api); "
          f"{len(keys)} keys; total matches: {total}")
    sys.exit(1 if total else 0)


if __name__ == "__main__":
    main()
