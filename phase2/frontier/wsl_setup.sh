#!/bin/bash
# One-time: WSL venv for the Set 4 runner (the Set 3 engine imports `openai`
# for its Ollama client; the API backends themselves use only the stdlib).
set -e
VENV="$HOME/stitch_set4_venv"
[ -x "$VENV/bin/python" ] || python3 -m venv "$VENV"
"$VENV/bin/pip" install -q "openai>=1,<3"
"$VENV/bin/python" -c 'import openai, sys; print("venv OK", sys.version.split()[0], "openai", openai.__version__)'
