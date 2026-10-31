"""Study selection shared by every pipeline script.

--study {2x2, mesh3x3, ni} on the command line (removed from sys.argv before the script's own argparse runs), else
$STITCH_STUDY, else 2x2. The choice is exported to $STITCH_STUDY so child processes see the same study.
2x2 lives in the study root (frozen layout); the others in <root>/<name>/ with the same sub-folders.
"""
from __future__ import annotations

import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))     # SiliconComparision/llm_oneshot_vs_stitch
REPO = os.path.dirname(os.path.dirname(ROOT))
DIRS = {"2x2": ROOT, "mesh3x3": os.path.join(ROOT, "mesh3x3"), "ni": os.path.join(ROOT, "ni")}
# ORFS / mesh-tb top. ni_pair is a wrapper (new1 -> nidepack), not golden: never generated, never prompted.
TOPS = {"2x2": "top_2x2_router", "mesh3x3": "top_3x3_router", "ni": "ni_pair"}
# Roots of the golden hierarchy (the modules that are generated). NI has two: packetiser and depacketiser.
ROOTS = {"2x2": ["top_2x2_router"], "mesh3x3": ["top_3x3_router"], "ni": ["new1", "nidepack"]}
WRAPPERS = {"ni": ["ni_pair"]}


def _pick() -> str:
    name = os.environ.get("STITCH_STUDY") or "2x2"
    for i, a in enumerate(sys.argv[1:], 1):
        if a == "--study" and i + 1 < len(sys.argv):
            name = sys.argv[i + 1]
            del sys.argv[i:i + 2]
            break
        if a.startswith("--study="):
            name = a.split("=", 1)[1]
            del sys.argv[i]
            break
    if name not in DIRS:
        raise SystemExit(f"--study must be one of {sorted(DIRS)}, not {name!r}")
    os.environ["STITCH_STUDY"] = name
    return name


NAME = _pick()
STUDY = DIRS[NAME]
TOP = TOPS[NAME]
