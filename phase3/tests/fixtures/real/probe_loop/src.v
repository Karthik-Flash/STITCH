module loop_t(input a, output y);
  wire n1, n2;
  assign n1 = a & n2;
  assign n2 = ~n1;
  assign y = n2;
endmodule
