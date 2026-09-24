"""
Phase 3 regression suite for stitch_interpreter_v3.py. All fixtures are REAL tool logs
(Yosys 0.33 / Verilator 5.020) -- see tests/fixtures/real/TOOL_VERSIONS.txt.

Run (any cwd):  python phase3/tests/run_tests.py      (no pytest needed)   or   python -m pytest phase3/tests -q
Sections:
  A  v2 mode reproduces production exactly (Phase 1/2 comparability)
  B  v3 passes production text through untouched where no rule applies
  C  each v3 rule does what the evidence file says (real MPSoC leaves + seeded tasks)
  D  CHARACTERISATION of production v2 behaviour found in Phase 3 (documents, does not fix).
     If one of these starts failing, production changed -- re-read phase3/evidence/PROD_V2_ON_REAL_LOGS.md.
"""
import glob
import json
import os
import sys

import pytest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.environ.get("STITCH_INTERPRETER_DIR") or os.environ.get("STITCH_INTERP_DIR")
                or os.path.join(HERE, "..", "..", "src", "interpreter"))
import stitch_interpreter as base          # noqa: E402  production v2, unmodified
import stitch_interpreter_v3 as V          # noqa: E402

FX = os.path.join(HERE, "fixtures", "real")


def load(case):
    d = os.path.join(FX, case)
    top = json.load(open(os.path.join(d, "case.json")))["top"]
    return (open(os.path.join(d, "verilator.log")).read(), open(os.path.join(d, "yosys.log")).read(),
            os.path.join(d, "src.v"), top)


ALL = sorted(os.path.basename(p) for p in glob.glob(os.path.join(FX, "*")) if os.path.isdir(p))


# ---------------------------------------------------------------- A
@pytest.mark.parametrize("case", ALL)
def test_A_v2_mode_is_production(case):
    v, y, src, top = load(case)
    r = V.interpret(v, y, src, version="v2", top=top)
    vt, vc = base.interpret_verilator(v, src)
    assert vt.strip("\n") in r["text"] or (not vt and True)
    assert r["codes_fired"][:len(vc)] == vc


def test_A_fingerprint_recorded():
    r = V.interpret("", "", None)
    assert len(r["base_sha256_lf"]) == 64


# ---------------------------------------------------------------- B
@pytest.mark.parametrize("case", ["mpsoc_mux3", "mpsoc_MuxPC", "mpsoc_mem_wb_mux", "mpsoc_execute_mux",
                                  "task_riscv_alu_flags", "probe_latch"])
def test_B_passthrough_identity(case):
    v, y, src, top = load(case)
    r2 = V.interpret(v, y, src, version="v2", top=top)
    r3 = V.interpret(v, y, src, version="v3", top=top)
    assert r3["text"] == r2["text"], f"v3 altered production text on {case} with rules {r3['rules_applied']}"


# ---------------------------------------------------------------- C
def v3(case):
    v, y, src, top = load(case)
    return V.interpret(v, y, src, version="v3", top=top)


@pytest.mark.parametrize("case", ["mpsoc_register_4bit", "mpsoc_register_32bit"])
def test_C_R1_missing_clock(case):
    r = v3(case)
    assert r["classes_fired"] == ["MISSING_CLOCK"]
    assert "always @(posedge clk)" in r["text"]
    assert "if (clk)" not in r["text"].replace("Do NOT add 'if (clk)'", "")


def test_C_N1_async_reset():
    r = v3("mpsoc_register_1bit")
    assert r["classes_fired"] == ["ASYNC_RESET"]
    assert "if (reset)" in r["text"] and "posedge clk or posedge reset" in r["text"]


def test_C_R3_partial_bits_not_gated():
    r = v3("mpsoc_Address_select")
    assert "if (Instruction_code)" not in r["text"]
    assert "UNUSEDSIGNAL(bits)x1" in r["suppressed"]
    r = v3("mpsoc_multiply")
    assert "'prod'" not in r["text"] and "R5" in r["rules_applied"]


def test_C_N2_verilator_only_loop():
    r = v3("mpsoc_IFU")
    assert "COMB_LOOP" in r["classes_fired"] and "PC = PC" in r["text"]


def test_C_N6_expression_width_and_no_answer_leak():
    r = v3("task_ni_flit_pack")
    assert r["classes_fired"] == ["WIDTHTRUNC"] and "N6" in r["rules_applied"]
    assert "head_flit" in r["text"]
    assert "payload[29:0]" not in r["text"] and "14'd0" not in r["text"]   # must not hand out the answer


def test_C_N4_no_duplicate_same_signal():
    r = v3("task_noc_xbar4")
    assert r["text"].count("'out_data'") == 2        # production directive only (names it twice itself)


def test_C_R4_style_named_lhs_and_correct_combdly():
    r = V.interpret(*load("probe_more")[:3], version="v3", max_directives=10)
    assert "'process'" not in r["text"]


def test_C_cap_respected():
    r = V.interpret(*load("mpsoc_Decoder")[:3], version="v3", top="Decoder", max_directives=2)
    assert len(r["codes_fired"]) <= 2


# ---------------------------------------------------------------- D (characterisation of production v2)
def test_D_production_multidriven_real_trigger_both_formats():
    """Resolves WARNING_TAXONOMY.md 'MULTIDRIVEN: real trigger not found'. RTL: probe_multi/src.v."""
    v, _, src, _ = load("probe_multi")
    assert "have multiple combinational drivers" in v                 # format A (two assigns)
    assert "multiple driving blocks with different clocking" in v     # format B (clk vs clk/rst blocks)
    _, codes = base.interpret_verilator(v, src)
    assert "MULTIDRIVEN" in codes


def test_D_production_style_codes_name_prose_word():
    v, _, src, _ = load("probe_more")
    t_nosrc, c_nosrc = base.interpret_verilator(v, None)
    assert "'process'" in t_nosrc                                     # BLKSEQ/COMBDLY name Verilator prose
    t_src, c_src = base.interpret_verilator(v, src)
    assert "BLKSEQ" not in c_src and "COMBDLY" not in c_src          # ...and are dropped when source is given


def test_D_production_latch_needs_lines_not_names():
    _, y, src, _ = load("probe_latch")
    names = base.detect_yosys_latches(y)
    assert "an output signal" in base.interpret_yosys_latches(names, src)


def test_D_production_width_expression_dropped():
    v, _, src, _ = load("task_ni_flit_pack")
    assert "WIDTHTRUNC" in v
    assert base.interpret_verilator(v, src) == ("", [])


def test_D_production_clock_gate_directive():
    v, _, src, _ = load("mpsoc_register_4bit")
    t, c = base.interpret_verilator(v, src)
    assert c == ["UNUSEDSIGNAL"] and "if (clk) begin" in t
