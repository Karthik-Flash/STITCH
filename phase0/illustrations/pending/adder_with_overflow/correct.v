// Reference implementation for the adder_with_overflow illustration candidate.
// Not model output -- this exists so the testbench oracle can be verified
// independently of any LLM run.
module adder_with_overflow (
    input      [7:0] a,
    input      [7:0] b,
    output reg [7:0] sum,
    output reg       overflow
);
    always @(*) begin
        {overflow, sum} = a + b;
    end
endmodule
