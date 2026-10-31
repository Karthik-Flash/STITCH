#!/usr/bin/env python3
"""Build golden/reference: golden/handwritten with ONLY register_1bit, register_4bit and register_32bit replaced
by phase3/tasks/<m>/golden.v (those present in the study). Then compare it with latch_study/B_repaired_golden/mesh2x2, file by file and
module by module (B keeps compose.py's layout: stripped originals plus __repaired_<m>.v files).

mesh3x3 and ni first copy golden/handwritten and golden/A1 from their sources (SOURCES below); 2x2's copies are
frozen. ni compares only its own files with B (mpsoc).
Usage: python pipeline/build_reference.py [--study 2x2|mesh3x3|ni]
"""
from __future__ import annotations

import re
import os
import shutil
import sys
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import studies  # noqa: E402

STUDY = Path(studies.STUDY)
REPO = Path(studies.REPO)
HANDWRITTEN = STUDY / "golden" / "handwritten"
REFERENCE = STUDY / "golden" / "reference"
LATCH = STUDY.parent / "latch_study" if studies.NAME == "2x2" else STUDY.parent.parent / "latch_study"
B = LATCH / "B_repaired_golden" / {"2x2": "mesh2x2", "mesh3x3": "mesh3x3", "ni": "mpsoc"}[studies.NAME]
# study -> (handwritten source, A1 source, files to copy or None = all *.v)
NI_FILES = ("new.v", "rp1.v", "nidepack.v", "depack.v", "router_fifo.v", "asynch_comparator.v", "gray_mod6.v",
            "jk_ff.v", "memory.v")
SOURCES = {
    "mesh3x3": (REPO / "phase3" / "designs" / "mesh3x3_ref", LATCH / "A1_original_synthesisable" / "mesh3x3", None),
    "ni": (REPO / "phase3" / "designs" / "mpsoc_ref", LATCH / "A1_original_synthesisable" / "mpsoc", NI_FILES),
}
REPLACED = ("register_1bit", "register_4bit", "register_32bit")
# Declaration-only fixes so Icarus (p3_eval: iverilog -g2012) can compile the reference. The hand-written files read
# a net in a sensitivity list before the instance port that implicitly declares it; Yosys accepts that, Icarus does
# not. An implicit net is a 1-bit wire, so declaring it changes nothing else.
SIM_FIXES = {
    "ip_chnl.v": ("     reg clr1,header,tailer_org;\n",
                  "     reg clr1,header,tailer_org;\n     wire rd_en_out; // added for Icarus: was implicit\n"),
    "allot_vc.v": ("\twire mux_out1,mux_out2,mux_out13,mux_out4;  \n",
                   "\twire mux_out1,mux_out2,mux_out13,mux_out4;  \n\twire mux_out3; // added for Icarus: was implicit\n"),
}


def modules(directory: Path) -> dict[str, str]:
    """module name -> whitespace-normalised text, comments removed."""
    found = {}
    for path in sorted(directory.glob("*.v")):
        text = path.read_bytes().decode("utf-8").replace("\r\n", "\n")
        text = re.sub(r"/\*.*?\*/", "", re.sub(r"//[^\n]*", "", text), flags=re.S)
        for m in re.finditer(r"\bmodule\s+(\w+).*?\bendmodule\b", text, re.S):
            assert m.group(1) not in found, f"{m.group(1)} defined twice in {directory}"
            found[m.group(1)] = " ".join(m.group(0).split())
    return found


def copy_sources() -> None:
    hw, a1, files = SOURCES[studies.NAME]
    for src, dst in ((hw, HANDWRITTEN), (a1, STUDY / "golden" / "A1")):
        if dst.exists():
            shutil.rmtree(dst)
        dst.mkdir(parents=True)
        for n in files or sorted(p.name for p in src.glob("*.v")):
            shutil.copyfile(src / n, dst / n)
        print(f"copied {len(list(dst.glob('*.v')))} files {src} -> {dst}")


def main() -> None:
    if studies.NAME in SOURCES:
        copy_sources()
    if REFERENCE.exists():
        shutil.rmtree(REFERENCE)
    shutil.copytree(HANDWRITTEN, REFERENCE)
    for name in (n for n in REPLACED if (REFERENCE / f"{n}.v").exists()):
        shutil.copyfile(REPO / "phase3" / "tasks" / name / "golden.v", REFERENCE / f"{name}.v")
    for filename, (old, new) in ((f, v) for f, v in SIM_FIXES.items() if (REFERENCE / f).exists()):
        text = (REFERENCE / filename).read_text(encoding="utf-8")
        assert text.count(old) == 1, filename
        (REFERENCE / filename).write_text(text.replace(old, new), encoding="utf-8", newline="")

    ref_files = {p.name: p.read_bytes() for p in REFERENCE.glob("*.v")}
    b_files = {p.name: p.read_bytes() for p in B.glob("*.v") if studies.NAME != "ni" or p.name in ref_files}
    same = sorted(n for n in ref_files.keys() & b_files.keys() if ref_files[n] == b_files[n])
    differ = sorted(n for n in ref_files.keys() & b_files.keys() if ref_files[n] != b_files[n])
    print(f"files: reference {len(ref_files)}, B {len(b_files)}; byte-identical {len(same)}; "
          f"differ {differ}; only in reference {sorted(ref_files.keys() - b_files.keys())}; "
          f"only in B {sorted(b_files.keys() - ref_files.keys())}")

    ref_mods, b_mods = modules(REFERENCE), modules(B)
    if studies.NAME == "ni":
        b_mods = {m: t for m, t in b_mods.items() if m in ref_mods}
    diff_mods = sorted(m for m in ref_mods.keys() & b_mods.keys() if ref_mods[m] != b_mods[m])
    print(f"modules: reference {len(ref_mods)}, B {len(b_mods)}; text differs (comments/whitespace ignored): "
          f"{diff_mods}; only in reference {sorted(ref_mods.keys() - b_mods.keys())}; "
          f"only in B {sorted(b_mods.keys() - ref_mods.keys())}")
    identical = not diff_mods and ref_mods.keys() == b_mods.keys()
    print("module-level identical to B:", identical)
    for m in diff_mods:
        extra = set(ref_mods[m].split(";")) - set(b_mods[m].split(";"))
        missing = set(b_mods[m].split(";")) - set(ref_mods[m].split(";"))
        print(f"  {m}: statements only in reference {sorted(extra)}; only in B {sorted(missing)}")


if __name__ == "__main__":
    main()
