#!/usr/bin/env python3
"""Run phase3/tests/test_v3_layer.py WITHOUT pytest (HPC venv has only stdlib + openai).
Supports the two pytest features the suite uses: pytest.mark.parametrize and plain asserts.
Usage (any cwd):  python phase3/tests/run_tests.py        -> exit 0 iff all pass"""
import importlib.util, os, sys, traceback, types

class _Mark:
    @staticmethod
    def parametrize(name, values):
        def deco(fn):
            fn._params = (name, list(values)); return fn
        return deco

try:
    import pytest  # noqa: F401  (use the real one if present)
except ImportError:
    shim = types.ModuleType("pytest"); shim.mark = _Mark(); sys.modules["pytest"] = shim

here = os.path.dirname(os.path.abspath(__file__))
spec = importlib.util.spec_from_file_location("test_v3_layer", os.path.join(here, "test_v3_layer.py"))
mod = importlib.util.module_from_spec(spec); spec.loader.exec_module(mod)
passed, failed = 0, []
for name in sorted(n for n in dir(mod) if n.startswith("test_")):
    fn = getattr(mod, name)
    params = getattr(fn, "_params", None) or getattr(getattr(fn, "pytestmark", [None])[0], "args", None)
    cases = [(params[0], v) for v in params[1]] if params else [(None, None)]
    for arg, val in cases:
        label = f"{name}[{val}]" if arg else name
        try:
            fn(**({arg: val} if arg else {})); passed += 1
        except Exception:
            failed.append(label); print("FAIL", label); traceback.print_exc(limit=1)
print(f"\n{passed} passed, {len(failed)} failed")
sys.exit(1 if failed else 0)
