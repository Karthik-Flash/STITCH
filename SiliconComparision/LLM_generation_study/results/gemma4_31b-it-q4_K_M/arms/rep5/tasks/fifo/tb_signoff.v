// SIGN-OFF copy of golden/tb/tb_fifo.v, made by scripts/make_tasks.py: seed + 1000, twice the traffic.
`timescale 1ns/1ps
// fifo: random writes and reads against a queue model; checks dout, empty and almost_full every cycle,
// including writes when full and reads when empty (both ignored).
module tb;
    reg clk = 0, reset = 1, wr_en = 0, rd_en = 0;
    reg  [31:0] din = 0;
    wire [31:0] dout;
    wire empty, almost_full;

    fifo dut (.clk(clk), .reset(reset), .wr_en(wr_en), .din(din), .rd_en(rd_en),
              .dout(dout), .empty(empty), .almost_full(almost_full));

    always #5 clk = ~clk;

    reg [31:0] q [0:3];
    integer head = 0, count = 0, errors = 0, cyc, wr_full = 0, rd_empty = 0, seed = 1011;

    task check;
        begin
            if (empty !== (count == 0)) begin
                errors = errors + 1; $display("FAIL cycle %0d: empty=%b, model count %0d", cyc, empty, count);
            end
            if (almost_full !== (count >= 3)) begin
                errors = errors + 1; $display("FAIL cycle %0d: almost_full=%b, model count %0d", cyc, almost_full, count);
            end
            if (count > 0 && dout !== q[head]) begin
                errors = errors + 1; $display("FAIL cycle %0d: dout=%h, expected %h", cyc, dout, q[head]);
            end
        end
    endtask

    initial begin
        repeat (3) @(negedge clk);
        reset = 0;
        for (cyc = 0; cyc < 40000; cyc = cyc + 1) begin
            @(negedge clk);
            check;
            // bias the traffic so the buffer spends time both full and empty
            if ((cyc / 500) % 2 == 0) begin
                wr_en = ($random(seed) % 4) != 0; rd_en = ($random(seed) % 4) == 0;
            end else begin
                wr_en = ($random(seed) % 4) == 0; rd_en = ($random(seed) % 4) != 0;
            end
            din = $random(seed);
            if (cyc == 10000) begin       // reset in mid-run empties the buffer
                reset = 1; @(posedge clk); count = 0; head = 0; @(negedge clk); reset = 0; check;
            end
            @(posedge clk);
            if (wr_en && count == 4) wr_full = wr_full + 1;
            if (rd_en && count == 0) rd_empty = rd_empty + 1;
            if (rd_en && count > 0 && !(wr_en && count == 4)) begin
                head = (head + 1) % 4; count = count - 1;
                if (wr_en) begin q[(head + count) % 4] = din; count = count + 1; end
            end else if (rd_en && count > 0) begin
                head = (head + 1) % 4; count = count - 1;
            end else if (wr_en && count < 4) begin
                q[(head + count) % 4] = din; count = count + 1;
            end
        end
        if (wr_full == 0 || rd_empty == 0) begin
            errors = errors + 1; $display("FAIL: corner cases not reached (writes when full %0d, reads when empty %0d)", wr_full, rd_empty);
        end
        if (errors == 0) $display("ALL TESTS PASSED (%0d cycles, %0d writes when full, %0d reads when empty)", cyc, wr_full, rd_empty);
        else $display("FAIL: %0d errors", errors);
        $finish;
    end
endmodule
