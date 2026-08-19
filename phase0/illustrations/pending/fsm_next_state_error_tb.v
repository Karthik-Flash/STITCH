// fsm_next_state_error_tb.v
// 2-state FSM: IDLE = 1'b0, ACTIVE = 1'b1.
//   posedge clk, rst high  -> state <= IDLE
//   posedge clk, go high   -> state <= ACTIVE
//   posedge clk, go low    -> state <= IDLE
//   error                  -> no error condition is ever exercised here, so it
//                             must read 1'b0 throughout
//
// On the 'error' expectation: the spec deliberately names 'error' as an output
// port without defining when it asserts. The only defensible expectation is
// therefore that it stays deasserted during legal operation -- which is what
// this testbench drives and checks. A model that assigns error at all passes;
// a model that leaves it undriven reads x and fails. No vector requires the
// model to guess an undefined error semantics.
//
// LLM failure mode this targets:
//   always @(posedge clk) begin
//     if (rst) state <= 1'b0;
//     else     state <= go;     <-- 'error' never assigned anywhere
//   end
// Expected from Verilator: "Signal is not driven: 'error'" (UNDRIVEN)
// iverilog:  FAIL on every error check, with state correct throughout
//
// The oracle uses !== so an undriven x is caught rather than silently
// comparing unknown against 0.
`timescale 1ns/1ps
module fsm_next_state_error_tb;
    reg  clk = 1'b0;
    reg  rst, go;
    wire state, error;
    integer errors = 0;

    fsm_next_state_error dut(.clk(clk), .rst(rst), .go(go),
                             .state(state), .error(error));

    always #5 clk = ~clk;

    // Sample midway between edges so the check sees settled values.
    task step(input tgo, input estate, input [255:0] name);
        begin
            go = tgo;
            @(posedge clk);
            #1;
            if (state !== estate) begin
                $display("FAIL %0s: go=%b state got %b expected %b",
                          name, tgo, state, estate);
                errors = errors + 1;
            end
            if (error !== 1'b0) begin
                $display("FAIL %0s: go=%b error got %b expected 0",
                          name, tgo, error);
                errors = errors + 1;
            end
        end
    endtask

    initial begin
        // ---- Reset ------------------------------------------------------
        rst = 1'b1; go = 1'b0;
        @(posedge clk); #1;
        if (state !== 1'b0) begin
            $display("FAIL reset: state got %b expected 0", state);
            errors = errors + 1;
        end
        if (error !== 1'b0) begin
            $display("FAIL reset: error got %b expected 0", error);
            errors = errors + 1;
        end
        rst = 1'b0;

        // ---- IDLE -> ACTIVE on go ---------------------------------------
        step(1'b1, 1'b1, "idle_to_active");
        step(1'b1, 1'b1, "hold_active");

        // ---- ACTIVE -> IDLE on !go --------------------------------------
        step(1'b0, 1'b0, "active_to_idle");
        step(1'b0, 1'b0, "hold_idle");

        // ---- Toggle back and forth --------------------------------------
        step(1'b1, 1'b1, "reassert_go");
        step(1'b0, 1'b0, "deassert_go");
        step(1'b1, 1'b1, "reassert_go_2");

        // ---- Reset from ACTIVE ------------------------------------------
        rst = 1'b1;
        @(posedge clk); #1;
        if (state !== 1'b0) begin
            $display("FAIL reset_from_active: state got %b expected 0", state);
            errors = errors + 1;
        end
        if (error !== 1'b0) begin
            $display("FAIL reset_from_active: error got %b expected 0", error);
            errors = errors + 1;
        end
        rst = 1'b0;

        step(1'b1, 1'b1, "recover_after_reset");

        if (errors == 0) $display("ALL TESTS PASSED");
        else             $display("FAIL: %0d test(s) failed", errors);
        $finish;
    end
endmodule
