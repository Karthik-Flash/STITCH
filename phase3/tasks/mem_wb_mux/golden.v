`timescale 1ns / 1ps
module mem_wb_mux(input [1:0] ex_mem_FWD_RS2, input ex_mem_memwrite, input [31:0] ex_mem_output_data_2,
                  input memtoreg, input [31:0] read_data, input [31:0] result,
                  output reg [31:0] write_data1, output reg [31:0] write_data2);
  always @(*) begin
    write_data1 = memtoreg ? read_data : result;
    write_data2 = ex_mem_output_data_2;
    if (ex_mem_memwrite && (ex_mem_FWD_RS2 == 2'b10 || ex_mem_FWD_RS2 == 2'b01))
      write_data2 = result;
  end
endmodule
