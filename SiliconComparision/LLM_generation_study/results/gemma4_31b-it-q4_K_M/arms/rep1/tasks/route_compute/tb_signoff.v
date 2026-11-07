// SIGN-OFF copy of golden/tb/tb_route_compute.v, made by scripts/make_tasks.py: seed + 1000.
`timescale 1ns/1ps
// route_compute: every flit type x every destination address x every router address (262,144 cases),
// with random values in the bits the routing must ignore.
module tb;
    reg  [31:0] flit;
    reg  [7:0]  current_address;
    wire [4:0]  req;
    reg  [4:0]  expected;
    integer t, d, c, errors = 0, cases = 0, seed = 1005;

    route_compute dut (.flit(flit), .current_address(current_address), .req(req));

    initial begin
        for (t = 0; t < 4; t = t + 1)
            for (d = 0; d < 256; d = d + 1)
                for (c = 0; c < 256; c = c + 1) begin
                    flit = $random(seed);
                    flit[30:29] = t;
                    flit[7:0] = d;
                    current_address = c;
                    #1;
                    if (t != 1)                     expected = 5'b00000;
                    else if (d[7:4] > c[7:4])       expected = 5'b00001;
                    else if (d[7:4] < c[7:4])       expected = 5'b00010;
                    else if (d[3:0] > c[3:0])       expected = 5'b00100;
                    else if (d[3:0] < c[3:0])       expected = 5'b01000;
                    else                            expected = 5'b10000;
                    cases = cases + 1;
                    if (req !== expected) begin
                        errors = errors + 1;
                        if (errors <= 10)
                            $display("FAIL: flit %h address %h: req %b, expected %b", flit, current_address, req, expected);
                    end
                end
        if (errors == 0) $display("ALL TESTS PASSED (%0d cases)", cases);
        else $display("FAIL: %0d of %0d cases wrong", errors, cases);
        $finish;
    end
endmodule
