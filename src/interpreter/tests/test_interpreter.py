"""
tests/test_interpreter.py — unit tests for the three interpreter fixes in
stitch_interpreter.py, the module shared by both the local Windows runner
(AutoChipAdvFB/autochip_stitch_runner.py) and the HPC port
(HPC/stitch_runner_hpc.py):
  Fix 1: signal-name extraction must not fabricate names from numeric literals
  Fix 2: UNDRIVEN must disambiguate "output never assigned" vs "never declared"
  Fix 3: directive persistence is a per-runner loop change (feedback.txt),
         not part of the shared module — sanity-checked separately by
         re-running a real iteration (Phase B), not here.

Tests the shared module directly rather than through either runner, since
that's the actual unit of behavior both runners now depend on identically.

Run with:  python -m pytest tests/test_interpreter.py -v
       or: python -m unittest tests.test_interpreter -v
"""

import importlib.util
import sys
import unittest
from pathlib import Path

_HERE = Path(__file__).resolve().parent
_INTERPRETER_PATH = _HERE.parent / "stitch_interpreter.py"

spec = importlib.util.spec_from_file_location("stitch_interpreter", _INTERPRETER_PATH)
stitch = importlib.util.module_from_spec(spec)
sys.modules["stitch_interpreter"] = stitch
spec.loader.exec_module(stitch)


class TestExtractSignalName(unittest.TestCase):
    """Fix 1: numeric-literal fragments must never be extracted as signal names."""

    def test_hex_literal_fragment_rejected(self):
        line = "%Warning-WIDTHEXPAND: file.v:12: Assign RHS's CONST generates value 8'h00"
        self.assertIsNone(stitch._extract_signal_name(line))

    def test_binary_literal_fragment_rejected(self):
        line = "%Warning-WIDTHTRUNC: file.v:9: Operand width mismatch, value 4'b1010"
        self.assertIsNone(stitch._extract_signal_name(line))

    def test_hex_literal_fragment_rejected_longer(self):
        line = "%Warning-WIDTHEXPAND: file.v:14: Constant does not fit, saw 16'hDEAD"
        self.assertIsNone(stitch._extract_signal_name(line))

    def test_quoted_hex_literal_rejected(self):
        # The quoted-extraction path must also reject a base-specifier fragment
        # if it ends up bounded by quote-like characters.
        line = "%Warning-WIDTHEXPAND: file.v:12: value '8'h00' does not fit target"
        self.assertIsNone(stitch._extract_signal_name(line))

    def test_real_signal_data_bus_extracted(self):
        line = "%Warning-UNDRIVEN: file.v:5: Signal is not driven: data_bus"
        self.assertEqual(stitch._extract_signal_name(line), "data_bus")

    def test_real_signal_wr_en_extracted(self):
        line = "%Warning-UNUSEDSIGNAL: file.v:7: Signal is not used: wr_en"
        self.assertEqual(stitch._extract_signal_name(line), "wr_en")

    def test_real_signal_q_reg_quoted_extracted(self):
        line = "%Warning-MULTIDRIVEN: file.v:3: Signal 'q_reg' has multiple drivers"
        self.assertEqual(stitch._extract_signal_name(line), "q_reg")

    def test_real_signal_starting_with_d_not_confused_for_literal(self):
        # 'data_bus' starts with 'd' (a base-specifier letter) but is not
        # hex-digit-shaped after it — must NOT be treated as a literal fragment.
        line = "%Warning-UNDRIVEN: file.v:2: Signal is not driven: data_bus"
        sig = stitch._extract_signal_name(line)
        self.assertEqual(sig, "data_bus")
        self.assertFalse(stitch._LITERAL_FRAGMENT_RE.match(sig))

    def test_no_match_returns_none(self):
        line = "%Warning-UNDRIVEN: file.v:1: (no parseable signal here)"
        self.assertIsNone(stitch._extract_signal_name(line))

    def test_real_signal_oe_not_rejected_as_octal_fragment(self):
        """2026-08-18 production bug: 'oe' (output enable) was silently
        swallowed by _LITERAL_FRAGMENT_RE because 'o' is an octal base
        specifier and 'e' is a hex digit. This is the VERBATIM line from a
        real gemma3:4b run on mux4_oe whose UNUSEDSIGNAL directive never
        reached the model as a result."""
        line = (
            "%Warning-UNUSEDSIGNAL: /mnt/d/BITS Files/Year 3/3-2/LLM_Verilog "
            "Project/AgenticAI/STITCH_v3/results/probes/gated_port_sweep_"
            "gemma3-4b/results_stitch/gemma3_4b/sem_adv/mux4_oe/iter_1/"
            "mux4_oe.v:2:9: Signal is not used: 'oe'"
        )
        self.assertEqual(stitch._extract_signal_name(line), "oe")

    def test_real_signals_that_look_hex_shaped_are_accepted(self):
        """Same bug class: every one of these is an ordinary Verilog
        identifier that the old shape-only guard rejected outright."""
        for sig in ("oe", "bcd", "be", "de", "da", "dead"):
            line = f"%Warning-UNUSEDSIGNAL: file.v:2:9: Signal is not used: '{sig}'"
            self.assertEqual(
                stitch._extract_signal_name(line), sig,
                f"real identifier '{sig}' must not be treated as a literal fragment",
            )

    def test_literal_fragment_still_rejected_by_context(self):
        """The guard must still reject genuine literal fragments — these sit
        directly after a sized-literal apostrophe, which is the real
        discriminator the shape test was standing in for."""
        self.assertIsNone(stitch._extract_signal_name(
            "%Warning-WIDTHEXPAND: file.v:12: value '8'h00' does not fit target"))
        self.assertIsNone(stitch._extract_signal_name(
            "%Warning-WIDTHTRUNC: file.v:9: Operand width mismatch, value 4'b1010"))

    def test_unusedsignal_oe_produces_a_directive_end_to_end(self):
        """Full integration on the real captured Verilator text: the whole
        point is that a directive is actually produced, not silently dropped."""
        raw = (
            "%Warning-WIDTHEXPAND: file.v:14:20: Operator ASSIGN expects 8 bits "
            "on the Assign RHS, but Assign RHS's CONST '1'bz' generates 1 bits.\n"
            "%Warning-UNUSEDSIGNAL: file.v:2:9: Signal is not used: 'oe'\n"
            "%Error: Exiting due to 2 warning(s)\n"
        )
        text, codes = stitch.interpret_verilator(raw, v_path=None)
        self.assertIn("UNUSEDSIGNAL", codes)
        self.assertIn("oe", text)


class TestUndrivenDisambiguation(unittest.TestCase):
    """Fix 2: UNDRIVEN must tell 'output never assigned' apart from 'never declared'."""

    def test_path_a_output_port_never_assigned(self):
        # Real short snippet in the style of a v2 decoder case: 'out' is a
        # declared output that some path through the always block never sets.
        source = """
        module decoder_3to8 (
            input enable,
            input [2:0] in,
            output reg [7:0] out
        );
        always @(*) begin
            if (enable) begin
                case (in)
                    3'd0: out = 8'b0000_0001;
                endcase
            end
        end
        endmodule
        """
        result = stitch._classify_undriven_signal("out", source)
        self.assertEqual(result, "output_port")
        msg = stitch._undriven_message("out", source)
        self.assertIn("never assigned", msg)
        self.assertNotIn("never declared", msg)

    def test_path_b_identifier_never_declared(self):
        # Real bug pattern from simple_cpu_alu / llama3.1:latest / sem_adv:
        # 'B' is read in the body but was dropped from the port list entirely.
        source = """
        module simple_cpu_alu (
            input [3:0] A,
            input [1:0] op,
            output reg [3:0] result,
            output wire zero
        );
        always @(*) begin
            case (op)
                2'b00: result = A + B;
                2'b01: result = A - B;
                default: result = 4'b0;
            endcase
        end
        assign zero = (result == 4'b0000);
        endmodule
        """
        result = stitch._classify_undriven_signal("B", source)
        self.assertEqual(result, "undeclared")
        msg = stitch._undriven_message("B", source)
        self.assertIn("never declared", msg.lower())
        self.assertIn("add it to the port list", msg.lower())
        # Must NOT tell the model to just add an assignment to B, which is
        # the wrong fix and is exactly what caused the original stall.
        self.assertNotIn("Add an assignment: 'B", msg)

    def test_ambiguous_when_no_source_given(self):
        result = stitch._classify_undriven_signal("X", None)
        self.assertEqual(result, "ambiguous")
        msg = stitch._undriven_message("X", None)
        self.assertIn("Check BOTH possibilities", msg)

    def test_input_port_is_ambiguous_not_output(self):
        # An UNDRIVEN firing on something that's actually an input port is a
        # third, weirder case — must not be misclassified as 'output_port'.
        source = """
        module foo (
            input clk, rst,
            output reg y
        );
        endmodule
        """
        result = stitch._classify_undriven_signal("clk", source)
        self.assertEqual(result, "ambiguous")


class TestInterpretVerilatorIntegration(unittest.TestCase):
    """Sanity check that interpret_verilator wires the fixes together correctly."""

    def test_widthexpand_with_literal_fragment_is_skipped_entirely(self):
        raw = "%Warning-WIDTHEXPAND: file.v:12: Assign RHS's CONST generates value 8'h00\n"
        text, codes = stitch.interpret_verilator(raw, v_path=None)
        # No trustworthy signal name -> this code contributes nothing, rather
        # than a directive naming a fake signal.
        self.assertEqual(codes, [])
        self.assertEqual(text, "")

    def test_combdly_grabbing_generic_prose_word_rejected_via_source_crosscheck(self):
        # Real regression found against actual sync_fifo_8/llama3.1 output:
        # Verilator's own message ends in the word "process" (not a signal),
        # and the fallback regex happily extracted it. Only catchable by
        # cross-checking against real source, since "process" isn't
        # numeric-literal-shaped.
        raw = (
            "%Warning-COMBDLY: file.v:46:10: Non-blocking assignment '<=' "
            "in combinational logic process\n"
        )
        source = """
        module sync_fifo_8 (input clk, output reg full);
        always @(*) begin
            full <= 1'b1;
        end
        endmodule
        """
        import tempfile, os as _os
        with tempfile.NamedTemporaryFile("w", suffix=".v", delete=False, encoding="utf-8") as f:
            f.write(source)
            tmp_path = f.name
        try:
            text, codes = stitch.interpret_verilator(raw, v_path=tmp_path)
            self.assertEqual(codes, [])
            self.assertEqual(text, "")
        finally:
            _os.unlink(tmp_path)

    def test_undriven_with_real_signal_and_no_source_falls_back_to_ambiguous(self):
        raw = "%Warning-UNDRIVEN: file.v:5: Signal is not driven: data_bus\n"
        text, codes = stitch.interpret_verilator(raw, v_path=None)
        self.assertEqual(codes, ["UNDRIVEN"])
        self.assertIn("Check BOTH possibilities", text)


class TestYosysLatchDetection(unittest.TestCase):
    """Regression tests for the false-positive bug found 2026-08-17: the old
    runner-side _LATCH_KEYWORDS substring check matched the Yosys pass-name
    banner and the negative 'No latch inferred' message, both without a real
    latch present. detect_yosys_latches/has_latches replace that with an
    anchored regex.

    A second, subtler bug was found the same day while re-verifying against
    REAL captured Yosys 0.33 output rather than synthetic examples: the
    first fix assumed a "Warning:" prefix on the positive message. Real
    Yosys 0.33 doesn't put one there (unlike the comb-loop message, which
    genuinely is Warning-class) — and the first fix's optional
    hierarchical-name group was unbounded, so it could run past the
    intended field into unrelated text later in the same line. Both are
    covered below with the real captured strings, not just the flat
    synthetic ones the first round of tests used (which happened to avoid
    both bugs and passed by accident)."""

    def test_latch_pass_banner_does_not_false_positive(self):
        """Yosys pass banner must not be mistaken for a latch warning."""
        output = (
            "\n2.14. Executing PROC_DLATCH pass (convert process syncs to latches).\n"
            "No latch inferred for signal `\\out' from process `$proc$foo.v:9$1'.\n"
        )
        self.assertEqual(stitch.detect_yosys_latches(output), [])
        self.assertFalse(stitch.has_latches(output))

    def test_latch_negative_message_does_not_false_positive(self):
        """'No latch inferred' must not match the positive latch pattern."""
        output = "No latch inferred for signal `\\out' from process `$proc$foo.v:9$1'."
        self.assertEqual(stitch.detect_yosys_latches(output), [])

    def test_latch_real_warning_matches(self):
        """Real Yosys latch warning (flat name, with 'Warning:' prefix) should be detected."""
        output = "Warning: Latch inferred for signal `\\out' from process `$proc$foo.v:9$1'."
        self.assertEqual(stitch.detect_yosys_latches(output), ["out"])
        self.assertTrue(stitch.has_latches(output))

    def test_latch_multiple_signals(self):
        output = (
            "\nWarning: Latch inferred for signal `\\out_a' from process `$proc$foo.v:9$1'.\n"
            "Warning: Latch inferred for signal `\\out_b' from process `$proc$foo.v:12$2'.\n"
        )
        self.assertEqual(stitch.detect_yosys_latches(output), ["out_a", "out_b"])

    def test_latch_real_yosys033_no_warning_prefix(self):
        """Real Yosys 0.33 output, captured verbatim from mode_mux_latch/broken.v:
        no 'Warning:' prefix at all — must still be detected as a genuine
        positive. This is the exact case the first-round fix missed."""
        output = (
            "Latch inferred for signal `\\mode_mux_latch.\\out' from process "
            "`\\mode_mux_latch.$proc$broken.v:9$1': $auto$proc_dlatch.cc:427:proc_dlatch$29"
        )
        self.assertEqual(stitch.detect_yosys_latches(output), ["out"])
        self.assertTrue(stitch.has_latches(output))

    def test_latch_hierarchical_name_does_not_overrun_into_later_text(self):
        """The module-qualifier group must not be greedy enough to cross into
        unrelated text later in the line (e.g. a '.' inside a file path) —
        this exact input previously extracted the wrong signal name."""
        output = (
            "Latch inferred for signal `\\decoder_3to8.\\out' from process "
            "`\\decoder_3to8.$proc$sem_adv_iter2_fixed.v:7$1'."
        )
        self.assertEqual(stitch.detect_yosys_latches(output), ["out"])

    def test_real_decoder_3to8_sem_adv_negative_yosys_regressed_in_production(self):
        """2026-08-18: this exact string is what actually reached the model in
        decoder_3to8's sem_adv iter_2 feedback.txt, captured verbatim from
        that real run, AFTER the Yosys path-quoting fix made Yosys actually
        run for the first time in this project's history. detect_yosys_latches
        (this function) correctly returned [] against it — the false
        "*** YOSYS: LATCH INFERRED for signal(s) 'out' ***" directive the
        model actually received came from illustration_runner.py's own
        separate, still-duplicate _LATCH_KEYWORDS check at the time, not from
        this function. Kept as a regression test now that the runner calls
        this function directly instead of maintaining its own copy."""
        output = (
            "2.2.8. Executing PROC_DLATCH pass (convert process syncs to latches).\n"
            "No latch inferred for signal `\\decoder_3to8.\\out' from process "
            "`\\decoder_3to8.$proc$/mnt/d/BITS$20Files/Year$203/3-2/LLM_Verilog$20"
            "Project/AgenticAI/STITCH_v3/results/probes/decoder_verify_gemma3-4b/"
            "results_stitch/gemma3_4b/sem_adv/decoder_3to8/iter_1/decoder_3to8.v:7$1'.\n"
            "2.15.5. Executing MEMORY_DFF pass (merging $dff cells to $memrd).\n"
            "created 8 $dff cells and 0 static cells of width 8.\n"
            "read interface: 0 $dff and 7 $mux cells.\n"
            "Number of cells:                 13\n"
            "Number of cells:                 13\n"
        )
        self.assertEqual(stitch.detect_yosys_latches(output), [])
        self.assertFalse(stitch.has_latches(output))

    def test_real_priority_chain_comb_full_synth_no_latches(self):
        """Full real Yosys 0.33 output from priority_chain_comb's broken.v
        (528 lines, read from disk verbatim — a combinational-loop bug, not
        a latch bug). Contains the PROC_DLATCH pass banner plus three
        "found logic loop" warnings, but zero genuine latch lines anywhere.
        Confirms detect_yosys_latches() returns [] on real, large,
        unrelated-warning-bearing output, not just short synthetic strings."""
        fixture = _HERE / "fixtures" / "priority_chain_comb_yosys_synth.txt"
        if not fixture.exists():
            self.skipTest(f"fixture not found: {fixture}")
        real_output = fixture.read_text(encoding="utf-8", errors="ignore")
        self.assertIn("Executing PROC_DLATCH pass", real_output)
        self.assertIn("found logic loop", real_output)
        self.assertNotIn("Latch inferred for signal", real_output)
        self.assertEqual(stitch.detect_yosys_latches(real_output), [])
        self.assertFalse(stitch.has_latches(real_output))


class TestYosysCombLoopDetection(unittest.TestCase):
    """New coverage: combinational-loop warnings had zero interpreter support
    before this — no dict entry, no dedicated function, confirmed while
    verifying the priority_chain_comb illustration module."""

    def test_comb_loop_detected(self):
        output = (
            "\nWarning: found logic loop in module `\\priority_chain_comb':\n"
            "    cell `$logic_and$foo.v:14$3' port Y\n"
            "    cell `$logic_not$foo.v:11$5' port Y\n"
        )
        self.assertEqual(stitch.detect_comb_loops(output), ["priority_chain_comb"])
        directive = stitch.interpret_comb_loop(output)
        self.assertIsNotNone(directive)
        self.assertIn("priority_chain_comb", directive)
        self.assertIn("CRITICAL", directive)

    def test_comb_loop_none_when_absent(self):
        self.assertEqual(stitch.detect_comb_loops("some unrelated yosys output"), [])
        self.assertIsNone(stitch.interpret_comb_loop("some unrelated yosys output"))

    def test_comb_loop_combinational_variant(self):
        """Yosys sometimes says 'combinational loop' instead of 'logic loop'."""
        output = "Warning: found combinational loop in module `\\foo':"
        self.assertEqual(stitch.detect_comb_loops(output), ["foo"])


class TestUnusedSignalTemplateParameterisation(unittest.TestCase):
    """2026-08-18: the UNUSEDSIGNAL template hard-coded `out = 8'b0;` as its
    else-branch example. Correct by luck for decoder_3to8 and mux4_oe (both a
    single 8-bit output named `out`), wrong for anything else. The directive
    now reads the module's real output ports and substitutes name + width,
    falling back to the generic template (and logging) when they cannot be
    resolved."""

    MUX4_OE = """
    module mux4_oe (
        input oe, input [1:0] sel,
        input [7:0] a, b, c, d,
        output reg [7:0] out
    );
    endmodule
    """

    REG4 = """
    module reg4 (input clk, input load, input [3:0] d, output reg [3:0] q);
    endmodule
    """

    ACC32 = """
    module acc32 (input clk, input en, input [31:0] din, output reg [31:0] accum);
    endmodule
    """

    PARAM = """
    module preg #(parameter WIDTH = 8) (
        input clk, input load,
        input [WIDTH-1:0] d,
        output reg [WIDTH-1:0] q
    );
    endmodule
    """

    MULTI = """
    module cmp8_en (
        input en, input [7:0] a, input [7:0] b,
        output reg gt, output reg eq, output reg lt
    );
    endmodule
    """

    def test_mux4_oe_matches_previous_hardcoded_behaviour(self):
        """8-bit output named 'out' -> identical to the old hard-coded text."""
        self.assertEqual(stitch._output_ports(self.MUX4_OE), [("out", 8)])
        msg = stitch._unusedsignal_message("oe", self.MUX4_OE)
        self.assertIn("out = 8'b0;", msg)
        self.assertNotIn("or whatever your output signal is named", msg)

    def test_four_bit_register_uses_its_own_name_and_width(self):
        self.assertEqual(stitch._output_ports(self.REG4), [("q", 4)])
        msg = stitch._unusedsignal_message("load", self.REG4)
        self.assertIn("q = 4'b0;", msg)
        self.assertNotIn("8'b0", msg)

    def test_thirty_two_bit_accumulator_uses_its_own_name_and_width(self):
        self.assertEqual(stitch._output_ports(self.ACC32), [("accum", 32)])
        msg = stitch._unusedsignal_message("en", self.ACC32)
        self.assertIn("accum = 32'b0;", msg)
        self.assertNotIn("8'b0", msg)

    def test_parameterised_width_falls_back_and_logs(self):
        """Width is not a literal integer range -> generic template, logged."""
        self.assertEqual(stitch._output_ports(self.PARAM), [("q", None)])
        with self.assertLogs("stitch_interpreter", level="INFO") as captured:
            msg = stitch._unusedsignal_message("load", self.PARAM)
        self.assertIn("out = 8'b0;  // or whatever your output signal is named", msg)
        joined = "\n".join(captured.output)
        self.assertIn("fell back", joined)
        self.assertIn("parameterised", joined)

    def test_no_source_falls_back_and_logs(self):
        with self.assertLogs("stitch_interpreter", level="INFO") as captured:
            msg = stitch._unusedsignal_message("oe", None)
        self.assertIn("or whatever your output signal is named", msg)
        self.assertIn("no output port could be extracted", "\n".join(captured.output))

    def test_multiple_outputs_all_zeroed(self):
        """cmp8_en has three 1-bit outputs; the else branch must clear each."""
        self.assertEqual(stitch._output_ports(self.MULTI), [("gt", 1), ("eq", 1), ("lt", 1)])
        msg = stitch._unusedsignal_message("en", self.MULTI)
        for name in ("gt", "eq", "lt"):
            self.assertIn(f"{name} = 1'b0;", msg)

    def test_parse_width_edge_cases(self):
        self.assertEqual(stitch._parse_width(" reg [7:0] out"), 8)
        self.assertEqual(stitch._parse_width(" gt"), 1)
        self.assertEqual(stitch._parse_width(" reg [31:0] accum"), 32)
        self.assertIsNone(stitch._parse_width(" reg [WIDTH-1:0] q"))

    def test_end_to_end_through_interpret_verilator(self):
        """The parameterised directive must actually reach the caller."""
        import tempfile, os as _os
        raw = "%Warning-UNUSEDSIGNAL: file.v:2:9: Signal is not used: 'load'\n"
        with tempfile.NamedTemporaryFile("w", suffix=".v", delete=False, encoding="utf-8") as f:
            f.write(self.ACC32.replace("input en,", "input load,"))
            tmp = f.name
        try:
            text, codes = stitch.interpret_verilator(raw, v_path=tmp)
            self.assertEqual(codes, ["UNUSEDSIGNAL"])
            self.assertIn("accum = 32'b0;", text)
        finally:
            _os.unlink(tmp)


class TestLatchDirectiveStructureAware(unittest.TestCase):
    """interpret_yosys_latches must prescribe a repair that APPLIES to the
    module in front of it (2026-08-19, plan v4 section 7 item 7).

    The template it replaces emitted two options unconditionally --
    "add else to every if" and "add default to every case" -- plus a causal
    join asserting "this is why enable=0 returns the previous output".
    Against priority_encoder_valid/broken.v, whose casez already HAS a
    default, option B was a literal no-op, option A was inapplicable (no if
    exists), and the real repair (assign the signal in every branch, not only
    the default) was not offered at all. That shape is the one SYSTEM_PROMPT
    rule 3 steers models into, so it is not exotic.
    """

    LATCH_LINE = (
        r"Latch inferred for signal `\priority_encoder_valid.\valid' from "
        r"process `\priority_encoder_valid.$proc$broken.v:19$1': "
        r"$auto$proc_dlatch.cc:427:proc_dlatch$58"
    )

    # The exact shape of illustrations/pending/priority_encoder_valid/broken.v:
    # a compliant default, and 'valid' unassigned on every other branch.
    BROKEN_DEFAULT_PRESENT = """
module priority_encoder_valid (
    input      [7:0] req,
    output reg [2:0] pos,
    output reg       valid
);
    always @(*) begin
        casez (req)
            8'b1???????: pos = 3'd7;
            8'b01??????: pos = 3'd6;
            8'b001?????: pos = 3'd5;
            8'b0001????: pos = 3'd4;
            8'b00001???: pos = 3'd3;
            8'b000001??: pos = 3'd2;
            8'b0000001?: pos = 3'd1;
            8'b00000001: pos = 3'd0;
            default:     begin pos = 3'd0; valid = 1'b0; end
        endcase
    end
endmodule
"""

    NO_CASE_AT_ALL = """
module gated_flag (
    input      en,
    output reg valid
);
    always @(*) begin
        if (en) valid = 1'b1;
    end
endmodule
"""

    def _directive(self, source, line=None):
        import tempfile, os as _os
        with tempfile.NamedTemporaryFile("w", suffix=".v", delete=False,
                                         encoding="utf-8") as f:
            f.write(source)
            tmp = f.name
        try:
            return stitch.interpret_yosys_latches([line or self.LATCH_LINE], tmp)
        finally:
            _os.unlink(tmp)

    # -- required by task 2e, part 1: real captured Yosys output ------------

    def test_real_yosys_output_detects_valid_only(self):
        """Real captured synth log: the positive line for 'valid' is picked up
        and the negative line for 'pos' in the SAME output is rejected."""
        fixture = _HERE / "fixtures" / "priority_encoder_valid_yosys_synth.txt"
        raw = fixture.read_text(encoding="utf-8", errors="ignore")
        self.assertEqual(stitch.detect_yosys_latches(raw), ["valid"])

    def test_real_case_with_default_asks_for_per_branch_assignment(self):
        """The fix must be per-branch assignment, NOT 'add a default'."""
        fixture = _HERE / "fixtures" / "priority_encoder_valid_yosys_synth.txt"
        raw = fixture.read_text(encoding="utf-8", errors="ignore")
        latch_lines = [l for l in raw.splitlines() if stitch.detect_yosys_latches(l)]
        self.assertTrue(latch_lines)

        import tempfile, os as _os
        with tempfile.NamedTemporaryFile("w", suffix=".v", delete=False,
                                         encoding="utf-8") as f:
            f.write(self.BROKEN_DEFAULT_PRESENT)
            tmp = f.name
        try:
            d = stitch.interpret_yosys_latches(latch_lines, tmp)
        finally:
            _os.unlink(tmp)

        self.assertIn("EVERY branch of the case", d)
        self.assertIn("'valid'", d)
        # The no-op advice must be gone: this module already HAS a default.
        self.assertNotIn("Add a default branch", d)
        self.assertNotIn("default: valid = <safe value>;", d)
        # And it must count the branches that actually omit the signal.
        self.assertIn("8 branch(es)", d)

    # -- required by task 2e, part 2: no case statement ---------------------

    def test_no_case_statement_does_not_offer_the_default_fix(self):
        """Fix B must not appear for a module with no case statement."""
        d = self._directive(self.NO_CASE_AT_ALL)
        self.assertNotIn("Add a default branch", d)
        self.assertNotIn("endcase", d)
        self.assertIn("else", d)

    # -- the fabricated causal join ----------------------------------------

    def test_no_fabricated_enable_causal_join(self):
        """The old template asserted 'this is why enable=0 returns the
        previous output' regardless of whether an enable port existed."""
        for src in (self.BROKEN_DEFAULT_PRESENT, self.NO_CASE_AT_ALL):
            d = self._directive(src)
            self.assertNotIn("enable=0", d)
            self.assertIn("not\nassigned on every code path", d)

    # -- the remaining structural shapes ------------------------------------

    def test_case_without_default_but_branches_complete_asks_for_default(self):
        src = """
module m (input [1:0] s, output reg [1:0] pos, output reg valid);
    always @(*) begin
        case (s)
            2'd0: begin pos = 2'd0; valid = 1'b1; end
            2'd1: begin pos = 2'd1; valid = 1'b1; end
        endcase
    end
endmodule
"""
        d = self._directive(src)
        self.assertIn("Add a default branch", d)
        self.assertNotIn("EVERY branch of the case", d)

    def test_case_without_default_and_incomplete_branches_asks_for_both(self):
        """A default alone would not fix this -- a listed branch omits it too."""
        src = """
module m (input [1:0] s, output reg [1:0] pos, output reg valid);
    always @(*) begin
        case (s)
            2'd0: begin pos = 2'd0; valid = 1'b1; end
            2'd1: pos = 2'd1;
        endcase
    end
endmodule
"""
        d = self._directive(src)
        self.assertIn("Close BOTH gaps", d)
        self.assertIn("1 branch(es)", d)

    def test_bit_range_colons_do_not_split_branches(self):
        """[3:0] inside a case expression must not register as a branch label."""
        src = """
module m (input [3:0] s, output reg [7:0] d, output reg valid);
    always @(*) begin
        case (s[3:0])
            4'd0: d = 8'h00;
            4'd1: begin d = 8'h11; valid = 1'b1; end
            default: begin d = 8'hFF; valid = 1'b0; end
        endcase
    end
endmodule
"""
        d = self._directive(src)
        self.assertIn("1 branch(es)", d)

    def test_comment_prose_does_not_fool_the_parser(self):
        """A comment reading 'no default:' must not be seen as a branch."""
        src = """
module m (input [1:0] s, output reg [1:0] pos, output reg valid);
    always @(*) begin
        // no default: here, this is prose not code
        case (s)
            2'd0: pos = 2'd0;
            2'd1: begin pos = 2'd1; valid = 1'b1; end
        endcase
    end
endmodule
"""
        d = self._directive(src)
        self.assertIn("Close BOTH gaps", d)

    def test_no_source_falls_back_to_generic_advice_and_logs(self):
        """Without the module, give generic path advice -- never assert a
        structure that was never inspected."""
        with self.assertLogs("stitch_interpreter", level="INFO") as cm:
            d = stitch.interpret_yosys_latches([self.LATCH_LINE])
        self.assertIn("assigned on EVERY path", d)
        self.assertNotIn("endcase", d)
        self.assertTrue(any("fell back to generic advice" in m for m in cm.output))

    def test_multiple_latched_signals_are_all_named(self):
        line2 = (
            r"Latch inferred for signal `\m.\ready' from process "
            r"`\m.$proc$b.v:9$1': $auto$proc_dlatch"
        )
        d = stitch.interpret_yosys_latches([self.LATCH_LINE, line2])
        self.assertIn("'valid'", d)
        self.assertIn("'ready'", d)
        self.assertIn("Apply the same repair to 'ready'", d)

    def test_empty_input_returns_empty_string(self):
        self.assertEqual(stitch.interpret_yosys_latches([]), "")


if __name__ == "__main__":
    unittest.main(verbosity=2)
