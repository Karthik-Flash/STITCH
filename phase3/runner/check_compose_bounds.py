#!/usr/bin/env python3
"""Gate G4: re-measure the 2x2-mesh composition bounds on THIS toolchain.
Expected (measured on Yosys 0.33, determined by design structure, so version-independent):
  no repair        -> top-level synthesis FAILS (register_1bit async-reset abort), 2880 latch cells elsewhere
  3 golden repairs -> top-level synthesis PASSES, 0 latch cells
Exit 0 only if both hold."""
import os, sys
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import compose as C
lo = C.compose_blackboxed("mesh2x2", {})
gold = {m: os.path.join(C.TASKS_DIR, m, "golden.v") for m in C.task_meta() if "mesh2x2" in C.designs_for([m])}
hi = C.compose_blackboxed("mesh2x2", gold)
print("no repair :", {k: lo.get(k) for k in ("top_level_synthesis_pass", "latch_cells_excl_crashed", "crashing_files")})
print("repaired  :", {k: hi.get(k) for k in ("top_level_synthesis_pass", "latch_cells_excl_crashed", "repaired_modules")})
ok = (lo["top_level_synthesis_pass"] is False and lo.get("latch_cells_excl_crashed") == 2880
      and hi["top_level_synthesis_pass"] is True and hi.get("latch_cells_excl_crashed") == 0)
print("G4:", "PASS" if ok else "FAIL"); sys.exit(0 if ok else 1)
