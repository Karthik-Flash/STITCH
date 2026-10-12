"""Step 0c leak audit over all git history (local + remote refs).
Prints commit IDs and counts only, never key text."""
import os
import subprocess
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from api_secrets import load  # noqa: E402


def log(*args):
    r = subprocess.run(["git", "log", "--all", "--format=%h", *args],
                       capture_output=True, text=True)
    return r.stdout.split()


print("stitch-api-key.txt in history:", len(log("--full-history", "--", "stitch-api-key.txt")))
for prefix in ("sk-proj-", "sk-ant-", "sk-", "AIza", "AQ."):
    c = log("-S" + prefix)
    print(f"prefix {prefix!r}: {len(c)} commits {c}")
leaked = 0
for name, value in load().items():
    c = log("-S" + value)
    leaked += len(c)
    print(f"{name} exact value: {len(c)} commits {c}")
print("LEAK STATUS:", "keys in history, rotate" if leaked else "clean")
