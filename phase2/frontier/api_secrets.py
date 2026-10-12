"""Key loader for Set 4. Named api_secrets.py, not secrets.py: a file called
secrets.py next to the runner would shadow the stdlib `secrets` module for
every library imported after it.

Order: process env vars win, else the env file. The env file is
$STITCH_KEYS_FILE, else ~/.stitch/api_keys.env, else (under WSL)
/mnt/c/Users/*/.stitch/api_keys.env.
"""
import glob
import os

NAMES = ("OPENAI_API_KEY", "ANTHROPIC_API_KEY", "MOONSHOT_API_KEY", "GEMINI_API_KEY")
PROVIDER_ENV = {"openai": "OPENAI_API_KEY", "anthropic": "ANTHROPIC_API_KEY",
                "moonshot": "MOONSHOT_API_KEY", "gemini": "GEMINI_API_KEY"}


def _env_file():
    cands = [os.environ.get("STITCH_KEYS_FILE", ""),
             os.path.join(os.path.expanduser("~"), ".stitch", "api_keys.env")]
    cands += sorted(glob.glob("/mnt/c/Users/*/.stitch/api_keys.env"))
    return next((c for c in cands if c and os.path.exists(c)), None)


def load():
    keys = {}
    path = _env_file()
    if path:
        with open(path, encoding="utf-8") as f:
            for line in f:
                if "=" in line and not line.lstrip().startswith("#"):
                    k, v = line.rstrip("\r\n").split("=", 1)
                    if k.strip() in NAMES and v.strip():
                        keys[k.strip()] = v.strip()
    for n in NAMES:
        if os.environ.get(n):
            keys[n] = os.environ[n]
    return keys


def key_for(provider):
    k = load().get(PROVIDER_ENV[provider])
    if not k:
        raise RuntimeError(f"no key loaded for provider {provider!r}")
    return k


def redact(text):
    """Replace every loaded key value in `text` with [REDACTED]."""
    text = str(text)
    for v in load().values():
        text = text.replace(v, "[REDACTED]")
    return text
