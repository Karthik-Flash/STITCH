// Reference implementation for the fsm_next_state_error illustration
// candidate. 'error' is driven on every path -- the spec never defines an
// error condition, so holding it deasserted is the only defensible reading.
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
            error <= 1'b0;
        end else begin
            if (go) state <= 1'b1;
            else    state <= 1'b0;
            error <= 1'b0;
        end
    end
endmodule
