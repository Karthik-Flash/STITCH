`timescale 1ns / 1ps
module tb;
  reg [1:0] f; reg mw, mt; reg [31:0] d2, rd, res; wire [31:0] w1, w2; integer i, err;
  mem_wb_mux dut(.ex_mem_FWD_RS2(f), .ex_mem_memwrite(mw), .ex_mem_output_data_2(d2), .memtoreg(mt),
                 .read_data(rd), .result(res), .write_data1(w1), .write_data2(w2));
  initial begin
    err = 0;
    for (i = 0; i < 400; i = i + 1) begin
      d2 = $random; rd = $random; res = $random; mt = $random; mw = 1; f = i % 3; #5;
      if (w1 !== (mt ? rd : res)) begin err = err + 1; $display("FAIL w1"); end
      if (w2 !== ((f == 2 || f == 1) ? res : d2)) begin err = err + 1; $display("FAIL w2 f=%0d", f); end
    end
    if (err == 0) $display("ALL TESTS PASSED"); else $display("FAIL: %0d errors", err);
    $finish;
  end
endmodule
