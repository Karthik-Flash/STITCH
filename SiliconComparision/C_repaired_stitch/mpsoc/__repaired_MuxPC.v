module MuxPC(
    input wire   [31:0] next_address,
    input wire   [31:0] B_addr,
    input wire   [31:0] J_addr,
    input wire   [1:0] PCsrc,
    output reg  [31:0] input_to_ifu
);
    always @(*)
    begin
        case(PCsrc)
            2'b00  : input_to_ifu = next_address;
            2'b01  : input_to_ifu = J_addr;
            2'b10  : input_to_ifu = B_addr;
            default : input_to_ifu = 32'b0;   // default case
        endcase
    end
endmodule
