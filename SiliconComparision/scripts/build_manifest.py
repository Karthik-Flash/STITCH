#!/usr/bin/env python3
"""Generate the handoff file inventory from repository-relative provenance."""
from __future__ import annotations

import hashlib
from pathlib import Path, PurePosixPath

ROOT = Path(__file__).resolve().parent.parent
DESIGN_SOURCES = {
    "mesh2x2": "mesh2x2_ref",
    "mesh3x3": "mesh3x3_ref",
    "mpsoc": "mpsoc_ref",
}
MODULE_FILES = {
    "Address_select": "Address_select.v",
    "execute_mux": "execution_unit.v",
    "mem_wb_mux": "mem_wb_mux.v",
    "mux3": "mux3.v",
    "MuxPC": "MuxPC.v",
    "register_1bit": "register_1bit.v",
    "register_32bit": "register_32bit.v",
    "register_4bit": "register_4bit.v",
}
MESH_MODULES = {"register_1bit", "register_32bit", "register_4bit"}
MPSOC_MODULES = set(MODULE_FILES)
C_SOURCES = {
    "Address_select": "phase3/results/phase3_run/deepseek-coder_6.7b/sem_esc_restart_v3/Address_select/rep2/iter3/dut.v",
    "MuxPC": "phase3/results/phase3_run/deepseek-coder_6.7b/sem_esc_restart_v3/MuxPC/rep2/iter3/dut.v",
    "execute_mux": "phase3/results/phase3_run/deepseek-coder_6.7b/sem_esc_restart_v3/execute_mux/rep2/iter2/dut.v",
    "mem_wb_mux": "phase3/results/phase3_run/deepseek-coder_6.7b/sem_esc_restart_v3/mem_wb_mux/rep2/iter6/dut.v",
    "mux3": "phase3/results/phase3_run/deepseek-coder_6.7b/sem_esc_restart_v3/mux3/rep2/iter1/dut.v",
    "ni_flit_pack": "phase3/results/phase3_run/deepseek-coder_6.7b/sem_esc_restart_v3/ni_flit_pack/rep2/iter1/dut.v",
    "noc_xbar4": "phase3/results/phase3_run/deepseek-coder_6.7b/sem_esc_restart_v3/noc_xbar4/rep2/iter6/dut.v",
    "register_1bit": "phase3/results/phase3_run/deepseek-coder_6.7b/sem_esc_restart_v3/register_1bit/rep2/iter3/dut.v",
    "register_32bit": "phase3/results/phase3_run/deepseek-coder_6.7b/sem_esc_restart_v3/register_32bit/rep2/iter2/dut.v",
    "register_4bit": "phase3/results/phase3_run/deepseek-coder_6.7b/sem_esc_restart_v3/register_4bit/rep2/iter2/dut.v",
    "riscv_alu_flags": "phase3/results/phase3_run/deepseek-coder_6.7b/sem_esc_restart_v3/riscv_alu_flags/rep2/iter6/dut.v",
}


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for block in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def source_for(relative: str) -> str:
    parts = PurePosixPath(relative).parts
    if parts[0] in {"A_original", "A1_original_synthesisable", "B_repaired_golden", "C_repaired_stitch"}:
        variant, design, filename = parts[0], parts[1], parts[2]
        if filename.startswith("__repaired_"):
            module = filename.removeprefix("__repaired_").removesuffix(".v")
            if variant == "A1_original_synthesisable" or variant == "B_repaired_golden":
                return f"phase3/tasks/{module}/golden.v"
            return C_SOURCES[module]

        source_dir = DESIGN_SOURCES[design]
        source = f"phase3/designs/{source_dir}/{filename}"
        if variant == "A_original":
            modules = set()
        elif design == "mpsoc":
            modules = {"register_1bit"} if variant == "A1_original_synthesisable" else MPSOC_MODULES
        else:
            modules = {"register_1bit"} if variant == "A1_original_synthesisable" else MESH_MODULES
        removed = sorted(module for module in modules if MODULE_FILES[module] == filename)
        if removed:
            source += f" (compose.py stripped: {', '.join(removed)})"
        return source

    if parts[0] == "leaves":
        task, filename = parts[1], parts[2]
        if filename == "defective.v":
            return f"phase3/tasks/{task}/input.v"
        if filename == "golden.v":
            return f"phase3/tasks/{task}/golden.v"
        return C_SOURCES[task]
    if relative == "COWORKER_BRIEF.md":
        return "user-provided exact brief"
    if relative == "scripts/run_yosys_stat.sh":
        return "authored for this handoff"
    if relative == "scripts/build_manifest.py":
        return "authored for this handoff"
    return "unknown"


def main() -> None:
    inventory = []
    for path in sorted(p for p in ROOT.rglob("*") if p.is_file() and p.name != "MANIFEST.md"):
        relative = path.relative_to(ROOT).as_posix()
        inventory.append((relative, source_for(relative), sha256(path)))

    compose_path = ROOT.parent / "phase3" / "results" / "phase3_run" / "compose_results.jsonl"
    compose_hash = sha256(compose_path)
    lines = [
        "# Handoff manifest",
        "",
        "Every delivered file is listed with its repository-relative source and SHA-256. This inventory excludes MANIFEST.md itself because embedding its final hash would be self-referential.",
        "",
        "## Toolchain and verification",
        "",
        "- Yosys: 0.69+71 (matched STITCH_SET4_OSSCAD suite).",
        "- A_original: expected abort on mesh2x2, mesh3x3, and mpsoc with `Multiple edge sensitive events found for this signal`. ",
        "- A1_original_synthesisable latches: mesh2x2 2,880; mesh3x3 6,480; mpsoc 269.",
        "- B_repaired_golden latches: mesh2x2 0; mesh3x3 0; mpsoc 122.",
        "- C_repaired_stitch latches: mesh2x2 0; mesh3x3 0; mpsoc 122.",
        "- All A1, B, and C tops synthesize successfully.",
        "",
        "## C provenance",
        "",
        "- Model: deepseek-coder:6.7b; condition: sem_esc_restart_v3; replicate: 2.",
        "- Compose record: phase3/results/phase3_run/compose_results.jsonl; SHA-256: " + compose_hash + ".",
        "- The eight real leaves spliced into C are sign-off clean; mesh2x2, mesh3x3, and mpsoc top-level synthesis passed.",
        "- The three seeded leaf artifacts are included for completeness; riscv_alu_flags is not sign-off clean and is not instantiated in these designs.",
        "",
        "## A1 versus B (name-only diff)",
        "",
        "- mesh2x2, mesh3x3: register_32bit, register_4bit.",
        "- mpsoc: Address_select, execute_mux, mem_wb_mux, mux3, MuxPC, register_32bit, register_4bit.",
        "- register_1bit is the same golden replacement in A1 and B.",
        "",
        "## File inventory",
        "",
        "| Handoff file | Source path | SHA-256 |",
        "|---|---|---|",
    ]
    lines.extend(f"| `{path}` | `{source}` | `{digest}` |" for path, source, digest in inventory)
    (ROOT / "MANIFEST.md").write_text("\n".join(lines) + "\n", encoding="utf-8", newline="")


if __name__ == "__main__":
    main()