"""Move API keys out of the repo tree into %USERPROFILE%\\.stitch\\api_keys.env.

Reads <REPO_ROOT>\\stitch-api-key.txt ("#provider" line, then the key
line), writes the env file, restricts its ACL to the current user, verifies
the written file round-trips, and only then deletes the in-repo file.
Prints provider / key length / format verdict only. Never prints a key.
Run on Windows (native python), not WSL.
"""
import getpass
import os
import subprocess
import sys

SRC = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "stitch-api-key.txt")
DEST_DIR = os.path.join(os.environ["USERPROFILE"], ".stitch")
DEST = os.path.join(DEST_DIR, "api_keys.env")

# header keyword -> (env var, expected prefix)
PROVIDERS = [
    (("anthropic", "claude"), "ANTHROPIC_API_KEY", "sk-ant-"),
    (("openai", "gpt"), "OPENAI_API_KEY", "sk-"),
    (("moonshot", "kimi"), "MOONSHOT_API_KEY", "sk-"),
    (("gemini", "google"), "GEMINI_API_KEY", "AIza"),
]


def parse(path):
    keys, current = {}, None
    with open(path, encoding="utf-8-sig") as f:
        for raw in f:
            line = raw.strip()
            if not line:
                continue
            if line.startswith("#"):
                header = line.lstrip("#").strip().lower()
                current = next((env for words, env, _ in PROVIDERS
                                if any(w in header for w in words)), None)
                if current is None:
                    print(f"unrecognised provider header: {header!r}")
                continue
            if current and current not in keys:
                keys[current] = line
            current = None
    return keys


def parse_env(path):
    out = {}
    with open(path, encoding="utf-8") as f:
        for line in f:
            if "=" in line and not line.lstrip().startswith("#"):
                k, v = line.rstrip("\r\n").split("=", 1)
                out[k.strip()] = v.strip()
    return out


def main():
    if not os.path.exists(SRC):
        sys.exit(f"{SRC} not found (already moved?)")
    if os.path.exists(DEST) and "--force" not in sys.argv:
        sys.exit(f"{DEST} already exists; rerun with --force to overwrite")

    keys = parse(SRC)
    for _, env, prefix in PROVIDERS:
        v = keys.get(env)
        if v is None:
            print(f"{env:18s} MISSING")
            continue
        fmt = "format OK" if v.startswith(prefix) else "format unexpected"
        if env == "OPENAI_API_KEY" and v.startswith("sk-ant-"):
            fmt = "format unexpected (looks like an Anthropic key)"
        print(f"{env:18s} length {len(v):3d}  {fmt}")
        if env == "GEMINI_API_KEY" and not v.startswith("AIza"):
            print("  WARNING: Gemini entry does not start with 'AIza'. It may be an "
                  "OAuth/access token rather than an API key and could expire mid-run.")

    os.makedirs(DEST_DIR, exist_ok=True)
    with open(DEST, "w", encoding="utf-8", newline="\n") as f:
        for _, env, _ in PROVIDERS:
            if env in keys:
                f.write(f"{env}={keys[env]}\n")

    user = f"{os.environ.get('USERDOMAIN', '')}\\{getpass.getuser()}".lstrip("\\")
    r = subprocess.run(["icacls", DEST, "/inheritance:r", "/grant:r", f"{user}:F"],
                       capture_output=True, text=True)
    print(f"ACL restricted to {user}: {'OK' if r.returncode == 0 else 'FAILED rc=%d' % r.returncode}")
    if r.returncode != 0:
        sys.exit("ACL step failed; in-repo file NOT deleted")

    if parse_env(DEST) != keys:
        sys.exit("round-trip verification FAILED; in-repo file NOT deleted")
    os.remove(SRC)
    print(f"wrote {DEST} ({len(keys)} keys), verified, deleted in-repo file")


if __name__ == "__main__":
    main()
