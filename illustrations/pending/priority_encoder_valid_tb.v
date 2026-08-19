// priority_encoder_valid_tb.v
// 8-to-3 priority encoder with a validity flag.
//   pos   = index of the HIGHEST set bit of req (bit 7 highest priority)
//   valid = 1 when any req bit is set, 0 when req == 8'b0
//
// LLM failure mode this targets:
//   casez (req)
//     8'b1???????: pos = 3'd7;      <-- 'valid' not assigned on this path
//     ...
//     default: begin pos = 3'd0; valid = 1'b0; end   <-- default IS present
//   endcase
// The default branch satisfies SYSTEM_PROMPT rule 3, so the prompt does not
// pre-empt the bug. 'valid' is still unassigned on eight of nine paths, so
// Yosys infers a latch on it: once req goes non-zero, valid holds 0 forever
// (or holds whatever it last had), because nothing ever drives it high.
//
// Yosys:     "Latch inferred for signal `\valid'"
// Expected from Verilator: silent -- the case is complete and valid is both driven and read
// iverilog:  FAIL lines on every non-zero req vector, with no cause given
`timescale 1ns/1ps
module priority_encoder_valid_tb;
    reg  [7:0] req;
    wire [2:0] pos;
    wire       valid;
    integer    errors = 0;

    priority_encoder_valid dut(.req(req), .pos(pos), .valid(valid));

    task check(input [7:0] treq, input [2:0] epos, input eval,
               input [127:0] name);
        begin
            req = treq; #10;
            if (valid !== eval) begin
                $display("FAIL %0s: req=%b valid got %b expected %b",
                          name, treq, valid, eval);
                errors = errors + 1;
            end
            // pos is only meaningful when a request is active
            if (eval === 1'b1 && pos !== epos) begin
                $display("FAIL %0s: req=%b pos got %b expected %b",
                          name, treq, pos, epos);
                errors = errors + 1;
            end
        end
    endtask

    initial begin
        // ---- No request: valid must be 0 -------------------------------
        check(8'b0000_0000, 3'd0, 1'b0, "no_request");

        // ---- Single request at each position: valid must be 1 ----------
        check(8'b0000_0001, 3'd0, 1'b1, "only_bit0");
        check(8'b0000_0010, 3'd1, 1'b1, "only_bit1");
        check(8'b0000_0100, 3'd2, 1'b1, "only_bit2");
        check(8'b0000_1000, 3'd3, 1'b1, "only_bit3");
        check(8'b0001_0000, 3'd4, 1'b1, "only_bit4");
        check(8'b0010_0000, 3'd5, 1'b1, "only_bit5");
        check(8'b0100_0000, 3'd6, 1'b1, "only_bit6");
        check(8'b1000_0000, 3'd7, 1'b1, "only_bit7");

        // ---- Multiple requests: highest bit wins, valid stays 1 --------
        check(8'b1000_0001, 3'd7, 1'b1, "bit7_over_bit0");
        check(8'b0011_0000, 3'd5, 1'b1, "bit5_over_bit4");
        check(8'b0000_0111, 3'd2, 1'b1, "bit2_over_low");
        check(8'b1111_1111, 3'd7, 1'b1, "all_set");

        // ---- Toggle back to idle and out again -------------------------
        // A latched 'valid' shows up here: it holds its previous level
        // instead of tracking req.
        check(8'b0000_0000, 3'd0, 1'b0, "back_to_idle");
        check(8'b0000_1000, 3'd3, 1'b1, "reassert_bit3");
        check(8'b0000_0000, 3'd0, 1'b0, "idle_again");

        if (errors == 0) $display("ALL TESTS PASSED");
        else             $display("FAIL: %0d test(s) failed", errors);
        $finish;
    end
endmodule
