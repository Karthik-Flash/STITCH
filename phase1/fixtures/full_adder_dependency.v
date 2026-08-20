module full_adder (
    input a,
    input b,
    input cin,
    output wire sum,   // Changed from reg to wire
    output wire cout   // Changed from reg to wire
);

    // Continuous assignment requires 'wire' outputs
    assign {cout, sum} = a + b + cin;

endmodule