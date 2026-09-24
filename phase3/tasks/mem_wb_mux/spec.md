Module `mem_wb_mux` -- write-back / store-data forwarding mux of a RISC-V pipeline (combinational).
Ports (keep exactly): input [1:0] ex_mem_FWD_RS2; input ex_mem_memwrite; input [31:0] ex_mem_output_data_2;
input memtoreg; input [31:0] read_data, result; output reg [31:0] write_data1, write_data2.
write_data1 = read_data when memtoreg==1, else result.
write_data2 = result when ex_mem_memwrite==1 and ex_mem_FWD_RS2 is 2'b10 or 2'b01;
write_data2 = ex_mem_output_data_2 in every other case.
