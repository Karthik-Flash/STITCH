// The DEFECT this candidate targets: 'error' is declared in the port list and
// never assigned anywhere. The state machine itself is entirely correct, so
// the failure set isolates the target defect exactly.
//
// Expected from Verilator: "Signal is not driven: 'error'" (UNDRIVEN)
// iverilog:  every error check reads x
//
// Hand-written for the pre-screen. Defect shape the spec is designed to
// elicit, not a captured model response.
module fsm_next_state_error (
    input      clk,
    input      rst,
    input      go,
    output reg state,
    output reg error
);
    always @(posedge clk) begin
        if (rst) begin
            state <= 1'b0;
        end else begin
            if (go) state <= 1'b1;
            else    state <= 1'b0;
        end
    end
endmodule
