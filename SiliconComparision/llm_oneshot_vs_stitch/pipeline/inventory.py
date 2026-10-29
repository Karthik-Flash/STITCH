#!/usr/bin/env python3
"""Build modules.csv: the module inventory of the hand-written 2x2 mesh rooted at top_2x2_router.

Structure (ports, parameters, children) comes from golden/handwritten after `hierarchy` only. Yosys cannot
run `proc` on the hand-written register_1bit ("Multiple edge sensitive events"), so storage, clock and reset
facts come from golden/A1, which differs only in that one file (golden register_1bit, same ports).
clock_ports / reset_ports / latch_enable_ports list the ports whose bits reach a storage cell's clock, reset or
latch-enable pin, directly or through a child's such port. Data signals used as clocks show up here too.

Needs Yosys: STITCH_YOSYS, else $STITCH_SET4_OSSCAD/bin/yosys, else PATH (same lookup as run_yosys_stat.sh).
Usage: python3 pipeline/inventory.py   (from llm_oneshot_vs_stitch/ or anywhere)
"""
from __future__ import annotations

import csv
import json
import os
import shutil
import subprocess
from collections import Counter
from pathlib import Path

STUDY = Path(__file__).resolve().parent.parent
REPO = STUDY.parent.parent
TOP = "top_2x2_router"
HANDWRITTEN = STUDY / "golden" / "handwritten"
A1 = STUDY / "golden" / "A1"
WORK = STUDY / "runs" / "inventory"
TASKS = REPO / "phase3" / "tasks"

FLOPS = {"$dff", "$dffe", "$adff", "$adffe", "$sdff", "$sdffe", "$sdffce", "$aldff", "$aldffe", "$dffsr", "$dffsre"}
LATCHES = {"$dlatch", "$adlatch", "$dlatchsr"}
MEMORIES = {"$mem", "$mem_v2", "$memwr", "$memwr_v2", "$memrd", "$memrd_v2"}
CLOCK_PINS = {"CLK", "WR_CLK", "RD_CLK"}
RESET_PINS = {"ARST", "SRST", "CLR", "SET", "ALOAD"}


def find_yosys() -> str:
    candidates = [os.environ.get("STITCH_YOSYS", "")]
    if os.environ.get("STITCH_SET4_OSSCAD"):
        base = Path(os.environ["STITCH_SET4_OSSCAD"])
        candidates += [str(base / "oss-cad-suite" / "bin" / "yosys"), str(base / "bin" / "yosys")]
    candidates.append(shutil.which("yosys") or "")
    for candidate in candidates:
        if candidate and os.access(candidate, os.X_OK):
            return candidate
    raise SystemExit("Yosys not found. Set STITCH_SET4_OSSCAD or STITCH_YOSYS.")


def yosys_json(yosys: str, design: Path, passes: str, out: Path) -> dict:
    sources = " ".join(sorted(p.name for p in design.glob("*.v")))
    script = f"read_verilog {sources}; hierarchy -check -top {TOP}; {passes}; write_json {out.as_posix()}"
    subprocess.run([yosys, "-q", "-p", script], cwd=design, check=True)
    return json.loads(out.read_text(encoding="utf-8"))["modules"]


def children(module: dict) -> Counter:
    return Counter(cell["type"] for cell in module["cells"].values() if not cell["type"].startswith("$"))


def bottom_up(modules: dict) -> list[str]:
    order: list[str] = []
    def visit(name: str) -> None:
        if name in order:
            return
        for child in sorted(children(modules[name])):
            visit(child)
        order.append(name)
    visit(TOP)
    return order


def port_names(module: dict, bits: set) -> list[str]:
    return [name for name, port in module["ports"].items() if bits.intersection(port["bits"])]


def main() -> None:
    WORK.mkdir(parents=True, exist_ok=True)
    yosys = find_yosys()
    hw = yosys_json(yosys, HANDWRITTEN, "delete */p:*", WORK / "handwritten_hierarchy.json")
    a1 = yosys_json(yosys, A1, "proc; opt_clean; opt_dff -nodffe", WORK / "a1_proc.json")
    order = bottom_up(hw)
    assert set(order) == set(hw) == set(a1), "module sets differ between handwritten and A1"

    rows = []
    clocks: dict[str, set] = {}
    resets: dict[str, set] = {}
    enables: dict[str, set] = {}
    stateful: dict[str, bool] = {}
    for index, name in enumerate(order, start=1):
        module, proc_module = hw[name], a1[name]
        assert list(module["ports"]) == list(proc_module["ports"]), f"{name}: port lists differ"
        clock_bits, reset_bits, enable_bits = set(), set(), set()
        storage = Counter()
        for cell in proc_module["cells"].values():
            kind, pins = cell["type"], cell["connections"]
            if kind in FLOPS | LATCHES | MEMORIES:
                storage[kind] += 1
                for pin, bits in pins.items():
                    if pin in CLOCK_PINS:
                        clock_bits.update(bits)
                    elif pin in RESET_PINS:
                        reset_bits.update(bits)
                    elif pin == "EN" and kind in LATCHES:
                        enable_bits.update(bits)
            elif not kind.startswith("$"):
                for pin, bits in pins.items():
                    if pin in clocks[kind]:
                        clock_bits.update(bits)
                    if pin in resets[kind]:
                        reset_bits.update(bits)
                    if pin in enables[kind]:
                        enable_bits.update(bits)
        clocks[name] = set(port_names(proc_module, clock_bits))
        resets[name] = set(port_names(proc_module, reset_bits))
        enables[name] = set(port_names(proc_module, enable_bits))
        kids = children(module)
        stateful[name] = bool(storage) or any(stateful[child] for child in kids)

        task = TASKS / name
        meta = json.loads((task / "meta.json").read_text(encoding="utf-8")) if task.is_dir() else {}
        latch_leaf = any("LATCH" in c for c in meta.get("defect_classes", [])) and meta.get("compose", {}).get("design") == "mesh"
        rows.append({
            "module": name,
            "file": module["attributes"]["src"].split(":")[0],
            "bottom_up_order": index,
            "ports": ";".join(
                f"{port['direction']} {pname}[{len(port['bits'])}]" for pname, port in module["ports"].items()
            ),
            "parameters": ";".join(f"{k}={v}" for k, v in module.get("parameter_default_values", {}).items()),
            "children": ";".join(f"{child}x{count}" for child, count in sorted(kids.items())),
            "kind": "sequential" if stateful[name] else "combinational",
            "own_storage": ";".join(f"{k}x{v}" for k, v in sorted(storage.items())),
            "clock_ports": ";".join(p for p in module["ports"] if p in clocks[name]),
            "reset_ports": ";".join(p for p in module["ports"] if p in resets[name]),
            "latch_enable_ports": ";".join(p for p in module["ports"] if p in enables[name]),
            "phase3_latch_leaf": "yes" if latch_leaf else "no",
            "phase3_task": f"phase3/tasks/{name}" if task.is_dir() else "",
        })

    # Self-check: every child is listed before its parent, and the top comes last.
    position = {row["module"]: row["bottom_up_order"] for row in rows}
    assert all(position[c] < position[n] for n in order for c in children(hw[n])) and order[-1] == TOP

    with (STUDY / "modules.csv").open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]), lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)
    print(f"modules: {len(rows)}")


if __name__ == "__main__":
    main()
