#!/usr/bin/env python3
"""Fill the generated Ports and Children blocks of specs/<module>.md from modules.csv.

Each spec holds two marked blocks; everything between a BEGIN and END marker is rewritten, the hand-written
text around them is left alone. `--check` exits 1 if any spec is missing or out of date.
Usage: python pipeline/spec_ports.py [--check]
"""
from __future__ import annotations

import csv
import re
import sys
from pathlib import Path

STUDY = Path(__file__).resolve().parent.parent
SPECS = STUDY / "specs"
BLOCK = re.compile(r"(<!-- BEGIN generated: (\w+) -->\n).*?(<!-- END generated: \2 -->)", re.S)


def parse_ports(field: str) -> list[tuple[str, str, int]]:
    ports = []
    for item in field.split(";"):
        direction, rest = item.split(" ", 1)
        name, width = rest.rstrip("]").split("[")
        ports.append((direction, name, int(width)))
    return ports


def render_ports(ports: list[tuple[str, str, int]]) -> str:
    """One declaration line per run of ports with the same direction and width, in port order."""
    lines, run = [], []
    for port in ports + [("", "", 0)]:
        if run and port[0::2] != run[0][0::2]:
            direction, _, width = run[0]
            prefix = f"{direction} [{width - 1}:0] " if width > 1 else f"{direction} "
            names, line = [p[1] for p in run], prefix
            for i, name in enumerate(names):
                piece = name + ("," if i < len(names) - 1 else ";")
                if len(line) + len(piece) > 110 and line.strip() != prefix.strip():
                    lines.append(line.rstrip())
                    line = " " * len(prefix)
                line += piece + " "
            lines.append(line.rstrip())
            run = []
        run.append(port)
    count = len(ports)
    return f"{count} ports, in this exact order:\n\n```verilog\n" + "\n".join(lines) + "\n```\n"


def render_children(row: dict, rows: dict) -> str:
    if not row["children"]:
        return "None. This module instantiates no other module.\n"
    out = ["Must instantiate exactly these modules (ports listed in each child's own order):", ""]
    for item in row["children"].split(";"):
        child, count = item.rsplit("x", 1)
        names = ", ".join(name for _, name, _ in parse_ports(rows[child]["ports"]))
        out.append(f"- `{child}` x {count}: ({names})")
    return "\n".join(out) + "\n"


def main() -> int:
    check = "--check" in sys.argv
    with (STUDY / "modules.csv").open(encoding="utf-8", newline="") as handle:
        rows = {row["module"]: row for row in csv.DictReader(handle)}
    stale = []
    for name, row in rows.items():
        path = SPECS / f"{name}.md"
        if not path.exists():
            stale.append(f"{name}: missing")
            continue
        text = path.read_text(encoding="utf-8")
        blocks = {
            "ports": render_ports(parse_ports(row["ports"]))
            + f"\nParameters: {row['parameters'] or 'none'}.\n",
            "children": render_children(row, rows),
        }
        found = {m.group(2) for m in BLOCK.finditer(text)}
        if found != set(blocks):
            stale.append(f"{name}: markers {sorted(found)}")
            continue
        new = BLOCK.sub(lambda m: m.group(1) + blocks[m.group(2)] + m.group(3), text)
        if new != text:
            stale.append(f"{name}: out of date")
            if not check:
                path.write_text(new, encoding="utf-8", newline="\n")
    for line in stale:
        print(line)
    return 1 if check and stale else 0


if __name__ == "__main__":
    sys.exit(main())
