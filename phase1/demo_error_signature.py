"""
demo_error_signature.py — TASK 0 deliverable.

Prints raw iverilog error text -> classify_error() bucket -> normalized
error_signature() for real examples, so the normalization can be eyeballed
for over-collapsing (distinct failures merged) and under-collapsing
(repeat failures not merged) before the escalation state machine is built
on top of it.

Every example below is copied verbatim from an existing phase0 run's
sim_log.txt (paths cited per example) — real captured iverilog output from
this project's own history, not synthetic text. Where the real file has
more error lines than shown, the example is an exact-prefix excerpt (noted
per entry) rather than the full file — error_signature() only ever looks
at the first 3 normalized lines anyway (see error_signature.py's
docstring), so a longer tail wouldn't change the signature shown. phase0/
is read-only source material here; nothing under phase0/ is modified or
re-run by this script.

Requires: nothing external — no WSL, no Ollama, no live run. Produced
the Task 0 sign-off (normalization confirmed, then widened from a
3-line to a 5-line window on review — see error_signature.py's
DEFAULT_WINDOW comment for why).

Usage: python phase1/demo_error_signature.py
"""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "src", "runner"))
from stitch_runner import classify_error  # noqa: E402  (reused unmodified)

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from error_signature import error_signature  # noqa: E402


# Each entry: (label, source sim_log.txt, raw text as captured)
EXAMPLES = [
    (
        "datapath_mux_alu/gemma3:4b/raw_adv iter_1 (exact-prefix excerpt: real file has 9 errors, first 3 shown)",
        "phase0/results/new_illustrations/datapath_mux_alu/results_stitch/gemma3_4b/raw_adv/datapath_mux_alu/iter_1/sim_log.txt",
        "COMPILATION ERROR:\n"
        "/mnt/d/Projects/STITCH/results/new_illustrations/datapath_mux_alu/results_stitch/gemma3_4b/raw_adv/datapath_mux_alu/iter_1/datapath_mux_alu.v:22: error: add_result is not a valid l-value in datapath_mux_alu_tb.dut.\n"
        "/mnt/d/Projects/STITCH/results/new_illustrations/datapath_mux_alu/results_stitch/gemma3_4b/raw_adv/datapath_mux_alu/iter_1/datapath_mux_alu.v:12:      : add_result is declared here as wire.\n"
        "/mnt/d/Projects/STITCH/results/new_illustrations/datapath_mux_alu/results_stitch/gemma3_4b/raw_adv/datapath_mux_alu/iter_1/datapath_mux_alu.v:24: error: sub_result is not a valid l-value in datapath_mux_alu_tb.dut.\n"
        "/mnt/d/Projects/STITCH/results/new_illustrations/datapath_mux_alu/results_stitch/gemma3_4b/raw_adv/datapath_mux_alu/iter_1/datapath_mux_alu.v:13:      : sub_result is declared here as wire.\n"
        "/mnt/d/Projects/STITCH/results/new_illustrations/datapath_mux_alu/results_stitch/gemma3_4b/raw_adv/datapath_mux_alu/iter_1/datapath_mux_alu.v:26: error: and_result is not a valid l-value in datapath_mux_alu_tb.dut.",
    ),
    (
        "datapath_mux_alu/gemma3:4b/raw_adv iter_2  (same stuck failure as iter_1; exact-prefix excerpt)",
        "phase0/results/new_illustrations/datapath_mux_alu/results_stitch/gemma3_4b/raw_adv/datapath_mux_alu/iter_2/sim_log.txt",
        "COMPILATION ERROR:\n"
        "/mnt/d/Projects/STITCH/results/new_illustrations/datapath_mux_alu/results_stitch/gemma3_4b/raw_adv/datapath_mux_alu/iter_2/datapath_mux_alu.v:22: error: add_result is not a valid l-value in datapath_mux_alu_tb.dut.\n"
        "/mnt/d/Projects/STITCH/results/new_illustrations/datapath_mux_alu/results_stitch/gemma3_4b/raw_adv/datapath_mux_alu/iter_2/datapath_mux_alu.v:12:      : add_result is declared here as wire.\n"
        "/mnt/d/Projects/STITCH/results/new_illustrations/datapath_mux_alu/results_stitch/gemma3_4b/raw_adv/datapath_mux_alu/iter_2/datapath_mux_alu.v:24: error: sub_result is not a valid l-value in datapath_mux_alu_tb.dut.\n"
        "/mnt/d/Projects/STITCH/results/new_illustrations/datapath_mux_alu/results_stitch/gemma3_4b/raw_adv/datapath_mux_alu/iter_2/datapath_mux_alu.v:13:      : sub_result is declared here as wire.\n"
        "/mnt/d/Projects/STITCH/results/new_illustrations/datapath_mux_alu/results_stitch/gemma3_4b/raw_adv/datapath_mux_alu/iter_2/datapath_mux_alu.v:26: error: and_result is not a valid l-value in datapath_mux_alu_tb.dut.",
    ),
    (
        "datapath_mux_alu/gemma3:4b/raw_adv iter_3  (model gave up mid-generation -- genuinely different failure)",
        "phase0/results/new_illustrations/datapath_mux_alu/results_stitch/gemma3_4b/raw_adv/datapath_mux_alu/iter_3/sim_log.txt",
        "COMPILATION ERROR:\n"
        "/mnt/d/Projects/STITCH/results/new_illustrations/datapath_mux_alu/results_stitch/gemma3_4b/raw_adv/datapath_mux_alu/iter_3/datapath_mux_alu.v:1: warning: macro verilog undefined (and assumed null) at this point.\n"
        "/mnt/d/Projects/STITCH/results/new_illustrations/datapath_mux_alu/results_stitch/gemma3_4b/raw_adv/datapath_mux_alu/iter_3/datapath_mux_alu.v:1: syntax error\n"
        "I give up.",
    ),
    (
        "datapath_mux_alu/gemma3:4b/raw_adv iter_4  (reverts to the SAME l-value failure as iter_1/2, different lines; exact-prefix excerpt)",
        "phase0/results/new_illustrations/datapath_mux_alu/results_stitch/gemma3_4b/raw_adv/datapath_mux_alu/iter_4/sim_log.txt",
        "COMPILATION ERROR:\n"
        "/mnt/d/Projects/STITCH/results/new_illustrations/datapath_mux_alu/results_stitch/gemma3_4b/raw_adv/datapath_mux_alu/iter_4/datapath_mux_alu.v:23: error: add_result is not a valid l-value in datapath_mux_alu_tb.dut.\n"
        "/mnt/d/Projects/STITCH/results/new_illustrations/datapath_mux_alu/results_stitch/gemma3_4b/raw_adv/datapath_mux_alu/iter_4/datapath_mux_alu.v:12:      : add_result is declared here as wire.\n"
        "/mnt/d/Projects/STITCH/results/new_illustrations/datapath_mux_alu/results_stitch/gemma3_4b/raw_adv/datapath_mux_alu/iter_4/datapath_mux_alu.v:26: error: sub_result is not a valid l-value in datapath_mux_alu_tb.dut.\n"
        "/mnt/d/Projects/STITCH/results/new_illustrations/datapath_mux_alu/results_stitch/gemma3_4b/raw_adv/datapath_mux_alu/iter_4/datapath_mux_alu.v:13:      : sub_result is declared here as wire.\n"
        "/mnt/d/Projects/STITCH/results/new_illustrations/datapath_mux_alu/results_stitch/gemma3_4b/raw_adv/datapath_mux_alu/iter_4/datapath_mux_alu.v:29: error: and_result is not a valid l-value in datapath_mux_alu_tb.dut.",
    ),
    (
        "adder_with_overflow/gemma3:4b/baseline iter_1  (elaboration bind error, distinct class)",
        "phase0/results/new_illustrations/adder_with_overflow/results_stitch/gemma3_4b/baseline/adder_with_overflow/iter_1/sim_log.txt",
        "COMPILATION ERROR:\n"
        "/mnt/d/Projects/STITCH/results/new_illustrations/adder_with_overflow/results_stitch/gemma3_4b/baseline/adder_with_overflow/iter_1/adder_with_overflow.v:10: error: Could not find variable ``carry'' in ``adder_with_overflow_tb.dut''\n"
        "/mnt/d/Projects/STITCH/results/new_illustrations/adder_with_overflow/results_stitch/gemma3_4b/baseline/adder_with_overflow/iter_1/adder_with_overflow.v:11: error: Unable to bind wire/reg/memory `carry' in `adder_with_overflow_tb.dut'\n"
        "2 error(s) during elaboration.",
    ),
    (
        "adder_with_overflow/gemma3:4b/baseline iter_2  (SystemVerilog construct, distinct class)",
        "phase0/results/new_illustrations/adder_with_overflow/results_stitch/gemma3_4b/baseline/adder_with_overflow/iter_2/sim_log.txt",
        "COMPILATION ERROR:\n"
        "/mnt/d/Projects/STITCH/results/new_illustrations/adder_with_overflow/results_stitch/gemma3_4b/baseline/adder_with_overflow/iter_2/adder_with_overflow.v:1: error: Variable declaration in unnamed block requires SystemVerilog.",
    ),
    (
        "adder_with_overflow/gemma3:4b/baseline iter_3  (byte-identical repeat of iter_2's raw text)",
        "phase0/results/new_illustrations/adder_with_overflow/results_stitch/gemma3_4b/baseline/adder_with_overflow/iter_3/sim_log.txt",
        "COMPILATION ERROR:\n"
        "/mnt/d/Projects/STITCH/results/new_illustrations/adder_with_overflow/results_stitch/gemma3_4b/baseline/adder_with_overflow/iter_3/adder_with_overflow.v:1: error: Variable declaration in unnamed block requires SystemVerilog.",
    ),
    (
        "decoder_3to8/gemma3:4b/sem_adv iter_1  (SIMULATION failure, logic class -- must not collapse with any COMPILATION example above)",
        "phase0/results/decoder_smoke/results_stitch/gemma3_4b/sem_adv/decoder_3to8/iter_1/sim_log.txt",
        "SIMULATION FAILED:\n"
        "FAIL en=0 in=0: got 00000001, exp 00000000\n"
        "FAIL en=0 in=1: got 00000010, exp 00000000\n"
        "FAIL en=0 in=3: got 00001000, exp 00000000\n"
        "FAIL en=0 in=5: got 00100000, exp 00000000\n"
        "FAIL en=0 in=7: got 10000000, exp 00000000\n"
        "FAIL en=0 in=2: got 00000100, exp 00000000\n"
        "FAIL: 6 test(s) failed\n"
        "/mnt/d/Projects/STITCH/results/decoder_smoke/results_stitch/gemma3_4b/sem_adv/decoder_3to8/iter_1/decoder_3to8_tb.v:67: $finish called at 160 (1s)",
    ),
    (
        "instr_decode_unit/gemma3:4b/baseline iter_1  (same root syntax error as iter_3 below, cascades to a tb duplicate-decl error; exact-prefix excerpt: real file has 16 error lines, first 5 shown)",
        "phase0/results/new_illustrations/instr_decode_unit/results_stitch/gemma3_4b/baseline/instr_decode_unit/iter_1/sim_log.txt",
        "COMPILATION ERROR:\n"
        "/mnt/d/Projects/STITCH/results/new_illustrations/instr_decode_unit/results_stitch/gemma3_4b/baseline/instr_decode_unit/iter_1/instr_decode_unit.v:17: syntax error\n"
        "/mnt/d/Projects/STITCH/results/new_illustrations/instr_decode_unit/results_stitch/gemma3_4b/baseline/instr_decode_unit/iter_1/instr_decode_unit.v:19: Syntax in assignment statement l-value.\n"
        "/mnt/d/Projects/STITCH/results/new_illustrations/instr_decode_unit/results_stitch/gemma3_4b/baseline/instr_decode_unit/iter_1/instr_decode_unit.v:38: syntax error\n"
        "/mnt/d/Projects/STITCH/results/new_illustrations/instr_decode_unit/results_stitch/gemma3_4b/baseline/instr_decode_unit/iter_1/instr_decode_unit_tb.v:22: error: Invalid module item.\n"
        "/mnt/d/Projects/STITCH/results/new_illustrations/instr_decode_unit/results_stitch/gemma3_4b/baseline/instr_decode_unit/iter_1/instr_decode_unit_tb.v:23: error: 'instr' has already been declared in this scope.",
    ),
    (
        "instr_decode_unit/gemma3:4b/baseline iter_3  (SAME root cause as iter_1, tail cascade differs -- window collapses them; exact-prefix excerpt: real file has 19 error lines, first 5 shown)",
        "phase0/results/new_illustrations/instr_decode_unit/results_stitch/gemma3_4b/baseline/instr_decode_unit/iter_3/sim_log.txt",
        "COMPILATION ERROR:\n"
        "/mnt/d/Projects/STITCH/results/new_illustrations/instr_decode_unit/results_stitch/gemma3_4b/baseline/instr_decode_unit/iter_3/instr_decode_unit.v:17: syntax error\n"
        "/mnt/d/Projects/STITCH/results/new_illustrations/instr_decode_unit/results_stitch/gemma3_4b/baseline/instr_decode_unit/iter_3/instr_decode_unit.v:19: Syntax in assignment statement l-value.\n"
        "/mnt/d/Projects/STITCH/results/new_illustrations/instr_decode_unit/results_stitch/gemma3_4b/baseline/instr_decode_unit/iter_3/instr_decode_unit.v:40: syntax error\n"
        "/mnt/d/Projects/STITCH/results/new_illustrations/instr_decode_unit/results_stitch/gemma3_4b/baseline/instr_decode_unit/iter_3/instr_decode_unit.v:41: error: Invalid module item.\n"
        "/mnt/d/Projects/STITCH/results/new_illustrations/instr_decode_unit/results_stitch/gemma3_4b/baseline/instr_decode_unit/iter_3/instr_decode_unit.v:42: syntax error",
    ),
]


def main():
    rows = []
    for label, source, raw in EXAMPLES:
        err_type = classify_error(raw)
        sig = error_signature("iverilog", raw, err_type)
        rows.append((label, source, raw, err_type, sig))

    for i, (label, source, raw, err_type, sig) in enumerate(rows, 1):
        print(f"\n{'='*100}")
        print(f"[{i}] {label}")
        print(f"    source: {source}")
        print(f"    err_type (classify_error, unmodified): {err_type}")
        print(f"    RAW:")
        for line in raw.splitlines():
            print(f"      {line}")
        print(f"    SIGNATURE:")
        print(f"      {sig}")

    print(f"\n{'='*100}")
    print("SAME-SIGNATURE PAIRS (should be genuinely the same stuck failure):")
    for i in range(len(rows)):
        for j in range(i + 1, len(rows)):
            if rows[i][4] == rows[j][4]:
                print(f"  [{i+1}] == [{j+1}]  ({rows[i][0]}  <=>  {rows[j][0]})")


if __name__ == "__main__":
    main()
