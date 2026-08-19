// The DEFECT this candidate targets: 'overflow' is declared in the port list
// and never assigned anywhere in the module body. Verilator reports UNDRIVEN;
// the testbench sees x on every overflow check.
//
// Hand-written for the pre-screen. This is the defect shape the spec is
// designed to elicit from a weak model, not a captured model response.
module adder_with_overflow (
    input      [7:0] a,
    input      [7:0] b,
    output reg [7:0] sum,
    output reg       overflow
);
    always @(*) begin
        sum = a + b;
    end
endmodule
