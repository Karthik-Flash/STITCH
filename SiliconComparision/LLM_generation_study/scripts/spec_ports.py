#!/usr/bin/env python3
"""Fill the generated Ports and Children blocks of specs/<module>.md from the golden RTL, so every port name,
direction and width in a spec is the golden's, in the golden's order.

Each spec holds two marked blocks; everything between a BEGIN and END marker is rewritten and the hand-written text
around them is left alone. --check exits 1 if a spec is missing a block or a block is out of date.
Usage (from the study folder): python scripts/spec_ports.py [--check]
"""
import os
import re
import sys

STUDY = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RTL = os.path.join(STUDY, "golden", "rtl")
SPECS = os.path.join(STUDY, "specs")
MODULES = ["fifo", "route_compute", "rr_arbiter", "flit_mux", "input_port", "output_port", "router_5port"]
BLOCK = re.compile(r"(<!-- BEGIN generated: (\w+) -->\n).*?(<!-- END generated: \2 -->)", re.S)
PORT = re.compile(r"^\s*(input|output)\s+(?:reg\s+|wire\s+)?(?:\[(\d+):0\]\s+)?(\w+)\s*,?\s*(?://.*)?$")


def ports(m):
    """[(direction, width, name)] from the golden module header (ANSI style, one port per line)."""
    src = open(os.path.join(RTL, m + ".v")).read()
    header = src[src.index(f"module {m}"):src.index(");")]
    out = [(d, int(w) + 1 if w else 1, n) for d, w, n in
           (PORT.match(l).groups() for l in header.splitlines() if PORT.match(l))]
    assert out, f"no ports parsed for {m}"
    return out


def children(m):
    """[(child module, count)] in first-instantiation order, from the golden source."""
    src = open(os.path.join(RTL, m + ".v")).read()
    found = re.findall(r"^\s*(\w+)\s+\w+\s*\(", src, re.M)
    names = [c for c in dict.fromkeys(found) if c in MODULES]
    return [(c, found.count(c)) for c in names]


def decl(p):
    d, w, n = p
    return f"{d} [{w - 1}:0] {n};" if w > 1 else f"{d} {n};"


def render_ports(m):
    ps = ports(m)
    return "\n".join([f"{len(ps)} ports, in this exact order:", "", "```verilog", *map(decl, ps), "```", "",
                      "Parameters: none.", ""])


def render_children(m):
    ch = children(m)
    if not ch:
        return "None. This module instantiates no other module.\n"
    lines = ["Must instantiate exactly these modules. Their files are provided; do not write them again.", ""]
    for c, k in ch:
        lines += [f"`{c}` x {k}, ports in this exact order:", "", "```verilog", *map(decl, ports(c)), "```", ""]
    return "\n".join(lines)


def main(check=None):
    check = "--check" in sys.argv if check is None else check
    bad = 0
    for m in MODULES:
        path = os.path.join(SPECS, m + ".md")
        if not os.path.exists(path):
            print(f"MISSING {path}")
            bad += 1
            continue
        text = open(path, encoding="utf-8").read()
        render = {"ports": render_ports(m), "children": render_children(m)}
        kinds = [k for _, k, _ in BLOCK.findall(text)]
        if sorted(kinds) != ["children", "ports"]:
            print(f"BAD {m}: blocks {kinds}, need ports and children")
            bad += 1
            continue
        new = BLOCK.sub(lambda g: g.group(1) + render[g.group(2)] + g.group(3), text)
        if new != text:
            if check:
                print(f"OUT OF DATE {m}")
                bad += 1
            else:
                open(path, "w", encoding="utf-8", newline="\n").write(new)
                print(f"updated {m}")
        else:
            print(f"ok {m}: {len(ports(m))} ports, children {children(m) or 'none'}")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
