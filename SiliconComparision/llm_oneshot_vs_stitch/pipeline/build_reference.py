#!/usr/bin/env python3
"""Build golden/reference: golden/handwritten with ONLY register_1bit, register_4bit and register_32bit replaced
by phase3/tasks/<m>/golden.v. Then compare it with latch_study/B_repaired_golden/mesh2x2, file by file and
module by module (B keeps compose.py's layout: stripped originals plus __repaired_<m>.v files).

Usage: python pipeline/build_reference.py
"""
from __future__ import annotations

import re
import shutil
from pathlib import Path

STUDY = Path(__file__).resolve().parent.parent
REPO = STUDY.parent.parent
HANDWRITTEN = STUDY / "golden" / "handwritten"
REFERENCE = STUDY / "golden" / "reference"
B = STUDY.parent / "latch_study" / "B_repaired_golden" / "mesh2x2"
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


def main() -> None:
    if REFERENCE.exists():
        shutil.rmtree(REFERENCE)
    shutil.copytree(HANDWRITTEN, REFERENCE)
    for name in REPLACED:
        shutil.copyfile(REPO / "phase3" / "tasks" / name / "golden.v", REFERENCE / f"{name}.v")
    for filename, (old, new) in SIM_FIXES.items():
        text = (REFERENCE / filename).read_text(encoding="utf-8")
        assert text.count(old) == 1, filename
        (REFERENCE / filename).write_text(text.replace(old, new), encoding="utf-8", newline="")

    ref_files = {p.name: p.read_bytes() for p in REFERENCE.glob("*.v")}
    b_files = {p.name: p.read_bytes() for p in B.glob("*.v")}
    same = sorted(n for n in ref_files.keys() & b_files.keys() if ref_files[n] == b_files[n])
    differ = sorted(n for n in ref_files.keys() & b_files.keys() if ref_files[n] != b_files[n])
    print(f"files: reference {len(ref_files)}, B {len(b_files)}; byte-identical {len(same)}; "
          f"differ {differ}; only in reference {sorted(ref_files.keys() - b_files.keys())}; "
          f"only in B {sorted(b_files.keys() - ref_files.keys())}")

    ref_mods, b_mods = modules(REFERENCE), modules(B)
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
